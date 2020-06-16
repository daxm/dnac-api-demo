ssid_j2 = """
{
            "name": "{{ item.name }}",
            "securityLevel": "{{ item.securityLevel }}",
            {% if item.securityLevel == "WPA2_PERSONAL" %}
                "passphrase": "{{ item.passphrase }}",
            {% endif %}
            "enableFastLane": {{ item.enableFastLane|lower }},
            "enableMACFiltering": {{ item.enableMACFiltering|lower }},
            "trafficType": "{{ item.trafficType }}",
            "radioPolicy": "{{ item.radioPolicy }}",
            "enableBroadcastSSID": {{ item.enableBroadcastSSID|lower }},
            "fastTransition": "{{ item.fastTransition }}"
}
"""

wireless_profile_j2 = """
{
    "profileDetails": {
        "name": "{{ item.profileName }}"
        {% if item.sites %}
           , "sites": [
                  {% for site in item.sites %}
                      "{{ site }}"
                      {{ "," if not loop.last }}
                  {% endfor %} 
              ]
        {% endif %}
        {% if item.ssidDetails %}
            , "ssidDetails": [

                {% for ssid in item.ssidDetails %}
                    {
                    {% if ssid.interfaceNameOTT %}
                        "interfaceName" : "{{ ssid.interfaceNameOTT }}",
                    {% endif  %}
                    "name" : "{{ ssid.name }}" ,
                    "enableFabric" : {{ ssid.enableFabric }}
                        {% if ssid.enableFlexConnect == "true" %}
                        , "flexConnect" : {
                            "enableFlexConnect" : {{ ssid.enableFlexConnect }},
                            "localToVlan" : {{ ssid.localToVlan }}   
                        }   
                        {% endif %}
                    } {{ "," if not loop.last }}          
                {% endfor %}

            ]
        {% endif %}
    }
}
"""

provision_j2 = """
[
    {
        "deviceName": "{{ item.deviceName }}",
        "site": "{{ item.site }}",
        "managedAPLocations": [
            {% for location in item.managedAPLocations %}
                "{{ location }}"
                {{ "," if not loop.last }}
            {% endfor %}
        ]
        {% if item.dynamicInterfaces %}
            ,  "dynamicInterfaces": [
            {% for interface in item.dynamicInterfaces %}
                {
                    {% if interface.interfaceIPAddress %}
                    "interfaceIPAddress": "{{ interface.interfaceIPAddress }}",
                    {% endif %}
                    {% if interface.interfaceNetmaskInCIDR %}
                    "interfaceNetmaskInCIDR": {{ interface.interfaceNetmaskInCIDR}},
                    {% endif %}
                    {% if interface.interfaceGateway %}
                    "interfaceGateway": "{{ interface.interfaceGateway}}",
                    {% endif %}
                    {% if interface.lagOrPortNumber %}
                    "lagOrPortNumber": {{ interface.lagOrPortNumber}},
                    {% endif %}
                    {% if interface.interfaceName %}
                    "interfaceName": "{{ interface.interfaceName }}",
                    {% endif %}
                    {% if interface.vlanId %}
                    "vlanId": {{ interface.vlanId }}
                    {% endif %}
                }
                {{ "," if not loop.last }}
            {% endfor %}
            ]
        {% endif %}
    }
]


"""

wireless_interface_j2 = """
[
    {
        "instanceType": "interface",
        "namespace": "global",
        "type": "interface.setting",
        "key": "interface.info",
        "value": {{ item }},
        "groupUuid": "-1",
        "inheritedGroupUuid": "",
        "inheritedGroupName": ""
    }
]
"""