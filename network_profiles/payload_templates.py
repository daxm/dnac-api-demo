add_profile_j2 = """
{
    "name": "{{ item.name }}",
    "namespace": "switching"
}
"""

add_templates_to_profile_j2 = """
{
    "name": "{{ item.name }}",
    "namespace": "switching",
    "profileAttributes": [
        {% if item.day0Template %}
        {
            "key": "day0.templates",
            "attribs": [
                
                {% for template in item.day0Template %}
                {
                    "key": "device.family",
                    "value": "Switches and Hubs",
                    "attribs": [
                        {
                            "key": "device.series",
                            "value": null,
                            "attribs": [
                                {
                                    "key": "device.type",
                                    "value": null,
                                    "attribs": [
                                        
                                        {
                                            "key": "template.id",
                                            "value": "{{ template.id }}",
                                            "attribs": [
                                                {
                                                    "key": "template.version",
                                                    "value": "{{ template.version }}"
                                                },
                                                {
                                                    "key": "template.name",
                                                    "value": "{{ template.name }}"
                                                }
                                            ]
                                        },
                                        {
                                            "key": "device.tag",
                                            "value": "",
                                            "attribs": []
                                        }
                                        
                                    ]
                                }
                            ]
                        }
                    ]
                
                }
                {{ "," if not loop.last }}
                {% endfor %}
            ]
        }
        {{ "," if item.cliTemplate }}
        {% endif %}
        {% if item.cliTemplate %}
        {
            "key": "cli.templates",
            "attribs": [
                
                {% for template in item.cliTemplate %}
                {
                    "key": "device.family",
                    "value": "Switches and Hubs",
                    "attribs": [
                        {
                            "key": "device.series",
                            "value": null,
                            "attribs": [
                                {
                                    "key": "device.type",
                                    "value": null,
                                    "attribs": [
                                        {
                                            "key": "template.id",
                                            "value": "{{ template.id }}",
                                            "attribs": [
                                                {
                                                    "key": "template.version",
                                                    "value": "{{ template.version }}"
                                                },
                                                {
                                                    "key": "template.name",
                                                    "value": "{{ template.name }}"
                                                }
                                            ]
                                        },
                                        {
                                            "key": "device.tag",
                                            "value": "",
                                            "attribs": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
                {{ "," if not loop.last }}
                {% endfor %}
            ]
        }
        {% endif %}
    ]
}
"""