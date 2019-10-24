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

readonly REPO_NAME="${1}"
readonly TAG_NAME="${2}"
readonly GITHUB_TOKEN="${GITHUB_TOKEN}"
readonly PYPI_TOKEN="${PYPI_TOKEN}"

pip3 install twine 
# Get GitHub user and GitHub repo from REPO_NAME
IFS='_' read -ra array <<< "${REPO_NAME}"
github_user="${array[1]}"
github_repo="${array[2]}"

if [[ -z "${github_user}" ]]
then
  github_user="GoogleCloudPlatform"
  github_repo="${REPO_NAME}"
fi
# Create request.json with request parameters
echo "{\"tag_name\": \"${TAG_NAME}\",\"name\": \"${TAG_NAME}\"}" > request.json
# Create a request for creating a release on GitHub page
readonly response_file="response.json"
response_code="$(curl -# -X POST \
-H "Content-Type:application/json" \
-H "Accept:application/json" \
-w "%{http_code}" \
--data-binary "@/workspace/request.json" \
"https://api.github.com/repos/${github_user}/${github_repo}/releases?access_token=${GITHUB_TOKEN}" \
-o "${response_file}")"
# Check status code
if [[ "${response_code}" != 201 ]]; then
  cat "${response_file}"
  exit 1
fi
# Get release id from response.json
release_id="$(grep -wm 1 "id" /workspace/response.json \
  | grep -Eo "[[:digit:]]+")"
# Get version from setup.py
version="$(grep -m 1 "version=" ./setup.py \
  | grep -Eo "[[:digit:]]+.[[:digit:]]+.[[:digit:]]+")"
file_name="dcmweb-${version}-py3-none-any.whl"
# Upload package to GitHub releases page
response_code="$(curl -# -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
-H "Content-Type:application/octet-stream" \
-w "%{http_code}" \
--data-binary "@/workspace/dist/${file_name}" \
"https://uploads.github.com/repos/${github_user}/${github_repo}/releases/${release_id}/assets?name=${file_name}" \
-o "${response_file}")"
# Check status code
if [[ "${response_code}" != 201 ]]; then
  cat "${response_file}"
  exit 1
fi
# Upload package to pip
python3 -m twine upload "./dist/${file_name}" --username=__token__ --password="${PYPI_TOKEN}"
