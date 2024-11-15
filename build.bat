@echo off
setlocal

rem Set the image name and tag
set IMAGE_NAME=magplex
set IMAGE_TAG=latest
set OUTPUT_FILE=magplex.tar

rem Build the Docker image
echo Building Docker image %IMAGE_NAME%:%IMAGE_TAG%...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .

rem Check if the build was successful
if errorlevel 1 (
    echo Docker image build failed!
    exit /b 1
)

rem Save the Docker image to a tar file
echo Saving Docker image to %OUTPUT_FILE%...
docker save -o %OUTPUT_FILE% %IMAGE_NAME%:%IMAGE_TAG%

rem Check if the save was successful
if errorlevel 1 (
    echo Docker image save failed!
    exit /b 1
)

echo Docker image saved successfully to %OUTPUT_FILE%.