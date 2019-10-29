# -*- coding: utf-8 -*-
"""Search method tests
"""
import json
import httpretty
from dcmweb import dcmweb
INDENT = dcmweb.INDENT
SORT_KEYS = dcmweb.SORT_KEYS


@httpretty.activate
def test_search():
    """request shuld use limit from search"""
    dcmweb_cli = dcmweb.Dcmweb("https://dicom.com/", False, None)
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/study/123?limit=1",
        body='[{"single": "response1"}]\n',
        match_querystring=True
    )
    response1 = [{"single": "response1"}]
    assert dcmweb_cli.search("study/123", "limit=1") == json.dumps(
        response1, indent=INDENT, sort_keys=SORT_KEYS)
    assert dcmweb_cli.search("study/123", "?limit=1") == json.dumps(
        response1, indent=INDENT, sort_keys=SORT_KEYS)
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/study/123?limit=5000",
        body='[{"single": "response2"}]\n',
        match_querystring=True
    )
    response2 = [{"single": "response2"}]
    assert dcmweb_cli.search("study/123", "") == json.dumps(
        response2, indent=INDENT, sort_keys=SORT_KEYS)
    httpretty.register_uri(
        httpretty.GET,
        "https://dicom.com/studies?limit=5000",
        body='[{"single": "response3"}]\n',
        match_querystring=True
    )
    response3 = [{"single": "response3"}]
    assert dcmweb_cli.search() == json.dumps(
        response3, indent=INDENT, sort_keys=SORT_KEYS)
