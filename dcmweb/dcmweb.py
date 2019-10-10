# -*- coding: utf-8 -*-
"""Module contains classes for interacting with DICOMweb
"""
import logging
import json
import google.auth
import google.auth.transport.requests
from . import requests_util

logging.basicConfig(format='%(asctime)s -- %(message)s',
                    level=logging.INFO)


class Dcmweb:  # pylint: disable=too-few-public-methods; this is temporary while only one method is present
    """A command line utility for interacting with DICOMweb servers."""

    def __init__(self, host_str, multithreading, authenticator):
        self.multithreading = multithreading
        self.requests = requests_util.Requests(host_str, authenticator)

    def search(self, path="studies", parameters=""):
        """Performs a search over studies, series or instances.
        parameters is the QIDO search parameters
        """
        search_result = self.requests.request(
            path, requests_util.add_limit_if_not_present(parameters), {}).text
        if "limit" not in parameters and len(json.loads(search_result)) >= requests_util.PAGE_SIZE:
            logging.info('Please note: by deafult search returns only first %s result,\
 please use additional parameters (offset,limit) to get more', requests_util.PAGE_SIZE)
        return search_result



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
