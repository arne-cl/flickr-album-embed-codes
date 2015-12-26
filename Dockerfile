# Dockerfile to build a discoursegraphs container image

FROM ubuntu:14.04

MAINTAINER Arne Neumann <flickr.programming@arne.cl>

RUN apt-get update
RUN apt-get install python-setuptools -y
RUN apt-get install git -y
#RUN apt-get install -y python-dev python-pip git graphviz-dev libxml2-dev libxslt-dev

#RUN easy_install -U setuptools

WORKDIR /opt/
RUN git clone https://github.com/arne-cl/flickr-album-embed-codes.git

WORKDIR /opt/flickr-album-embed-codes/
#RUN python setup.py install

