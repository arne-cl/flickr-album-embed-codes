# Dockerfile to build a discoursegraphs container image

FROM ubuntu:14.04

MAINTAINER Arne Neumann <flickr.programming@arne.cl>

RUN apt-get update && apt-get upgrade -y
RUN apt-get install python-setuptools git xvfb firefox -y

WORKDIR /opt/
RUN git clone https://github.com/arne-cl/flickr-album-embed-codes.git

WORKDIR /opt/flickr-album-embed-codes/
RUN python setup.py install

ENTRYPOINT ["flickr-album-embed-codes"]

