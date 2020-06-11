import logging
import common
import re
import yaml
import pkgutil
from fabric import payload_templates as templates

logger = logging.getLogger('main.fabric')

##### Fabric related API calls #####
# URI: GET used in number of Fabric related calls
fabric_url = 'api/v2/data/customer-facing-service/ConnectivityDomain'
# URI: GET used in number of Fabric related calls
fabric_domain_url = 'api/v2/data/customer-facing-service/ConnectivityDomain'
# URI: GET used to check for the existing Fabric Site
fabric_sites_url_pattern = 'api/v2/data/customer-facing-service/summary/ConnectivityDomain?cdFSiteList={}'
# URI: GET used to discover Virtual Networks
vn_url = 'api/v2/data/customer-facing-service/virtualnetworkcontext'
# URI: GET used to check for the existing VNs
vn_url_pattern = 'api/v2/data/customer-facing-service/VirtualNetwork?cdVnList={}'
# URI: GET used to discover authentication templates
template_url = 'api/v1/siteprofile?namespace=authentication'
# URI: GET used to discover site topology
site_url = 'api/v1/topology/site-topology'
# URI: GET used to check whether device is part of the fabric
fabric_device_url = '/dna/intent/api/v1/business/sda/device'
# URI: GET/POST used in number of Fabric Edge related calls
edge_url = 'dna/intent/api/v1/business/sda/edge-device'
# URI: GET/POST used in number of Fabric Edge related calls
control_url = '/dna/intent/api/v1/business/sda/control-plane-device'
# URI: GET/POST used in number of Fabric Border related calls
border_url = 'dna/intent/api/v1/business/sda/border-device'
# URI: GET used to check Device Info for Fabric Role changes
device_url = 'api/v2/data/customer-facing-service/DeviceInfo'
# URI: GET used to check Device ID
device_id_url = 'api/v1/network-device'

##### Policy related API calls #####
# URI: GET used to discover Scalable Groups
sgt_url = 'api/v2/data/customer-facing-service/summary/scalablegroup/access'
# URI: PUT used to delete Scalable Groups
mod_sgt_url = 'api/v2/data/customer-facing-service/scalablegroup/access'
# URI: POST used to add Scalable Groups
add_sgt_url = 'api/v2/data/customer-facing-service/scalablegroup/access'
# URI: GET used to obtain the next available SGT decimal number
get_next_sgt_url = 'api/v2/data/customer-facing-service/summary/scalablegroup/access?getNextSgt=true'
# URI: GET/POST used to Discover/CREATE/DELETE Contracts
contract_url = 'api/v2/data/customer-facing-service/contract/access'
# URI: GET/POST/PUT used to Discover/CREATE/DELETE policy
policy_url = 'api/v2/data/customer-facing-service/policy/access'
# URI: POST used to delete contract
delete_contract_url = 'api/v2/data/cfs-intent/contract/access'


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def create_fabric_site(api, workflow_dict):
    _schema = 'fabric_sites.schema.fabric'
    logger.info('fabric::create_fabric_site')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if 'present' in row['presence']:
                _add_site_to_fabric(api, row)
    else:
        logger.error('schema not found: {}'.format(_schema))


