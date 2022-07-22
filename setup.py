# ! important
# see https://stackoverflow.com/a/27868004/1497139
from setuptools import setup
from collections import OrderedDict
from lodstorage.version import Version
import pathlib

# where is this setup file?
here = pathlib.Path(__file__).parent.resolve()
# get thre requirements
requirements = (here / 'requirements.txt').read_text(encoding='utf-8').split("\n")
# and the README content
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name=Version.name,
    version=Version.version,
    description=Version.description,
    packages=['lodstorage','sampledata'],
    package_data={
          'sampledata': ['*.yaml'],
    },
    author='Wolfgang Fahl',
    author_email='wf@bitplan.com',
    maintainer='Wolfgang Fahl',
    url='https://github.com/WolfgangFahl/pyLodStorage',
    project_urls=OrderedDict(
        (
            ("Documentation", "http://wiki.bitplan.com/index.php/PyLoDStorage"),
            ("Code", "https://github.com/WolfgangFahl/pyLoDStorage/blob/master/lodstorage/sql.py"),
            ("Issue tracker", "https://github.com/WolfgangFahl/pyLodStorage/issues"),
        )
    ),
    license='Apache License',
   
    install_requires=requirements,
    classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10'
    ],
    entry_points={
      'console_scripts': [
        'sparqlquery = lodstorage.querymain:mainSPARQL',
        'sqlquery=lodstorage.querymain:mainSQL',
        'lodquery=lodstorage.querymain:main'
      ],
    },
    long_description=long_description,
    long_description_content_type='text/markdown'
)
