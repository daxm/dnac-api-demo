FROM python:latest
MAINTAINER Dax Mickelson (dmickels@cisco.com)

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /userdata
COPY userdata.xlsx /userdata/.
COPY dnac_workflows .

CMD [ "python", "./dna_workflows --build-xlsx /userdata/userdata.xlsx" ]
