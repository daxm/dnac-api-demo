import logging
import common
from network_settings import payload_templates as templates
import json
import yaml
import pkgutil

logger = logging.getLogger('main.network_settings')

# URI:  Base Network Settings
network_settings_intent_uri = "/dna/intent/api/v1/network"
network_settings_uri = "/api/v1/commonsetting/global/-1"


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def create_network_settings(api, workflow_dict):
    """ Creates DNA Center Global Network Settings based on input from workflow_dict.  If adding Client/Network AAA server
    settings, AAA server will need to already be configured in DNA Center.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows Network Settings (DHCP, DNS, etc) (see schema.yaml);

    :returns: Nothing """

    _schema = 'globalSettings.schema.network_settings'
    logger.info('network_settings::create_network_settings')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get settings for config
        settings = {}
        # rearrange into 1 dict so it is easier to work with
        for row in table_data:
            settings[row['item']] = row['value']

        csv_fields = ['dhcpServer', 'syslogServer', 'snmpServer', 'ntpServer']

        # convert csv strings to List
        for field in csv_fields:
            if settings[field]:
                settings[field] = common.csv_string_to_list(settings[field])

        if settings:
            # proceed if site specified - if not exit
            if settings['site']:
                site_info = api.sites.get_site(name=settings['site'])
                site_id = site_info['response'][0]['id'] if site_info['response'] else None

                # build URI and create network settings
                create_network_settings_uri = "{}/{}".format(network_settings_intent_uri, site_id)

                # using json builder from helper file
                data = common.build_json_from_template(templates.network_settings_intent_j2, settings)
                result = api.custom_caller.call_api('POST', create_network_settings_uri, json=data)
                logger.debug(result)
                common.wait_for_task_completion(api, result)
            else:
                logger.error('network_settings::create_network_settings:: Site required to update network settings')
                pass
    else:
        logger.error('schema not found: {}'.format(_schema))

def delete_network_settings(api, workflow_dict):
    """ Deletes DNA Center Global Credentials.  A dummy DNS server and DNs domain are pushed to DNAC due to current limitations

        :param api: An instance of the dnacentersdk.DNACenterAPI class
        :param workflow_dict: Not Used;

        :returns: Nothing """

    #I couldn't get the intent api to delete certain settings so used old api call with blank values populated to delete
    logger.info('network_settings::delete_network_credentials')
    data = json.loads(templates.network_settings_j2)
    result = api.custom_caller.call_api('POST', network_settings_uri, json=data)
    status = common.wait_for_task_completion(api, result['response'])
    logger.debug(status)


