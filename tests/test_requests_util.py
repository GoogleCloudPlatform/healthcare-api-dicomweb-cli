# -*- coding: utf-8 -*-
"""Requests utils tests
"""
import os
import unittest
import random
import pytest_check as check
import httpretty
from dcmweb import requests_util
from dcmweb import resources

URL = "https://dicom.com"

DELETE_CASES = {"/studies/1": 200,
                "/studies/1/series/1": 200,
                "/studies/1/series/1/instances/1": 200,
                "/studies/notExist": 404}
ADJUST_CASES = {"image/png": "multipart/related; type=\"image/png\"; ",
                "application/dicom; transfer-syntax=1.2.840.10008.1.2.1": "multipart/related; \
type=\"application/dicom\"; transfer-syntax=1.2.840.10008.1.2.1",
                "": "application/dicom; transfer-syntax=*",
                "application/dicom; transfer-syntax=*; something=else": None,
                "transfer-syntax=1.2.840.10008.1.2.1": None
                }


class RequestsUtilTests(unittest.TestCase):
    """class is needed to handle exceptions"""

    @httpretty.activate
    def test_requests_handling(self):
        """url should be validated"""
        httpretty.register_uri(
            httpretty.GET,
            URL + "/",
            body='body'
        )
        httpretty.register_uri(
            httpretty.GET,
            URL + "/not200",
            body='404',
            status=404
        )
        requests = requests_util.Requests(URL, None)
        assert requests.request("", "", {}).text == "body"
        with self.assertRaises(requests_util.NetworkError):
            print(requests.request("not200", "", {}))

    @httpretty.activate
    def test_delete(self):
        """files should be deleted correctly"""
        requests = requests_util.Requests(URL, None)
        for url, status in DELETE_CASES.items():
            httpretty.register_uri(
                httpretty.DELETE,
                URL + url,
                status=status
            )
            if status == 200:
                requests.delete_dicom(url)
            else:
                with self.assertRaises(requests_util.NetworkError):
                    requests.delete_dicom(url)

    def test_adjust_mime_type(self):
        """mime type should be adjusted"""
        for mime_type, mime_type_adjusted in ADJUST_CASES.items():
            if mime_type_adjusted:
                check.equal(requests_util.adjust_mime_type(
                    mime_type), mime_type_adjusted)
            else:
                with self.assertRaises(ValueError):
                    requests_util.adjust_mime_type(mime_type)


def test_url_builder():
    """should build correct urls"""
    requests = requests_util.Requests(URL, None)
    expected_url = URL + "/test?param=1"
    check.equal(requests.build_url("test", "param=1"), expected_url)
    check.equal(requests.build_url("test", "?param=1"), expected_url)
    check.equal(requests.build_url("/test", "?param=1"), expected_url)


@httpretty.activate
def test_auth():
    """header should be added"""
    authenticator = Authenticator()
    httpretty.register_uri(
        httpretty.GET,
        URL + "/",
        body=authenticator.request_callback
    )
    requests = requests_util.Requests(URL, authenticator)
    requests.request("", "", {})


class Authenticator:
    """Handles authenticattion"""

    def __init__(self):
        self.token = str(random.random())

    def apply_credentials(self, headers):
        """Adds token to request"""
        headers["Authorization"] = self.token
        return headers

    def request_callback(self, request, uri, response_headers):
        """checks if token same to generated one"""
        check.equal(request.headers.get("Authorization"), self.token)
        check.equal(uri, URL + "/")
        return [200, response_headers, ""]


@httpretty.activate
def test_upload():
    """file should be uploaded correctly"""
    requests = requests_util.Requests(URL, None)
    httpretty.register_uri(
        httpretty.POST,
        URL + "/studies",
        body=request_callback
    )
    assert requests.upload_dicom("./cloudBuild/dcms/1.dcm") == 8706


def request_callback(request, uri, response_headers):
    """checks post request"""
    content_type = request.headers.get('Content-Type')
    check.equal(content_type, 'application/dicom', 'expected application/dicom\
     but received Content-Type: {}'.format(content_type))
    check.equal(uri, URL + "/studies")
    return [200, response_headers, ""]


@httpretty.activate
def test_download_dicom():
    """should download correct file"""
    httpretty.register_uri(
        httpretty.GET,
        URL + "/studies/1/series/2/instances/3",
        body="3.dcm",
        adding_headers={
            'Content-Type': 'application/dicom'}
    )
    requests = requests_util.Requests(URL, None)
    requests.download_dicom("/studies/1/series/2/instances/3",
                            "./testData/1/2/", "3", None)
    assert os.path.isfile("./testData/1/2/3.dcm")
    file = open("./testData/1/2/3.dcm", 'r')
    data = file.read()
    assert data == "3.dcm"


