# Logging

## Overview

HIL supports basic logging of the API calls received in the below format,
recording the user who issued the API call (or guest if the user was
unauthenticated) and the time. Log files are rotated daily.

```
2016-03-31 14:55:07,961 - hil.rest - INFO - (guest) - API call: list_projects()
```

## Setup
Logging can be configured with the following options in `hil.cfg`.

```
[general]
log_level = DEBUG
log_dir = /var/log/hil
```

`log_dir` specifies the directory where the log files will be stored.
The HIL user must have write permissions to this directory.
If the option is omitted logging to files is disabled.

`log_level` specifies the logging level to record. Valid options are:
`CRITICAL`, `DEBUG`, `ERROR`, `FATAL`, `INFO`, `WARN`, `WARNING`.
The default value is `WARNING`, but an option of `INFO` is recommended
for an API log (A log level of `INFO` is set for API calls).

For more information on logging visit the
[python 2 documentation](https://docs.python.org/2/howto/logging.html#when-to-use-logging).