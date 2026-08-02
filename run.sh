#!/bin/bash

# Setup logging
truncate -s 0 build.log
exec > >(tee build.log) 2>&1

BRANCH=`git rev-parse --abbrev-ref HEAD`
TIME=`date "+%Y-%m-%d %H:%M:%S"`

echo "[${TIME}] Running pi-gen for branch ${BRANCH}..."

# Execute pi-gen
sudo ./build.sh

# Generate manifest from deploy directory
python manifest/add_custom_images.py

