USERNAME=$(shell id -un)
USERID=$(shell id -u)
PASSWORD=changeme
IMAGENAME=metafit
DOCKERFILEDIR=docker/Dockerfile

build:
	docker build \
		--build-arg USERID=$(USERID) \
		--build-arg USERNAME=$(USERNAME) \
		--build-arg PASSWORD=$(PASSWORD) \
		-t $(IMAGENAME) \
		--network=host \
		-f $(DOCKERFILEDIR) .

run:
	docker run --gpus all -it --rm --shm-size 32GB --name $(IMAGENAME) \
	            --network host \
	            -v $(shell pwd):/metafit \
	            $(IMAGENAME)
