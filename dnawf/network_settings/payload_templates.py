network_settings_intent_j2 = """
{
    "settings": {
        "dhcpServer": [
            {% if item.dhcpServer != None %}
                {% for server in item.dhcpServer %}
                "{{ server }}"
                {{ "," if not loop.last }}
                {% endfor %}
            {% else %}
            ""
            {% endif %}
        ],
        "dnsServer": {
            "domainName": "{{ item.dnsDomain if item.dnsDomain != None else "" }}",
            "primaryIpAddress": "{{ item.dnsPrimary if item.dnsPrimary != None else "" }}",
            "secondaryIpAddress": "{{ item.dnsSecondary if item.dnsSecondary != None else "" }}"
        },
        "syslogServer": {
            "ipAddresses": [
                {% if item.syslogServer != None %}
                    {% for server in item.syslogServer %}
                    "{{ server }}"
                    {{ "," if not loop.last }}
                {% endfor %}
                {% else %}
                ""
                {% endif %}
            ],
            "configureDnacIP": {{ item.syslogDNAC if item.syslogDNAC != None else "true"}}
        },
        "snmpServer": {
            "ipAddresses": [
                {% if item.snmpServer != None %}
                    {% for server in item.snmpServer %}
                    "{{ server }}"
                    {{ "," if not loop.last }}
                {% endfor %}
                {% else %}
                ""
                {% endif %}
            ],
            "configureDnacIP": {{ item.snmpDNAC if item.snmpDNAC != None else "true"}}
        },
        "netflowcollector": {
            "ipAddress": "{{ item.netflowIp if item.netflowIp != None else ""}}",
            "port": "{{ item.netflowPort if (item.netflowIp and item.netflowPort) != None else ""}}"
        },
        "ntpServer": [
            {% if item.ntpServer != None %}
                {% for server in item.ntpServer %}
                "{{ server }}"
                {{ "," if not loop.last }}
                {% endfor %}
            {% else %}
            ""
            {% endif %}
        ],
        "timezone": "{{ item.timezone if item.timezone != None else "GMT"}}",
        "messageOfTheday": {
            "bannerMessage": "{{ item.motd if item.motd else ""}}",
            "retainExistingBanner": "True"
        }
        {{ "," if (item.networkAAA_server or item.clientAAA_server) }}
        {% if item.networkAAA_server %}
        "network_aaa": {
            "servers": "{{ item.networkAAA_server }}",
            "ipAddress": "{{ item.networkAAA_ip }}",
            "network": "{{ item.networkAAA_network }}",
            "protocol": "{{ item.networkAAA_protocol }}",
            "sharedSecret": "{{ item.networkAAA_secret if item.networkAAA_secret else ""}}"
        }
        {{ "," if item.clientAAA_server }}
        {% endif %}
        {% if item.clientAAA_server %}
        "clientAndEndpoint_aaa": {
            "servers": "{{ item.clientAAA_server }}",
            "ipAddress": "{{ item.clientAAA_ip }}",
            "network": "{{ item.clientAAA_network }}",
            "protocol": "{{ item.clientAAA_protocol }}",
            "sharedSecret": "{{ item.clientAAA_secret if item.clientAAA_secret else ""}}"
        }
        {% endif %}
    }
}
"""

network_settings_j2 = """
[ {
    "instanceType" : "pan",
    "namespace" : "global",
    "type" : "pan.setting",
    "key" : "aaa.server.pan.network",
    "value" : [ "None" ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "banner",
    "namespace" : "global",
    "type" : "banner.setting",
    "key" : "device.banner",
    "value" : [ {
      "bannerMessage" : "",
      "retainExistingBanner" : true
    } ],
    "groupUuid" : "-1",
    "inheritedGroupUuid" : "",
    "inheritedGroupName" : ""
  }, {
    "instanceType" : "timezone",
    "namespace" : "global",
    "type" : "timezone.setting",
    "key" : "timezone.site",
    "value" : [ "GMT" ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "aaa",
    "namespace" : "global",
    "type" : "aaa.setting",
    "key" : "aaa.endpoint.server.1",
    "value" : [ {
      "ipAddress" : "",
      "sharedSecret" : "",
      "protocol" : ""
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "ip",
    "namespace" : "global",
    "type" : "ip.address",
    "key" : "dhcp.server",
    "value" : [ ],
    "groupUuid" : "-1",
    "inheritedGroupUuid" : "",
    "inheritedGroupName" : ""
  }, {
    "instanceType" : "aaa",
    "namespace" : "global",
    "type" : "aaa.setting",
    "key" : "aaa.endpoint.server.2",
   "value" : [ {
      "ipAddress" : "",
      "sharedSecret" : "",
      "protocol" : ""
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "syslog",
    "namespace" : "global",
    "type" : "syslog.setting",
    "key" : "syslog.server",
    "value" : [ {
      "ipAddresses" : [ "" ],
      "configureDnacIP" : true
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "netflow",
    "namespace" : "global",
    "type" : "netflow.setting",
    "key" : "netflow.collector",
    "value" : [ {
      "ipAddress" : "",
      "port" : null
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "aaa",
    "namespace" : "global",
    "type" : "aaa.setting",
    "key" : "aaa.network.server.1",
    "value" : [ {
      "ipAddress" : "",
      "sharedSecret" : "",
      "protocol" : ""
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "ip",
    "namespace" : "global",
    "type" : "ip.address",
    "key" : "ntp.server",
    "value" : [ "" ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "snmp",
    "namespace" : "global",
    "type" : "snmp.setting",
    "key" : "snmp.trap.receiver",
    "value" : [ {
      "ipAddresses" : [ "" ],
      "configureDnacIP" : true
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "aaa",
    "namespace" : "global",
    "type" : "aaa.setting",
    "key" : "aaa.network.server.2",
    "value" : [ {
      "ipAddress" : "",
      "sharedSecret" : "",
      "protocol" : ""
    } ],
    "groupUuid" : "-1"
  }, {
    "instanceType" : "dns",
    "namespace" : "global",
    "type" : "dns.setting",
    "key" : "dns.server",
    "value" : [ {
      "domainName" : "dummy.local",
      "primaryIpAddress" : "1.1.1.1",
      "secondaryIpAddress" : ""
    } ],
    "groupUuid" : "-1"
  },  {
    "instanceType" : "pan",
    "namespace" : "global",
    "type" : "pan.setting",
    "key" : "aaa.server.pan.endpoint",
    "value" : [ "None" ],
    "groupUuid" : "-1"
  } ]"""