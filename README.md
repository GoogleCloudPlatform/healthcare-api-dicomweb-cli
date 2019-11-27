# DICOMweb command line tool
DICOMweb command line tool is a command line utility for interacting with DICOMweb servers.

## Requirements

- python (3.5+)
- pip

## Installation

### Using GitHub:

```bash
pip install PLACEHOLDER_AWAITING_FIRST_RELEASE
```

NOTE: Getting errors due to not having Python3? See [instructions below](#running-on-machine-with-python2).

## Interface

### dcmweb [-m] \<host> \<store|retrieve|search|delete> [parameters]

* **-m**
\
 Whether to perform batch operations in parallel or sequentially, default is sequentially.

* **host**
\
 The full DICOMweb endpoint URL. E.g. `https://healthcare.googleapis.com/v1beta1/projects/<project_id>/locations/<location_id>/datasets/<dataset_id>/dicomStores/<dicom_store_id>/dicomWeb`

* **store**
\
 Stores one or more files by posting multiple StoreInstances requests. Requests will be sent in sequence or in parallel based on the -m flag.
 
 	* --masks \*string
	\
	Positional argument, contains list of file paths or masks to upload, mask support wildcard(\*) and cross directory boundaries wildcard(\*\*) char, 


* **retrieve**
\
 Retrieves one or more studies, series, instances, or frames from the server. Outputs the instances to the directory specified by the --output option.

	* --path string
	\
	Positional argument, can either be empty (indicates downloading of all studies) or specify a resource path (studies/<uid>[/series/<uid>[/instances/<uid>[/frames/<frame_num]]]) to download from the server

	* --type string
	\
	Controls what format to request the files in (defaults to application/dicom; transfer-syntax=*). The tool will use this as the part content type in the multipart accept header being sent to the server. 

	* --output string
	\
	Controls where to write the files to (defaults to current directory).
	The following folder structure will be created:
	\
		```
		- study_uid
			- series_uid
				- instance_uid[_frame_X].<ext>
		```



* **search**
\
Performs a search over studies, series, or instances and outputs the result to stdout, limited to 5000 items by default. You can specify limit/offset parameters to change this.

    * --path string
	\
	Positional argument, specifies a path (studies/[<uid>/series/[<uid>/instances/]]) to search on the server, default is "/studies"

    * --parameters string
	\
	QIDO search parameters formatted as URL query parameters.

* **delete**
\
 Deletes the given study, series, or instance from the server. Uses an un-standardized extension to the DICOMweb spec.

    * --path string
    \
	Positional argument, specifies a resource path (studies/<uid>[/series/<uid>[/instances/<uid>[/frames/<frame_num]]]) to delete from the server

## Examples

**search**

```bash
# will return json list of instances in dicomstore with date==1994.10.13
dcmweb $host search instances StudyDate=19941013 
```

```bash
# will return list of studies without any filter
dcmweb $host search 
```

Since search returns JSON data it can be redirected into parse tools like [jq](https://stedolan.github.io/jq/).

```bash
# will parse StudyUIDs/PatientNames for each study in search results
dcmweb $host search | jq '.[] | .["0020000D"].Value[0],.["00100010"].Value[0]'
```

Output of jq may be redirected as well:
```bash
# will parse StudyUIDs for each study in search results
# and count lines of jq output by wc
dcmweb $host search | jq '.[] | .["0020000D"].Value[0]' | wc -l
```
The list of DICOM tags can be found in this [page](https://dicom.innolitics.com/ciods/).

**store**

```bash
# will upload list of files generated from current folder by shell
dcmweb $host store ./* 
```

```bash
# will upload list of files generated from current folder by python
dcmweb $host store "./*" 
```

```bash
# will upload list of files generated from current folder recursively by python
dcmweb $host store "./**" 
```

```bash
# will upload list of files in parallel
dcmweb -m $host store "./**" 
```
**retrieve**

```bash
# will download all instances from dicomstore into current folder
dcmweb $host retrieve 
```

```bash
# will download all instances from dicomstore into current folder in parallel
dcmweb -m $host retrieve 
```

```bash
# will download all instances from dicomstore into ./data folder
dcmweb $host retrieve --output ./data 
```

```bash
# will download all instances from dicomstore into ./data folder as png images,
# in instance is multiframe, frames will be saved as separate files
dcmweb $host retrieve --output ./data --type "image/png" 
```

```bash
# will download all instances from study 1 into ./data folder
dcmweb $host retrieve studies/1 --output ./data 
```

**delete**

```bash
# will delete study 1
dcmweb $host delete studies/1
```

## Build

```bash
python ./setup.py sdist bdist_wheel 
```
## Run tests

```bash
pip install tox
tox
```

## Developing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Running on machine with Python2

This tool requires Python3 to be run which may cause issues for environments that
have Python2 installed and can't upgrade due to other dependencies. Here are 2 options
for getting the tool to work in this enviornment:

### Using pip local install

1.  Install python3 & python3-pip (e.g. `sudo apt install python3 python3-pip`)
1.  Download zip file from latest release from
    [GitHub](https://github.com/GoogleCloudPlatform/healthcare-api-dicomweb-cli/releases)
1.  Run `python3 -m pip install healthcare-api-dicomweb-cli-X.Y.zip --user`
1.  Run `export PATH=$PATH:"${HOME}/.local/bin"` -- this is where pip --user
    installs things to
1.  Then you should be able to run `dcmweb`

### Using virtualenv

1.  Install python3 & python3-venv (e.g. `sudo apt install python3 python3-venv`)
1.  Start a virtualenv `python3 -m venv py3-env && cd py3-env && source ./bin/activate`
1.  Download zip file from latest release from
    [GitHub](https://github.com/GoogleCloudPlatform/healthcare-api-dicomweb-cli/releases)
1.  Install within virtualenv`pip install healthcare-api-dicomweb-cli-X.Y.zip`
1.  Then you should be able to run `dcmweb`

## Apache License 2.0
Project License can be found [here](LICENSE).