def _add_site_to_fabric(api, row):
    sites_db = api.sites.get_site()
    site_id = common.get_object_id(sites_db['response'], siteNameHierarchy=row['fabricSite'])

    if site_id is None:
        log_string = 'Cannot add site {} to Fabric Domain {}: Site does not exist'
        logger.warning(log_string.format(row['fabricSite'], row['fabricName']))
        return

    fabric_domain_db = api.custom_caller.call_api('GET', fabric_domain_url)
    fabric_domain = common.get_object_by_attribute(fabric_domain_db['response'], name=row['fabricName'])
    fabric_domain_id = common.get_object_id(fabric_domain_db['response'], name=row['fabricName'])

    # Test if Fabric Domain already exists in which case do PUT
    if fabric_domain_id is not None:
        logger.info('Adding site {} to existing Fabric Domain: {}'.format(row['fabricSite'], row['fabricName']))
        fabric_site_uuid = _fabric_site_exists(api, fabric_domain_id, site_id)
        if fabric_site_uuid is not None:
            log_string = 'Fabric site "{}" already exists with under Fabric Domain "{}"'
            logger.info(log_string.format(row['fabricSite'], row['fabricName']))
            vn_data = _check_fabric_vn_list(api, fabric_site_uuid, row)
            if vn_data is not None:
                logger.warning('Fabric site "{}" VNs appears to out of sync: TBD'.format(row['fabricSite']))
                logger.warning('Update currently not supported. Please remove the fabric site and re-add')
                # Need to only add/remove VNs that are changing in the list
                # To remove, do a PUT after removing the idRef of the VN
                # To add, use ONLY the VN payload to be added.  E.g. If you try to add with existing name it will fail
        else:
            fabric_site_name = '{}_{}'.format(row['fabricSite'].replace(" ", "_"), row['fabricName'])
            row.update({'fabric_site_name': fabric_site_name})
            fabric_site = common.build_json_from_template(templates.fabric_site_j2, row)
            fabric_site['siteId'] = site_id
            fabric_site['virtualNetwork'] = _build_fabric_vn_list(api, row)

            # Copy required fabric domain attributes
            fabric_domain_update = [common.build_json_from_template(templates.fabric_domain_j2, row)]
            fabric_domain_update[0]['id'] = fabric_domain['id']

            # Copy the current and add the new fabric site to siteSpecificDomain list
            fabric_domain_update[0]['siteSpecificDomain'] = fabric_domain['siteSpecificDomain']
            fabric_domain_update[0]['siteSpecificDomain'].append(fabric_site)
            result = api.custom_caller.call_api('PUT', fabric_domain_url, json=fabric_domain_update)
            status = common.wait_for_task_completion(api, result['response'], timeout=30)
            logger.debug(status)

    # Else if Fabric Domain does not yet exist do a POST including fabric site in payload
    else:
        fabric_site_name = '{}_{}'.format(row['fabricSite'].replace(" ", "_"), row['fabricName'])
        row.update({'fabric_site_name': fabric_site_name})
        fabric_site = common.build_json_from_template(templates.fabric_site_j2, row)
        fabric_site['siteId'] = site_id
        fabric_site['virtualNetwork'] = _build_fabric_vn_list(api, row)

        fabric_domain = [common.build_json_from_template(templates.fabric_domain_j2, row)]
        fabric_domain[0]['siteSpecificDomain'].append(fabric_site)

        logger.info('Creating fabric domain {} with site {}'.format(row['fabricName'], row['fabricSite']))
        result = api.custom_caller.call_api('POST', fabric_domain_url, json=fabric_domain)
        status = common.wait_for_task_completion(api, result['response'], timeout=30)
        logger.debug(status)


def _fabric_site_exists(api, fabric_domain_id, site_id):
    fabric_sites_url = fabric_sites_url_pattern.format(fabric_domain_id)
    fabric_domain_summary = api.custom_caller.call_api('GET', fabric_sites_url)
    fabric_site_uuid = None
    for site in fabric_domain_summary['response'][0]['summaries']:
        if (site['siteId'] == site_id):
            fabric_site_uuid = (site['id'])

    if fabric_site_uuid is None:
        return None
    else:
        return fabric_site_uuid


# To Do - Not fully implemented.  We compare list length only today
def _check_fabric_vn_list(api, fabric_site_uuid, fabric_site):
    vn_url = vn_url_pattern.format(fabric_site_uuid)
    vn_db = api.custom_caller.call_api('GET', vn_url)

    existing_vn = []
    for vn in vn_db['response']:
        existing_vn.append(vn['name'])

    _vn_name_list = fabric_site['virtualNetworks'].split(",")
    if 'DEFAULT_VN' not in _vn_name_list:
        _vn_name_list.append('DEFAULT_VN')

    if 'INFRA_VN' not in _vn_name_list:
        _vn_name_list.append('INFRA_VN')

    if len(_vn_name_list) != len(existing_vn):
        return _build_fabric_vn_list(api, fabric_site)

    return None


def _build_fabric_vn_list(api, fabric_site):
    _vn_name_list = fabric_site['virtualNetworks'].split(',')
    _fabric_name = '{}_{}'.format(fabric_site['fabricSite'], fabric_site['fabricName'])

    vn_db = api.custom_caller.call_api('GET', vn_url)
    vn_obj_list = []

    if 'DEFAULT_VN' not in _vn_name_list:
        _vn_name_list.append('DEFAULT_VN')

    if 'INFRA_VN' not in _vn_name_list:
        _vn_name_list.append('INFRA_VN')

    for vn in _vn_name_list:
        vn_id = common.get_object_id(vn_db['response'], name=vn)
        fabric_vn_name = '{}-{}'.format(vn, _fabric_name)
        template_vars = {'virtualNetworkContextId': vn_id}
        template_vars.update({'fabric_vn_name': fabric_vn_name.replace(" ", "_")})
        vn_dict = common.build_json_from_template(templates.fabric_vn_j2, template_vars)
        if 'DEFAULT_VN' == vn:
            vn_dict['isDefault'] = True
        if 'INFRA_VN' == vn:
            vn_dict['isInfra'] = True
        vn_obj_list.append(vn_dict)

    return vn_obj_list


