# -*- coding: utf-8 -*-
"""Wrapper for command line calls of dcmweb
"""
import sys
import fire
from . import dcmweb

CUSTOM_HELP = "DICOMweb command line tool is a command line utility for \
interacting with DICOMweb servers.\n\
\n\
dcmweb [-m] <host> <store|retrieve|search|delete> [parameters]\n\
\n\
    -m \n\
Whether to perform batch operations in parallel or sequentially, default is in sequentially\n\
\n\
    host  \n\
The full DICOMweb endpoint URL. E.g. `https://healthcare.googleapis.com/v1beta1/projects/<project_id>/\
locations/<location_id>/datasets/<dataset_id>/dicomStores/<dicom_store_id>/dicomWeb`\n\
\n\
    store  \n\
Stores one or more files by posting multiple StoreInstances requests. Requests will be sent in sequence or in parallel based on the -m flag.\n\
 --masks  string\n\
Positional argument, contains list of file paths or masks to upload, mask support wildcard(*) and cross directory boundaries wildcard(**) char,\n\
\n\
    retrieve  \n\
Retrieves one or more studies, series, instances or frames from the server. Outputs the instances to the directory specified by the --output option.\n\
 --path string\n\
Positional argument, can either be empty (indicates downloading of all studies) or specify a resource path (studies/<uid>[/series/<uid>\n\
[/instances/<uid>[/frames/<frame_num]]]) to download from the server\n\
 --type string\n\
Controls what format to request the files in (defaults to application/dicom; transfer-syntax= ). The tool will use this as the part content\n\
type in the multipart accept header being sent to the server. \n\
 --output string\n\
Controls where to write the files to (defaults to current directory).\
The following folder structure will be created:\n\
- study_uid\n\
  - series_uid\n\
    - instance_uid[_frame_X].<ext>\n\
\n\
    search\n\
Performs a search over studies, series or instances and outputs the result to stdout, limited to 5000 items by default. You can specify limit/offset parameters to change this.\n\
 --path string\n\
Positional argument, specifies a path (studies/[<uid>/series/[<uid>/instances/]]) to search on the server, default is \"/studies\"\n\
 --parameters string\n\
QIDO search parameters formatted as URL query parameters."


def host_wrapper(host, m):  # pylint: disable=invalid-name; disabled because m is also configuration for Fire library and it have to be one letter
    """host - url for dicomWeb
    m - whether to perform batch operations in parallel
    or sequentially, default is in parallel"""
    return dcmweb.Dcmweb(host, m == 1, dcmweb.GoogleAuthenticator())


def main():
    """Main fuction to call dcmweb"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print(CUSTOM_HELP)
            sys.exit(0)
        if sys.argv[1] == '-m':
            sys.argv.insert(2, "1")
        else:
            sys.argv.insert(1, "-m")
            sys.argv.insert(2, "0")
    fire.Fire(host_wrapper)
