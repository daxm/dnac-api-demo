fabric_domain_j2 = """
{
    "type": "ConnectivityDomain",
    "name": "{{ item.fabricName }}",
    "description": "",
    "domainType": "FABRIC_LAN",
    "virtualNetwork": [],
    "isDefault": false,
    "enableMonitoring": true,
    "siteSpecificDomain": []
}
"""

fabric_site_j2 = """
{
    "type": "ConnectivityDomain",
    "name": "{{ item.fabric_site_name }}",
    "description": "",
    "domainType": "FABRIC_SITE",
    "siteId": "$string",
    "virtualNetwork": [],
    "isDefault": false,
    "enableMonitoring": true
}
"""

fabric_vn_j2 = """
{
    "name": "{{ item.fabric_vn_name }}",
    "isDefault": false,
    "isInfra": false,
    "virtualNetworkContextId": "{{ item.virtualNetworkContextId }}",
    "type": "VirtualNetwork"
}
"""

virtual_network_j2 = """
[{
    "name":"{{ item.vnName }}",
    "virtualNetworkContextType":"{{ item.vnType }}"
}]
"""

scalable_group_tag_j2 = """
[{
    "name":"{{ item.sgtName }}",
    "securityGroupTag":0,
    "description":"{{ item.description }}",
    "vnAgnostic":false,
    "propagateToAci":false,
    "scalableGroupType":"USER_DEVICE"
}]
"""

contract_j2 = """
[{
    "name": "{{ item.contractName }}",
    "type": "contract",
    "description": "Created by DNA Workflows",
    "contractClassifier": [],
    "clause": [{
        "access": "{{ item.defaultAction }}",
        "logging": "{{ item.defaultRuleLogging }}"
    }]
}]
"""

contract_classifier_j2 = """
{
    "access": "{{ item.ruleAction }}",
    "applicationName": "advanced",
    "dstNetworkIdentities": [{
        "protocol": "{{ item.sourceProtocol }}",
{% if item.sourcePort is not none %}
        "ports": "{{ item.sourcePort }}"
{% else %}
        "ports": ""
{% endif %}
    }, {
        "protocol": "{{ item.destinationProtocol }}",
{% if item.destinationPort is not none %}
        "ports": "{{ item.destinationPort }}"
{% else %}
        "ports": ""
{% endif %}
    }],
    "logging": "{{ item.aceLogging }}"
}
"""

policy_j2 = """
[{
    "name": "{{ item.policyName }}",
    "consumer": {
        "scalableGroup": [{
            "idRef": "{{ item.srcSgtId }}"
        }]
    },
    "producer": {
        "scalableGroup": [{
            "idRef": "{{ item.dstSgtId }}"
        }]
    },
    "contract": {
        "idRef": "{{ item.contractId }}"
    },
    "description": "",
    "isEnabled": true,
    "policyScope": "2827e5bf-d291-3d54-aeda-3e21b29a9d5d",
    "priority": 65535
}]
"""

auth_template_j2 = """
[{
        "id": "{{ item.id }}",
        "type": "{{ item.type }}",
        "name": "{{ item.fabric_site_name }}",
        "domainType": "{{ item.domainType }}",
        "isDefault": false,
        "virtualNetwork": [],
        "deviceInfo": {{ item.deviceInfo }},
        "multicastInfo": {{ item.multicastInfo }},
        "migrationStatus": {{ item.migrationStatus }},
        "resourceVersion": {{ item.resourceVersion }},
        "siteId": "{{ item.siteID }}",
        "siteSpecificDomain": {{ item.siteSpecificDomain }},
        "l2FloodingIndex": "{{ item.l2FloodingIndex }}"
}]
"""

add_edge = """
[{
        "deviceManagementIpAddress": "{{ item.mgmtIp }}",
        "siteNameHierarchy": "{{ item.siteNameHierarchy }}"

}]
"""

add_control = """
[{
        "deviceManagementIpAddress": "{{ item.mgmtIp }}",
        "siteNameHierarchy": "{{ item.siteNameHierarchy }}"

}]
"""

add_border = """
[{
        "deviceManagementIpAddress": "{{ item.mgmtIp }}",
        "siteNameHierarchy": "{{ item.siteNameHierarchy }}",
        "externalDomainRoutingProtocolName": "{{ item.handoffProtocol }}",
        "internalAutonomouSystemNumber": "{{ item.internalAS }}",
        "externalConnectivityIpPoolName": "{{ item.handoffPool }}",
        "borderSessionType": "{{ item.borderType }}",
        "connectedToInternet": {{ item.connectedToInternet }},
        "externalConnectivitySettings": [{
                "interfaceName": "{{ item.handoffInterface }}",
                "externalAutonomouSystemNumber": "{{ item.externalAS }}",
                "l3Handoff": [{
                        "virtualNetwork": {
                            "virtualNetworkName": "{{ item.handoffVNs }}"
                        }
                    }]
            }]
}]
"""

transit_j2 = """
[
    {
        "type":"ConnectivityDomain",
        "name":"{{ item.name }}",
        "description":"{{ item.description }}",
        "domainType":"TRANSIT",
        "enableMonitoring":true,
        "transitType":"{{ item.transitType }}",
        "transitMetaData":[
            {
                "name":"{{ item.routingProtocol }}",
                "value":"{{ item.bgpAS }}",
                "remoteAsNotation":"{{ item.remoteAsNotation }}"
            }
        ],
        "deviceInfo":[]
    }
]
"""