def delete_fabric_site(api, workflow_dict):
    _schema = 'fabric_sites.schema.fabric'
    logger.info('fabric::delete_fabric_site')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        fabric_domain_db = api.custom_caller.call_api('GET', fabric_url)

        for row in table_data:
            if 'absent' in row['presence']:

                # Try to get the id for the Fabric Domain
                fabric_domain = common.get_object_by_attribute(fabric_domain_db['response'], name=row['fabricName'])
                if fabric_domain is None:
                    logger.info('Fabric Domain {} not found'.format(row['fabricName']))
                    continue

                sites_db = api.sites.get_site()
                site_id = common.get_object_id(sites_db['response'], siteNameHierarchy=row['fabricSite'])
                fabric_domain_id = fabric_domain['id']
                fabric_site_uuid = _fabric_site_exists(api, fabric_domain_id, site_id)
                if fabric_site_uuid is None:
                    logger.info(
                        'Fabric site {} not found under Fabric Domain {}'.format(row['fabricSite'], row['fabricName']))
                    continue

                # If fabric domain exists ...
                if fabric_site_uuid is not None:
                    logger.info(
                        'Removing Fabric Site {} from Fabric Domain {}'.format(row['fabricSite'], row['fabricName']))
                    delete_fabric_url = '{}/{}'.format(fabric_url, fabric_site_uuid)
                    result = api.custom_caller.call_api('DELETE', delete_fabric_url)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)

                # Refresh the Fabric Domain DB and check if any sites remain
                fabric_db = api.custom_caller.call_api('GET', fabric_url)
                site_specific_domain_list = common.get_object_id(
                    fabric_db['response'],
                    return_param='siteSpecificDomain',
                    name=row['fabricName']
                )

                # Only remove Fabric Domain if the list of fabric sites is empty
                if site_specific_domain_list is not None and len(site_specific_domain_list) == 0:
                    fabric_domain_id = common.get_object_id(fabric_db['response'], name=row['fabricName'])
                    logger.info(
                        'Removing Fabric Domain {} since there are no more sites'.format(row['fabricName']))
                    delete_fabric_url = '{}/{}'.format(fabric_url, fabric_domain_id)
                    result = api.custom_caller.call_api('DELETE', delete_fabric_url)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_virtual_networks(api, workflow_dict):
    _schema = 'virtual_network.schema.fabric'
    logger.info('fabric::create_virtual_networks')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        vn_db = api.custom_caller.call_api('GET', vn_url)

        for row in table_data:
            if 'present' in row['presence']:
                vn_id = common.get_object_id(vn_db['response'], name=row['vnName'])
                if vn_id is None:
                    logger.info('Creating VN with name {}'.format(row['vnName']))
                    virtual_network = common.build_json_from_template(templates.virtual_network_j2, row)
                    result = api.custom_caller.call_api('POST', vn_url, json=virtual_network)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
                else:
                    logger.info('VN {} already exists with ID: {}'.format(row['vnName'], vn_id))
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_virtual_networks(api, workflow_dict):
    _schema = 'virtual_network.schema.fabric'
    logger.info('fabric::delete_virtual_networks')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        vn_db = api.custom_caller.call_api('GET', vn_url)

        for row in table_data:
            if 'absent' in row['presence']:
                vn_id = common.get_object_id(vn_db['response'], name=row['vnName'])
                if vn_id is not None:
                    logger.info('deleting VN {} with ID: {}'.format(row['vnName'], vn_id))
                    delete_vn_url = '{}/{}'.format(vn_url, vn_id)
                    result = api.custom_caller.call_api('DELETE', delete_vn_url)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
                else:
                    logger.info('VN {} not found'.format(row['vnName']))
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_scalable_group_tag(api, workflow_dict):
    _schema = 'sgt.schema.fabric'
    logger.info('fabric::create_scalable_group_tag')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        sgt_db = api.custom_caller.call_api('GET', sgt_url)

        for row in table_data:
            if 'present' in row['presence']:
                sgt_id = common.get_object_id(sgt_db['response'][0]['acaScalableGroupSummary'], name=row['sgtName'])
                if sgt_id is None:
                    sgt_val = _get_next_tag(api)
                    sgt = common.build_json_from_template(templates.scalable_group_tag_j2, row)
                    sgt[0]['securityGroupTag'] = sgt_val
                    logger.info('Creating SGT {} with TAG value: {}'.format(row['sgtName'], sgt_val))
                    result = api.custom_caller.call_api('POST', add_sgt_url, json=sgt)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
                else:
                    logger.info('SGT {} already exists with ID: {}'.format(row['sgtName'], sgt_id))
    else:
        logger.error('schema not found: {}'.format(_schema))


