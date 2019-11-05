# -*- coding: utf-8 -*-
"""Retrieve method tests
"""
import os
import shutil
import unittest
import httpretty
import pytest_check as check
from dcmweb import dcmweb

URL = "https://dicom.com/"

RETRIEVE_CASES = {"": ["1/2/3.dcm", "1/2/4.dcm", "3/2/1.dcm"],
                  "studies/1": ["1/2/3.dcm"],
                  "studies/1/series/2/instances/3": ["1/2/3.dcm"],
                  "studies/3/series/2/instances/1": ["3/2/1.dcm"],
                  "studies/1/series/2/instances/3/frames/1": ["1/2/3_frame_1.png"]}


class RetrieveTests(unittest.TestCase):
    """class to handle http mock and retrieve tests"""

    def setUp(self):
        httpretty.enable()
        httpretty.register_uri(
            httpretty.GET,
            generate_page_url(URL, 0),
            body=generate_array_response(
                [generate_response(1, 2, 3), generate_response(1, 2, 4)]),
            match_querystring=True
        )
        httpretty.register_uri(
            httpretty.GET,
            generate_page_url(URL, 5000),
            body=generate_array_response([generate_response(3, 2, 1)]),
            match_querystring=True
        )
        httpretty.register_uri(
            httpretty.GET,
            generate_page_url(URL, 10000),
            body="[]",
            match_querystring=True
        )
        httpretty.register_uri(
            httpretty.GET,
            generate_page_url(URL+"studies/1/", 0),
            body=generate_array_response([generate_response(1, 2, 3)]),
            match_querystring=True
        )
        httpretty.register_uri(
            httpretty.GET,
            generate_page_url(URL+"studies/1/", 5000),
            body="[]",
            match_querystring=True
        )
        httpretty.register_uri(
            httpretty.GET,
            URL+"studies/1/series/2/instances/3",
            body="3.dcm",
            adding_headers={
                'Content-Type': 'application/dicom'},
        )
        httpretty.register_uri(
            httpretty.GET,
            URL+"studies/1/series/2/instances/4",
            body="4.dcm",
            adding_headers={
                'Content-Type': 'application/dicom'},
        )
        httpretty.register_uri(
            httpretty.GET,
            URL+"studies/3/series/2/instances/1",
            body="1.dcm",
            adding_headers={
                'Content-Type': 'application/dicom'},
        )

        mock_data = [
            b'1C\r\n--456 Content-Type:image/png\r\n4\r\ndata\r\n5\r\n--456\r\n0\r\n\r\n']
        httpretty.register_uri(
            httpretty.GET,
            URL+"studies/1/series/2/instances/3/frames/1",
            body=(l for l in mock_data),
            adding_headers={
                'Content-Type': 'multipart/related; type="image/png"; boundary=456;',
                'transfer-encoding': 'chunked'},
            streaming=True
        )

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def test_retrieve(self):  # pylint: disable=no-self-use; method in class for cleaner look by setup method
        """should get all avalible files and single one"""
        output = "./testData/"
        for multithreading in (True, False):
            dcmweb_cli = dcmweb.Dcmweb(
                URL, multithreading, None)
            for path, files in RETRIEVE_CASES.items():
                dcmweb_cli.retrieve(path, output)
                for file in files:
                    file_path = output + file
                    file_exists = os.path.isfile(file_path)
                    check.is_true(file_exists, "can't find file {} in {} mode after retrieving {}"\
                        .format(file_path, "parallel" if multithreading else "sequential", path))
                    if file_exists:
                        os.remove(file_path)
                shutil.rmtree(output)


def generate_response(study_id, series_id, instance_id):
    """generates json string for instance"""
    return '{"00080018":{"vr":"UI","Value":["'+str(instance_id)+'"]},\
    "0020000D":{"vr":"UI","Value":["'+str(study_id)+'"]},\
    "0020000E":{"vr":"UI","Value":["'+str(series_id)+'"]}}'

def generate_array_response(responses):
    """generates json string for list of instances"""
    return "[" + ",".join(responses) + "]"

def generate_page_url(base, offset):
    """generates url"""
    return base + "instances?includefield=0020000D&\
includefield=0020000E&limit=5000&offset={}".format(offset)
