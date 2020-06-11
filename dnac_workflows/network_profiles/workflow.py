import logging
import common
from network_profiles import payload_templates as templates
import yaml
import pkgutil

logger = logging.getLogger('main.network_profiles')

network_profile_base_url = "/api/v1/siteprofile"


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


# TODO Maybe break this up into multiple functions later, IDK
# TODO Update get template available to log message if template not available for specified product series
def create_network_profile(api, workflow_dict):
    """ Creates switching Network Profiles.  Wireless profile creation is handled
    in wireless module.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of network profiles (see schema.py);

    :returns: Nothing """

    _schema = 'network_profiles.schema.network_profiles'
    logger.info('network_profiles::create_network_profiles')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get profiles to be created
        new_profiles = [profile for profile in table_data if profile['presence'] == 'present']

        if new_profiles:
            # check for dupe profile names
            result = api.custom_caller.call_api('GET', network_profile_base_url, params={"namespace": "switching"})
            current_profiles = result['response']
            current_profile_names = [profile['name'] for profile in current_profiles]

            # get site ids
            sites = api.sites.get_site()

            # now create it
            for profile in new_profiles:
                if profile['name'] in current_profile_names:
                    logger.info('network_profiles:: {} already exists'.format(profile['name']))
                    pass

                else:
                    logger.info('network profiles: Creating {}'.format(profile['name']))
                    data = common.build_json_from_template(templates.add_profile_j2, profile)
                    result = api.custom_caller.call_api('POST', network_profile_base_url, json=data)
                    logger.debug(result)
                    create_result = common.wait_for_task_completion(api, result['response'])

                    # if successful creation lets move on to adding sites
                    if create_result['response']['isError'] == False:
                        data = api.custom_caller.call_api('GET', network_profile_base_url, params={"name": profile['name']})
                        profile['id'] = data['response'][0]['siteProfileUuid']
                        # if location then assign it to profile
                        # split up sites if csv
                        if profile['sites']:
                            logger.info('network_profiles::update_site')
                            profile['sites'] = common.csv_string_to_list(profile['sites'])

                            # get site id and add it to profile
                            for new_site in profile['sites']:
                                site_id = common.get_object_id(sites['response'], siteNameHierarchy=new_site)
                                site_add_url = "{}/{}/site/{}".format(network_profile_base_url, profile['id'], site_id)
                                result = api.custom_caller.call_api('POST', site_add_url)
                                logger.debug(result)
                                common.wait_for_task_completion(api, result['response'])

                        # Assign templates to profile
                        # first build out objects needed starting with day0
                        if profile['day0Template'] or profile['cliTemplate']:
                            if profile['day0Template']:
                                day0_list = common.csv_string_to_list(profile['day0Template'])
                                day0_obj = []
                                if profile['product_series']:
                                    template_db = api.template_programmer.gets_the_templates_available(
                                        product_family="Switches and Hubs",
                                        product_series=profile['product_series']
                                    )
                                else:
                                    template_db = api.template_programmer.gets_the_templates_available(
                                        productFamily="Switches and Hubs")

                                # build object with names/ids
                                for template in day0_list:

                                    for item in template_db:

                                        if item['name'] == template:
                                            # Get latest version
                                            version_list = [version['version'] for version in item['versionsInfo']]
                                            version = max(version_list)
                                            # Update Object
                                            day0_obj.append(
                                                {"name": item['name'], "id": item['templateId'], "version": version})
                                profile['day0Template'] = day0_obj

                            # now build day 1 objects
                            if profile['cliTemplate']:
                                day1_list = common.csv_string_to_list(profile['cliTemplate'])
                                day1_obj = []

                                if profile['product_series']:
                                    template_db = api.template_programmer.gets_the_templates_available(
                                        product_family="Switches and Hubs",
                                        product_series=profile['product_series']
                                    )
                                else:
                                    template_db = api.template_programmer.gets_the_templates_available(
                                        product_family="Switches and Hubs")

                                # build object with names/ids
                                for template in day1_list:

                                    for item in template_db:

                                        if item['name'] == template:
                                            # Get latest version
                                            version_list = [version['version'] for version in item['versionsInfo']]
                                            version = max(version_list)
                                            # Update Object
                                            day1_obj.append(
                                                {"name": item['name'], "id": item['templateId'], "version": version})

                                # update profile with additional info needed (id,version #)
                                profile['cliTemplate'] = day1_obj

                            logger.info('network profiles::adding templates')
                            data = common.build_json_from_template(templates.add_templates_to_profile_j2, profile)
                            add_template_profile_url = "{}/{}".format(network_profile_base_url, profile['id'])
                            result = api.custom_caller.call_api('PUT', add_template_profile_url, json=data)
                            logger.debug(result)
                            common.wait_for_task_completion(api, result['response'])

                        else:
                            logger.info('network profiles:: No Templates to add')
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_network_profiles(api, workflow_dict):
    """ Deletes switching Network Profiles configured based oo input from workflow_dict.  Wireless profile deletion is handled
    by wireless delete function.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of network profiles (see schema.py);

    :returns: Nothing """

    _schema = 'network_profiles.schema.network_profiles'
    logger.info('network_profiles::delete_network_profiles')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        # get profile list to delete marked as absent
        profiles = [profile for profile in table_data if profile['presence'] == 'absent' and profile['name']]
        # get site ids
        sites = api.sites.get_site()
        # remove Profiles
        if profiles:

            for profile in profiles:
                # TODO This is the second time for this to be used... maybe create a function
                # get current sites and site ids
                data = api.custom_caller.call_api('GET', network_profile_base_url, params={"name": profile['name']})
                if data['response']:
                    profile['id'] = data['response'][0]['siteProfileUuid']

                    # if location then assign it to profile
                    # split up sites if csv
                    if profile['sites']:
                        logger.info('network_profiles::delete_site')
                        profile['sites'] = common.csv_string_to_list(profile['sites'])

                        # get site id and add it to profile
                        for new_site in profile['sites']:
                            site_id = common.get_object_id(sites['response'], siteNameHierarchy=new_site)
                            site_add_url = "{}/{}/site/{}".format(network_profile_base_url, profile['id'], site_id)
                            result = api.custom_caller.call_api('DELETE', site_add_url)
                            logger.debug(result)
                            common.wait_for_task_completion(api, result['response'])
                    else:
                        logger.info('network_profiles:  No Sites to delete')

                    # Now delete the profile
                    logger.info('network profiles: Deleting {}'.format(profile['name']))
                    profile_url = "{}/{}".format(network_profile_base_url, profile['id'])
                    result = api.custom_caller.call_api('DELETE', profile_url)
                    logger.debug(result)
                    common.wait_for_task_completion(api, result['response'])
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_all(api, workflow_dict):
    """ Deletes all switching Network Profiles regardless of input from workflow_dict.  Wireless profile deletion is handled
    by wireless delete_all function.

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: Not used;

    :returns: Nothing """

    _schema = None
    logger.info('network_profiles::delete_network_profiles')
    logger.debug('schema: {}'.format(_schema))

    # get profile list
    response = api.custom_caller.call_api('GET', network_profile_base_url, params={"namespace": "switching"})
    if response['response']:
        profiles = response['response']
        # get site ids
        sites = api.sites.get_site()

        # remove Profiles
        for profile in profiles:

            # get sites for profiles - why can't this be an easy one liner?
            profile_site_parameters = {
                "includeSites": True,
                "excludeSettings": True,
                "populated": False
            }
            response = api.custom_caller.call_api('GET',
                                                  "{}/{}".format(network_profile_base_url, profile['siteProfileUuid']),
                                                  params=profile_site_parameters)
            # if profile associated to site, delete site first from profile
            if response['response']['sites']:

                site_in_profile = response['response']['sites']

                for site in site_in_profile:
                    site_remove_url = "{}/{}/site/{}".format(network_profile_base_url, profile['siteProfileUuid'],
                                                             site['uuid'])
                    result = api.custom_caller.call_api('DELETE', site_remove_url)
                    logger.debug(result)
                    common.wait_for_task_completion(api, result['response'])

            # Now delete the profile
            logger.info('network profiles: Deleting {}'.format(profile['name']))
            profile_url = "{}/{}".format(network_profile_base_url, profile['siteProfileUuid'])
            result = api.custom_caller.call_api('DELETE', profile_url)
            logger.debug(result)
            common.wait_for_task_completion(api, result['response'])
