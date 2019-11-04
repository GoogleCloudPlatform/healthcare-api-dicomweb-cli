# -*- coding: utf-8 -*-
"""Module contains helper classes with methods to perform dicomweb requests
"""

import logging
import os
from threading import Lock
import urllib.parse as urlparse
import requests

from . import resources

PAGE_SIZE = 5000

DCM_EXTENSION = ".dcm"
JPEG_EXTENSION = ".jpg"
PNG_EXTENSION = ".png"

CONTENT_TYPE = "Content-Type"
MULTIPART = "multipart/related"
TRANSFER_SYNTAX = "transfer-syntax="


def filter_urllib3_logging():
    """Filter header errors from urllib3 due to a urllib3 bug.
     https://github.com/urllib3/urllib3/issues/800"""
    urllib3_logger = logging.getLogger("urllib3.connectionpool")
    if not any(isinstance(x, NoHeaderErrorFilter)
               for x in urllib3_logger.filters):
        urllib3_logger.addFilter(
            NoHeaderErrorFilter()
        )


class NoHeaderErrorFilter(logging.Filter):  # pylint: disable=too-few-public-methods; this Class only filtering bug
    """Filter out urllib3 Header Parsing Errors due to a urllib3 bug."""

    def filter(self, record):
        """Filter out Header Parsing Errors."""
        return "Failed to parse headers" not in record.getMessage()


filter_urllib3_logging()


def add_limit_if_not_present(parameters, limit=PAGE_SIZE):
    """Adds limit parameter if it's not present"""
    if "limit" not in parameters:
        if len(parameters) > 0:
            parameters += "&"
        parameters += "limit={}".format(limit)
    return parameters


def extension_by_headers(content_type):
    """Generates extension string and multipart flag"""
    if "dicom" in content_type:
        return DCM_EXTENSION
    if "jpeg" in content_type:
        return JPEG_EXTENSION
    if "png" in content_type:
        return PNG_EXTENSION

    raise ValueError("unknown extension {}".format(content_type))


def parse_boundary(content_type):
    """Returns boundary from content type"""
    boundary_start = content_type.find("boundary=")+9
    return bytes(content_type[boundary_start:content_type.find(
        ";", boundary_start)], "utf-8")


def adjust_mime_type(mime_type):
    """"Adjusts mime type to format:
    "multipart/related; type=<type>[; transfer-syntax=<transfer-syntax>]"
    """
    if not mime_type:
        return "application/dicom; "+TRANSFER_SYNTAX+"*"
    transfer_syntax = ""
    if TRANSFER_SYNTAX in mime_type:
        mime_type_splitted = mime_type.split("; ")
        if len(mime_type_splitted) != 2:
            raise ValueError("incorect type value {}".format(mime_type))
        mime_type = mime_type_splitted[0]
        transfer_syntax = TRANSFER_SYNTAX+'={}'.format(
            mime_type_splitted[1][16:])

    return MULTIPART + '; type="{}"; '.format(mime_type) + transfer_syntax

def build_multipart_file_name(file_name, frame_index, extension):
    """"Builds file name for different extensions and frames"""
    if extension != DCM_EXTENSION:
        file_name += "_frame_" + str(frame_index)
    return file_name + extension

class NetworkError(Exception):
    """exception for unexpected responses"""


