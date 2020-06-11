"""
    Remove all "id" instances in template,
    remove projectID, 
    remove parentTemplateId
    remove createTime
    remove lastUpdateTime
    
    Check content and if there are \ replace them with \\, for example \n with \\n
"""

template_tune_clock = """
{
    "composite": false, 
    "containingTemplates": [], 
    "description": "Tune clock, summer time, etc.", 
    "deviceTypes": [
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9500 Series Switches"
        }, 
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9300 Series Switches"
        }
    ], 
    "name": "TUNE_CLOCK", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "IOS-XE", 
    "softwareVariant": "XE", 
    "tags": [], 
    "templateContent": "clock timezone CET 1 0\\nclock summer-time CEST recurring last Sun Mar 2:00 last Sun Oct 3:00\\n\\nntp source Loopback0", 
    "templateParams": []
}
"""

template_tune_snmp = """
{
    "composite": false, 
    "containingTemplates": [], 
    "description": "Tune SNMP queue and enable persistant interface IDs.", 
    "deviceTypes": [
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9500 Series Switches"
        }, 
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9300 Series Switches"
        }
    ], 
    "name": "TUNE_SNMP", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "IOS-XE", 
    "softwareVariant": "XE", 
    "tags": [
        {
            "name": "management_optimization"
        }
    ], 
    "templateContent": "snmp-server queue-length $snmp_queue_lenght\\nsnmp-server ifindex persist\\n", 
    "templateParams": [
        {
            "binding": "", 
            "dataType": "INTEGER", 
            "defaultValue": 100, 
            "description": null, 
            "displayName": null, 
            "group": null, 
            "instructionText": null, 
            "key": null, 
            "notParam": false, 
            "order": 1, 
            "paramArray": false, 
            "parameterName": "snmp_queue_lenght", 
            "provider": null, 
            "range": [
                {
                    "minValue": 10, 
                    "maxValue": 100
                }
            ],
            "required": true, 
            "selection": {
                "defaultSelectedValues": [], 
                "selectionType": null, 
                "selectionValues": {}
            }
        }
    ]
}
 """



template_tune_logging = """
{
    "composite": false, 
    "containingTemplates": [], 
    "description": "Fine tune logging", 
    "deviceTypes": [
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9500 Series Switches"
        }, 
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9300 Series Switches"
        }
    ], 
    "name": "TUNE_LOGGING", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "IOS-XE", 
    "softwareVariant": "XE", 
    "tags": [
        {
            "name": "management_optimization"
        }
    ], 
    "templateContent": "service timestamps log datetime msec localtime show-timezone year\\n\\nlogging buffered $logBuffer\\nlogging source-interface loopback 0\\n", 
    "templateParams": [
        {
            "binding": "", 
            "dataType": "INTEGER", 
            "defaultValue": "512000", 
            "description": null, 
            "displayName": "Logging buffer size", 
            "group": null, 
            "instructionText": null, 
            "key": null, 
            "notParam": false, 
            "order": 1, 
            "paramArray": false, 
            "parameterName": "logBuffer", 
            "provider": null, 
            "range": [
                {
                    "maxValue": 1024000, 
                    "minValue": 128000
                }
            ], 
            "required": true, 
            "selection": {
                "defaultSelectedValues": [], 
                "selectionType": null, 
                "selectionValues": {}
            }
        }
    ]
}
"""

template_configure_services = """
{
    "composite": false, 
    "containingTemplates": [], 
    "createTime": 1557850297296, 
    "description": "Fine tune services", 
    "deviceTypes": [
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9500 Series Switches"
        }, 
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9300 Series Switches"
        }
    ], 
    "lastUpdateTime": 1564497043476, 
    "name": "TUNE_SERVICES", 
    "parentTemplateId": "10ad2858-55fa-4a3a-ab8e-b0c63b50e332", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "IOS-XE", 
    "softwareVariant": "XE", 
    "tags": [
        {
            "id": "3897eb0c-f43a-448f-861f-374daf1e4b96", 
            "name": "management_optimization"
        }
    ], 
    "templateContent": "no service config\\nservice tcp-keepalives-in\\nservice tcp-keepalives-out", 
    "templateParams": []
}
"""

template_catch_all_commands = """
{
    "composite": false, 
    "containingTemplates": [], 
    "description": "Catch all commands, configuration and exec.", 
    "deviceTypes": [
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9500 Series Switches"
        }, 
        {
            "productFamily": "Switches and Hubs", 
            "productSeries": "Cisco Catalyst 9300 Series Switches"
        }
    ], 
    "name": "COMMAND_LOGGING", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "IOS-XE", 
    "softwareVariant": "XE", 
    "tags": [], 
    "templateContent": "#if ($enableCommandLogging == \\"Yes\\")\\n  event manager applet catchall\\n  event cli pattern \\".*\\" sync no skip no\\n  action 1 syslog msg \\"$_cli_msg\\"\\n#else\\n  no event manager applet catchall\\n#end", 
    "templateParams": [
        {
            "binding": "", 
            "dataType": null, 
            "defaultValue": null, 
            "description": null, 
            "displayName": null, 
            "group": null, 
            "instructionText": null, 
            "key": null, 
            "notParam": false, 
            "order": 1, 
            "paramArray": false, 
            "parameterName": "enableCommandLogging", 
            "provider": null, 
            "range": [], 
            "required": true, 
            "selection": {
                "defaultSelectedValues": [
                    "Disable"
                ], 
                "selectionType": "SINGLE_SELECT", 
                "selectionValues": {
                    "Disable": "No", 
                    "Enable": "Yes"
                }
            }
        }, 
        {
            "binding": "", 
            "dataType": null, 
            "defaultValue": null, 
            "description": null, 
            "displayName": null, 
            "group": null, 
            "instructionText": null, 
            "key": null, 
            "notParam": true, 
            "order": 2, 
            "paramArray": false, 
            "parameterName": "_cli_msg", 
            "provider": null, 
            "range": [], 
            "required": false, 
            "selection": {
                "defaultSelectedValues": [], 
                "selectionType": null, 
                "selectionValues": {}
            }
        }
    ]
}
"""

blank_template_j2 = """
{
    "composite": false,
    {% if item.templateId %}
    "id" : "{{ item.templateId }}",
    {% endif %} 
    "containingTemplates": [], 
    "description": "{{ item.description }}", 
    "deviceTypes": {{ item.deviceTypes }},
    "name": "{{ item.templateName }}", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "{{ item.softwareType }}", 
    "tags": [], 
    "templateContent": "{{ item.templateContent }}",
    "templateParams": []
}
"""

deploy_template_j2 = """
{
    "forcePushTemplate": false,
    "isComposite": false,
    "targetInfo": [
        {
            "hostName": "{{ item.hostName }}",
            "id": "{{ item.ipAddress }}",
            "params": {},
            "type": "MANAGED_DEVICE_IP"
        }
    ],
    "templateId": "{{ item.templateId }}"
}
"""