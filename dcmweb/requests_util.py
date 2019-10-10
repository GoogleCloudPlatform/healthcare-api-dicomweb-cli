# -*- coding: utf-8 -*-
"""Module contains helper classes with methods to perform dicomweb requests
"""

import logging
import requests
import validators

PAGE_SIZE = 5000


class NetworkError(Exception):
    """exception for unexpected responses"""


def validate_host_str(host):
    """Function to check host url"""
    if not validators.url(host):
        raise ValueError('Invalid url')
    if host[-1] != '/':
        host += '/'
    return host

def get_dicom_tag(dictionary, tag):
    """Wrapper for dicom json dict"""
    return dictionary[tag]["Value"][0]

def add_limit_if_not_present(parameters):
    """Adds limit parameter if it's not present"""
    if "limit" not in parameters:
        if len(parameters) > 0:
            parameters += "&"
        parameters += "limit={}".format(PAGE_SIZE)
    return parameters

class Requests:
    """Class keep state of credentials
     and performs request to dicomWeb"""

    def __init__(self, host_str, authenticator):
        self.host = validate_host_str(host_str)
        self.authenticator = authenticator

    def apply_credentials(self, headers):
        """Applyes credentials from authenticator to headers"""
        if self.authenticator:
            self.authenticator.apply_credentials(headers)
        return headers

    def request(self, path, parameters, headers):
        """Performs request to dicomWeb"""
        url = self.build_url(path, parameters)
        logging.debug('requesting %s', url)
        response = requests.get(url,
                                headers=self.apply_credentials(headers))
        if response.status_code != 200:
            raise NetworkError("Unexpected return code {}\n {}".format(
                response.status_code, response.text))

        return response

    def upload_dicom(self, file_name):
        """Uploads single file to dicomWeb"""
        with open(file_name, 'rb') as file:
            headers = self.apply_credentials(
                {'Content-Type': 'application/dicom'})
            response = requests.post(self.build_url(
                "studies", ""), headers=headers, data=file)
            if response.status_code == 200:
                logging.info('%s is uploaded', file_name)
            else:
                logging.info('failed to upload %s\n %s',
                             file_name, response.text)
            return response.status_code

    def build_url(self, path, parameters):
        """Builds url from host and path"""
        path_str = str(path)
        if len(path_str) > 0 and path_str[0] == '/':
            path_str = path_str[1:]
        if parameters and parameters[0] != '?':
            path_str += "?"
        return self.host+path_str+parameters
