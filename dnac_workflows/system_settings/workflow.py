import logging
import common
from system_settings import payload_templates as templates
import yaml
import pkgutil
import time


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


logger = logging.getLogger('main.system_settings')

# URI: GET/POST to list and create/delete ISE Server
aaa_uri = 'api/v1/aaa'


def add_aaa(api, workflow_dict):
    """ Creates DNA Center Global AAA Server based on input from workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows with AAA server settings required (see schema.yaml);

    :returns: Nothing """

    _schema = 'aaa.schema.system_settings'
    logger.info('system_settings::add_aaa')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get Current AAA Servers and get a name list
        _aaa_db = api.custom_caller.call_api('GET', aaa_uri)['response']
        if _aaa_db:
            aaa_ips = [aaa['ipAddress'] for aaa in _aaa_db]
        else:
            aaa_ips = []

        # process each row
        for row in table_data:

            # if present marked and ise not already added to dnac
            if row['presence'] == 'present':
                if row['ipAddress'] not in aaa_ips:
                    logger.info('Adding AAA: {}.  This may take some time...'.format(row['ipAddress']))
                    data = common.build_json_from_template(templates.aaa_j2, row)
                    result = api.custom_caller.call_api('POST', aaa_uri, json=data)
                    status = common.wait_for_task_completion(api, result.response, timeout=60)
                    logger.debug(status)

                    # if added successfully, wait until ise process is completed
                    if not status['response']['isError']:
                        logger.info('Waiting on AAA to move from INPROGRESS to ACTIVE')
                        _wait_on_ise_completion(api, row)

                    else:
                        logger.error(status['response']['failureReason'])
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_aaa(api, workflow_dict):
    """ Deletes DNA Center Global AAA Server based on input from workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows with AAA server settings required (see schema.yaml);

    :returns: Nothing """

    _schema = 'aaa.schema.system_settings'
    logger.info('system_settings::delete_aaa')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get Current AAA Servers and get a name list
        _aaa_db = api.custom_caller.call_api('GET', aaa_uri)['response']

        # TODO Check to make sure ISE not specified in network settings

        if _aaa_db:
            aaa_ips = [aaa['ipAddress'] for aaa in _aaa_db]

            for row in table_data:

                if row['presence'] == 'absent':

                    if row['ipAddress'] in aaa_ips:
                        aaa_id = common.get_object_id(_aaa_db, ipAddress=row['ipAddress'], return_param="instanceUuid")
                        logger.info('Deleting AAA: {}'.format(row['ipAddress']))
                        result = api.custom_caller.call_api('DELETE', "{}/{}".format(aaa_uri, aaa_id))
                        status = common.wait_for_task_completion(api, result.response)
                        logger.debug(status)
                    else:
                        logger.info('system_settings::AAA {} does not exist in system'.format(row['ipAddress']))
        else:
            logger.info('system_settings::No AAA Servers are currently Configured')
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all_aaa(api, workflow_dict):
    """ Deletes all DNA Center Global AAA Servers.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not Used;

    :returns: Nothing """

    _schema = None
    logger.info('system_settings::delete_all_aaa')
    logger.debug('schema: {}'.format(_schema))

    # get Current AAA Servers and get a id list
    _aaa_db = api.custom_caller.call_api('GET', aaa_uri)['response']

    if _aaa_db:
        aaa_ids = [(aaa['instanceUuid'], aaa['ipAddress']) for aaa in _aaa_db]

        for aaa_id in aaa_ids:
            logger.info('Deleting AAA: {}'.format(aaa_id[1]))
            result = api.custom_caller.call_api('DELETE', "{}/{}".format(aaa_uri, aaa_id[0]))
            status = common.wait_for_task_completion(api, result.response)
            logger.debug(status)
    else:
        logger.info('No AAA servers to Delete')


def _wait_on_ise_completion(api, row, timeout=30):
    _result = api.custom_caller.call_api('GET', aaa_uri)

    if _result['response']:
        aaa_server = [aaa for aaa in _result['response'] if aaa['ipAddress'] == row['ipAddress']]
        t = timeout

        while True:
            if aaa_server[0]['state'] == 'INPROGRESS':
                logger.debug(_result)
                logger.debug('sleeping for 2 seconds ...')
                time.sleep(2)
                _result = api.custom_caller.call_api('GET', aaa_uri)
                aaa_server = [aaa for aaa in _result['response'] if aaa['ipAddress'] == row['ipAddress']]
                logger.debug(_result)
                t = t - 2
            elif aaa_server[0]['state'] == 'ACTIVE':
                logger.info('AAA {} now in ACTIVE state'.format(row['ipAddress']))
                logger.debug(_result)
                break
            elif aaa_server[0]['state'] == 'INACTIVE':
                logger.error('AAA {} in INACTIVE state. Please check error logs for more info'.format(row['ipAddress']))
                logger.debug(_result)
                break

            if t < 1:
                logger.info('Timeout waiting for task to complete')
                logger.debug(_result)
                break
