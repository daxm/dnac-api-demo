aaa_j2 = """
{
    "ipAddress":"{{ item.ipAddress }}",
    "sharedSecret":"{{ item.sharedSecret }}",
    "role":"{{ item.role }}",
    "protocol":"{{ item.protocol }}",
    "port":0,
    "authenticationPort":"{{ item.authenticationPort }}",
    "accountingPort":"{{ item.accountingPort }}",
    "retries":"{{ item.retries }}",
    "timeoutSeconds":"{{ item.timeoutSeconds }}",
    "isIseEnabled":{{ item.isIseEnabled|lower }},
    "ciscoISEUrl": null
    {% if item.isIseEnabled == True %}
        ,"ciscoIseDtos":[
            {
            "description":"",
            "userName":"{{ item.iseUsername }}",
            "password":"{{ item.isePassword }}",
            "fqdn":"{{ item.iseFqdn }}",
            "subscriberName":"{{ item.iseSubscriberName }}",
            "ipAddress":"{{ item.iseIpAddress }}",
            "sshkey":""
        }
    ]
    {% endif %}
}
"""
