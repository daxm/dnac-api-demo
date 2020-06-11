FROM python:latest
MAINTAINER Dax Mickelson (dmickels@cisco.com)

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY userdata.xlsx /
COPY run_dna_workflows.py .

CMD [ "python", "./run_dna_workflows.py --build-xlsx /userdata.xlsx" ]
