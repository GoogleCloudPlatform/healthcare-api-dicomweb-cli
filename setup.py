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
        'console_scripts': ['dcmweb=dcmweb.command_line:main'],
    },

    url="https://github.com/GoogleCloudPlatform/healthcare-api-dicomweb-cli",

    packages=setuptools.find_packages(),

    install_requires=[
        'fire',
        'google.auth',
        'requests',
        'validators',
        'requests_toolbelt'
    ],

    classifiers=[

        "Programming Language :: Python :: 3",

        "License :: OSI Approved :: Apache Software License",

        "Operating System :: OS Independent",

    ],

    python_requires='>=3.5',

)
