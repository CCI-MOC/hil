
from setuptools import setup, find_packages
setup(name='haas',
      version='1.0',
      url='https://github.com/CCI-MOC/moc-public',
      packages=find_packages(),
      scripts=['haas_init.py', 'haas_restful.py', 'haas_shell.py'],
      install_requires=[
          'flask',
          'sqlalchemy',
          'Flask-HTTPAuth',
          'tabulate',
      ],
      )
