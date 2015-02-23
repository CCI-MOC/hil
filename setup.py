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

setup(name='moc-rest',
      version='0.1',
      url='https://github.com/CCI-MOC/moc-rest',
      packages=find_packages(),
      install_requires=['Werkzeug==0.9.4',
                        'pytest==2.6.2',
                        'pytest-cov==1.8.0',
                        'schema==0.3.1',
                        ])
