Leasing scripts is used to free a node
from a specific project after a certain amount of time.

The procedure is as follows:
Cron job will call the leasing script in pre-defined time
intervals (e.g., every 30 seconds). Leasing script checks
node's status in the status file and updates the number
of times cron job has called the leasing script while the node
has been asigned to a project.
If this number of times passes the threshold, the node
will be freed from that project.
So, threshould * cron_job_interval = the time that the node
will be released after. For example, if threshold is 5 and intervals
are set to 1 minutes, then after 5*1 = 5 minutes, the node will
be released.

Tenants who need more time should ask time extension.
One can change the "assigned to a project" time for all nodes
(by chanigng threshold in config file) or for one node
(by changing the line in the status file related to the node.)

Script reads a config file from /etc/leasing.cfg
which includes the name of the nodes, time threshold,
admin user name and password, status file and endpoint
which specifies the ip address and port number which hil runs at.

status file includes each node's status, which node is in
which project, and which node is free or for how long the node
has been assigned to a project.

Note: this script does NOT support other auth backends
such as keystone.

*******************

Config file format (/etc/leasing.cfg): Read the comments in the config file.

******************

Status file format (e.g., var/lib/leasing):
node_name project_name cron_job_called_script_times