def _get_next_tag(api):
    sgt_value = api.custom_caller.call_api('GET', get_next_sgt_url)

    return sgt_value['response'][0]['securityGroupTag']


def delete_scalable_group_tag(api, workflow_dict):
    _schema = 'sgt.schema.fabric'
    logger.info('fabric::delete_scalable_group_tag')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        sgt_db = api.custom_caller.call_api('GET', sgt_url)

        for row in table_data:
            if 'absent' in row['presence']:
                sgt_object = common.get_object_by_attribute(sgt_db['response'][0]['acaScalableGroupSummary'],
                                                            name=row['sgtName'])
                if sgt_object is not None:
                    sgt = common.build_json_from_template(templates.scalable_group_tag_j2, row)
                    sgt[0].update({'id': sgt_object['id']})
                    _dec_sgt, _hex_sgt = sgt_object['securityGroupTag'].split('/')
                    sgt[0].update({'securityGroupTag': _dec_sgt})
                    sgt[0].update({'isDeleted': True})
                    logger.info('Deleting SGT {} with ID: {}'.format(row['sgtName'], sgt_object['id']))
                    result = api.custom_caller.call_api('PUT', mod_sgt_url, json=sgt)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
                else:
                    logger.info('SGT {} not found.'.format(row['sgtName']))
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_contract(api, workflow_dict):
    _schema = 'contracts.schema.fabric'
    logger.info('fabric::create_contract')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        contract_config = _build_contract_config(table_data)
        contract_db = api.custom_caller.call_api('GET', contract_url)

        for contract in contract_config:
            contract_id = common.get_object_id(contract_db['response'], name=contract['contractName'])
            if contract_id is None:
                if 'present' in contract['presence']:
                    data = common.build_json_from_template(templates.contract_j2, contract)
                    data[0]['contractClassifier'] = contract['contractRules']
                    logger.info('Create contract {}'.format(data[0]['name']))
                    result = api.custom_caller.call_api('POST', contract_url, json=data)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
            else:
                logger.info(
                    'Contract with name {} already exists with ID: {}'.format(contract['contractName'], contract_id))
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_contract(api, workflow_dict):
    _schema = 'contracts.schema.fabric'
    logger.info('fabric::delete_contract')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        contract_config = _build_contract_config(table_data)
        contract_db = api.custom_caller.call_api('GET', contract_url)

        for contract in contract_config:
            contract_id = common.get_object_id(contract_db['response'], name=contract['contractName'])
            if contract_id is not None:
                if 'absent' in contract['presence']:
                    logger.info('Delete contract {}'.format(contract['contractName']))
                    data = {'deleteList': [contract_id]}
                    result = api.custom_caller.call_api('POST', delete_contract_url, json=data)
                    status = common.wait_for_task_completion(api, result['response'], timeout=10)
                    logger.debug(status)
            else:
                logger.info('Contract {} not found.'.format(contract['contractName']))
    else:
        logger.error('schema not found: {}'.format(_schema))


def _build_contract_config(contract_table):
    logger.info('Checking contract table configuration for consistency')
    contract_dict = {}

    # Initialise dictionaries
    for row in contract_table:
        logger.debug('Parsing contract data for "{}"'.format(row['contractName']))
        contract_dict.update({row['contractName']: {}})
        contract_dict[row['contractName']].update({'contractRules': []})

    for row in contract_table:

        # If we have an invalid configuration, we remove the contract so skip if this this is the case
        if row['contractName'] not in contract_dict.keys():
            continue

        if 'defaultAction' not in contract_dict[row['contractName']].keys():
            contract_dict[row['contractName']].update({'defaultAction': row['defaultAction']})
        elif row['defaultAction'] != contract_dict[row['contractName']]['defaultAction']:
            logger.warning(
                'One or more "defaultAction" settings do not match for contract {}'.format(row['contractName']))
            logger.warning('Using first instance {}'.format(contract_dict[row['contractName']]['defaultAction']))

        if 'defaultRuleLogging' not in contract_dict[row['contractName']].keys():
            contract_dict[row['contractName']].update({'defaultRuleLogging': row['defaultRuleLogging']})
        elif row['defaultRuleLogging'] != contract_dict[row['contractName']]['defaultRuleLogging']:
            logger.warning(
                'One or more "defaultRuleLogging" settings do not match for contract {}'.format(row['contractName']))
            logger.warning('Using first instance {}'.format(contract_dict[row['contractName']]['defaultRuleLogging']))

        if 'presence' not in contract_dict[row['contractName']].keys():
            contract_dict[row['contractName']].update({'presence': row['presence']})
        elif row['presence'] != contract_dict[row['contractName']]['presence']:
            logger.error('One or more "presence" settings do not match for contract {}'.format(row['contractName']))
            logger.error('Contract config for {} will be NOT BE DEPLOYED'.format(row['contractName']))
            contract_dict[row['contractName']].update({'presence': 'ERROR'})

        _rule = common.build_json_from_template(templates.contract_classifier_j2, row)
        contract_dict[row['contractName']]['contractRules'].append(_rule)

    contract_list = []
    for key, value in contract_dict.items():
        value.update({'contractName': key})
        contract_list.append(value)

    # print(contract_list)
    return contract_list


