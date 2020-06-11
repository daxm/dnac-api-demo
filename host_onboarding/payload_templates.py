

port_template_j2 = """
[
  {
    "siteNameHierarchy": "{{ item.siteNameHierarchy }}",
    "deviceManagementIpAddress": "{{ item.deviceIP }}",
    "interfaceName": "{{ item.interfaceName }}",
    "dataIpAddressPoolName": "{{ item.dataPoolName }}",
    "voiceIpAddressPoolName": "{{ item.voicePoolName if item.voicePoolName else ""}}",
    "authenticateTemplateName": "{{ item.authTemplateName }}"
  }
]
"""
