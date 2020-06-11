
device_to_site_j2 = """
{
  "device": [
    {
      "ip": "{{ item.device_ip }}"
    }
  ]
}
"""

provision_device_j2 = """
[{
  "type": "DeviceInfo",
  "name": "{{ item.name }}",
  "networkDeviceId": "{{ item.networkDeviceId }}",
  "targetIdList": ["{{ item.networkDeviceId }}"],
  "siteId": "{{ item.siteId }}"
}]
"""

device_role_j2 = """
{
    "id": "{{ item.id }}",
    "role": "{{ item.role }}",
    "roleSource": "MANUAL"
}
"""
