#!/usr/bin/env python3
# -*- coding: utf-
"""
    This part of DNA workflows was inspired in reuses lots of code from Adam Radford's GitHub project
    See: https://github.com/CiscoDevNet/DNAC-TemplateTool 
"""

import logging
import common
import json
import inspect

from templates import payload_templates as json_templates
import yaml
import pkgutil


def get_module_definition():
    data = pkgutil.get_data(__package__, 'module')
    return yaml.load(data, Loader=yaml.SafeLoader)


############################################################################################################################################################
##### CONSTANTS
_LOGGER_MODULE_NAME_ = 'templates::'
_TABLE_DATA_START_NAME_ = 'templatesData'
_PROJECTS_TABLE_NAME_ = "projects"
_PROJECTS_TABLE_PROJECT_NAME_COLUMN_ = "projectName"
_PROJECTS_TABLE_PROJECT_DESCRIPTION_COLUMN_ = "projectDescription"
_PROJECTS_TABLE_PROJECT_TAGS_COLUMN_ = "projectTags"
_TEMPLATES_TABLE_NAME_ = 'templates'
_TEMPLATES_TABLE_TEMPLATE_NAME_COLUMN_ = "templateName"
_TEMPLATES_TABLE_TEMPLATE_DESCRIPTION_COLUMN_ = "templateDescription"
_TEMPLATES_TABLE_PROJECT_NAME_COLUMN_ = "project"
_TEMPLATES_TABLE_COMPOSITE_COLUMN_ = "composite"
_TEMPLATES_TABLE_CONTAINING_TEMPLATES_COLUMN_ = "containingTemplates"
_TEMPLATES_TABLE_TEMPLATE_CONTENT_ = "templateContent"
_TEMPLATES_TABLE_PRODUCT_FAMILY_ = "productFamily"
_TEMPLATES_TABLE_PRODUCT_SERIES_ = "productSeries"
_TEMPLATES_TABLE_SOFTWARE_TYPE_ = "softwareType"

_PRESENT_ = "present"
_ABSENT_ = "absent"
_PRESENCE_ROW_ = "presence"

_TEMPLATE_CONTENTS_ = {
    "COMMAND_LOGGING": json_templates.template_catch_all_commands,
    "TUNE_SERVICES": json_templates.template_configure_services,
    "TUNE_CLOCK": json_templates.template_tune_clock,
    "TUNE_LOGGING": json_templates.template_tune_logging,
    "TUNE_SNMP": json_templates.template_tune_snmp
}

############################################################################################################################################################
logger = logging.getLogger('main.templates')


def create_projects(api, workflow_dict):
    """ Creates Template Projects

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of template projects (see schema.py);

    :returns: Nothing """

    _logInfo(inspect.currentframe().f_code.co_name)
    _schema = 'projects.schema.templates'
    logger.info('templates::create_projects')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if _PRESENT_ in row[_PRESENCE_ROW_]:
                projectName = row[_PROJECTS_TABLE_PROJECT_NAME_COLUMN_]
                projectDescription = row[_PROJECTS_TABLE_PROJECT_DESCRIPTION_COLUMN_]
                projectTags = row[_PROJECTS_TABLE_PROJECT_TAGS_COLUMN_]

                if _getProject(api, projectName) is None:
                    _logInfo(projectName + " will be created")
                    response = api.template_programmer.create_project(name=projectName, description=projectDescription)
                    status = common.wait_on_task(api, response, "Creating template project: " + projectName)
                    _logDebug(status)
                else:
                    _logInfo(row[_PROJECTS_TABLE_PROJECT_NAME_COLUMN_] + " SKIPPING since it ALREADY EXISTS!")
    else:
        logger.error('schema not found: {}'.format(_schema))