def create_policy(api, workflow_dict):
    _schema = 'policy.schema.fabric'
    logger.info('fabric::create_policy')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        sgt_db = api.custom_caller.call_api('GET', sgt_url)
        contract_db = api.custom_caller.call_api('GET', contract_url)
        policy_db = api.custom_caller.call_api('GET', policy_url)

        for row in table_data:

            if 'present' in row['presence']:
                policy_id = common.get_object_id(policy_db['response'], name=row['policyName'])
                source_sgt_id = common.get_object_id(sgt_db['response'][0]['acaScalableGroupSummary'],
                                                     name=row['sourceSgt'])
                destination_sgt_id = common.get_object_id(sgt_db['response'][0]['acaScalableGroupSummary'],
                                                          name=row['destinationSgt'])
                contract_id = common.get_object_id(contract_db['response'], name=row['contract'])

                if policy_id is None:
                    if source_sgt_id is not None and destination_sgt_id is not None and contract_id is not None:
                        row.update({'srcSgtId': source_sgt_id})
                        row.update({'dstSgtId': destination_sgt_id})
                        row.update({'contractId': contract_id})
                        data = common.build_json_from_template(templates.policy_j2, row)
                        logger.info('Creating policy with name {}'.format(row['policyName']))
                        result = api.custom_caller.call_api('POST', policy_url, json=data)
                        status = common.wait_for_task_completion(api, result['response'], timeout=10)
                        logger.debug(status)
                    else:
                        logger.error('One or more of the required policy elements was not found')
                        logger.error('Contract name {}, Id {}'.format(row['contract'], contract_id))
                        logger.error('Source SGT name {}, Id {}'.format(row['sourceSgt'], source_sgt_id))
                        logger.error('Destination SGT name {}, Id {}'.format(row['destinationSgt'], destination_sgt_id))
                else:
                    logger.info('Policy {} already exists with id {}'.format(row['policyName'], policy_id))
                    _policy = common.get_object_by_attribute(policy_db['response'], name=row['policyName'])
                    if 'DISABLED' == _policy['policyStatus']:
                        logger.info('Policy {} in state DISABLED.  Trying to ENABLE'.format(row['policyName']))
                        if source_sgt_id is not None and destination_sgt_id is not None and contract_id is not None:
                            row.update({'srcSgtId': source_sgt_id})
                            row.update({'dstSgtId': destination_sgt_id})
                            row.update({'contractId': contract_id})
                            data = common.build_json_from_template(templates.policy_j2, row)
                            data[0].update({'id': policy_id})
                            data[0].update({'policyStatus': 'ENABLED'})
                            logger.info('Enable policy with name {}'.format(row['policyName']))
                            result = api.custom_caller.call_api('PUT', policy_url, json=data)
                            status = common.wait_for_task_completion(api, result['response'], timeout=10)
                            logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def disable_policy(api, workflow_dict):
    _schema = 'policy.schema.fabric'
    logger.info('fabric::disable_policy')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        sgt_db = api.custom_caller.call_api('GET', sgt_url)
        contract_db = api.custom_caller.call_api('GET', contract_url)
        policy_db = api.custom_caller.call_api('GET', policy_url)

        for row in table_data:
            if 'absent' in row['presence']:
                policy_id = common.get_object_id(policy_db['response'], name=row['policyName'])
                # print(policy_id)
                if policy_id is not None:
                    source_sgt_id = common.get_object_id(sgt_db['response'][0]['acaScalableGroupSummary'],
                                                         name=row['sourceSgt'])
                    destination_sgt_id = common.get_object_id(sgt_db['response'][0]['acaScalableGroupSummary'],
                                                              name=row['destinationSgt'])
                    contract_id = common.get_object_id(contract_db['response'], name=row['contract'])
                    if source_sgt_id is not None and destination_sgt_id is not None and contract_id is not None:
                        row.update({'srcSgtId': source_sgt_id})
                        row.update({'dstSgtId': destination_sgt_id})
                        row.update({'contractId': contract_id})
                        data = common.build_json_from_template(templates.policy_j2, row)
                        data[0].update({'id': policy_id})
                        data[0].update({'policyStatus': 'DISABLED'})
                        logger.info('Disable policy {}'.format(row['policyName']))
                        result = api.custom_caller.call_api('PUT', policy_url, json=data)
                        status = common.wait_for_task_completion(api, result['response'], timeout=10)
                        logger.debug(status)
                else:
                    logger.info('Policy {} not found.'.format(row['policyName']))
    else:
        logger.error('schema not found: {}'.format(_schema))


