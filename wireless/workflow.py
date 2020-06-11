import logging
import common
import json
from wireless import payload_templates as templates
import yaml
import pkgutil


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


logger = logging.getLogger('main.wireless')

wireless_int_url = "/api/v1/commonsetting/global/-1?key=interface.info"
temp_get_wireless_profile_url = "/api/v1/siteprofile?namespace=wlan"


def create_enterprise_ssid(api, workflow_dict):
    """ Creates DNA Center Enterprise SSIDs.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of Enterprise SSID definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ssids.schema.wireless'
    logger.info('wireless::create_enterprise_ssid')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        _ent_ssid_db = api.non_fabric_wireless.get_enterprise_ssid()

        # Get existing SSID List
        ssid_list = []
        for item in _ent_ssid_db,:

            if item:
                for wlan_profile in item:
                    for ssid in wlan_profile['ssidDetails']:
                        ssid_list.append(ssid['name'])
            else:
                ssid_list = []

        for row in table_data:
            if 'present' in row['presence']:
                if row['name'] in ssid_list:
                    logger.info('SSID: {} already exists'.format(row['name']))
                    pass
                else:
                    logger.info('Creating Enterprise SSID: {}'.format(row['name']))
                    data = common.build_json_from_template(templates.ssid_j2, row)
                    result = api.non_fabric_wireless.create_enterprise_ssid(payload=data)
                    logger.debug(result)
                    common.wait_for_task_completion(api, result)
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_wireless_profile(api, workflow_dict):
    """ Creates DNA Center Wireless Profiles.  Use for creation of new wireless profiles.  If updating profile
    see "update_wireless_profile"

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of Wireless Profiles with associated parameters. (see schema.yaml);

    :returns: Nothing """

    _schema = 'wireless_profiles.schema.wireless'
    logger.info('wireless::create_wireless_profile')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # Intent api broken when GET for wireless profile and no current values
        # _ent_profile_db = api.non_fabric_wireless.get_wireless_profile()

        # Work around Hack

        result = api.custom_caller.call_api('GET', temp_get_wireless_profile_url)
        _ent_profile_db = result['response']

        # Get current profile names
        if _ent_profile_db:
            profile_list = [profile['name'] for profile in _ent_profile_db]
        else:
            profile_list = []

        for row in table_data:
            if 'present' in row['presence']:

                # If sites comma separated, split them up into a list
                if "," in row['sites']:
                    row['sites'] = row['sites'].split(",")
                    row['sites'] = [item.lstrip() for item in row['sites']]
                else:
                    row['sites'] = [row['sites']]

                if row['profileName'] in profile_list:
                    logger.info('Profile: {} already exists'.format(row['profileName']))
                    pass
                else:
                    logger.info('Creating Profile: {}'.format(row['profileName']))
                    data = common.build_json_from_template(templates.wireless_profile_j2, row)
                    result = api.non_fabric_wireless.create_wireless_profile(payload=data)
                    logger.debug(result)
                    common.wait_for_task_completion(api, result)
    else:
        logger.error('schema not found: {}'.format(_schema))


def update_wireless_profile(api, workflow_dict):
    """ Updates DNA Center Wireless Profiles.  Use for updating of existing wireless profiles.  If creating profile
    see "create_wireless_profile"

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of Wireless Profiles with associated parameters. (see schema.yaml);

    :returns: Nothing """

    _schema = 'wireless_profiles.schema.wireless'
    logger.info('wireless::update_wireless_profile')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

    # API does not seem to like setting SSID info during create process so have to use update to add SSID details
        for row in table_data:
            if 'present' in row['presence']:

                # Get current profile names
                _ent_profile_db = api.non_fabric_wireless.get_wireless_profile()
                # Get Current Profiles
                profile_list = [profile['profileDetails']['name'] for profile in _ent_profile_db]

                # If sites comma separated, split them up into a list
                if "," in row['sites']:
                    row['sites'] = row['sites'].split(",")
                    row['sites'] = [item.lstrip() for item in row['sites']]
                else:
                    row['sites'] = [row['sites']]

                # filter out mapping for specific profile in row
                filtered_mappings = [mappings for mappings in workflow_dict['ssid_to_profile_mapping.schema.wireless']
                                     if mappings['profileName'] == row['profileName']
                                     and mappings['presence'] == "present"]

                row['ssidDetails'] = filtered_mappings

                if row['profileName'] in profile_list:
                    logger.info('Updating Profile: {}'.format(row['profileName']))
                    data = common.build_json_from_template(templates.wireless_profile_j2, row)
                    result = api.non_fabric_wireless.update_wireless_profile(payload=data)
                    logger.debug(result)
                    common.wait_for_task_completion(api, result)
                else:
                    logger.info('Profile: {} does not exist'.format(row['profileName']))
                    pass
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_wireless_interface(api, workflow_dict):
    # consider moving this as a child function

    """ Creates DNA Center Wireless Over The Top (OTT) Interfaces.  If using OTT, wireless interfaces will need to be created
    before assigning them to a wireless profile

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of Wireless info with associated parameters. (see schema.yaml);

    :returns: Nothing """

    _schema = 'ssid_to_profile_mapping.schema.wireless'
    logger.info('wireless::create_wireless_interface')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # create list of to be added interface mappings if they do not exist in current mappings
        new_interface_mappings = [
            {
                "interfaceName": interface['interfaceNameOTT'],
                "vlanId": interface['ottVlan']
             }
            for interface in table_data if interface['interfaceNameOTT'] is not None and interface['presence'] == "present"
        ]

        # if new interfaces proceed to adding new interfaces
        if new_interface_mappings:

            # get current wireless interfaces as PUT is not supported so we need to post all interfaces when adding a
            # new one
            result = api.custom_caller.call_api('GET', wireless_int_url)
            current_wireless_interfaces = result['response'][0]['value']

            # create list of current interface mappings
            current_interface_mappings = [
                {
                    "interfaceName": interface['interfaceName'],
                    "vlanId": interface['vlanId']
                }
                for interface in current_wireless_interfaces if interface['interfaceName'] is not None
            ]
            current_int_names = [current_interface['interfaceName'] for current_interface in current_interface_mappings]

            # add new interfaces to current list
            for interface in new_interface_mappings:
                if interface["interfaceName"] not in current_int_names:
                    current_interface_mappings.append(
                        {"interfaceName": interface['interfaceName'], "vlanId": interface['vlanId']})

            # format list and send create request
            current_interface_mappings = json.dumps(current_interface_mappings)
            logger.info('Creating Wireless Interfaces ')
            data = common.build_json_from_template(templates.wireless_interface_j2, current_interface_mappings)
            result = api.custom_caller.call_api('POST', wireless_int_url, json=data)
            logger.debug(result)
            common.wait_for_task_completion(api, result['response'])
        else:
            logger.info('Creating Wireless Interfaces: No Wireless interfaces to Create')
            pass
    else:
        logger.error('schema not found: {}'.format(_schema))


def provision_wireless_device(api, workflow_dict):
    """ Provisions  Wireless LAN Controllers (WLCs) in Cisco DNA Center.  Flexconnect and OTT interface parameters (if in use) are required input
    or provision will fail

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of Wireless WLCs with associated parameters. (see schema.yaml);

    :returns: Nothing """

    _schema = 'wireless_provisioning.schema.wireless'
    logger.info('wireless::provision_wireless_device')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get devices to be provisioned.
        new_provision_devices = [device for device in table_data if device['presence'] == 'present']

        if new_provision_devices:
            for device in new_provision_devices:
                # break up managed locations if csv
                if "," in device['managedAPLocations']:
                    device['managedAPLocations'] = device['managedAPLocations'].split(",")
                else:
                    device['managedAPLocations'] = [device['managedAPLocations']]
                # #get IP interface configs for specific WLC
                # Needed for centrail SSID's but not yet implemented
                wireless_int_detail = [detail for detail in workflow_dict['wireless_profisioning_interface.schema.wireless']
                                       if detail['deviceName'] == device['deviceName'] and detail['presence'] == 'present']
                if wireless_int_detail:
                    device['dynamicInterfaces'] = wireless_int_detail

                logger.info('Provisioning WLC: {}'.format(device['deviceName']))
                data = common.build_json_from_template(templates.provision_j2, device)
                result = api.non_fabric_wireless.provision(payload=data)
                logger.debug(result)
                common.wait_for_task_completion(api, result, timeout=30)
        else:
            logger.info('Provisioning WLC:  No WLCs to Provision')
            pass
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_wireless(api, workflow_dict):
    """ Deletes wireless SSID's, profiles, and interfaces specified in workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of wireless information (see schema.yaml);

    :returns: Nothing """

    _schema = 'ssids.schema.wireless'
    logger.info('wireless::delete_wireless::ssids')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # SSID's to remove
        ssids = [ssid['name'] for ssid in table_data if ssid['presence'] == "absent"]

        # delete new SSIDs
        if ssids:
            for ssid in ssids:
                logger.info('Delete Wireless::delete SSID {}'.format(ssid))
                result = api.non_fabric_wireless.delete_enterprise_ssid(ssid)
                logger.debug(result)
                common.wait_for_task_completion(api, result)
        else:
            logger.info('Delete Wireless:  No SSIDs to delete')
    else:
        logger.error('schema not found: {}'.format(_schema))

    _schema = 'wireless_profiles.schema.wireless'
    logger.info('wireless::delete_wireless::wireless_profiles')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        profiles = [profile['profileName'] for profile in table_data if profile['presence'] == "absent"]

        # remove wireless Profiles
        if profiles:

            for profile in profiles:
                no_site_profile = {'profileName': profile, 'sites': ""}

                # remove sites from profile
                data = common.build_json_from_template(templates.wireless_profile_j2, no_site_profile)
                result = api.non_fabric_wireless.update_wireless_profile(payload=data)
                logger.debug(result)
                common.wait_for_task_completion(api, result)

                # now good to delete profile
                logger.info('Delete Wireless::delete Profile {}'.format(profile))
                wireless_profile_delete_url = "/dna/intent/api/v1/wireless-profile/{}".format(profile)
                result = api.custom_caller.call_api('DELETE', wireless_profile_delete_url)
                logger.debug(result)
                common.wait_for_task_completion(api, result)
        else:
            logger.info('Delete Wireless:  No Profiles to delete')
    else:
        logger.error('schema not found: {}'.format(_schema))

    _schema = 'ssid_to_profile_mapping.schema.wireless'
    logger.info('wireless::delete_wireless::ssid_to_profile_mapping')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]
        # delete wireless interfaces
        # Get current interface list
        result = api.custom_caller.call_api('GET', wireless_int_url)
        current_wireless_interfaces = result['response'][0]['value']
        # Get interfaces to remove
        interfaces_to_remove = [interface['interfaceNameOTT'] for interface in table_data
                                if interface['interfaceNameOTT'] is not None and interface['presence'] == "absent"]

        # create remove targeted interfaces from list and post new list
        if interfaces_to_remove:
            interfaces = json.dumps([interface for interface in current_wireless_interfaces
                                     if interface['interfaceName'] not in interfaces_to_remove])
            logger.info('Deleting Wireless Interfaces ')
            data = common.build_json_from_template(templates.wireless_interface_j2, interfaces)
            result = api.custom_caller.call_api('POST', wireless_int_url, json=data)
            logger.debug(result)
            common.wait_for_task_completion(api, result['response'])
        else:
            logger.info('Delete Wireless:  No Wireless Interfaces to delete')
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all(api, workflow_dict):
    """ Deletes all Wireless Design Information regardless of input from workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not used;

    :returns: Nothing """

    _schema = None
    logger.info('wireless::delete all')
    logger.debug('schema: {}'.format(_schema))

    # SSID's to remove
    ssids = api.non_fabric_wireless.get_enterprise_ssid()

    # delete SSIDs
    if ssids:
        for ssid in ssids:
            for detail in ssid['ssidDetails']:
                logger.info('Delete Wireless::delete SSID {}'.format(detail['name']))
                result = api.non_fabric_wireless.delete_enterprise_ssid(detail['name'])
                logger.debug(result)
                common.wait_for_task_completion(api, result)
    else:
        logger.info('Delete Wireless:  No SSIDs to delete')

    # delete profiles

    try:
        profiles = api.non_fabric_wireless.get_wireless_profile()

        if profiles:

            for profile in profiles:
                no_site_profile = {'profileName': profile['profileDetails']['name'], 'sites': ""}

                # remove sites from profile
                data = common.build_json_from_template(templates.wireless_profile_j2, no_site_profile)
                result = api.non_fabric_wireless.update_wireless_profile(payload=data)
                logger.debug(result)
                common.wait_for_task_completion(api, result)

                # now good to delete profile
                logger.info('Delete Wireless::delete Profile {}'.format(profile['profileDetails']['name']))
                wireless_profile_delete_url = "/dna/intent/api/v1/wireless-profile/{}".format(
                    profile['profileDetails']['name'])
                result = api.custom_caller.call_api('DELETE', wireless_profile_delete_url)
                logger.debug(result)
                common.wait_for_task_completion(api, result)

    except:
        logger.info('delete_all::no wireless profiles found')

    # delete wireless interfaces.  Can't delete management so we have to make sure it is added
    interface = json.dumps([{"interfaceName": "management", "vlanId": 0}])
    data = common.build_json_from_template(templates.wireless_interface_j2, interface)
    result = api.custom_caller.call_api('POST', wireless_int_url, json=data)
    logger.debug(result)
    common.wait_for_task_completion(api, result['response'])
