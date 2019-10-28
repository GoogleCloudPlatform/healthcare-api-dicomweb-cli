# -*- coding: utf-8 -*-
"""Module contains classes for interacting with DICOMweb
"""
import logging
import glob
import os
import json
import concurrent.futures
import google.auth
import google.auth.transport.requests

from . import requests_util

logging.basicConfig(format='%(asctime)s -- %(message)s',
                    level=logging.INFO)

INDENT = 2
SORT_KEYS = True
QUEUE_LIMIT = 100


def execute_futures(futures_arguments, multithreading):
    """Executing features builded from futures_arguments set"""
    running_futures = set([])
    with concurrent.futures.ThreadPoolExecutor(max_workers=None if multithreading else 1)\
            as executor:
        for future_arguments in futures_arguments:
            running_futures = wait_for_futures_limit(
                running_futures, QUEUE_LIMIT)
            running_futures.add(executor.submit(*future_arguments))
        wait_for_futures_limit(running_futures, 0)


def wait_for_futures_limit(running_futures, limit):
    """Waits until running_futures set reaches size of limit"""
    while len(running_futures) > limit:
        done_futures, running_futures = concurrent.futures.wait(
            running_futures, timeout=1)
        for done_future in done_futures:
            try:
                done_future.result()
            except requests_util.NetworkError as exception:
                logging.error('Request failure: %s', exception)
    return running_futures


class Dcmweb:
    """A command line utility for interacting with DICOMweb servers."""

    def __init__(self, host_str, multithreading, authenticator):
        self.multithreading = multithreading
        self.requests = requests_util.Requests(host_str, authenticator)

    def search(self, path="studies", parameters=""):
        """Performs a search over studies, series or instances.
        parameters is the QIDO search parameters
        """
        search_result = json.loads(self.requests.request(
            path, requests_util.add_limit_if_not_present(parameters), {}).text)
        if "limit" not in parameters and len(search_result) >= requests_util.PAGE_SIZE:
            logging.info('Please note: by deafult search returns only first %s result,\
 please use additional parameters (offset,limit) to get more', requests_util.PAGE_SIZE)
        return json.dumps(search_result, indent=INDENT, sort_keys=SORT_KEYS)

    def store(self, *masks):
        """Stores one or more files by posting multiple StoreInstances requests."""
        execute_futures(
            self._files_to_upload(*masks), self.multithreading)

    def retrieve(self, path="", output="./", type=None):  # pylint: disable=redefined-builtin; part of Fire lib configuration
        """Retrieves one or more studies, series, instances or frames from the server."""
        ids = requests_util.ids_from_path(path)
        if requests_util.get_path_level(ids) in ("instances", "frames"):
            self.requests.download_dicom_by_ids(ids, output, type)
            return
        execute_futures(self._files_to_download(
            ids, output, type), self.multithreading)

    def delete(self, path):
        """Deletes the given study, series or instance from the server."""
        try:
            self.requests.delete_dicom(path)
        except requests_util.NetworkError as exception:
            logging.error('Delete failure: %s', exception)

    def _files_to_upload(self, *masks):
        """Generates set of argumets to run upload based on masks"""
        for mask in masks:
            mask = mask.replace("**", "**/*")
            for file_name in glob.glob(mask, recursive=True):
                if not os.path.isdir(file_name):
                    yield (self.requests.upload_dicom, file_name)

    def _files_to_download(self, ids, output, mime_type):
        """Generates set of argumets to run download based on ids dict"""
        page = 0
        instances = []
        while page == 0 or len(instances) > 0:
            page_content = self.requests.search_instances_by_page(
                ids, "includefield={}&includefield={}"
                .format(requests_util.STUDY_TAG, requests_util.SERIES_TAG), page)
            instances = json.loads(page_content)
            for instance in instances:
                yield (self.requests.download_dicom_by_ids,
                       requests_util.ids_from_json(instance), output, mime_type)
            page += 1


class GoogleAuthenticator:
    """Handles authenticattion with Google"""

    def __init__(self):
        self.credentials = None

    def apply_credentials(self, headers):
        """Adds token to request"""
        self.check_and_refresh_credentials()
        self.credentials.apply(headers)
        return headers

    def check_and_refresh_credentials(self):
        """Updates credentials if not valid"""
        if self.credentials is None:
            self.credentials = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform'])[0]
        if not self.credentials.valid:
            auth_req = google.auth.transport.requests.Request()
            self.credentials.refresh(auth_req)
