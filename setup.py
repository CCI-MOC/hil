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

setup(name='haas',
      version='0.1',
      url='https://github.com/CCI-MOC/haas',
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
                        ])
