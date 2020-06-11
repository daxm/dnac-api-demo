import logging
from jinja2 import Template
import ipaddress
import common
from border_handoff import payload_templates as templates
from templates import workflow as template_flow
import yaml
import pkgutil

logger = logging.getLogger('main.border_handoff')


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def get_borders(api, workflow_dict):
    """ Retrieves fabric border details from DNA Center.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of sites (see schema.py);

    :returns: Nothing """

    _schema = 'border_ip.schema.border_handoff'
    logger.info('reports::get_borders')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # URI: (GET: list of VN IDs ONLY)
        uri = '/api/v2/data/customer-facing-service/VirtualNetwork'
        vn_db = api.custom_caller.call_api('GET', uri)
        # URI: (GET: list of VN Contexts to resolve VN names)
        uri = '/api/v2/data/customer-facing-service/virtualnetworkcontext'
        vn_ctx_db = api.custom_caller.call_api('GET', uri)

        for row in table_data:

            logger.info('Looking for IP Transit Border Handoff for: {}'.format(row['borderIp']))
            # URI: (GET: Details on border device selected by IP)
            uri = '/dna/intent/api/v1/business/sda/border-device?deviceIPAddress={}'.format(row['borderIp'])
            response = api.custom_caller.call_api('GET', uri)
            if 'failed' in response['status']:
                logger.warning('{}'.format(response['description']))
                continue

            logger.info('Our AS: AS{}'.format(response['deviceSettings']['internalDomainProtocolNumber']))
            local_as = response['deviceSettings']['internalDomainProtocolNumber']
            if response['deviceSettings']['extConnectivitySettings']:
                for extConn in response['deviceSettings']['extConnectivitySettings']:
                    if extConn['externalDomainProtocolNotation'] == 'ASPLAIN':
                        remote_as = extConn['externalDomainProtocolNumber']
                        local_intf = extConn['interfaceUuid']
                        peer_dict = {extConn['interfaceUuid']: []}
                        logger.info('Found IP Transit: AS{}, Interface: {}'.format(
                            remote_as,
                            local_intf
                        ))
                        for transit in extConn['l3Handoff']:
                            vn_name = get_vn_name_by_idref(
                                vn_db['response'],
                                vn_ctx_db['response'],
                                transit['virtualNetwork']['idRef']
                            )
                            logger.info('Building BGP peer for VN: {} on {}'.format(vn_name, local_intf))

                            local_ip_addr = get_ip_address(transit['localIpAddress'])
                            local_ip_subnet = get_ip_subnet(transit['localIpAddress'])
                            remote_ip_addr = get_ip_address(transit['remoteIpAddress'])
                            remote_ip_subnet = get_ip_subnet(transit['remoteIpAddress'])

                            peer_dict[extConn['interfaceUuid']].append({
                                'remote_as': extConn['externalDomainProtocolNumber'],
                                'local_as': local_as,
                                'vlan': transit['vlanId'],
                                'local_ip_subnet': '{} {}'.format(local_ip_addr, local_ip_subnet),
                                'local_ip': local_ip_addr,
                                'remote_ip_subnet': '{} {}'.format(remote_ip_addr, remote_ip_subnet),
                                'remote_ip': remote_ip_addr,
                                'vn_name': vn_name,
                                'description': 'To {} - {}'.format(row['borderName'], extConn['interfaceUuid'])
                            })
                print(peer_dict)
                for interface, peers in peer_dict.items():
                    print()
                    print('***** Peering config for device connected to {} - {} ******'.format(row['borderName'],
                                                                                               interface))
                    template_content = ""
                    for peer in peers:
                        tm = Template(templates.template_vn_peer)
                        config = tm.render(peer)
                        print(config)
                        print('********************************************************')

                        # get template content
                        template_content = "{}{}".format(template_content, config)

                if row['pushConfig']:
                    row['templateContent'] = template_content.replace('\n', '\\n')
                    response = deploy_config_to_fusion(api, row)

            else:
                logger.error("No Peers Found for device")
    else:
        logger.error('schema not found: {}'.format(_schema))


def deploy_config_to_fusion(api, row):

    logger.info("border_handoff::Deploying config to {}".format(row['fusionIp']))

    response = api.devices.get_device_list(managementIpAddress=row['fusionIp'])
    if response['response']:
        fusion_details = response['response'][0]
        response = api.devices.sync_devices_using_forcesync(payload=[fusion_details['id']])
        common.wait_for_task_completion(api, response['response'])

        # format input correctly for functions
        if fusion_details['reachabilityStatus'] == "Reachable":
            row['templateName'] = "{}_Fusion_Border_Handoff_Config".format(row['fusionIp'])
            row['templateDescription'] = "Fusion Border Config By DNA Workflows"
            row['project'] = "Fusion Border Automation"
            row['composite'] = False
            row['productFamily'] = fusion_details['family']
            row['productSeries'] = fusion_details['series']
            row['softwareType'] = fusion_details['softwareType']
            row['ipAddress'] = row['fusionIp']
            row['hostName'] = row['fusionName']
            row['presence'] = "present"

            # This is a hack... need to fix this to something more logical to feed into other modules
            data = {}
            data['templatesData?deployment'] = []
            data['templatesData?templates'] = []
            data['templatesData?deployment'].append(row)
            data['templatesData?templates'].append(row)

            # check for project and create if needed
            project = api.template_programmer.get_projects(row['project'])

            if not project:
                # create project
                response = api.template_programmer.create_project(payload={'name': row['project']})

            # create template for fusion config
            response = template_flow.create_templates(api, data)

            # deploy config if template successfully pushed
            if not response['response']["isError"]:
                response = template_flow.deploy_templates(api, data)
                print(response)

    else:
        logger.info("border_handoff::{} does not exist in DNA Center. Templates not Pushed".format(row['fusionName']))

    return


def get_vn_name_by_idref(vn_db, vn_ctx_db, id_ref):
    for vn in vn_db:
        if vn['id'] == id_ref:
            vn_context_id = vn['virtualNetworkContextId']

    for vn in vn_ctx_db:
        if vn['id'] == vn_context_id:
            vn_name = vn['name']

    return vn_name


def get_ip_address(addr):
    """Get ipv4 address within given subnet.

    Args:
        addr: ipv4 address in prefix format

    Returns:
        ipv4 address

    """
    addr = ipaddress.ip_interface(addr)

    return str(addr.ip)


def get_ip_subnet(addr):
    """Get subnet mask of ipv4 in prefix format

    Args:
        addr:   ipv4 address in prefix format

    Returns:
        subnet mask

    """
    addr = ipaddress.IPv4Network(addr, strict=False)
    return str(addr.netmask)
