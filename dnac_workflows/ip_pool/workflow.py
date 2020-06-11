import logging
import common
from ip_pool import payload_templates as templates
from jinja2 import Template
import json
import yaml
import pkgutil

logger = logging.getLogger('main.ip_pool')


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


# URI: GET/POST/DELETE to list and create/delete IP Pools
pools_uri = 'api/v2/ippool'
# URI: GET/POST/DELETE to list and create/delete IP Reservations
groups_uri_base = 'api/v2/ippool/group'


def create_pools(api, workflow_dict):
    """ Creates DNA Center IP Pools.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of IP Pool definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ip_pool.schema.ip_pool'
    logger.info('ip_pool::create_pools')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        _ip_pool_db = api.custom_caller.call_api('GET', pools_uri)

        for row in table_data:
            if 'present' in row['presence']:
                _id = common.get_object_id(_ip_pool_db['response'], ipPoolName=row['ipPoolName'])
                if _id is not None:
                    logger.info('IP Pool: {} already exists with id: {}'.format(row['ipPoolName'], _id))
                    pass
                else:
                    logger.info('Creating IP Pool: {}'.format(row['ipPoolName']))
                    data = common.build_json_from_template(templates.ip_pool_j2, row)
                    result = api.custom_caller.call_api('POST', pools_uri, json=data)
                    status = common.wait_for_task_completion(api, result.response)
                    logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_reservations(api, workflow_dict):
    """ Creates DNA Center IP Reservations.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of IP Reservation definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ip_reservation.schema.ip_pool'
    logger.info('ip_pool::create_reservations')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        _ip_pool_db = api.custom_caller.call_api('GET', pools_uri)
        _sites_db = api.sites.get_site()

        for row in table_data:
            if 'present' in row['presence']:
                _site_id = common.get_object_id(_sites_db['response'], siteNameHierarchy=row['siteName'])
                row['_site_id'] = _site_id
                parents = row['ipPoolsParent'].split(',')
                # Fill the row dictionary with the parentUuid for each version of IP in a list
                row['_pool_parent_id'] = []
                row['_pool_parent_id'].append(common.get_object_id(_ip_pool_db['response'], ipPoolName=parents[0]))
                if len(parents) > 1:
                    row['_pool_parent_id'].append(common.get_object_id(_ip_pool_db['response'], ipPoolName=parents[1]))

                groups_uri = '{}?siteId={}'.format(groups_uri_base, _site_id)
                _ip_groups_db = api.custom_caller.call_api('GET', groups_uri)
                _id = common.get_object_id(_ip_groups_db['response'], groupName=row['groupName'])
                # Validate that this reservation doesn't already exist
                if _id is not None:
                    logger.info('Reservation: {} already exists with id: {}'.format(row['groupName'], _id))
                    continue
                # Get the parent name(s) for the reservation
                row['ipPoolsParent'] =  row['ipPoolsParent'].split(',')
                if len(row['ipPoolsParent']) == 1:
                    row['ipPoolsParent'].append(None)
                row['ipPoolCidr'] = row['ipReservation'].split(',')
                # Validate if there is at least one IPv4 ip_address
                if common.get_ip_version(row['ipPoolCidr'][0]) != 4:
                    logger.info('There should be at least one IPv4 address for this reservation')
                    continue
                # Validate if the second address is valid
                if len(row['ipPoolCidr']) > 1 and common.get_ip_version(row['ipPoolCidr'][1]) != 6:
                    logger.info('The second IP address is not a valid IPv6 address')
                    continue
                # Add te DHCP, DNS and gateway addresses
                row['dhcpServerIps'] = _generate_ip_list(row['dhcpServerIps'])
                row['dnsServerIps'] = _generate_ip_list(row['dnsServerIps'])
                row['gateways'] = _generate_ip_list(row['gateways'])
                # Render the template
                template = Template(templates.ip_reservation)
                render = template.render(row)
                data = json.loads(render)

                logger.info('Creating IP Reservation: {}'.format(row['groupName']))
                result = api.custom_caller.call_api('POST', groups_uri_base, json=data)
                status = common.wait_for_task_completion(api, result.response)
                logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_reservations(api, workflow_dict):
    """ Deletes DNA Center IP Pools.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of IP Reservation definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ip_reservation.schema.ip_pool'
    logger.info('ip_pool::delete_reservations')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        _ip_pool_db = api.custom_caller.call_api('GET', pools_uri)
        _sites_db = api.sites.get_site()
        logger.debug('******** _ip_pool_db *********')
        logger.debug(_ip_pool_db)
        logger.debug('******** _sites_db *********')
        logger.debug(_sites_db)

        for row in table_data:
            if 'absent' in row['presence']:
                _site_id = common.get_object_id(_sites_db['response'], siteNameHierarchy=row['siteName'])

                groups_uri = '{}?siteId={}'.format(groups_uri_base, _site_id)
                _ip_groups_db = api.custom_caller.call_api('GET', groups_uri)
                _id = common.get_object_id(_ip_groups_db['response'], groupName=row['groupName'])

                if _id is not None:
                    logger.info('Releasing reservation: {} with id: {}'.format(row['groupName'], _id))
                    delete_uri = '{}/{}'.format(groups_uri_base, _id)
                    result = api.custom_caller.call_api('DELETE', delete_uri)
                    status = common.wait_for_task_completion(api, result.response)
                    logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all_reservations(api, workflow_dict):
    """ Deletes ALL DNA Center IP Reservations.
    This method will not attempt to remove any dependencies
    where IP assignments exist from the reservation.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not used;

    :returns: Nothing """

    _schema = None
    logger.info('ip_pool::delete_all_reservations')
    logger.debug('schema: {}'.format(_schema))

    _ip_pool_db = api.custom_caller.call_api('GET', pools_uri)
    _sites_db = api.sites.get_site()
    for site in _sites_db['response']:
        groups_uri = '{}?siteId={}'.format(groups_uri_base, site['id'])
        _ip_groups_db = api.custom_caller.call_api('GET', groups_uri)
        for ip_reservation in _ip_groups_db['response']:
            logger.info('Releasing reservation: {} with id: {}'.format(ip_reservation['groupName'], ip_reservation['id']))
            delete_uri = '{}/{}'.format(groups_uri_base, ip_reservation['id'])
            result = api.custom_caller.call_api('DELETE', delete_uri)
            status = common.wait_for_task_completion(api, result.response)
            logger.debug(status)


def delete_pools(api, workflow_dict):
    """ Creates DNA Center IP Pools.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of IP Pool definitions (see schema.yaml);

    :returns: Nothing """

    _schema = 'ip_pool.schema.ip_pool'
    logger.info('ip_pool::delete_pools')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        _ip_pool_db = api.custom_caller.call_api('GET', pools_uri)
        logger.debug(_ip_pool_db)

        for row in table_data:
            _sites_db = api.sites.get_site()
            if 'absent' in row['presence']:
                _id = common.get_object_id(_ip_pool_db['response'], ipPoolName=row['ipPoolName'])
                if _id is not None:
                    logger.info('Deleting: {} with id: {}'.format(row['ipPoolName'], _id))
                    _delete_uri = '{}/{}'.format(pools_uri, _id)
                    result = api.custom_caller.call_api('DELETE', _delete_uri, json=common.dot_to_json(row))
                    status = common.wait_for_task_completion(api, result.response)
                    logger.debug(status)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all_pools(api, workflow_dict):
    """ Deletes ALL DNA Center IP Pools.
    This method will not attempt to remove any dependencies
    where IP Reservations exist from the pool.  Please run the
    delete_all_reservations() method first

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not used;

    :returns: Nothing """

    _schema = None
    logger.info('ip_pool::delete_all_pools')
    logger.debug('schema: {}'.format(_schema))

    _ip_pool_db = api.custom_caller.call_api('GET', pools_uri)
    logger.debug(_ip_pool_db)

    for _ip_pool in _ip_pool_db['response']:
        logger.info('Deleting: {} with id: {}'.format(_ip_pool['ipPoolName'], _ip_pool['id']))
        _delete_uri = '{}/{}'.format(pools_uri, _ip_pool['id'])
        result = api.custom_caller.call_api('DELETE', _delete_uri)
        status = common.wait_for_task_completion(api, result.response)
        logger.debug(status)


# Local functions
# Generates a list of lists of IPs
def _generate_ip_list(data):
    temp = [[], []]
    if data is not None:
        for ip in  data.split(','):
            version = common.get_ip_version(ip)
            if version == 4:
                temp[0].append(ip)
            elif version == 6:
                temp[1].append(ip)
    return temp
