FROM python:latest
MAINTAINER Dax Mickelson (dmickels@cisco.com)

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./entry_point.py" ]
