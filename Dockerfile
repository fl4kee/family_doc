FROM python:3.9
ENV PYTHONUNBUFFERED = 1
WORKDIR /family_doc
COPY requirements.txt requirements.txt
RUN pip3.9 install -r requirements.txt