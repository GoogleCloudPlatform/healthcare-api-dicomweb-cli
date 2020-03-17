# -*- coding: utf-8 -*-
"""dcmweb utils tests
"""
import unittest
import pytest_check as check
from dcmweb import resources


class DcmwebUtilTests(unittest.TestCase):
    """class is needed to handle exceptions"""

    def test_validate_host_str(self):
        """url should be validated"""
        with self.assertRaises(ValueError):
            resources.validate_host_str("invalid url")
        assert resources.validate_host_str(
            "https://valid.url") == "https://valid.url/"

    def test_validate_path(self):
        """path should be validated"""
        assert resources.validate_path("/studies/1") == "studies/1"
        assert resources.validate_path(
            "/studies/1/series/1/instances/1") == "studies/1/series/1/instances/1"
        with self.assertRaises(ValueError):
            resources.validate_path("/study/1")

    def test_get_dicom_tag(self):
        """ids should be reached by tags"""
        tags = {resources.STUDY_TAG: {"Value": ["1"]}, resources.SERIES_TAG: {
            "Value": ["2"]}, resources.INSTANCE_TAG: {"Value": ["3"]}}
        assert resources.get_dicom_tag(tags, resources.SERIES_TAG) == "2"
        assert resources.get_dicom_tag(tags, resources.STUDY_TAG) == "1"
        with self.assertRaises(LookupError):
            resources.get_dicom_tag(tags, "notag")


def test_get_path_level():
    """should get correct level"""
    check.equal(resources.get_path_level(
        resources.ids_from_path("")), "root")
    check.equal(resources.get_path_level(
        resources.ids_from_path("study/1/series/1/instances/3")), "instances")
    check.equal(resources.get_path_level(
        resources.ids_from_path("study/1/series/1/instances/3/frames/2")), "frames")


def test_ids_from_json():
    """should get correct ids from json"""
    tags = {resources.STUDY_TAG: {"Value": ["1"]}, resources.SERIES_TAG: {
        "Value": ["2"]}, resources.INSTANCE_TAG: {"Value": ["3"]}}
    assert resources.ids_from_json(
        tags) == {'study_id': '1', 'series_id': '2', 'instance_id': '3'}


def test_path_from_ids():
    """should get correct path from ids"""
    path = "/studies/1/series/2/instances/3"
    assert resources.path_from_ids(resources.ids_from_path(path)) == path


def test_file_system_full_path_by_ids():
    """should generate correct path and filename from json"""
    ids = {'study_id': '1', 'series_id': '2', 'instance_id': '3'}
    assert resources.file_system_full_path_by_ids(ids) == ('./1/2/', '3')


def test_ids_from_path():
    """should get correct ids"""
    check.equal(resources.ids_from_path(
        "study/1/series/2/instances/3"), {'study_id': '1', 'series_id': '2', 'instance_id': '3', })
    check.equal(resources.ids_from_path(
        "study/1/series/2/instances/3/frames/4"),
                {'study_id': '1', 'series_id': '2', 'instance_id': '3', 'frame_id': '4'})


def test_pretty_format():
    """should parse xml"""
    check.equal(resources.pretty_format(
        '<NativeDicomModel><Value number="1">redact</Value></NativeDicomModel>',
        'application/dicom+xml'), '\
<?xml version="1.0" ?>\n\
<NativeDicomModel>\n\
    <Value number="1">redact</Value>\n\
</NativeDicomModel>\n')
