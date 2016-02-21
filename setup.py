# Copyright 2013-2015 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

from setuptools import setup, find_packages
from os.path import dirname, join
readme_file = 'README.rst'

def _get_readme():
    with open(join(dirname(__file__), readme_file)) as f:
        return f.read()

setup(name='haas',
      version='0.2rc2',
      maintainer='Developers of the HaaS Project at MOC',
      maintainer_email='haas-dev-list@bu.edu',
      url='https://github.com/CCI-MOC/haas',
      description='A bare-metal isolation service that automates allocation and management ' \
                  'of non-virtualized compute resources across mutually untrusting ' \
                  'and incompatible provisioning systems.',
      long_description=_get_readme(),
      license='Apache 2.0',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'Intended Audience :: System Administrators', 
                   'Intended Audience :: Science/Research', 
                   'Topic :: System :: Cloud :: Installation/Setup',
                   'Topic :: System :: Systems Administration :: Clustering :: Utilities ',
                   'License :: OSI Approved :: Apache Software License, version 2.0',
                   'Environment :: Console',
                   'Environment :: Web Environment',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                  ],
      keywords='cloud bare-metal setuptools data-center isolation',

      packages=find_packages(),
      scripts=['scripts/haas', 'scripts/create_bridges'],
      install_requires=['SQLAlchemy==0.9.7',
                        'Werkzeug==0.9.4',
                        'schema==0.3.1',
                        'importlib==1.0.3',
                        'passlib==1.6.2',
                        'pexpect==3.3',
                        'requests==2.4.1',
                        'pytest==2.6.2',
                        'pytest-cov==1.8.0',
                        'pytest-xdist',
                        ])
