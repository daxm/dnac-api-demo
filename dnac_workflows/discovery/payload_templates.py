discovery_j2 = """
{
    "discoveryType": "{{ item.discoveryType }}",
    "preferredMgmtIPMethod": "{{ item.preferredMgmtIPMethod }}",
    "ipAddressList": "{{ item.discovery_range }}",
    "protocolOrder": "ssh",
    "timeout": 5,
    "retry": 3,
    {% if item.netconfPort %}
    "netconfPort": "{{ item.netconfPort }}",
    {% endif %}
    "globalCredentialIdList": [],
    "name": "{{ item.name }}"
}
"""

