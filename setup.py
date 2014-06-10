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
