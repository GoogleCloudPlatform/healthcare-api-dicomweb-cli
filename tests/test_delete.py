# -*- coding: utf-8 -*-
"""Delete method tests
"""
import json
import random
import httpretty
from dcmweb import dcmweb


@httpretty.activate
def test_delete():
    """delete request should be performed in old and new api"""
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/v1/dicomWeb/studies?limit=1",
        match_querystring=True
    )
    dcmweb_cli = dcmweb.Dcmweb("https://dicom.com/v1/dicomWeb/", False, None)
    empty_response = DeleteResponse('{}')

    httpretty.register_uri(
        httpretty.DELETE,
        "https://dicom.com/v1/dicomWeb/studies/1",
        status=200,
        match_querystring=True,
        body=empty_response.request_callback
    )
    dcmweb_cli.delete("studies/1")

    assert empty_response.requested

    operation_response = DeleteResponse('{"name":"/operation/1"}')
    operation_progress = OperationProgress()

    httpretty.register_uri(
        httpretty.DELETE,
        "https://dicom.com/v1/dicomWeb/studies/2",
        status=200,
        match_querystring=True,
        body=operation_response.request_callback
    )

    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/v1/operation/1",
        status=200,
        match_querystring=True,
        body=operation_progress.request_callback
    )

    dcmweb_cli.delete("studies/2")

    assert operation_progress.requests < 1
    assert operation_response.requested

    operation_response = DeleteResponse('{"name":"/operation/2"}')
    httpretty.register_uri(
        httpretty.DELETE,
        "https://dicom.com/v1/dicomWeb/studies/3",
        status=200,
        match_querystring=True,
        body=operation_response.request_callback
    )

    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/v1/operation/2",
        status=404,
        match_querystring=True,
    )

    assert dcmweb_cli.delete("studies/3") == "/operation/2"


class OperationProgress: # pylint: disable=too-few-public-methods; disabled because this is simple class for request callback
    """Counts random amount of requests"""

    def __init__(self):
        self.requests = random.randint(1, 5)

    def request_callback(self, request, uri, response_headers): # pylint: disable=unused-argument
        """Counts requests and returns json based on it"""
        self.requests -= 1
        resp_body = json.dumps({})
        if self.requests < 1 :
          resp_body = json.dumps({"done": True})
        return [200, response_headers, resp_body]

class DeleteResponse: # pylint: disable=too-few-public-methods; disabled because this is simple class for request callback
    """Returns body and keep flag"""

    def __init__(self, data):
        self.data = data
        self.requested = False

    def request_callback(self, request, uri, response_headers): # pylint: disable=unused-argument
        """Returns body and sets flag"""
        self.requested = True
        return [200, response_headers, self.data]
