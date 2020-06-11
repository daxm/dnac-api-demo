import logging
import common
from netaddr import *
import yaml
import time
import jinja2
from pathlib import Path
from devices import payload_templates as templates
import pkgutil

logger = logging.getLogger('main.devices')

# URI: GET used to discover the IP of device using the Hostname
topology_db_uri = 'api/v1/topology/physical-topology?nodeType=device&__preventCache=1573344887666'
# URI: GET used to discover discover site membership
site_member_uri_pattern = 'dna/intent/api/v1/membership/{}'
# URI: POST used to provision devices
provision_device_url = 'api/v2/data/customer-facing-service/DeviceInfo'


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def day0(api, workflow_dict):
    logger.info('devices::day0')

    interface_db = _build_link_dict(
        workflow_dict['native?devices?networkLinks'],
        workflow_dict['native?devices?underlayLinkPools']
    )

    # remove devices where day0 will not be generated
    device_db = [device for device in workflow_dict['native?devices?networkDevices'] if device['mgmtIp']]

    devices_dict = _build_device_dict(
        device_db,
        workflow_dict['native?devices?globals'],
        workflow_dict['native?devices?underlayLo0Pools'],
        interface_db
    )

    # Render day0 templates
    _render_host_templates(devices_dict)


def assign_to_site(api, workflow_dict):
    _schema = 'devices.schema.devices'
    logger.info('devices::assign_to_site')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # Hack until we figure out how to check device inventory status correctly
        # logger.info('devices::Sleep for 5 minutes ...')
        # time.sleep(300)

        sites_db = api.sites.get_site()

        for device in table_data:

            if 'absent' == device['presence']:
                continue

            site_id = common.get_object_id(sites_db['response'], siteNameHierarchy=device['location'])
            topology_db = api.custom_caller.call_api('GET', topology_db_uri)
            device_ip = common.get_object_id(topology_db['response']['nodes'], return_param='ip',
                                             label=device['hostname'], strict=False)

            if device_ip is None:
                logger.info('Device {} not found in topology database'.format(device['hostname']))
                logger.info('Entering wait loop for maximum 60 seconds')
                topology_db = _wait_for_device_presence(api, device['hostname'], timeout=60)
                device_ip = common.get_object_id(topology_db['response']['nodes'], return_param='ip',
                                                 label=device['hostname'], strict=False)

            if site_id is not None:
                # TODO Can this be converted to native SDK call?
                # URI: GET used to discover discover site membership
                site_member_uri = site_member_uri_pattern.format(site_id)
                site_membership = api.custom_caller.call_api('GET', site_member_uri)
                device_provisioned = 0
                for members_response in site_membership['device']:
                    # Check if device already provisioned under this site
                    # This is suboptimal since the device could be provisioned under a different site already
                    if len(members_response['response']):
                        device_id = common.get_object_id(members_response['response'], return_param='instanceUuid',
                                                         hostname=device['hostname'], strict=False)
                        if device_id is not None:
                            logger.info(
                                'Device {} already allocated to site {}'.format(device['hostname'], device['location']))
                            logger.debug('Hostname: {} instanceUuid: {}'.format(device['hostname'], device_id))
                            device_provisioned = 1
                        else:
                            logger.info('Adding device {} to site {}'.format(device['hostname'], device['location']))
                            data = common.build_json_from_template(templates.device_to_site_j2,
                                                                   {'device_ip': device_ip})
                            result = api.sites.assign_device_to_site(site_id, payload=data)
                            status = common.wait_for_task_completion(api, result)
                            logger.debug(status)
                            device_provisioned = 1

                if not device_provisioned:
                    # If we didn't find a device under this site, try and assign the device to site
                    # Again, not optimal as the device may exist under a different site
                    logger.info(
                        'Device {} not found under target site {}'.format(device['hostname'], device['location']))
                    logger.info('Trying to add device {} to site {}'.format(device['hostname'], device['location']))
                    data = common.build_json_from_template(templates.device_to_site_j2, {'device_ip': device_ip})
                    result = api.sites.assign_device_to_site(site_id, payload=data)
                    status = common.wait_for_task_completion(api, result)
                    logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def provision_devices(api, workflow_dict):
    _schema = 'devices.schema.devices'
    logger.info('devices::provision_devices')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        sites_db = api.sites.get_site()
        devices_db = api.devices.get_device_list()

        for device in table_data:

            if device['presence'] == 'absent' or device['provisionDevice'] == False:
                continue

            site_id = common.get_object_id(sites_db['response'], siteNameHierarchy=device['location'])
            device_id = common.get_object_id(devices_db['response'], hostname=device['hostname'], strict=False)
            device_name = common.get_object_id(devices_db['response'], return_param='hostname',
                                               hostname=device['hostname'], strict=False)

            logger.info('Provisioning for device: {}, at site: {}'.format(device['hostname'], device['location']))
            payload_data = {}
            payload_data.update({'name': device_name})
            payload_data.update({'networkDeviceId': device_id})
            payload_data.update({'siteId': site_id})
            data = common.build_json_from_template(templates.provision_device_j2, payload_data)
            result = api.custom_caller.call_api('POST', provision_device_url, json=data)
            status = common.wait_for_task_completion(api, result['response'], timeout=45, tree=True)
            logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_devices(api, workflow_dict):
    _schema = 'devices.schema.devices'
    logger.info('devices::delete_devices')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        devices_db = api.devices.get_device_list()
        for device in table_data:
            if device['hostname']:
                device_id = common.get_object_id(devices_db['response'], hostname=device['hostname'], strict=False)
                if device['presence'] == 'absent' and device_id is not None:
                    logger.info('device {} with id: {} will be deleted'.format(device['hostname'], device_id))
                    # URI: GET device-info is used to check if a device is provisioned or not.
                    device_info_url = 'api/v2/data/customer-facing-service/DeviceInfo'
                    device_info = api.custom_caller.call_api('GET', device_info_url,
                                                             params={'networkDeviceId': device_id})

                    # If device is already provisioned, we need to use a DeviceInfo API to delete it.
                    device_info_id = common.get_object_id(device_info['response'], networkDeviceId=device['id'])
                    if device_info_id is not None:
                        # URI: DELETE but only if the device is already provisioned.  We check if the device is in "device-info"
                        delete_url = 'api/v2/data/customer-facing-service/DeviceInfo/{}'.format(device_info_id)
                    else:
                        # URI: DELETE if the device is not 'in use' by provisioning
                        delete_url = 'api/v1/network-device/{}'.format(device_id)
                    result = api.custom_caller.call_api('DELETE', delete_url, params={'cleanConfig': True})
                    status = common.wait_for_task_completion(api, result['response'], timeout=30)
                    logger.debug(status)

                    # if device fails cleanup - force device delete
                    if status['response']['isError'] == True and "Configuration cleanup failed" in status['response'][
                        'progress']:
                        delete_url = 'api/v1/network-device/{}'.format(device['id'])
                        result = api.custom_caller.call_api('DELETE', delete_url, params={'isForceDelete': True})
                        status = common.wait_for_task_completion(api, result['response'], timeout=30)
                        logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all(api, workflow_dict):
    _schema = None
    logger.info('devices::delete_all')
    logger.debug('schema: {}'.format(_schema))

    # TODO: Test with CSR with pnp
    logger.info('devices::delete_all')
    devices_db = api.devices.get_device_list()
    for device in devices_db['response']:
        logger.info('device {} with id: {} will be deleted'.format(device['hostname'], device['id']))
        # URI: GET device-info is used to check if a device is provisioned or not.
        device_info_url = 'api/v2/data/customer-facing-service/DeviceInfo'
        device_info = api.custom_caller.call_api('GET', device_info_url, params={'networkDeviceId': device['id']})

        # If device is already provisioned, we need to use a DeviceInfo API to delete it.
        device_info_id = common.get_object_id(device_info['response'], networkDeviceId=device['id'])
        if device_info_id is not None:
            # URI: DELETE but only if the device is already provisioned.  We check if the device is in "device-info"
            delete_url = 'api/v2/data/customer-facing-service/DeviceInfo/{}'.format(device_info_id)
        else:
            # URI: DELETE if the device is not 'in use' by provisioning
            delete_url = 'api/v1/network-device/{}'.format(device['id'])

        result = api.custom_caller.call_api('DELETE', delete_url, params={'cleanConfig': True})
        status = common.wait_for_task_completion(api, result['response'], timeout=30)
        logger.debug(status)

        # if device fails cleanup - force device delete
        if status['response']['isError'] == True and "Configuration cleanup failed" in status['response']['progress']:
            delete_url = 'api/v1/network-device/{}'.format(device['id'])
            result = api.custom_caller.call_api('DELETE', delete_url, params={'isForceDelete': True})
            status = common.wait_for_task_completion(api, result['response'], timeout=30)
            logger.debug(status)


