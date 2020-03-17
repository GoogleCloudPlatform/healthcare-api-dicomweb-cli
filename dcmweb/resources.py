# -*- coding: utf-8 -*-
"""Module contains helper fuctions to validate and trasform dicom paths and ids
"""

import xml.dom.minidom
import validators


STUDY_TAG = "0020000D"
SERIES_TAG = "0020000E"
INSTANCE_TAG = "00080018"

STUDY_ID = "study_id"
SERIES_ID = "series_id"
INSTANCE_ID = "instance_id"
FRAME_ID = "frame_id"

ID_PATH_MAP = {STUDY_ID: "studies", SERIES_ID: "series",
               INSTANCE_ID: "instances", FRAME_ID: "frames"}

SPLIT_CHAR = '/'

DICOM_XML_CONTENT_TYPE = "application/dicom+xml"

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
    ids[STUDY_ID] = get_dicom_tag(
        json_dict, STUDY_TAG)
    ids[SERIES_ID] = get_dicom_tag(
        json_dict, SERIES_TAG)
    ids[INSTANCE_ID] = get_dicom_tag(
        json_dict, INSTANCE_TAG)
    return ids


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
        path += id_to_string(STUDY_ID,
                             ids[STUDY_ID])
    if SERIES_ID in ids:
        path += id_to_string(SERIES_ID,
                             ids[SERIES_ID])
    if INSTANCE_ID in ids:
        path += id_to_string(INSTANCE_ID,
                             ids[INSTANCE_ID])
    if FRAME_ID in ids:
        path += id_to_string(FRAME_ID,
                             ids[FRAME_ID])
    return path


def id_to_string(id_key, id_value):
    """ Builds string based key and value of id"""
    return SPLIT_CHAR+ID_PATH_MAP[id_key]\
    +SPLIT_CHAR+id_value


def file_system_full_path_by_ids(ids, base_dir="./"):
    """Builds file system path and file name based on ids"""
    path = ids[STUDY_ID] + SPLIT_CHAR + \
        ids[SERIES_ID] + SPLIT_CHAR
    if base_dir[-1] != SPLIT_CHAR:
        path = SPLIT_CHAR + path
    path = base_dir + path
    file_name = ids[INSTANCE_ID]
    return path, file_name

def pretty_format(body, content_type):
    """Function to format response body by content_type"""
    if content_type.lower() == DICOM_XML_CONTENT_TYPE:
        body = xml.dom.minidom.parseString(body).toprettyxml(indent='    ')
    return body
