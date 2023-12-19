FROM nvidia/cuda:11.8.0-runtime-ubuntu20.04
ENV YOLOV5_VERSION=v7.0
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg wget git python3-pip python3-opencv && rm -fr /var/lib/apt/lists/*

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

WORKDIR /work
RUN git clone -b $YOLOV5_VERSION https://github.com/ultralytics/yolov5
WORKDIR /work/yolov5

# Need this version of numpy to make sure we don't run into np.bool problems
RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir numpy==1.23.1 &&\
    pip3 install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu118 &&\
    pip3 install --no-cache-dir -r requirements.txt

# set work directory
WORKDIR /usr/src/app