def set_auth_template(api, workflow_dict):
    _schema = 'fabric_sites.schema.fabric'
    logger.info('fabric::set_auth_template')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        fabric_db = api.custom_caller.call_api('GET', fabric_url)
        template_db = api.custom_caller.call_api('GET', template_url)
        site_db = api.custom_caller.call_api('GET', site_url)

        for row in table_data:
            if 'present' in row['presence']:

                fabric_domain_id = common.get_object_id(fabric_db['response'], name=row['fabricName'])

                if_template_valid = _check_auth_template(row)
                if if_template_valid is True:
                    logger.info('{} is a valid site authentication template'.format(row['authTemplate']))
                    template_id = common.get_object_id(template_db['response'], name=row['authTemplate'],
                                                       return_param='siteProfileUuid')
                    sites_db = api.sites.get_site()
                    site_id = common.get_object_id(sites_db['response'], siteNameHierarchy=row['fabricSite'])
                    row.update({'siteID': site_id})
                    row.update({'authenticationProfileId': template_id})
                    if site_id is not None:
                        fabric_site_uuid = _fabric_site_exists(api, fabric_domain_id, site_id)
                        if fabric_site_uuid is not None:
                            _get_fabric_site(api, row)
                            fabric_profile = common.build_json_from_template(templates.auth_template_j2, row)
                            fabric_profile[0].update(
                                {'fabricAuthenticationProfile': row['fabricAuthenticationProfile']})
                            fabric_profile[0].update({'authenticationProfiles': row['authenticationProfiles']})
                            result = api.custom_caller.call_api('PUT', fabric_url, json=fabric_profile)
                            status = common.wait_for_task_completion(api, result['response'], timeout=30)
                            logger.debug(status)
                        else:
                            logger.info('Fabric site {} not found under Fabric Domain {}'.format(row['fabricSite'],
                                                                                                 row['fabricName']))
                            continue
                    else:
                        logger.warning('Cannot add authentication template to a {} as site does not exist in the '
                                       'hierarchy. Please create it first before assigning authentication '
                                       'template'.format(row['fabricSite']))
                        continue
                else:
                    logger.warning(
                        '{} is NOT a valid site authentication template. Please correct the xls input data'.format(
                            row['authTemplate']))
                    continue
    else:
        logger.error('schema not found: {}'.format(_schema))


def _check_auth_template(row):
    authTemplateList = ['Closed Authentication', 'Easy Connect', 'No Authentication', 'Open Authentication',
                        'Wireless Authentication']
    if_template_valid = False
    for i in authTemplateList:
        if (i == row['authTemplate']):
            if_template_valid = True
    return if_template_valid


def _get_fabric_site(api, row):
    fabric_site_name = '{}_{}'.format(row['fabricSite'].replace(" ", "_"), row['fabricName'])
    row.update({'fabric_site_name': fabric_site_name})
    fabric_url = 'api/v2/data/customer-facing-service/ConnectivityDomain?name=' + row['fabric_site_name']
    fabric_db = api.custom_caller.call_api('GET', fabric_url)
    fabricAuthenticationProfile_id = common.get_object_id(fabric_db['response'][0]['authenticationProfiles'],
                                                          name=row['authTemplate'])
    fabricAuthenticationProfile = eval(("{'idRef': '" + fabricAuthenticationProfile_id + "'}"))
    row.update({'id': fabric_db['response'][0]['id']})
    row.update({'virtualNetwork': fabric_db['response'][0]['virtualNetwork']})
    row.update({'isDefault': fabric_db['response'][0]['isDefault']})
    row.update({'enableMonitoring': fabric_db['response'][0]['enableMonitoring']})
    row.update({'migrationStatus': fabric_db['response'][0]['migrationStatus']})
    row.update({'type': fabric_db['response'][0]['type']})
    row.update({'domainType': fabric_db['response'][0]['domainType']})
    row.update({'deviceInfo': fabric_db['response'][0]['deviceInfo']})
    row.update({'multicastInfo': fabric_db['response'][0]['multicastInfo']})
    row.update({'resourceVersion': fabric_db['response'][0]['resourceVersion']})
    row.update({'siteSpecificDomain': fabric_db['response'][0]['siteSpecificDomain']})
    row.update({'l2FloodingIndex': fabric_db['response'][0]['l2FloodingIndex']})
    row.update({'authenticationProfiles': fabric_db['response'][0]['authenticationProfiles']})
    row.update({'fabricAuthenticationProfile': fabricAuthenticationProfile})
    return


