# -*- coding: utf-8 -*-
"""Module contains helper classes with methods to perform dicomweb requests
"""

import logging
import os
from threading import Lock
import urllib.parse as urlparse
import requests
import validators


PAGE_SIZE = 5000

STUDY_TAG = "0020000D"
SERIES_TAG = "0020000E"
INSTANCE_TAG = "00080018"

STUDY_ID = "study_id"
SERIES_ID = "series_id"
INSTANCE_ID = "instance_id"
FRAME_ID = "frame_id"

DCM_EXTENSION = ".dcm"
JPEG_EXTENSION = ".jpg"
PNG_EXTENSION = ".png"

CONTENT_TYPE = "Content-Type"
MULTIPART = "multipart/related"

ID_PATH_MAP = {STUDY_ID: "studies", SERIES_ID: "series",
               INSTANCE_ID: "instances", FRAME_ID: "frames"}

SPLIT_CHAR = '/'


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


class NetworkError(Exception):
    """exception for unexpected responses"""


def validate_host_str(host):
    """Function to check host url"""
    if not validators.url(host):
        raise ValueError('Invalid url')
    if host[-1] != SPLIT_CHAR:
        host += SPLIT_CHAR
    return host


def validate_path(path):
    """Function to check path"""
    if path:
        if path[0] == SPLIT_CHAR:
            path = path[1:]
        if path[-1] == SPLIT_CHAR:
            path = path[:-1]
        path_splitted = path.split(SPLIT_CHAR)
        number_of_pieces = len(path_splitted)
        if number_of_pieces < 2 or number_of_pieces % 2 \
                or path_splitted[-2] not in ["root", "studies", "series", "instances", "frames"]:
            raise ValueError("incorrect path")
    return path


def get_dicom_tag(dictionary, tag):
    """Wrapper for dicom json dict"""
    if tag not in dictionary:
        raise LookupError("Can't find {} tag ".format(tag))
    return dictionary[tag]["Value"][0]


def ids_from_json(json_dict):
    """Generates dict of ids based on json dict object"""
    ids = {}
    ids[STUDY_ID] = get_dicom_tag(json_dict, STUDY_TAG)
    ids[SERIES_ID] = get_dicom_tag(json_dict, SERIES_TAG)
    ids[INSTANCE_ID] = get_dicom_tag(json_dict, INSTANCE_TAG)
    return ids


def add_limit_if_not_present(parameters, limit=PAGE_SIZE):
    """Adds limit parameter if it's not present"""
    if "limit" not in parameters:
        if len(parameters) > 0:
            parameters += "&"
        parameters += "limit={}".format(limit)
    return parameters


def get_path_level(ids):
    """Return level of path
    :param: a dict of ids study_id:<uid>, series_id:<uid>,\
              instance_id:<uid>, [frame_id:<frame_num>]
    :returns: string level(root, studies, series, instances, frames)"""
    if not ids:
        return "root"
    if FRAME_ID in ids:
        return ID_PATH_MAP[FRAME_ID]
    if INSTANCE_ID in ids:
        return ID_PATH_MAP[INSTANCE_ID]
    if SERIES_ID in ids:
        return ID_PATH_MAP[SERIES_ID]
    if STUDY_ID in ids:
        return ID_PATH_MAP[STUDY_ID]
    raise ValueError("unknown level of path")


def ids_from_path(path):
    """Parses path to get Ids of study, series, instance and frame as optional
    :param path: path to dicom object(instance or frame)
             in form of url path /studies/<uid>/series/<uid>/instances/<uid>[/frames/<frame_num>]
    :returns: a dict of ids study_id:<uid>, series_id:<uid>,\
              instance_id:<uid>, [frame_id:<frame_num>]
    """
    path = validate_path(path)
    path_splitted = path.split(SPLIT_CHAR)
    ids = {}

    if len(path_splitted) >= 2:
        ids[STUDY_ID] = path_splitted[1]

    if len(path_splitted) >= 4:
        ids[SERIES_ID] = path_splitted[3]

    if len(path_splitted) >= 6:
        ids[INSTANCE_ID] = path_splitted[5]

    if len(path_splitted) >= 8:
        ids[FRAME_ID] = path_splitted[7]
    return ids


