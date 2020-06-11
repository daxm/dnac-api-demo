First things first; ***We accept no responsibility for any kind of loss or damage caused by using this arrangement of software code.  We also do not provide any promises or commitment of support for said code.  It is pretty much all on you.***

 * Please see the main [DNA Workflows project](https://github.com/cunningr/dna_workflows) for documentation on how to use these modules

Very quick example usage;

```
$ pwd
/Users/cunningr/git-projects/dnawf_dnac_module_pack
$ docker run --rm -ti --name python3.8 -v ${PWD}:/mnt python:3.8.3-slim-buster /bin/bash
root@ddaf6aefedfe:/# pip3 install dna_workflows
...install...
root@ddaf6aefedfe:/# cd /mnt/
root@ddaf6aefedfe:/mnt# cat credentials
dnacentersdk:
    api_version: "1.3.0"
    base_url: "https://10.201.14.12"
    username: "admin"
    password: "***********"
    verify: False
isepac:
    host: '10.201.14.14'
    username: admin
    password: "***********"
    verify: False
    disable_warnings: True
root@ddaf6aefedfe:/mnt# dna_workflows --noop
2020-06-08 14:29:34,301 - main - INFO - API connectivity established with dnacentersdk
2020-06-08 14:29:34,301 - main - INFO - API connectivity established with isepac
2020-06-08 14:29:34,309 - main - INFO - Executing STAGE-1 workflow: noop::noop
root@ddaf6aefedfe:/mnt# dna_workflows --build-xlsx example.xlsx
```
