FROM pytorch/pytorch:1.7.1-cuda11.0-cudnn8-runtime

ARG DEBIAN_FRONTEND=noninteractive
ARG PW=changeme

ARG USERNAME
ARG USERID

RUN useradd -m ${USERNAME} --uid=${USERID} && echo "${USERNAME}:${PW}" | chpasswd

RUN apt update && apt install -y libgl1-mesa-glx gcc libglib2.0-0 libsm6 libxrender1 libxext6

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
COPY . /metafit

USER ${USERNAME}
WORKDIR /metafit
