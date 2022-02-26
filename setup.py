# ! important
# see https://stackoverflow.com/a/27868004/1497139
from setuptools import setup
from collections import OrderedDict

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pylodstorage',
    version='0.1.12',

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
    description='python List of Dict (Table) Storage library',
    install_requires=[
          'SPARQLWrapper',
          'PyYAML',
          'pandas',
          'jsonpickle',
          'tabulate',
          'pylatexenc~=2.10'
    ],
    classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9'
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