def path_from_ids(ids):
    """Builds path based on dict of ids
    :returns: a dict of ids study_id:<uid>, series_id:<uid>,\
              instance_id:<uid>, [frame_id:<frame_num>]
    :param path: path to dicom object(instance or frame)
             in form of url path /studies/<uid>/series/<uid>/instances/<uid>[/frames/<frame_num>]
    """
    path = ""
    if not ids:
        return path
    if STUDY_ID in ids:
        path += id_to_string(STUDY_ID, ids[STUDY_ID])
    if SERIES_ID in ids:
        path += id_to_string(SERIES_ID, ids[SERIES_ID])
    if INSTANCE_ID in ids:
        path += id_to_string(INSTANCE_ID, ids[INSTANCE_ID])
    if FRAME_ID in ids:
        path += id_to_string(FRAME_ID, ids[FRAME_ID])
    return path


def id_to_string(id_key, id_value):
    """ Builds string based kay and value of id"""
    return SPLIT_CHAR+ID_PATH_MAP[id_key]+SPLIT_CHAR+id_value


def extention_by_headers(content_type):
    """Generates extention string and multipart flag"""
    if "dicom" in content_type:
        return DCM_EXTENSION
    if "jpeg" in content_type:
        return JPEG_EXTENSION
    if "png" in content_type:
        return PNG_EXTENSION

    raise ValueError("unknown extention {}".format(content_type))


def file_system_full_path_by_ids(ids, base_dir="./"):
    """Builds file system path and file name based on ids"""
    path = ids[STUDY_ID] + SPLIT_CHAR + ids[SERIES_ID] + SPLIT_CHAR
    if base_dir[-1] != SPLIT_CHAR:
        path = SPLIT_CHAR + path
    path = base_dir + path
    file_name = ids[INSTANCE_ID]
    return path, file_name


def parse_boundary(content_type):
    """Returns boundary from content type"""
    boundary_start = content_type.find("boundary=")+9
    return bytes(content_type[boundary_start:content_type.find(
        ";", boundary_start)], "utf-8")

class Requests:
    """Class keep state of credentials
     and performs request to dicomWeb"""

    def __init__(self, host_str, authenticator):
        self.host = validate_host_str(host_str)
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
        path = validate_path(path)
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
            raise ValueError("limit can\'t be more than {}".format(PAGE_SIZE))

        text = self.request(
            path_from_ids(
                ids)+"/instances", add_limit_if_not_present(parameters, limit)
            + "&offset={}".format(limit*page), {}).text
        return text

    def download_dicom(self, url, folder, file_name, mime_type):
        """Downloads dicom object or frames from this dicom object according to mime_type
        :param url: url to dicom object
        :param folder: folder in local file system to store files,
                       would be created if not exist
        :param file_name: base for file name,
                                   extention and frame number added based on response headers
        :param mime_type: mime_type to request (image/png, image/jpeg)
        """

        if mime_type:
            mime_type = MULTIPART + '; type="{}"'.format(mime_type)
        else:
            mime_type = "application/dicom; transfer-syntax=*"

        if not os.path.exists(folder):
            os.makedirs(folder)

        response = self.request(url, "", {'Accept': mime_type}, stream=True)

        content_type = response.headers[CONTENT_TYPE].lower()
        extention = extention_by_headers(content_type)
        is_multipart = content_type.startswith(MULTIPART)
        file_name = folder + file_name
        boundary = None
        if is_multipart:
            frame_index = 0
            file = None
            boundary = parse_boundary(content_type)
        else:
            file = open(file_name+extention, 'wb')
        transferred = 0
        for chunk, new_file in MultipartChunksReader(
                response.iter_content(chunk_size=8192), boundary).read_chunks():
            if new_file:
                if file:
                    file.close()
                frame_index += 1
                file = open(file_name+"_frame_" +
                            str(frame_index)+extention, 'wb')
            transferred += file.write(chunk)

        if not file.closed:
            file.close()
        return transferred

    def download_dicom_by_ids(self, ids, output="./", mime_type=None):
        """Downloads instance based on ids dict object"""
        url = path_from_ids(ids)
        folder, file_name = file_system_full_path_by_ids(ids, output)
        return self.download_dicom(url, folder, file_name, mime_type)

    def build_url(self, path, parameters):
        """Builds url from host and path"""
        path_str = str(path)
        if len(path_str) > 0 and path_str[0] == SPLIT_CHAR:
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
