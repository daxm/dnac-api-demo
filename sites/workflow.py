import logging
import common
import requests
import json
import yaml
from sites import payload_templates as templates
import pkgutil

logger = logging.getLogger('main.sites')


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


def create(api, workflow_dict):
    """ Creates DNA Center areas, sites and floors.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of sites (see schema.py);

    :returns: Nothing """

    _schema = 'sites.schema.sites'
    logger.info('sites::create')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        _sites_db = api.sites.get_site()

        _create_areas(api, _sites_db['response'], table_data)
        _create_buildings(api, _sites_db['response'], table_data)
        _create_floors(api, _sites_db['response'], table_data)
    else:
        logger.error('schema not found: {}'.format(_schema))


def _create_areas(api, sites_db, table_data):

    _table_key = 'name'

    # Cycle through the rows and create entries with 'present' set
    for row in table_data:
        if 'present' in row['presence'] and 'area' in row['type']:
            site_name_hierarchy = '{}/{}'.format(row['parentName'], row['name'])
            _id = common.get_object_id(sites_db, siteNameHierarchy=site_name_hierarchy)
            if _id is not None:
                logger.info('Area: {}/{} already exists with id: {}'.format(row['parentName'], row[_table_key], _id))
            else:
                logger.info('Creating area: {}/{}'.format(row['parentName'], row[_table_key]))

                data = common.build_json_from_template(templates.area_j2, row)

                logger.debug('Site payload: {}'.format(data))
                result = api.sites.create_site(__runsync=True, payload=data)
                status = common.wait_for_task_completion(api, result)
                logger.debug(status)


def _create_buildings(api, sites_db, table_data):
    _table_key = 'name'

    # Cycle through the rows and create entries with 'present' set
    for row in table_data:
        if 'present' in row['presence'] and 'building' in row['type']:
            site_name_hierarchy = '{}/{}'.format(row['parentName'], row['name'])
            _id = common.get_object_id(sites_db, siteNameHierarchy=site_name_hierarchy)
            if _id is not None:
                logger.info('Building: {}/{} already exists with id: {}'.format(row['parentName'], row[_table_key], _id))
            else:
                logger.info('Creating building: {}/{}'.format(row['parentName'], row[_table_key]))

                data = common.build_json_from_template(templates.building_j2, row)

                data['site']['building']['address'] = '{}, {}, {}'.format(
                    row['street'],
                    row['city'],
                    row['country']
                )

                # If lat and lon are defined, they are used instead of _address_lookup
                if row['latitude'] is not None and row['longitude'] is not None:
                    data['site']['building']['longitude'] = float(row['longitude'])
                    data['site']['building']['latitude'] = float(row['latitude'])
                else:
                    location = _address_lookup(row['street'], row['city'], row['country'])
                    if location is not None:
                        logger.info('Address lookup: SUCCESS')
                        data['site']['building']['address'] = location['address']
                        data['site']['building']['longitude'] = float(location['lon'])
                        data['site']['building']['latitude'] = float(location['lat'])
                    else:
                        logger.info('Address lookup: FAILURE')

                logger.debug('Building payload: {}'.format(data))
                result = api.sites.create_site(payload=data)
                status = common.wait_for_task_completion(api, result)
                logger.debug(status)


def _create_floors(api, sites_db, table_data):
    _table_key = 'name'

    # Cycle through the rows and create entries with 'present' set
    for row in table_data:
        if 'present' in row['presence'] and 'floor' in row['type']:
            site_name_hierarchy = '{}/{}'.format(row['parentName'], row['name'])
            _id = common.get_object_id(sites_db, siteNameHierarchy=site_name_hierarchy)
            if _id is not None:
                logger.info('Floor: {}/{} already exists with id: {}'.format(row['parentName'], row[_table_key], _id))
            else:
                logger.info('Creating floor: {}/{}'.format(row['parentName'], row[_table_key]))

                data = common.build_json_from_template(templates.floor_j2, row)

                logger.debug('Building payload: {}'.format(data))
                result = api.sites.create_site(payload=data)
                status = common.wait_for_task_completion(api, result)
                logger.debug(status)


def delete(api, workflow_dict):
    """ Deletes DNA Center areas, sites and floors.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of sites (see schema.py);

    :returns: Nothing """

    _schema = 'sites.schema.sites'
    logger.info('sites::delete')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            _sites_db = api.sites.get_site()
            _deleted_sites = []
            if 'absent' in row['presence']:
                site_name_hierarchy = '{}/{}'.format(row['parentName'], row['name'])
                _id = common.get_object_id(_sites_db['response'], siteNameHierarchy=site_name_hierarchy)
                if _id is not None:
                    # When deleting a site we need to figure out the children and delete in reverse
                    _child_list_sorted = _get_sorted_child_list(_sites_db['response'], _id)
                    for _child in _child_list_sorted:
                        logger.info('Deleting site: {}'.format(_child[0]))
                        logger.debug('Deleting: {} with id: {}'.format(_child[0], _child[1]))
                        if _child[1] not in _deleted_sites:
                            result = api.sites.delete_site(site_id=_child[1])
                            status = common.wait_for_task_completion(api, result)
                            logger.debug(status)
                            _deleted_sites.append(_child[1])
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all(api, workflow_dict):
    """ Deletes ALL DNA Center areas, sites and floors.
    This task will calculate the order in which floors, sites, areas
    will need to be removed however it will not attempt to remove any
    dependencies such as IP Reservations or assigned devices.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not used;

    :returns: Nothing """

    _schema = None
    logger.info('sites::delete_all')
    logger.debug('schema: {}'.format(_schema))

    _sites_db = api.sites.get_site()
    _deleted_sites = []
    for _site in _sites_db['response']:
        _id = _site['id']
        _child_list_sorted = _get_sorted_child_list(_sites_db['response'], _id)
        for _child in _child_list_sorted:
            if _child[1] not in _deleted_sites and _child[0] != "Global":
                logger.info('Deleting site: {}'.format(_child[0]))
                logger.debug('Deleting: {} with id: {}'.format(_child[0], _child[1]))
                result = api.sites.delete_site(site_id=_child[1])
                status = common.wait_for_task_completion(api, result)
                logger.debug(status)
                _deleted_sites.append(_child[1])

# Internal functions


def _get_sorted_child_list(site_db, _id):
    # Find our site and get the siteHierarchy
    _site_tuple_list = []
    for site in site_db:
        if _id == site['id']:
            _site_hierarchy = site['siteHierarchy']

    for site in site_db:
        if _site_hierarchy in site['siteHierarchy']:
            _child_id = site['id']
            _child_depth = len(site['siteHierarchy'].split('/'))
            _child_name = site['siteNameHierarchy']

            site_tuple = (_child_name, _child_id, _child_depth)
            _site_tuple_list.append(site_tuple)

    return sorted(_site_tuple_list, key=lambda tup: tup[2], reverse=True)


def _address_lookup(street, city, country):
    maps_url = 'https://nominatim.openstreetmap.org/search?format=json&'
    search_string = 'street={}&city={}&country={}'.format(street, city, country)

    search_url = '{}&{}'.format(maps_url, search_string)
    try:
        response = requests.get(search_url)
    except requests.exceptions.Timeout:
        logger.error('GET towards OSM timeout')
        return None
    except requests.exceptions.RequestException as e:
        print(e)
        return None

    search_result = json.loads(response.text)
    if len(search_result) == 1:
        location = {
            'address': search_result[0]['display_name'],
            'lat': search_result[0]['lat'],
            'lon': search_result[0]['lon']
        }
        return location
    else:
        return None
