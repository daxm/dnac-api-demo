"""
Common helper functions
"""
import logging
import functools
import time
from jinja2 import Template
import json
import threading
from ipaddress import ip_address, ip_network

logger = logging.getLogger('main.helpers')


def dot_to_json(a):
    output = {}
    for key, value in a.items():
        path = key.split('.')
        if path[0] == 'json':
            path = path[1:]
        target = functools.reduce(lambda d, k: d.setdefault(k, {}), path[:-1], output)
        target[path[-1]] = value
    return output


def build_json_from_template(template, data):
    """Build a python dict from a json template

     Args:
         template: A jinja2 template containing a valid json string
         data: A dictionary containing values to be used when parsing the template

     Returns:
         A python dictionary loaded from json

     """
    t = Template(template)
    json_string = t.render(item=data)
    parsed = json.loads(json_string)

    return parsed


def get_object_id(object_list, **kwargs):
    """Get object id

    Args:
        object_list: A list of json objects
        **kwargs: a list of filters to search the object list for
            return_param: specify the key that should be returned (id = default)
            strict: True or False. Specifies the type of string match

    Returns:
        The value of the json key 'id' or 'None' is no object is found

    """
    if 'return_param' in kwargs:
        return_param = kwargs['return_param']
        kwargs.pop('return_param')
    else:
        return_param = 'id'

    if 'strict' in kwargs:
        strict = kwargs['strict']
        kwargs.pop('strict', None)
    else:
        strict = True

    for item in object_list:
        _match = 0
        for key, value in kwargs.items():
            if item[key] == value:
                logger.debug('{}'.format(item))
                _match = 1
            elif value in item[key] and not strict:
                logger.debug('{}'.format(item))
                _match = 1
            else:
                _match = 0
                break

        if _match:
            return item[return_param]

    return None


def get_object_by_attribute(object_list, **kwargs):
    """Get object

    Args:
        object_list: A list of json objects
        **kwargs: a list of filters to search the object list for

    Returns:
        The the full json object if found or 'None' is no object is found

    """
    for item in object_list:
        _match = 0
        for key, value in kwargs.items():
            if item[key] == value:
                logger.debug('{}'.format(item))
                _match = 1
            else:
                _match = 0
                break

        if _match:
            return item

    return None


def wait_for_task_completion(api, task, timeout=10, **kwargs):

    if task['executionStatusUrl']:
        _exec_url = task['executionStatusUrl']
        _intent_api = 1

        # workaround for DNAC using wrong IP in executionStatusUrl
        #base_dnac_ip = api.base_url.split('//')[1]
        #base_returned_ip = _exec_url.split('//')[1].split('/')[0]
        #exec_uri = _exec_url.split('//')[1].split('/', 1)[1]

        #if base_returned_ip != base_dnac_ip:
        #    logger.warning("DNAC URL returned from API using incorrect IP Address. Changing to DNAC Management IP ")
        #    _exec_url = "https://{}/{}".format(base_dnac_ip, exec_uri)

    elif task['url']:
        _intent_api = 0
        _exec_url = task['url']


    # URI: (GET: Retrieve status on job.  We have different URIs for different APIs)
    _result = api.custom_caller.call_api('GET', _exec_url)

    t = timeout
    while True:
        if _intent_api:
            if _result['status'] == 'IN_PROGRESS':
                logger.debug(_result)
                logger.debug('sleeping for 2 seconds ...')
                time.sleep(2)
                _result = api.custom_caller.call_api('GET', _exec_url)
                logger.debug(_result)
                t = t - 2
            else:
                logger.info('Task "{}" with execution id: {} status: {}'.format(
                    _result['bapiName'], _result['bapiExecutionId'], _result['status']))
                logger.debug(_result)
                break

            if t < 1:
                logger.info('Timeout waiting for task to complete')
                logger.debug(_result)
                break
        else:
            if not _result['response']['endTime']:
                logger.debug(_result)
                logger.debug('sleeping for 2 seconds ...')
                time.sleep(2)
                _result = api.custom_caller.call_api('GET', _exec_url)
                logger.debug(_result)
                t = t - 2
            else:
                logger.info('Task status: "{}", Error status: {}'.format(
                    _result['response']['progress'], _result['response']['isError']))
                logger.debug(_result)
                break

            if t < 1:
                logger.info('Timeout waiting for task to complete')
                logger.debug(_result)
                break

    if 'tree' in kwargs:
        _exec_url_tree = '{}/{}'.format(_exec_url, 'tree')
        _result_tree = api.custom_caller.call_api('GET', _exec_url_tree)
        return _result_tree
    else:
        return _result



def monitor_task_status(api, taskId, taskName, interval=1):
    """
        Thread to monitor task status.
    """

    logger.info("In monitoring task ..." + taskName)

    # SDK: GET task by ID
    taskStatus = api.task.get_task_by_id(task_id=taskId)
    logger.info(taskStatus)

    while taskStatus.response.endTime is None:
        time.sleep(interval)
        logger.info("Another run task ...")
        taskStatus = api.task.get_task_by_id(task_id=taskId)
        logger.info(taskStatus)

    if taskStatus.response.isError == True:
        logText = taskName + ' Task has finished with error: ' + str(taskStatus.response.failureReason)
    else:
        logText = taskName + ' Task has finished successfully.'

    logger.info(logText)

    return logText


def wait_on_task(api, response, taskName, interval=1):
    """
        Wait on task completion.
    """

    taskId = response["response"]["taskId"]

    logger.info("In monitoring task ..." + taskName)

    taskStatus = api.task.get_task_by_id(task_id=taskId)
    logger.info(taskStatus)

    while taskStatus.response.endTime is None:
        time.sleep(interval)
        logger.info("Another run task ...")
        taskStatus = api.task.get_task_by_id(task_id=taskId)
        logger.info(taskStatus)

    if taskStatus.response.isError == True:
        logText = taskName + ' -> Task has finished with error: ' + str(taskStatus.response.failureReason)
    else:
        logText = taskName + ' -> Task has finished successfully.'
        templateId = taskStatus.response.data

    logger.info(logText)

    return templateId



def report_task_completion(api, taskId, taskName, interval=1):
    """
        Get task, create worker that will monitor it and report its completion.
    """

    logger.info("Entering task completion monitoring ...")

    worker = threading.Thread(target=monitor_task_status(api=api, taskId=taskId, taskName=taskName, interval=interval))
    worker.setDaemon(True)
    worker.start()

    return


def get_ip_version(address, callback=None):
    """
    Params:
    - address: The ip address as a string
    - callback: What should be done if the address is invalid
    Returns:
    - The ip version in use as an integer.
    - None if not a valid ip.
    """
    # It is an ip address
    try:
        return ip_address(address).version
    except:
        pass
    # Maybe it's a network address
    try:
        return ip_network(address).version
    except:
        # It's not a valid address
        if callback is not None:
            callback()

def csv_string_to_list(csv_string):
    """
    Params:
    - csv_string: Comma Separated string
    Returns:
    - List of values
    - If not comma separated, List containing one string.
    """
    if "," in csv_string:
        csv_list = csv_string.split(",")
        return [item.lstrip() for item in csv_list]
    else:
        return [csv_string]
