FROM ubuntu:18.04
MAINTAINER Ridwan Shariffdeen <rshariffdeen@gmail.com>
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates software-properties-common

# Installing dependencies for Darjeeling

# Refresh local apt keys & update
RUN apt-key adv --refresh-keys --keyserver keyserver.ubuntu.com \
    && apt-get update -qq

# add deadsnakes ppa
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get -y install \
    curl \
    git \
    nano \
    python3.9 \
    python3.9-distutils

# remove old, default python version
RUN apt remove python3.6-minimal -y

# Create a python3 symlink pointing to latest python version
RUN ln -sf /usr/bin/python3.9 /usr/bin/python3

# Install matching pip version
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python3.9 get-pip.py \
    && rm get-pip.py



RUN python3 -m pip install pipenv virtualenv

RUN git clone https://github.com/rshariffdeen/Darjeeling /opt/darjeeling
WORKDIR /opt/darjeeling
RUN git submodule update --init --recursive
RUN python3.9 -m pip install .


# install dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      docker.io \
      gcc \
      gcovr \
      libc6-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# create docker user
RUN apt-get update \
 && apt-get install --no-install-recommends -y sudo patch \
 && useradd -ms /bin/bash docker \
 && echo 'docker ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers \
 && adduser docker sudo \
 && apt-get clean \
 && mkdir -p /home/docker \
 && sudo chown -R docker /home/docker \
 && sudo chown -R docker /usr/local/bin \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
USER docker


