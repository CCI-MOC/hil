.. image:: https://travis-ci.org/CCI-MOC/hil.svg?branch=master
    :target: https://travis-ci.org/CCI-MOC/hil


HIL
===

HIL is a low-level tool for reserving physical machines and connecting
them via isolated networks. It does not prescribe a particular
method for imaging/managing said machines, allowing the user to use
any solution of their choosing.

We call this paradigm "hardware as a service" (HaaS); HIL is our
implementation of this idea.

HIL keeps track of available resources in a database, which a system
administrator must populate initially.

**This includes information such as:**

- What machines are available
- What network interfaces they have
- Where those NICs are connected (what port on what switch)

**From there, a regular user may:**

- Reserve physical machines
- Create isolated logical networks
- Create "headnodes," which are small virtual machines usable for
  management/provisioning purposes
- Connect network interfaces belonging to physical and/or headnodes to
  logical networks.
- Reboot their machines, view the serial consoles -- aditionaly such management
  features may exist in the future.

**A typical user workflow might look like:**

1. Reserve some machines.
#. Create a logical "provisioning" network.
#. Connect a NIC from each machine to the provisioning network. In particular,
   one could connect a NIC from which the machine will attempt to boot.
#. Create a headnode, and attach it to the provisioning network
#. Log in to the headnode, set up a PXE server, reboot the nodes, and deploy an
   operating system on them via the network.

Requirements
============

Required software/hardware for running a production HIL include:

* Network switches:

  * At least one switch from the Cisco Nexus 5xxx or Dell PowerConnect 55xx families
  * For environments including more than one switch, all VLANs must be trunked to all managed switches

* A single node that has the following:

  * A webserver capable of supporting the WSGI standard (Apache/mod_wsgi is the only one tested)
  * python 2.7, with the ability to install packages via pip
  * Access to:

    * The Internet or intranet (a way for users to connect to the HIL service)
    * The administrative telnet IP on the managed switches

  * Currently only CentOS and RHEL 7.x have been tested, though any node that otherwise meets these requirements should function.

* Database: a Postgres database server. Sqlite works but is not recommended for production.

For IPMI proxy functionality:

* Network access from the HIL service node to the IPMI interfaces of node under management
* Nodes that support IPMI v2+
* A recent version of ipmitool installed on the HIL service node

For headnode functionality:

* A recent Linux version for the HIL service node that has libvirt with KVM installed
* Some number of VM templates
* A trunk port connected between the switch and HIL service node that carries all VLANs accessible from HIL

Documentation
=============


* The full documentation is availalbe at `ReadTheDocs <http://hil.readthedocs.io/en/latest/>`_ in a beautiful and easy to navigate web interface.
* `The docs directory <docs/>`_ contains documentation in .rst and .md format
* `examples <examples/>`_ contains examples of config files, templates for creating headnode VM images and a script to register nodes with HaaS.


Of particular relevance to developers:

* `Developer guidelines <docs/developer-guidelines.md>`_
* `Specifications <specs/>`_

Please note that the documentation is a mix of Markdown and reStructured Text,
since the latter is preferred by the python and OpenStack communities and the
former was what was originally used.

References
----------

If you would like to learn more about HIL's design or cite it in a publication, please refer to:

    Jason Hennessey, Sahil Tikale, Ata Turk, Emine Ugur Kaynar, Chris Hill, Peter Desnoyers, and Orran Krieger. 2016. `HIL: Designing an Exokernel for the Data Center <https://open.bu.edu/handle/2144/19198>`_. In Proceedings of the Seventh ACM Symposium on Cloud Computing (SoCC '16). DOI: `10.1145/2987550.2987588 <https://dx.doi.org/10.1145/2987550.2987588>`_


Bibtex:

.. code:: bib

  @inproceedings{hil-designing-an-exokernel,
  author = {Hennessey, Jason and Tikale, Sahil and Turk, Ata and Kaynar, Emine Ugur and Hill, Chris and Desnoyers, Peter and Krieger, Orran},
  title = {HIL: Designing an Exokernel for the Data Center},
  booktitle = {Proceedings of the Seventh ACM Symposium on Cloud Computing},
  series = {SoCC '16},
  year = {2016},
  isbn = {978-1-4503-4525-5},
  location = {Santa Clara, CA, USA},
  pages = {155--168},
  numpages = {14},
  url = {https://doi.acm.org/10.1145/2987550.2987588},
  doi = {10.1145/2987550.2987588},
  acmid = {2987588},
  publisher = {ACM},
  address = {New York, NY, USA},
  keywords = {IaaS, PaaS, bare metal, cloud computing, datacenter management, exokernel},
  }

An early short paper on HIL (then called "Hardware as a Service/HaaS"):

    Jason Hennessey, Chris Hill, Ian Denhardt, Viggnesh Venugopal, George Silvis, Orran Krieger, and Peter Desnoyers, `Hardware as a service - enabling dynamic, user-level bare metal provisioning of pools of data center resources. <https://open.bu.edu/handle/2144/11221>`_ in 2014 IEEE High Performance Extreme Computing Conference, Waltham, MA, USA, 2014.

Other work that has involved HIL can be found on the Mass Open Cloud `papers page <https://massopen.cloud/publicationsandtalks/>`_.

Mass Open Cloud
===============

This project is part of the larger `Massachusetts Open Cloud
<https://massopen.cloud/>`_. For a description of the team and other
information, see
`<https://github.com/CCI-MOC/moc-public/blob/master/README.md>`_.
