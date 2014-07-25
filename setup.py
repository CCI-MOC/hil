# Copyright 2013-2014 Massachusetts Open Cloud Contributors
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
from pip.req import parse_requirements

requirements = parse_requirements('requirements.txt')
requirements = map(lambda r : str(r.req), requirements)

setup(name='haas',
      version='1.0',
      url='https://github.com/CCI-MOC/moc-public',
      packages=find_packages(),
      scripts=['scripts/haas'],
      install_requires=requirements,
      )
