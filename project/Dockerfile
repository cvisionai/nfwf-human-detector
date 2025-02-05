# pull official base image
FROM python:3.9.5-slim-buster
RUN apt-get update && apt-get install --no-install-recommends -y wget xz-utils && rm -fr /var/lib/apt/lists/*
# set work directory
WORKDIR /tmp
RUN wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
RUN tar -xf ffmpeg-git-amd64-static.tar.xz
RUN mv ffmpeg-git-*-amd64-static/ffmpeg /usr/local/bin/
RUN mv ffmpeg-git-*-amd64-static/ffprobe /usr/local/bin/
RUN rm -fr ffmpeg-git-*

WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip setuptools wheel
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
