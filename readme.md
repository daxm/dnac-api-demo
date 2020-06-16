# DNA Center API Demo
The purpose of this repository is to maintain a Dockerfile that runs a Python script that issues some API calls to a
DNA Center.

## Quickstart
1.  Install Docker on your PC.
1.  Connect your PC into the network that has access to your DNA Center.
1.  Configure your DNA Center credentials and sample code in userdata.xlsx file.
1.  Issue the following commands: (**Note:  You may need to run as Administrator or root.**)
```commandline
docker pull dmickels/dnac-api-demo:latest
docker stop dnac-api-demo
docker run --rm --name dnac-api-demo dmickels/dnac-api-demo:latest
```

You can then access DNA Center UI and view your changes.

**Note:**  If you have your own XLSX file that you want to use then mount it as /userdata.xlsx:
```commandline
docker run --rm --name dnac-api-demo -v your.xlsx:/userdata.xlsx dmickels/dnac-api-demo:latest
```
