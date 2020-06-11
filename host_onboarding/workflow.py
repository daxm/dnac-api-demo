import logging
import common
from host_onboarding import payload_templates as templates
import time
import yaml
import pkgutil

logger = logging.getLogger('main.host_onboarding')

base_sda_pool_uri = "/dna/intent/api/v1/business/sda/virtualnetwork/ippool"
base_sda_segment_uri = "/api/v2/data/customer-facing-service/Segment"
base_wlan_info_uri = "/api/v2/data/customer-facing-service/Wlan"
add_port_uri_base = "/dna/intent/api/v1/business/sda/hostonboarding"


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def assign_pool_to_SSID(api, workflow_dict):
    """ FIXME.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of discovery job definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'wireless_pool.schema.host_onboarding'
    logger.info('host_onboarding::Assign IP Pool to SSID')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        new_assignments = [assignment for assignment in table_data if assignment['presence'] == "present"]

        if new_assignments:

            for assignment in new_assignments:
                # Get pool info (specifically auth policy name
                sda_pool_detail = api.custom_caller.call_api("GET", base_sda_pool_uri,
                                                             params={"ipPoolName": assignment['ipPoolName'],
                                                                     "virtualNetworkName": assignment[
                                                                         'virtualNetworkName']})
                logger.debug(sda_pool_detail)

                # if found successfully lets get full segment info filtered on auth policy name
                if sda_pool_detail['status'] == "success":
                    segment_details = api.custom_caller.call_api("GET",
                                                                 base_sda_segment_uri,
                                                                 params={
                                                                     "name": sda_pool_detail['authenticationPolicyName']})[
                        'response']
                    # if existing SSID assignment get info
                    wlan_info = []

                    for wlan in segment_details[0]['wlan']:
                        if 'idRef' in wlan:
                            data = api.custom_caller.call_api("GET", base_wlan_info_uri, params={"id": wlan['idRef']})[
                                'response']
                            for item in data:
                                wlan_info.append(item)

                    # Get wlan info for new assignment
                    data = api.custom_caller.call_api("GET", base_wlan_info_uri, params={"ssid": assignment['ssid']})[
                        'response']
                    for item in data:
                        wlan_info.append(item)

                    # add wlan info to post request
                    segment_details[0]['wlan'] = wlan_info

                    # Now lets assign IP pool to ssid...
                    logger.info('host onboarding: Assigning IP Pool: {} to SSID: {}'.format(assignment['ipPoolName'],
                                                                                            assignment['ssid']))
                    result = api.custom_caller.call_api("PUT", base_sda_segment_uri, json=segment_details)
                    logger.debug(result)
                    common.wait_for_task_completion(api, result['response'])
                else:
                    logger.error('host onboarding: Assigning IP Pool: {} has not been configured in Host Onboarding'.format(
                        assignment['ipPoolName'],
                        assignment['ssid']))
    else:
        logger.error('schema not found: {}'.format(_schema))


def add_port_assignment(api, workflow_dict):
    """ FIXME.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of discovery job definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ports.schema.host_onboarding'
    logger.info('host onboarding::add port assignment')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get info from db
        port_assignments = [assignment for assignment in table_data if assignment['presence'] == 'present']

        if port_assignments:
            for assignment in port_assignments:
                # provision AP Port
                if assignment['portType'] and assignment['portType'] == "ap":
                    # check to make sure pool is of AP Provisioning
                    segment_db = api.custom_caller.call_api('GET', base_sda_segment_uri)['response']
                    ap_provision_segments = [segment['name'] for segment in segment_db if
                                             segment['isApProvisioning'] == True]

                    # if true assign the port
                    if assignment['dataPoolName'] in ap_provision_segments:
                        logger.info(
                            'host onboarding: Assigning {} to AP Port on Switch {}'.format(assignment['interfaceName'],
                                                                                           assignment['deviceIP']))
                        ap_port_uri = "{}/{}".format(add_port_uri_base, "access-point")
                        data = common.build_json_from_template(templates.port_template_j2, assignment)
                        result = api.custom_caller.call_api('POST', ap_port_uri, json=data)
                        common.wait_for_task_completion(api, result)

                        # rate limited after 5 calls so need to sleep temporarily
                        if len(port_assignments) > 5:
                            time.sleep(12)

                # provision User port
                elif assignment['portType'] and assignment['portType'] == "user":
                    logger.info(
                        'host onboarding: Assigning {} to User Port on Switch {}'.format(assignment['interfaceName'],
                                                                                         assignment['deviceIP']))
                    user_port_uri = "{}/{}".format(add_port_uri_base, "user-device")
                    data = common.build_json_from_template(templates.port_template_j2, assignment)
                    result = api.custom_caller.call_api('POST', user_port_uri, json=data)
                    common.wait_for_task_completion(api, result)

                    # rate limited after 5 calls so need to sleep temporarily
                    if len(port_assignments) > 5:
                        time.sleep(12)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_port_assignment(api, workflow_dict):
    """ FIXME.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of discovery job definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ports.schema.host_onboarding'
    logger.info('host onboarding::delete port assignment')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # The intent api is broken - all ports may not be cleared
        # get info from db
        port_assignments = [assignment for assignment in table_data if assignment['presence'] == 'absent']
        # reverse the list order as bug in api will only allow port clearing in reverse order that they were added
        port_assignments.reverse()

        if port_assignments:
            for assignment in port_assignments:
                if assignment['portType'] and assignment['portType'] == "ap":

                    logger.info('host onboarding: Clearing {}'.format(assignment['interfaceName']))
                    ap_port_uri = "{}/{}".format(add_port_uri_base, "access-point")
                    result = api.custom_caller.call_api('DELETE', ap_port_uri, params={'device-ip': assignment['deviceIP'],
                                                                                       'interfaceName': assignment[
                                                                                           'interfaceName']
                                                                                       })
                    common.wait_for_task_completion(api, result)
                    # rate limited after 5 calls so need to sleep temporarily
                    if len(port_assignments) > 5:
                        time.sleep(12)

                if assignment['portType'] and assignment['portType'] == "user":

                    logger.info('host onboarding: Clearing {}'.format(assignment['interfaceName']))
                    user_port_uri = "{}/{}".format(add_port_uri_base, "user-device")

                    result = api.custom_caller.call_api('DELETE', user_port_uri,
                                                        params={'device-ip': assignment['deviceIP'],
                                                                'interfaceName': assignment['interfaceName']
                                                                })

                    common.wait_for_task_completion(api, result)
                    # rate limited after 5 calls so need to sleep temporarily
                    if len(port_assignments) > 5:
                        time.sleep(12)
    else:
        logger.error('schema not found: {}'.format(_schema))