def add_edge(api, workflow_dict):

    _schema = 'fabric_edge.schema.fabric'
    logger.info('fabric::add_edge')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if 'present' in row['presence']:
                fabric_edge_url = edge_url + "?deviceIPAddress=" + row['mgmtIp']
                edge_status_db = api.custom_caller.call_api('GET', fabric_edge_url)

                if edge_status_db['status'] == 'failed':
                    device_id = _get_device_id(api, row)

                    if device_id is not None:
                        site_id = _get_site_id(api, device_id)

                        if site_id is not None:
                            connectivity_domain = api.custom_caller.call_api('GET', fabric_domain_url)

                            for site in connectivity_domain['response']:
                                if (site['siteId'] == site_id):
                                    siteName = (site['name'])

                            siteNameHierarchy = re.sub(r'_.*', "", siteName)
                            row.update({'siteNameHierarchy': siteNameHierarchy})
                            fabric_edge = common.build_json_from_template(templates.add_edge, row)
                            result = api.custom_caller.call_api('POST', edge_url, json=fabric_edge)
                            status = common.wait_for_task_completion(api, result, timeout=30)
                            logger.debug(status)

                        else:
                            logger.info(
                                'Device {} not found under Fabric Domain. Device needs to be provisioned to the site '
                                'before roles can be assigned.'.format(
                                    row['mgmtIp']))
                            continue
                    else:
                        logger.info(
                            'Device {} not found in inventory. Device needs to be discovered and provisioned to the '
                            'site before roles can be assigned.'.format(
                                row['mgmtIp']))
                        continue
                else:
                    logger.info('Device {} is already part of the Fabric'.format(row['mgmtIp']))
                    continue
    else:
        logger.error('schema not found: {}'.format(_schema))


def add_control(api, workflow_dict):

    _schema = 'fabric_cp.schema.fabric'
    logger.info('fabric::add_control')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if 'present' in row['presence']:
                fabric_control_url = control_url + "?deviceIPAddress=" + row['mgmtIp']
                control_status_db = api.custom_caller.call_api('GET', fabric_control_url)

                if control_status_db['status'] == 'failed':
                    device_id = _get_device_id(api, row)

                    if device_id is not None:
                        site_id = _get_site_id(api, device_id)

                        if site_id is not None:
                            connectivity_domain = api.custom_caller.call_api('GET', fabric_domain_url)

                            for site in connectivity_domain['response']:
                                if (site['siteId'] == site_id):
                                    siteName = (site['name'])

                            siteNameHierarchy = re.sub(r'_.*', "", siteName)
                            row.update({'siteNameHierarchy': siteNameHierarchy})
                            fabric_control = common.build_json_from_template(templates.add_control, row)
                            result = api.custom_caller.call_api('POST', control_url, json=fabric_control)
                            status = common.wait_for_task_completion(api, result, timeout=30)
                            logger.debug(status)

                        else:
                            logger.info(
                                'Device {} not found under Fabric Domain. Device needs to be provisioned to the site '
                                'before roles can be assigned.'.format(
                                    row['mgmtIp']))
                            continue
                    else:
                        logger.info(
                            'Device {} not found in inventory. Device needs to be discovered and provisioned to the '
                            'site before roles can be assigned.'.format(
                                row['mgmtIp']))
                        continue
                else:
                    logger.info('Device {} is already part of the Fabric'.format(row['mgmtIp']))
                    continue
    else:
        logger.error('schema not found: {}'.format(_schema))


def add_border(api, workflow_dict):

    _schema = 'fabric_border.schema.fabric'
    logger.info('fabric::add_border')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if 'present' in row['presence']:
                fabric_border_url = fabric_device_url + "?deviceIPAddress=" + row['mgmtIp']
                border_status_db = api.custom_caller.call_api('GET', fabric_border_url)

                if border_status_db['status'] == 'failed':
                    device_id = _get_device_id(api, row)

                    if device_id is not None:
                        site_id = _get_site_id(api, device_id)

                        if site_id is not None:
                            connectivity_domain = api.custom_caller.call_api('GET', fabric_domain_url)

                            for site in connectivity_domain['response']:
                                if (site['siteId'] == site_id):
                                    siteName = (site['name'])

                            # _build_vn_handoff_list(row)
                            siteNameHierarchy = re.sub(r'_.*', "", siteName)
                            row.update({'siteNameHierarchy': siteNameHierarchy})
                            fabric_border = common.build_json_from_template(templates.add_border, row)
                            result = api.custom_caller.call_api('POST', border_url, json=fabric_border)
                            status = common.wait_for_task_completion(api, result, timeout=30)
                            logger.debug(status)

                        else:
                            logger.info(
                                'Device {} not found under Fabric Domain. Device needs to be provisioned to the site '
                                'before roles can be assigned.'.format(
                                    row['mgmtIp']))
                            continue
                    else:
                        logger.info(
                            'Device {} not found in inventory. Device needs to be discovered and provisioned to the '
                            'site before roles can be assigned.'.format(
                                row['mgmtIp']))
                        continue
                else:
                    logger.info('Device {} is already part of the Fabric'.format(row['mgmtIp']))
                    continue
    else:
        logger.error('schema not found: {}'.format(_schema))