def _build_link_dict(link_db, link_pool_db):
    interface_db = {}
    pool_dict = _build_ip_pool_dict(link_pool_db)

    for link in link_db:
        _int_net = list(IPNetwork(pool_dict[link['linkIpPool']]['ipPoolPrefix']).subnet(30))[link['index']]
        _a_device = link['a_device']
        _b_device = link['b_device']
        _a_int_list = link['a_interface'].split(",")
        _b_int_list = link['b_interface'].split(",")

        _a_interface = {
            'device': _a_device,
            'description': "*** To " + _b_device + " " + link['b_interface'] + " ***",
            'name': _a_int_list,
            'ipv4_addr': str(list(_int_net)[1]),
            'ipv4_netmask': str(_int_net.netmask)
        }
        _b_interface = {
            'device': _b_device,
            'description': "*** To " + _a_device + " " + link['a_interface'] + " ***",
            'name': _b_int_list,
            'ipv4_addr': str(list(_int_net)[2]),
            'ipv4_netmask': str(_int_net.netmask)
        }

        if _a_interface is not None:
            _interface_name_a = 'interfaceA' + '%04d' % link['index']
            interface_db[_interface_name_a] = _a_interface
        if _b_interface is not None:
            _interface_name_b = 'interfaceB' + '%04d' % link['index']
            interface_db[_interface_name_b] = _b_interface

    return interface_db


