
import logging
import common
import time
from discovery import payload_templates as templates
import yaml
import pkgutil

logger = logging.getLogger('main.discovery')

# URI: GET existing discoveries
discovery_url = '/api/v1/discovery'
# URI:  Base Network Settings
network_settings_intent_uri = "/dna/intent/api/v1/network"


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def run_discovery(api, workflow_dict):
    """ Initiates DNA Center Device Discovery based on input from workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of discovery job definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'discovery.schema.discovery'
    logger.info('discovery::run_discovery')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        get_discoveries_url = '{}/1/99'.format(discovery_url)

        # Cycle through the rows and create entries with 'present' set
        for row in table_data:
            if row['presence'] and 'present' in row['presence']:

                # URI: GET to discover ID of existing discoveries so that we can delete/update
                _discovery = api.custom_caller.call_api('GET', get_discoveries_url)
                _id = common.get_object_id(_discovery['response'], name=row['name'])

                if _id is not None:
                    data = { 'id': _id, 'discoveryStatus': 'Active'}
                    # URI: PUT to start/rerun an existing discovery
                    # discovery_url = 'api/v1/discovery'
                    result = api.custom_caller.call_api('PUT', discovery_url, json=data)
                    logger.info('Waiting a few seconds for discovery to start ...')
                    time.sleep(5)
                    status = common.wait_for_task_completion(api, result['response'], timeout=30)
                    logger.debug(status)
                    _wait_for_discovery_to_complete(api, _id)

                else:

                    _creds = []

                    _cli = api.network_discovery.get_global_credentials('CLI')
                    _id = common.get_object_id(_cli['response'], description=row['cli'])
                    _creds.append(_id)

                    _cli = api.network_discovery.get_global_credentials('SNMPV2_READ_COMMUNITY')
                    _id = common.get_object_id(_cli['response'], description=row['snmp_ro'])
                    _creds.append(_id)

                    _cli = api.network_discovery.get_global_credentials('SNMPV2_WRITE_COMMUNITY')
                    _id = common.get_object_id(_cli['response'], description=row['snmp_rw'])
                    _creds.append(_id)

                    _discovery_range = '{}-{}'.format(row['startIp'], row['endIp'])
                    row.update({'discovery_range': _discovery_range})

                    data = common.build_json_from_template(templates.discovery_j2, row)
                    data['globalCredentialIdList'] = _creds
                    logger.info('Adding discovery ... ')
                    result = api.network_discovery.start_discovery(payload=data)
                    status = common.wait_for_task_completion(api, result['response'])
                    logger.debug(status)

                    _discovery = api.custom_caller.call_api('GET', get_discoveries_url)
                    _id = common.get_object_id(_discovery['response'], name=row['name'])
                    _wait_for_discovery_to_complete(api, _id)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_discovery(api, workflow_dict):
    """ Deletes DNA Center Device Discoveries based on input from workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of discovery job definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'discovery.schema.discovery'
    logger.info('discovery::delete_discovery')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # Cycle through the rows and create entries with 'absent' set
        for row in table_data:
            if row['presence'] and 'absent' in row['presence']:
                # URI: GET to discover ID of existing discoveries so that we can delete/update
                _discovery = api.custom_caller.call_api('GET', '/api/v1/discovery/1/10')
                _id = common.get_object_id(_discovery['response'], name=row['name'])
                if _id is not None:
                    logger.info('Deleting discovery with id: {}'.format(_id))
                    api.network_discovery.delete_discovery_by_id(_id)
                else:
                    logger.info('Discovery with name "{}" does not exist'.format(row['name']))
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all_discovery(api, workflow_dict):

    """ Deletes ALL DNA Center Device Discoveries.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not Used;

    :returns: Nothing """

    _schema = None
    logger.info('discovery::delete_all_discovery')
    logger.debug('schema: {}'.format(_schema))

    _discoveries = api.custom_caller.call_api('GET', '/api/v1/discovery/1/99')
    for _discovery in _discoveries['response']:
        logger.info('Deleting discovery with id: {}'.format(_discovery['id']))
        api.network_discovery.delete_discovery_by_id(_discovery['id'])


def _wait_for_discovery_to_complete(api, discovery_id, timeout=30):

    time.sleep(10)
    # URI: GET to discover the status of a discovery and wait for completion
    discovery_status_url = '{}/{}/job/'.format(discovery_url, discovery_id)
    discovery_status = api.custom_caller.call_api('GET', discovery_status_url)

    t = timeout
    if len(discovery_status['response']) > 0:
        while True:
            if discovery_status['response'][0]['jobStatus'] == 'RUNNING':
                logger.debug(discovery_status)
                logger.debug('sleeping for 2 seconds ...')
                time.sleep(2)
                discovery_status = api.custom_caller.call_api('GET', discovery_status_url)
                logger.debug(discovery_status)
                t = t - 2
            elif discovery_status['response'][0]['jobStatus'] == 'SUCCESS':
                logger.info('Discovery "{}" completed with SUCCESS'.format(discovery_id))
                logger.debug(discovery_status)
                break
            else:
                logger.info('Something unexpected happened with discovery {}'.format(discovery_id))
                logger.debug(discovery_status)
                break

            if t < 1:
                logger.info('Timeout waiting for task to complete')
                logger.debug(discovery_status)
                break
    else:
        logger.error('Not able to retrieve discovery')

    return discovery_status