def _get_device_id(api, row):
    id = None
    device_id_db = api.custom_caller.call_api('GET', device_id_url)

    for device in device_id_db['response']:
        if device['managementIpAddress'] == row['mgmtIp']:
            id = (device['id'])
            name = (device['hostname'])
    return id


def _get_site_id(api, device_id):
    site_id = None
    devices_db = api.custom_caller.call_api('GET', device_url)

    for device in devices_db['response']:
        if device['networkDeviceId'] == device_id:
            site_id = (device['siteId'])

    return site_id


def _build_vn_handoff_list(row):
    _vn_border_list = row['handoffVNs'].split(',')
    print(_vn_border_list)


def create_transits(api, workflow_dict):
    """ Creates Fabric Transit Networks based on input from workflow_dict. Currently only supports IP Transit

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows with Transit Network Settings required (see schema.yaml);

    :returns: Nothing """

    _schema = 'transit.schema.fabric'
    logger.info('fabric::create_transit')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

    # Get Existing Transits
        result = api.custom_caller.call_api('GET', fabric_url)['response']

        _transit_names = [transit['name'] for transit in result if transit['domainType'] == 'TRANSIT']

        for row in table_data:

            if row['name']:
                if row['presence'] and row['presence'] == "present":
                    if row['name'] not in _transit_names:
                        logger.info('Adding Transit {}'.format(row['name']))
                        data = common.build_json_from_template(templates.transit_j2, row)
                        result = api.custom_caller.call_api('POST', fabric_url, json=data)
                        status = common.wait_for_task_completion(api, result['response'])
                        logger.debug(status)

                    else:
                        logger.warning('Transit {} already exists'.format(row['name']))

                else:
                    logger.info('No Transit Networks to Add')
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_transits(api, workflow_dict):
    """ Deletes Fabric Transit Networks based on input from workflow_dict. Currently only supports IP Transit

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows with Transit Network Settings required (see schema.yaml);

    :returns: Nothing """

    _schema = 'transit.schema.fabric'
    logger.info('fabric::delete_transit')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # transit table with empty rows removed
        _new_transit_db = [transit for transit in table_data if transit['presence'] == 'absent']
        # get existing Transits
        result = api.custom_caller.call_api('GET', fabric_url)['response']
        if _new_transit_db:
            if result:
                _transit_db = [transit for transit in result if transit['domainType'] == 'TRANSIT']
                _transit_names = [transit['name'] for transit in _transit_db]

                for row in _new_transit_db:

                    if row['name']:
                        if row['name'] in _transit_names:
                            transit_id = common.get_object_id(_transit_db, name=row['name'])
                            logger.info('removing Transit {}'.format(row['name']))
                            result = api.custom_caller.call_api('DELETE', "{}/{}".format(fabric_url, transit_id))
                            status = common.wait_for_task_completion(api, result['response'])
                            logger.debug(status)

                        else:
                            logger.info(' Transit {} does not exist in DNAC'.format(row['name']))

        else:
            logger.info('No Transits to Delete')
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all_transits(api, workflow_dict):
    """ Deletes all Fabric Transit Networks.  Use with Caution

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not Used;

    :returns: Nothing """

    _schema = None
    logger.info('fabric::delete_all_transits')
    logger.debug('schema: {}'.format(_schema))

    # get existing Transits
    result = api.custom_caller.call_api('GET', fabric_url)['response']

    # if there are Transit networks lets delete them
    if result:
        _transit_db = [transit for transit in result if transit['domainType'] == 'TRANSIT']
        _transit_names = [(transit['name'], transit['id']) for transit in _transit_db]

        for transit in _transit_names:
            logger.info('removing Transit {}'.format(transit[0]))
            result = api.custom_caller.call_api('DELETE', "{}/{}".format(fabric_url, transit[1]))
            status = common.wait_for_task_completion(api, result['response'])
            logger.debug(status)
    else:
        logger.info('No Transits Networks exist in DNAC')
