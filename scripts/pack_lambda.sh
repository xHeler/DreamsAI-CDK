#!/bin/bash

cd ..
cd lambdas/images_generation/

pip install -r requirements.txt -t package/

cd package
zip -r9 ../function.zip .
