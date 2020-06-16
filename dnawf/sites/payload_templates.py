
area_j2 = """
{
    "type": "area",
    "site": {
        "area": {
            "name": "{{ item.name }}",
            "parentName": "{{ item.parentName }}"
        }
    }
}
"""

building_j2 = """
{
    "type": "building",
    "site": {
        "building": {
            "name": "{{ item.name }}",
            "address": "$string",
            "parentName": "{{ item.parentName }}",
            "latitude": "{{ item.latitude }}",
            "longitude": "{{ item.longitude }}"
        }
    }
}
"""

floor_j2 = """
{
    "type": "floor",
    "site": {
        "floor": {
            "name": "{{ item.name }}",
            "parentName": "{{ item.parentName }}",
            "rfModel": "{{ item.rfModel }}",
            "width": 5,
            "length": 5,
            "height": 3
        }
    }
}
"""