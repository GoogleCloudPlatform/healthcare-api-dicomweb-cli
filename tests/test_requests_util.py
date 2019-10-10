# -*- coding: utf-8 -*-
"""Requests utils tests
"""
import unittest
import random
import httpretty
from dcmweb import requests_util

URL = "https://dicom.com"


class RequestsUtilTests(unittest.TestCase):
    """class is needed to handle exceptions"""
    def test_url_validation(self):
        """url should be validated"""
        with self.assertRaises(ValueError):
            requests_util.validate_host_str("invalid url")
        assert requests_util.validate_host_str(
            "https://valid.url") == "https://valid.url/"

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


def test_url_builder():
    """should build correct urls"""
    requests = requests_util.Requests(URL, None)
    expected_url = URL + "/test?param=1"
    assert requests.build_url("test", "param=1") == expected_url
    assert requests.build_url("test", "?param=1") == expected_url
    assert requests.build_url("/test", "?param=1") == expected_url

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
        assert request.headers.get("Authorization") == self.token
        assert uri == URL + "/"
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
    assert requests.upload_dicom("./tests/test_requests_util.py") == 200


def request_callback(request, uri, response_headers):
    """checks post request"""
    content_type = request.headers.get('Content-Type')
    assert content_type == 'application/dicom', 'expected application/dicom\
     but received Content-Type: {}'.format(content_type)
    assert uri == URL + "/studies"
    return [200, response_headers, ""]
