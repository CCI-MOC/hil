# REST API Mapping

This document describes how the api described in [apidesc.md] is
implemented in terms of http.

## General Principles

* Authentication (for now) will happen via http basic auth. We therefore
  require https.
* Some objects have fields which may contain characters not allowed in
  URLs (or which have special meaning). When these fields are
  transmitted in a URL (perhaps in the query string), they must be URL encoded.
* Guidelines for URLs of objects:
  * URLs should be namespaced by the type of object, e.g.
    `network/my_net`.
  * With the exception of users and admin-only objects, all objects have
    URLs which are namespaced by a group. For example, a headnode
    belonging to the group `acme_corp` might have the URL:

        https://<haas_endpoint>/acme_corp/headnode/anvil_mgmt

  * Objects which are logically subordinate to other objects should be
    namespaced by those objects. For example:

        https://<haas_endpoint>/acme_corp/headnode/anvil_mgmt/hnic/ipmi

    Could be the name of a nic belonging to the headnode in the previous
    example.

* To create an object, the client should use an HTTP PUT request on the
  object's URL.

* For any request, any needed information not provided in the url should
  be supplied as a json object in the body of the request.

* All other object-mutating operations happen via POST requests on the
  primary object's URL. For example, a command `foo_connect_bar` would
  take the form of a POST request on the URL for the relevant `foo`
  object.

* Query operations happen via a GET request.
