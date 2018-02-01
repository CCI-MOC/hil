### HIL Python Client API
#### How to get started?
```
import requests
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
