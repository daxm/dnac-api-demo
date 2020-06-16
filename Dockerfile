FROM python:latest
MAINTAINER Dax Mickelson (dmickels@cisco.com)

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY dnawf/userdata.xlsx /
COPY dnawf/ .

CMD [ "python", "/usr/src/app/run_dna_workflows.py", "--db", "/userdata.xlsx", "--debug" ]
