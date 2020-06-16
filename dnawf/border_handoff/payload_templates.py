blank_template_j2 = """
{
    "composite": false,
    {% if item.templateId %}
    "id" : "{{ item.templateId }}",
    {% endif %} 
    "containingTemplates": [], 
    "description": "{{ item.description }}", 
    "deviceTypes": [
        {
            "productFamily":"Switches and Hubs"
            }
    ],
    "name": "{{ item.templateName }}", 
    "rollbackTemplateContent": "", 
    "rollbackTemplateParams": [], 
    "softwareType": "{{ item.softwareType }}", 
    "tags": [], 
    "templateContent": "{{ item.templateContent }}",
    "templateParams": []
}
"""

template_vn_peer = """
vlan {{ vlan }}
  name {{ vn_name }}_TRANSIT_VLAN
!
interface Vlan{{ vlan }}
  description {{ description }}
  ip address {{ remote_ip_subnet }}
  no ip redirects
  no ip proxy-arp
!
router bgp {{ remote_as }}
  address-family ipv4
    neighbor {{ local_ip }} remote-as {{ local_as }}
    neighbor {{ local_ip }} description {{ description }}
    neighbor {{ local_ip }} activate
  exit-address-family
!
"""

deploy_template_j2 = """
{
    "forcePushTemplate": false,
    "isComposite": false,
    "targetInfo": [
        {
            "hostName": "{{ item.fusionName }}",
            "id": "{{ item.fusion_ip }}",
            "params": {},
            "type": "MANAGED_DEVICE_IP"
        }
    ],
    "templateId": "{{ item.templateId }}"
}
"""