def create_global_credentials(api, workflow_dict):
    """ Creates DNA Center Global Credentials.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows credential definitions (cli, snmp-ro/rw) (see schema.yaml);

    :returns: Nothing """

    _schema = 'snmpWrite.schema.network_settings'
    logger.info('network_settings::create_global_credentials::snmpWrite')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # Cycle through the rows and create entries with 'present' set
        for row in table_data:
            if row['presence']:
                if 'present' in row['presence']:
                    _creds = api.network_discovery.get_global_credentials('SNMPV2_WRITE_COMMUNITY')
                    _id = common.get_object_id(_creds['response'], description=row['description'])
                    if _id is not None:
                        logger.info('SNMPV2_WRITE_COMMUNITY exists with id: {}'.format(_id))
                    else:
                        logger.info('Creating SNMPV2_WRITE_COMMUNITY')
                        result = api.network_discovery.create_snmp_write_community(payload=[common.dot_to_json(row)])
                        logger.debug(result)
    else:
        logger.error('schema not found: {}'.format(_schema))

    _schema = 'snmpRead.schema.network_settings'
    logger.info('network_settings::create_global_credentials::snmpRead')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if row['presence']:
                if 'present' in row['presence']:
                    _creds = api.network_discovery.get_global_credentials('SNMPV2_READ_COMMUNITY')
                    _id = common.get_object_id(_creds['response'], description=row['description'])
                    if _id is not None:
                        logger.info('SNMPV2_READ_COMMUNITY exists with id: {}'.format(_id))
                    else:
                        logger.info('Creating SNMPV2_READ_COMMUNITY')
                        result = api.network_discovery.create_snmp_read_community(payload=[common.dot_to_json(row)])
                        logger.debug(result)
    else:
        logger.error('schema not found: {}'.format(_schema))

    _schema = 'cli.schema.network_settings'
    logger.info('network_settings::create_global_credentials::cli')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if row['presence']:
                if 'present' in row['presence']:
                    _creds = api.network_discovery.get_global_credentials('CLI')
                    _id = common.get_object_id(_creds['response'], description=row['description'])
                    if _id is not None:
                        logger.info('CLI exists with id: {}'.format(_id))
                    else:
                        logger.info('Creating CLI credentials for username: {}'.format(row['username']))
                        result = api.network_discovery.create_cli_credentials(payload=[common.dot_to_json(row)])
                        logger.debug(result)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_global_credentials(api, workflow_dict):
    """ Deletes DNA Center Global Credentials based on input from workflow_dict.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of credential definitions (cli, snmp-ro/rw) (see schema.yaml);

    :returns: Nothing """

    _schema = 'snmpWrite.schema.network_settings'
    logger.info('network_settings::delete_global_credentials::snmpWrite')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # Cycle through the rows and create entries with 'present' set
        for row in table_data:
            if 'absent' in row['presence'] and 'writeCommunity' in row.keys():
                _creds = api.network_discovery.get_global_credentials('SNMPV2_WRITE_COMMUNITY')
                _id = common.get_object_id(_creds['response'], description=row['description'])
                if _id is not None:
                    logger.info('Deleting SNMPV2_WRITE_COMMUNITY with id: {}'.format(_id))
                    api.network_discovery.delete_global_credentials_by_id(_id)
                else:
                    logger.info('SNMPV2_WRITE_COMMUNITY with description "{}" does not exist'.format(_id))
    else:
        logger.error('schema not found: {}'.format(_schema))

    _schema = 'snmpRead.schema.network_settings'
    logger.info('network_settings::delete_global_credentials::snmpRead')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if 'absent' in row['presence'] and 'readCommunity' in row.keys():
                _creds = api.network_discovery.get_global_credentials('SNMPV2_READ_COMMUNITY')
                _id = common.get_object_id(_creds['response'], description=row['description'])
                if _id is not None:
                    logger.info('Deleting SNMPV2_READ_COMMUNITY with id: {}'.format(_id))
                    api.network_discovery.delete_global_credentials_by_id(_id)
                else:
                    logger.info('SNMPV2_READ_COMMUNITY with description "{}" does not exist'.format(_id))
    else:
        logger.error('schema not found: {}'.format(_schema))

    _schema = 'cli.schema.network_settings'
    logger.info('network_settings::delete_global_credentials::cli')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if 'absent' in row['presence'] and 'username' in row.keys():
                _creds = api.network_discovery.get_global_credentials('CLI')
                _id = common.get_object_id(_creds['response'], description=row['description'])
                if _id is not None:
                    logger.info('Deleting CLI with id: {}'.format(_id))
                    api.network_discovery.delete_global_credentials_by_id(_id)
                else:
                    logger.info('CLI with description "{}" does not exist'.format(_id))
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all_global_credentials(api, workflow_dict):
    """ Deletes All DNA Center Global Credentials.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not Used;

    :returns: Nothing """

    _schema = None
    logger.info('network_settings::delete_all_global_credentials')
    logger.debug('schema: {}'.format(_schema))

    logger.info('network_settings::delete_all_global_credentials')
    _credential_types = [
        'SNMPV2_WRITE_COMMUNITY',
        'SNMPV2_READ_COMMUNITY',
        'CLI',
        'SNMPV3',
        'HTTP_WRITE',
        'HTTP_READ',
        'NETCONF'
    ]

    for _type in _credential_types:
        _creds = api.network_discovery.get_global_credentials(_type)
        for _cred in _creds['response']:
            logger.info('Deleting {} with name: {} and id: {}'.format(_type, _cred['description'], _cred['id']))
            result = api.network_discovery.delete_global_credentials_by_id(_cred['id'])
            status = common.wait_for_task_completion(api, result.response)
            logger.debug(status)