class Requests:
    """Class keep state of credentials
     and performs request to dicomWeb"""

    def __init__(self, host_str, authenticator):
        self.host = resources.validate_host_str(host_str)
        self.authenticator = authenticator
        self.authenticator_lock = Lock()

    def apply_credentials(self, headers):
        """Applyes credentials from authenticator to headers"""
        if self.authenticator:
            with self.authenticator_lock:
                self.authenticator.apply_credentials(headers)
        return headers

    def request(self, path, parameters, headers, stream=False):
        """Performs request to dicomWeb"""
        url = self.build_url(path, parameters)
        logging.debug('requesting %s', url)
        response = requests.get(url,
                                headers=self.apply_credentials(headers), stream=stream)
        if response.status_code != 200:
            raise NetworkError("Unexpected return code {}\n {}".format(
                response.status_code, response.text))

        return response

    def upload_dicom(self, file_name):
        """Uploads single file to dicomWeb
           :param file_name: path to dicom file in file system
           :returns: amount of bytes transferred during upload"""
        with open(file_name, 'rb') as file:
            headers = self.apply_credentials(
                {CONTENT_TYPE: 'application/dicom'})
            response = requests.post(self.build_url(
                "studies", ""), headers=headers, data=file)
            if response.status_code != 200:
                raise NetworkError("uploading file: {}\n response: {}".format(
                    file_name, response.text))
            return file.tell()

    def delete_dicom(self, path):
        """ Deletes single dicom object by sending DELETE http request"""
        path = resources.validate_path(path)
        response = requests.delete(self.build_url(
            path, ""), headers=self.apply_credentials({}))
        if response.status_code != 200:
            raise NetworkError("sending http delete request: {}\n response: {}".format(
                path, response.text))

    def search_instances_by_page(self, ids, parameters, page):
        """Performs page request"""
        limit = PAGE_SIZE
        par = urlparse.parse_qs(parameters)
        if "offset" in par:
            raise ValueError("offset shouldnt be specified")
        if "limit" in par:
            limit = int(par["limit"][0])
        if limit > PAGE_SIZE:
            raise ValueError("limit can\'t be more than {}".format(
                PAGE_SIZE))

        text = self.request(
            resources.path_from_ids(
                ids)+"/instances", add_limit_if_not_present(parameters, limit)
            + "&offset={}".format(limit*page), {}).text
        return text

    def download_dicom(self, url, folder, file_name, mime_type):
        """Downloads dicom object or frames from this dicom object according to mime_type
        :param url: url to dicom object
        :param folder: folder in local file system to store files,
                       would be created if not exist
        :param file_name: base for file name,
                                   extension and frame number added based on response headers
        :param mime_type: mime_type to request (image/png, image/jpeg)
        """
        mime_type = adjust_mime_type(mime_type)

        if not os.path.exists(folder):
            os.makedirs(folder)

        response = self.request(url, "", {'Accept': mime_type}, stream=True)
        content_type = response.headers[CONTENT_TYPE].lower()
        extension = extension_by_headers(content_type)
        is_multipart = content_type.startswith(MULTIPART)
        file_name = folder + file_name
        boundary = None
        if is_multipart:
            frame_index = 0
            file = None
            boundary = parse_boundary(content_type)
        else:
            file = open(file_name+extension, 'wb')
        transferred = 0
        for chunk, new_file in MultipartChunksReader(
                response.iter_content(chunk_size=8192), boundary).read_chunks():
            if new_file:
                if file:
                    file.close()
                frame_index += 1
                file = open(build_multipart_file_name(
                    file_name, frame_index, extension), 'wb')
            transferred += file.write(chunk)

        if not file.closed:
            file.close()
        return transferred

    def download_dicom_by_ids(self, ids, output="./", mime_type=None):
        """Downloads instance based on ids dict object"""
        url = resources.path_from_ids(ids)
        folder, file_name = resources.file_system_full_path_by_ids(ids, output)
        return self.download_dicom(url, folder, file_name, mime_type)

    def build_url(self, path, parameters):
        """Builds url from host and path"""
        path_str = str(path)
        if len(path_str) > 0 and path_str[0] == resources.SPLIT_CHAR:
            path_str = path_str[1:]
        if parameters and parameters[0] != '?':
            path_str += "?"
        return self.host+path_str+parameters


class MultipartChunksReader:  # pylint: disable=too-few-public-methods; need for readability
    """Class keep state of multipart stream"""

    def __init__(self, chunks, boundary):
        self.chunks = chunks
        self.boundary = boundary

    def read_chunks(self):
        """Streaming  flag of new file and chunks and except boundary chunks"""
        new_file = False
        for chunk in self.chunks:
            if self.boundary and self.boundary in chunk:
                if bytes(CONTENT_TYPE, "utf-8") in chunk:
                    new_file = True
            else:
                yield chunk, new_file
                new_file = False
