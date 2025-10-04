IMAGE_NAME := magplex
IMAGE_TAG := latest
PORT_APP := 8080
OUTPUT_FILE := magplex.tar

# Set delete command as Windows or Linux.
ifeq ($(OS),Windows_NT)
    RM := del /Q
else
    RM := rm -f
endif

.PHONY: all build clean

all: clean build

build:
	@echo Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)...
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo Docker image built successfully.
	docker save -o magplex.tar magplex:latest
	@echo Docker image saved successfully.

clean:
	@echo Deleting $(OUTPUT_FILE)...
	$(RM) $(OUTPUT_FILE)
	@echo Clean complete.