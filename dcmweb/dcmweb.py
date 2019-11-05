# -*- coding: utf-8 -*-
"""Module contains classes for interacting with DICOMweb
"""
import logging
import glob
import os
import sys
import json
import concurrent.futures
import google.auth
import google.auth.transport.requests
from hurry.filesize import size

from . import requests_util
from . import resources

logging.basicConfig(format='%(asctime)s -- %(message)s',
                    level=logging.INFO)

INDENT = 2
SORT_KEYS = True
QUEUE_LIMIT = 100


def execute_file_transfer_futures(futures_arguments, multithreading):
    """Executing features builded from futures_arguments set
    :param futures_arguments: set of tuples to set up futures
    :param multithreading: flag for multithreading execution
    :returns: a dict {'bytes':<amount of transferred bytes>, 'files':<amount of transferred files>}
    """
    running_futures = set([])
    transferred = {'bytes': 0, 'files': 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=None if multithreading else 1)\
            as executor:
        for future_arguments in futures_arguments:
            running_futures, transferred = wait_for_futures_limit(
                running_futures, transferred, QUEUE_LIMIT)
            running_futures.add(executor.submit(*future_arguments))
        wait_for_futures_limit(running_futures, transferred, 0)
    logging.info('')#new line to avoid overlap by next output
    return transferred


def wait_for_futures_limit(running_futures, transferred, limit):
    """Waits until running_futures set reaches size of limit
    :param running_futures: set of futures awaited to be done,
                            each future should return amount of transferred bytes
    :param transferred: a dict {'bytes': <amount of transferred bytes>,
                        'files': <amount of transferred files>}
    :returns: updated transferred dict
    """
    transferred_bytes = 0
    transferred_files = 0
    while len(running_futures) > limit:
        done_futures, running_futures = concurrent.futures.wait(
            running_futures, timeout=1)
        for done_future in done_futures:
            try:
                transferred_bytes += done_future.result()
                transferred_files += 1
            except requests_util.NetworkError as exception:
                logging.error('Request failure: %s', exception)
    if transferred_files > 0:
        transferred['files'] += transferred_files
        transferred['bytes'] += transferred_bytes
        #extra spaces to cover previous line if it has few charates
        logging.info('Transferred %s in %s files     \x1b[1A\x1b[\x1b[80D', size(
            transferred['bytes']), transferred['files'])
    return running_futures, transferred


class Dcmweb:
    """A command line utility for interacting with DICOMweb servers."""

    def __init__(self, host_str, multithreading, authenticator):
        self.multithreading = multithreading
        self.requests = requests_util.Requests(host_str, authenticator)
        self._validate_request()

    def search(self, path="studies", parameters=""):
        """Performs a search over studies, series or instances.
        parameters is the QIDO search parameters
        """
        search_result = {}
        try:
            search_result = json.loads(self.requests.request(
                path, requests_util.add_limit_if_not_present(parameters), {}).text)
        except requests_util.NetworkError as exception:
            logging.error('Search failure: %s', exception)
            return "[]"
        if "limit" not in parameters and len(search_result) >= requests_util.PAGE_SIZE:
            logging.info('Please note: by deafult search returns only first %s result,\
 please use additional parameters (offset,limit) to get more', requests_util.PAGE_SIZE)
        return json.dumps(search_result, indent=INDENT, sort_keys=SORT_KEYS)

    def store(self, *masks):
        """Stores one or more files by posting multiple StoreInstances requests."""
        execute_file_transfer_futures(
            self._files_to_upload(*masks), self.multithreading)

    def retrieve(self, path="", output="./", type=None):  # pylint: disable=redefined-builtin; part of Fire lib configuration
        """Retrieves one or more studies, series, instances or frames from the server."""
        ids = resources.ids_from_path(path)
        logging.info('Saving files into %s', output)
        if resources.get_path_level(ids) in ("instances", "frames"):
            try:
                self.requests.download_dicom_by_ids(ids, output, type)
            except requests_util.NetworkError as exception:
                logging.error('Retrieve failure: %s', exception)
            return
        execute_file_transfer_futures(self._files_to_download(
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
                .format(resources.STUDY_TAG, resources.SERIES_TAG), page)
            instances = json.loads(page_content)
            for instance in instances:
                yield (self.requests.download_dicom_by_ids,
                       resources.ids_from_json(instance), output, mime_type)
            page += 1

    def _validate_request(self):
        """Performs request to check availability of service"""
        try:
            self.requests.request("studies", "limit=1", {})
        except requests_util.NetworkError as exception:
            logging.error('host %s is inaccessible: %s', self.requests.host, exception)
            sys.exit(1)

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
