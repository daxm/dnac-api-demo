FROM python:latest
MAINTAINER Dax Mickelson (dmickels@cisco.com)

WORKDIR /usr/src/app
ARG build_xlsx=build-xlsx

ENV arg_var=$build_xlsx

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY dnawf/userdata.xlsx /
COPY dnawf/ .

CMD [ "python", "./run_dna_workflows.py --$arg_var /userdata.xlsx" ]
