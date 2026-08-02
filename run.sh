#!/bin/bash

# Setup logging
exec > >(tee --append build.log) 2>&1

BRANCH=`git rev-parse --abbrev-ref HEAD`

TIME=`date "+%Y-%m-%d %H:%M:%S"`
echo "[${TIME}] Running pi-gen for branch ${BRANCH}..."

# Execute pi-gen
sudo ./build.sh

# Generate manifest from deploy directory
TIME=`date "+%Y-%m-%d %H:%M:%S"`
echo "[${TIME}] Updating Pi Imager manifest..."

python manifest/add_custom_images.py