def create_templates(api, workflow_dict):
    """ Creates Templates.  Template content can either be added to template content field or templates can be added to sample templates
    directory under templates module.  If using templates json file, templateName field will need to match the name of template json identified in
    the __TEMPLATE_CONTENTS__ global variable.  New template json files will need to be added to the __TEMPLATE_CONTENTS__.


    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of templates (see schema.py);

    :returns: Nothing """
    _logInfo(inspect.currentframe().f_code.co_name)
    _schema = 'templates.schema.templates'
    logger.info('templates::create_templates')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        projects = _listTemplateProjects(api)

        for row in table_data:
            if _PRESENT_ in row[_PRESENCE_ROW_]:
                templateName = row[_TEMPLATES_TABLE_TEMPLATE_NAME_COLUMN_]
                templateDescription = row[_TEMPLATES_TABLE_TEMPLATE_DESCRIPTION_COLUMN_]
                projectName = row[_TEMPLATES_TABLE_PROJECT_NAME_COLUMN_]

                _logDebug(("ProjectName: {}; TemplateName: {}").format(projectName, templateName))

                projectID = _getProjectID(api, projectName)
                existing_template = _getTemplateInProjectId(api, templateName, projectID)
                _logDebug(("ProjectID: {}; Existing TemplateID:{}").format(projectID, existing_template))

                #                         pprint.pprint(existing_template)
                if templateName not in _TEMPLATE_CONTENTS_.keys():
                    # if project exists create template
                    if projectID:
                        row['projectId'] = projectID

                        # row['parentTemplateId'] = existing_template.id
                        row['deviceTypes'] = []
                        row['deviceTypes'].append({"productFamily": row['productFamily']})
                        row['deviceTypes'] = json.dumps(row['deviceTypes'])

                        # check if template already exists if... if it does then use update
                        if existing_template is not None:
                            row['templateId'] = existing_template.id
                            logger.info("templates::create templates {} template exists, updating".format(
                                row['templateName']))
                            data = common.build_json_from_template(json_templates.blank_template_j2, row)
                            response = api.template_programmer.update_template(projectID, payload=data)
                            logger.debug(response)
                            template_data = common.wait_for_task_completion(api, response['response'])

                            # commit template to new version if template was created correctly
                            if template_data['response']['data']:
                                templateID = template_data['response']['data']
                                response = api.template_programmer.version_template(
                                    templateId=template_data['response']['data'])
                                common.wait_for_task_completion(api, response['response'])
                                logger.info("border_handoff::{} template update successful".format(
                                    row['templateName']))

                                return {"response": {"description": "Template Created Successfully",
                                                     "isError": False,
                                                     "templateId": templateID}}
                            else:
                                logger.error("templates:: create {} template failed".format(row['templateName']))

                        # Otherwise create a new one
                        else:
                            logger.info("templates::create templates:: create {} template".format(
                                row['templateName']))
                            data = common.build_json_from_template(json_templates.blank_template_j2, row)
                            response = api.template_programmer.create_template(projectID, payload=data)
                            logger.debug(response)
                            template_data = common.wait_for_task_completion(api, response['response'])

                            # commit template to version 1 if template was created correctly
                            if template_data['response']['data']:
                                templateId = template_data['response']['data']
                                response = api.template_programmer.version_template(
                                    templateId=templateId)
                                common.wait_for_task_completion(api, response['response'])

                                return {"response": {"description": "Template Created Successfully", "isError": False,
                                                     "templateId": templateId}}
                            else:
                                return {"response": {"description": "Template Not Created", "isError": True}}

                # if existing template files exist generate template from json file
                else:
                    template_content = _getTemplateContent(templateName)
                    template_content["description"] = templateDescription

                    if projectID is not None:
                        if existing_template is None:
                            # Create a new template
                            _logDebug("Creating new template: " + templateName)
                            response = api.template_programmer.create_template(**template_content, project_id=projectID)
                            templateID = common.wait_on_task(api, response, "Create template: " + templateName)
                            _logDebug(templateID)

                            response = api.template_programmer.version_template(templateId=templateID)
                            _logDebug(str(response))

                            return {
                                "response": {"description": "Template Created Successfully", "isError": False,
                                             "templateId": templateID}}
                        else:
                            # Update existing template
                            _logDebug("Updating existing template: " + existing_template.name)
                            template_content['projectId'] = projectID
                            template_content['id'] = existing_template.id
                            template_content['parentTemplateId'] = existing_template.id

                            #                                 pprint.pprint(template_content)
                            response = api.template_programmer.update_template(**template_content)

                            templateID = common.wait_on_task(api, response,
                                                             "Update template: " + existing_template.name)
                            return {
                                "response": {"description": "Template Updated Successfully", "isError": False,
                                             "templateId": templateID}}
                    else:
                        _logInfo(templateName + " -> Project does not exist.")
    else:
        logger.error('schema not found: {}'.format(_schema))