def _build_device_dict(device_db, common_vars, lo0_pool_db, interface_db):
    pool_dict = _build_ip_pool_dict(lo0_pool_db)

    for device in device_db:

        device.update({'labMgmtIp': str(IPNetwork(device['mgmtIp']).ip)})
        device.update({'labMgmtNetmask': str(IPNetwork(device['mgmtIp']).netmask)})

        # Add common vars
        for row in common_vars:
            device.update({row['item']: row['value']})

        device.update({'interfaces': {}})

        # Add the Loopback0 interface
        loopback0_addr = list(IPNetwork(pool_dict[device['lo0IpPool']]['ipPoolPrefix']).subnet(32))[device['index']]
        device['interfaces']['loopback0'] = {
            'name': 'Loopback0',
            'template': '_mgmt_lo_v01.j2',
            'ipv4_addr': str(loopback0_addr.ip),
            'ipv4_netmask': str(loopback0_addr.netmask)
        }

        # Merge the links DB with the device
        for item, interface in interface_db.items():

            if device['hostname'] == interface['device']:
                device['interfaces'].update({item: interface})

    return device_db


def _build_ip_pool_dict(link_pool_db):
    pool_dict = {}
    for pool in link_pool_db:
        pool_dict.update({pool['ipPoolName']: pool})
        pool_dict[pool['ipPoolName']].pop('ipPoolName')

    return pool_dict


def _render_host_templates(devices):
    template_loader = jinja2.FileSystemLoader(searchpath="./devices/day0_templates")
    template_env = jinja2.Environment(loader=template_loader)

    for device in devices:
        host = {'value': device, 'key': device['hostname']}
        template_file = device['day0']
        t = template_env.get_template(template_file)
        _config = t.render(item=host)

        # Save the results
        Path(device['config_dir']).mkdir(parents=True, exist_ok=True)
        file_name = '{}/{}-config'.format(device['config_dir'], device['hostname'])
        with open(file_name, "w") as fh:
            fh.write(_config)


def _wait_for_device_presence(api, hostname, timeout=10):
    time.sleep(5)

    # URI: GET We are trying to determine, after a device has been discovered, when it is ready for provisioning (DNW)
    topology_db_uri = 'api/v1/topology/physical-topology?nodeType=device&__preventCache=1573344887666'
    topology_db = api.custom_caller.call_api('GET', topology_db_uri)
    device_ip = common.get_object_id(topology_db['response']['nodes'], return_param='ip', label=hostname)

    t = timeout
    while True:
        if device_ip is None:
            # logger.debug(topology_db)
            logger.info('Device IP for {} not found.  Sleeping for 5 seconds ...'.format(hostname))
            time.sleep(5)
            topology_db = api.custom_caller.call_api('GET', topology_db_uri)
            device_ip = common.get_object_id(topology_db['response']['nodes'], return_param='ip', label=hostname, strict=False)
            logger.debug('Device search returned ip: {}'.format(device_ip))
            t = t - 5
        else:
            logger.info('Device {} now found in topology DB with IP: {}'.format(hostname, device_ip))
            # logger.info('Doing a lame sleep for 60 seconds')
            # time.sleep(60)
            logger.debug(topology_db)
            break

        if t < 1:
            logger.error('Timeout waiting for task to complete: Unable to find {}'.format(hostname))
            logger.debug(topology_db)
            break

    return topology_db


def add_device_role(api, workflow_dict):
    _schema = 'devices.schema.devices'
    logger.info('devices::delete_devices')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        device_role_changes = [row for row in table_data if row['role']]
        _device_db = api.devices.get_device_list()['response']
        device_name_list = [(device['hostname'], device['id']) for device in _device_db]
        device_uuid_list = []

        # get device id for names without domain name attached
        if device_role_changes:
            for device in device_name_list:
                for change_device in device_role_changes:
                    if device[0].split('.')[0] == change_device['hostname'].split('.')[0]:
                        device_uuid_list.append(
                            {'hostname': change_device['hostname'], 'id': device[1], 'role': change_device['role']})

        # now push the role changes
        if device_uuid_list:
            for device in device_uuid_list:
                data = common.build_json_from_template(templates.device_role_j2, device)
                result = api.devices.update_device_role(payload=data)
                status = common.wait_for_task_completion(api, result['response'])
                logger.debug(status)

        else:
            logger.error("Device does not exist.  Role not updated")
    else:
        logger.error('schema not found: {}'.format(_schema))
