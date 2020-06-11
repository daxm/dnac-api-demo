
ip_pool_j2 = """
{
    "ipPoolName": "{{ item.ipPoolName }}",
    "ipPoolCidr": "{{ item.ipPoolCidr }}",
    "gateways": null,
    "dhcpServerIps": null,
    "dnsServerIps": null
}
"""

ip_reservation = '''{
    "groupName": "{{ groupName }}",
    "type": "{{ type }}",
    "siteId": "{{ _site_id }}",
    "groupOwner": "DNAC",
    "ipPools": [{% for i in range(ipPoolCidr|length) %}{
        "ipPoolCidr": "{{ ipPoolCidr[i] }}",
        "parent": "{{ ipPoolsParent[i] }}",
        "dhcpServerIps": [{% for j in range(dhcpServerIps[i]|length) %}"{{ dhcpServerIps[i][j] }}"{% if j != dhcpServerIps[i]|length - 1 %}, {% endif %}{% endfor %}],
        "dnsServerIps": [{% for j in range(dnsServerIps[i]|length) %}"{{ dnsServerIps[i][j] }}"{% if j != dnsServerIps[i]|length - 1 %}, {% endif %}{% endfor %}],
        "gateways": [{% for j in range(gateways[i]|length) %}"{{ gateways[i][j] }}"{% if j != gateways[i]|length - 1 %}, {% endif %}{% endfor %}],
        "parentUuid": "{{ _pool_parent_id[i] }}",
        "ipPoolOwner": "DNAC",
        "shared": true
    }{% if i != ipPoolCidr|length - 1 %}, {% endif %}{% endfor %}]
}'''
