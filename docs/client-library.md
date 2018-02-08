# HIL Client Library

## Description
The HIL API Client Library for Python is designed for Python client-application developers. It offers simple access to HIL APIs.

## How to Install HIL Modules?
```
$ pip install git+https://github.com/cci-moc/hil
```

## How to Get Started?
```
import os
from hil.client.client import Client, RequestsHTTPClient

ep = os.environ.get('HIL_ENDPOINT')
basic_username = os.getenv('HIL_USERNAME')
basic_password = os.getenv('HIL_PASSWORD')

http_client = RequestsHTTPClient()
http_client.auth = (basic_username, basic_password)
C = Client(ep, http_client)
print C.project.create("test-project")

```

## More Examples.
[leasing script](https://github.com/CCI-MOC/hil/blob/master/examples/leasing/node_release_script.py)
