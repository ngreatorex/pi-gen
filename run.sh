#!/bin/bash
echo > build.log

sudo ./build.sh 2>&1 | tee build.log
python manifest/add_custom_images.py | tee build.log

#pushd deploy/
#tar -zcvf custom-images.tar.gz *
#popd

