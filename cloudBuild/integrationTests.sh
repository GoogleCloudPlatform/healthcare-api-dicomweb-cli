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

check_exit_code() {
  exit_code="${1}"
  error_message="${2}"
  if [[ "${exit_code}" != 0 ]]; then
    echo "${error_message}"
    exit 1
  fi
}

compare_files(){
  difflines=$(diff ${1} ${2})
  if [ ! -z "$difflines" ]
    then
        echo $difflines
        exit 1
  fi
}

apt-get -qq install python3 python3-pip -y 
pip3 install -r requirements.txt
pip3 install ./dist/*.whl 

readonly dicom_store_name="$(openssl rand -hex 12)"

# Creates unique DICOM Store
gcloud alpha healthcare dicom-stores create "${dicom_store_name}" \
  --location="${LOCATION}" \
  --dataset="${DATASET}" \
  --quiet
host="https://healthcare.googleapis.com/${STAGE}/projects/${PROJECT}/locations/${LOCATION}/datasets/${DATASET}/dicomStores/${dicom_store_name}/dicomWeb"

dcmweb $host store ./cloudBuild/dcms/1.dcm
single_upload_exit_code=$?

dcmweb $host search studies > ./cloudBuild/searchResults.json
search_exit_code=$?

dcmweb $host retrieve studies/111/series/111/instances/111
retrieve_exit_code=$?

gcloud alpha healthcare dicom-stores delete "${dicom_store_name}" \
  --location=$LOCATION \
  --dataset=$DATASET \
  --quiet

compare_files ./cloudBuild/searchResults.json ./cloudBuild/expectedSearchResults.json
compare_files ./111/111/111.dcm ./cloudBuild/dcms/1.dcm


check_exit_code $single_upload_exit_code "single upload failed"
check_exit_code $search_exit_code "search failed"
check_exit_code $retrieve_exit_code "retrieve failed"
