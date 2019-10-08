# -*- coding: utf-8 -*-
"""Search method tests
"""
import httpretty
from dcmweb import dcmweb

@httpretty.activate
def test_search():
    """request shuld use limit from search"""
    dcmweb_cli = dcmweb.Dcmweb("https://dicom.com/", 0, None)
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/study/123?limit=1",
        body='[{"single": "response1"}]\n',
        match_querystring=True
    )
    assert dcmweb_cli.search("study/123", "limit=1") == "[{\"single\": \"response1\"}]\n"
    assert dcmweb_cli.search("study/123", "?limit=1") == "[{\"single\": \"response1\"}]\n"
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/study/123?limit=5000",
        body='[{"single": "response2"}]\n',
        match_querystring=True
    )
    assert dcmweb_cli.search("study/123", "") == "[{\"single\": \"response2\"}]\n"
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/studies?limit=5000",
        body='[{"single": "response3"}]\n',
        match_querystring=True
    )
    assert dcmweb_cli.search() == "[{\"single\": \"response3\"}]\n"