def deploy_templates(api, workflow_dict):
    """ Deploys Templates

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of devices and templates to be pushed (see schema.py);

    :returns: Nothing """

    _schema = 'deploy.schema.templates'
    logger.info('templates::deploy_templates')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        deployment_details = [device for device in table_data if device['presence'] == 'present']

        for deployment in deployment_details:

            # get template id
            response = api.template_programmer.gets_the_templates_available()
            template_data = common.get_object_by_attribute(response, name=deployment['templateName'])

            # if template exists go ahead and deploy
            if template_data['templateId'] is not None:
                deployment['templateId'] = template_data['templateId']
                data = common.build_json_from_template(json_templates.deploy_template_j2, deployment)
                response = api.template_programmer.deploy_template(payload=data)
                # api response is broken for deployment api response.  just printing the response for now
                # common.wait_for_task_completion(response)

                return response
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_templates(api, workflow_dict):
    """ Deletes Templates

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of templates (see schema.py);

    :returns: Nothing """
    _logInfo(inspect.currentframe().f_code.co_name)
    _schema = 'templates.schema.templates'
    logger.info('templates::delete_templates')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if _ABSENT_ in row[_PRESENCE_ROW_]:
                templateName = row[_TEMPLATES_TABLE_TEMPLATE_NAME_COLUMN_]
                projectName = row[_TEMPLATES_TABLE_PROJECT_NAME_COLUMN_]

                projectID = _getProjectID(api, projectName)
                templateID = _getTemplateID(api, templateName, projectID)

                _logDebug("ProjectID: {}; Existing TemplateID:{}".format(projectID, templateID))
                #                         print(projectID, templateID)

                if projectID is not None and templateID is not None:
                    response = api.template_programmer.delete_template(template_id=templateID)
                    taskId = response["response"]["taskId"]
                    status = common.report_task_completion(api, taskId, "Deleting template: " + templateName)
    else:
        logger.error('schema not found: {}'.format(_schema))


def delete_projects(api, workflow_dict):
    """ Deletes Template Projects

    :param api: An instance of the dnacentersdk.DNACenterAPI class
    :param workflow_dict: A dictionary containing rows of template projects (see schema.py);

    :returns: Nothing """

    _logInfo(inspect.currentframe().f_code.co_name)
    _schema = 'projects.schema.templates'
    logger.info('templates::delete_projects')
    logger.debug('schema: {}'.format(_schema))

    if _schema in workflow_dict.keys():
        table_data = workflow_dict[_schema]

        for row in table_data:
            if _ABSENT_ in row[_PRESENCE_ROW_]:
                projectName = row[_PROJECTS_TABLE_PROJECT_NAME_COLUMN_]
                _logInfo(projectName + " will be deleted")
                projectID = _getProjectID(api, projectName)
                if projectID is not None:
                    response = api.template_programmer.delete_project(project_id=projectID)
                    status = common.wait_on_task(api, response, "Deleting project: " + projectName)
                    _logDebug(status)


def _logInfo(msg):
    logger.info(_LOGGER_MODULE_NAME_ + msg)


def _logDebug(msg):
    logger.debug(_LOGGER_MODULE_NAME_ + msg)


def _listTemplateProjects(api):
    """
        Get all template projects
    """

    projects = api.template_programmer.get_projects()

    for project in projects:
        _logDebug(project.name)

    return projects


def _getProject(api, projectName):
    projects = api.template_programmer.get_projects(projectName)

    for project in projects:
        if project.name == projectName:
            return project
    else:
        return None


def _getProjectID(api, projectName):
    project = _getProject(api, projectName)

    if project is not None:
        return project["id"]
    else:
        return None


def _getProjectById(api, projectId):
    projects = api.template_programmer.get_projects()
    for project in projects:
        if project.id == projectId:
            return project
    else:
        return None


def _getTemplate(api, templateName, projectID):
    templates = api.template_programmer.gets_the_templates_available(project_id=projectID)

    for template in templates:
        _logDebug("Checking template: " + template.name)
        if template.name == templateName:
            _logDebug("Found template!")
            return template

    return None


def _getTemplateInProjectId(api, templateName, projectId):
    project = _getProjectById(api, projectId)
    print(project)
    for template in project.templates:
        _logDebug("Checking template: " + template.name)
        if template.name == templateName:
            return template

    return None


def _getTemplateID(api, templateName, projectID):
    #     print("Getting templateName: " + templateName)
    template = _getTemplate(api, templateName, projectID)

    if template is not None:
        return template["templateId"]
    else:
        return None


def _listTemplateAvailableTemplates(api):
    """
        Get all available templates
    """

    templates = api.template_programmer.gets_the_templates_available()

    #     for template in templates:
    #         print(template.name, template.projectId, template.templateId)

    return templates


def _getTemplateContent(templateName):
    contentJson = _TEMPLATE_CONTENTS_[templateName]
    _logDebug(contentJson)

    content = json.loads(contentJson)

    return content