@httpretty.activate
def test_download_path():
    """should download correct file by path"""
    httpretty.register_uri(
        httpretty.GET,
        URL + "/studies/1/series/2/instances/3",
        body="3.dcm",
        adding_headers={
            'Content-Type': 'application/dicom'}
    )
    requests = requests_util.Requests(URL, None)
    requests.download_dicom_by_ids(resources.ids_from_path(
        "studies/1/series/2/instances/3"), "./testData", None)
    assert os.path.isfile("./testData/1/2/3.dcm")
    file = open("./testData/1/2/3.dcm", 'r')
    data = file.read()
    assert data == "3.dcm"


@httpretty.activate
def test_download_instance_json():
    """should download correct file by json based dict"""
    httpretty.register_uri(
        httpretty.GET,
        URL + "/studies/3/series/4/instances/5",
        body="5.dcm",
        adding_headers={
            'Content-Type': 'application/dicom'}
    )
    requests = requests_util.Requests(URL, None)
    requests.download_dicom_by_ids(resources.ids_from_json(
        {resources.STUDY_TAG: {"Value": ["3"]}, resources.SERIES_TAG: {
            "Value": ["4"]}, resources.INSTANCE_TAG: {"Value": ["5"]}}), "./testData", None)
    assert os.path.isfile("./testData/1/2/3.dcm")
    file = open("./testData/3/4/5.dcm", 'r')
    data = file.read()
    assert data == "5.dcm"

@httpretty.activate
def test_download_dicom_by_ids():
    """should download correct file by json based dict"""
    httpretty.register_uri(
        httpretty.GET,
        URL + "/studies/1/series/2/instances/6",
        body="idsData",
        adding_headers={
            'Content-Type': 'application/dicom'}
    )
    requests = requests_util.Requests(URL, None)
    requests.download_dicom_by_ids({'study_id': '1', 'series_id': '2', 'instance_id': '6', },\
    "./testData", None)
    assert os.path.isfile("./testData/1/2/6.dcm")
    file = open("./testData/1/2/6.dcm", 'r')
    data = file.read()
    assert data == "idsData"


@httpretty.activate
def test_download_multipart():
    """should download correct file by json based dict"""
    mock_data = [b'1C\r\n--123 Content-Type:image/png\r\n4\r\ndata\r\n1C\r\n\
--123 Content-Type:image/png\r\n5\r\ndata2\r\n5\r\n--123\r\n0\r\n\r\n']
    httpretty.register_uri(
        httpretty.GET,
        URL + "/studies/6/series/7/instances/8",
        body=(l for l in mock_data),
        adding_headers={
            'Content-Type': 'multipart/related; type="image/png"; boundary=123;',
            'transfer-encoding': 'chunked'},
        streaming=True
    )
    requests = requests_util.Requests(URL, None)
    requests.download_dicom_by_ids(resources.ids_from_path(
        "studies/6/series/7/instances/8"), "./testData", "image/png")
    assert os.path.isfile("./testData/6/7/8_frame_1.png")
    assert os.path.isfile("./testData/6/7/8_frame_2.png")
    file = open("./testData/6/7/8_frame_2.png", 'r')
    data = file.read()
    assert data == 'data2'


def test_extension_by_headers():
    """should get correct extension"""
    check.equal(requests_util.extension_by_headers(
        'multipart/related; type="application/dicom"'), (".dcm"))
    check.equal(requests_util.extension_by_headers(
        'type="application/dicom"'), (".dcm"))
    check.equal(requests_util.extension_by_headers(
        'type="image/jpeg"'), (".jpg"))
    check.equal(requests_util.extension_by_headers(
        'multipart/related; type="image/png"'), (".png"))


@httpretty.activate
def test_multipart_reader():
    """should download correct file by json based dict"""
    mock_data = [b'1C\r\n--321 Content-Type:image/png\r\n4\r\ndata\r\n4\r\ndata\r\n1C\r\n\
--321 Content-Type:image/png\r\n5\r\ndata2\r\n5\r\n--321\r\n0\r\n\r\n']
    httpretty.register_uri(
        httpretty.GET,
        URL + "/studies/6/series/7/instances/8",
        body=(l for l in mock_data),
        adding_headers={
            'Content-Type': 'multipart/related; type="image/png"; boundary=321;',
            'transfer-encoding': 'chunked'},
        streaming=True
    )

    requests = requests_util.Requests(URL, None)
    response = requests.request("/studies/6/series/7/instances/8", "", {}, True)
    chunks = requests_util.MultipartChunksReader(
        response.iter_content(chunk_size=8192), bytes("--321", "utf-8"))
    chunks_expected = [(b'data', True), (b'data', False), (b'data2', True)]
    i = 0
    for chunk in chunks.read_chunks():
        assert chunk == chunks_expected[i]
        i += 1
