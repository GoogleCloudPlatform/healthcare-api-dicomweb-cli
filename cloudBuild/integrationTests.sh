#!/bin/bash

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

readonly STAGE="${1}"
readonly PROJECT="${2}"
readonly LOCATION="${3}"
readonly DATASET="${4}"


apt-get -qq install python3 python3-pip -y 
pip3 install -r requirements.txt
pip3 install ./dist/*.whl 

readonly dicom_store_name="$(openssl rand -hex 12)"

# Creates unique DICOM Store
gcloud alpha healthcare dicom-stores create "${dicom_store_name}" \
  --location="${LOCATION}" \
  --dataset="${DATASET}" \
  --quiet

#for now just prints []
dcmweb https://healthcare.googleapis.com/${STAGE}/projects/${PROJECT}/locations/${LOCATION}/datasets/${DATASET}/dicomStores/${dicom_store_name}/dicomWeb search studies
search_exit_code=$?

if [[ "${search_exit_code}" != 0 ]]; then
  echo "search failed"
  exit 1
fi

gcloud alpha healthcare dicom-stores delete "${dicom_store_name}" \
  --location=$LOCATION \
  --dataset=$DATASET \
  --quiet
