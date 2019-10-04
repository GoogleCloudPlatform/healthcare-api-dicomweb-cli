import setuptools

with open("README.md", "r") as fh:

  long_description = fh.read()

setuptools.setup(

    name='dcmweb',

    version='0.0.1',

    author="Google",

    author_email="dzelemba@google.com",

    description="A command line utility for interacting with DICOMweb servers.",

    long_description=long_description,

    long_description_content_type="text/markdown",

    entry_points={
        'console_scripts': ['dcmweb=dcmweb.place_holder:main'],
    },

    url="https://github.com/GoogleCloudPlatform/healthcare-api-dicomweb-cli",

    packages=setuptools.find_packages(),

    classifiers=[

        "Programming Language :: Python :: 3",

        "License :: Apache License 2.0",

        "Operating System :: OS Independent",

    ],

    python_requires='>=3.6',

)
