# Developer Guidelines

This document represents the developer policies and procedures for maintaining
Hardware as a Service (HIL), including the accepted [coding style](#Coding-style).

## Getting started

If you are new to HIL and would like to jump in, then welcome!

Contributions can come in many forms: installing hil and using it in your
environment (and giving us feedback), improving the testing, squashing bugs and
introducing new functionality.

If you are interested in any of this, a good place to start is by reading the
documentation (linked from the [Readme](./README.html)).

If you're looking to code, there are a few ways to help:
* Improving the HIL documentation
* Better testing
* Reviewing [Pull Requests](https://github.com/CCI-MOC/hil/pulls)
* Taking a github issue marked with the [easy label](https://github.com/CCI-MOC/hil/labels/easy). (Talk to one of the core team members to have it assigned to you officially!)
* Taking on a github issue that is part of one of the next [milestones in github](https://github.com/CCI-MOC/hil/milestones?state=open)

Please fill and sign the [Individual Contributor License Agreement](https://massopen.cloud/blog/individual-contributor-license-agreement/) prior to commiting any code.

## Communicating

* IRC: The MOC team hangs out on #moc on [freenode](https://www.freenode.net/)
* IRL (In Real Life): The MOC group office is on the BU campus, at 3 Cummington Mall, Boston, MA room 451. Anyone interested in HIL is welcome to drop in and work there.
* Email: HIL developers or anyone else wishing to stay up to date should
subscribe to hil-dev-list@bu.edu by sending a plain text email to
majordomo@bu.edu with "subscribe hil-dev-list" in the body.

## Coding style/conventions

By default, HIL (like many other python projects) uses
[PEP8](https://www.python.org/dev/peps/pep-0008/) as its naming guide, and
[PEP257](https://www.python.org/dev/peps/pep-0257/) for documentation.
Departures are acceptable when called for, but should be discussed first.

## REST API calls - @rest\_call

Any functionality that is intended to be externally visible (ie -
available through the REST API) will need to be exposed by decorating a
function with the `@rest_call` decorator, [available in
rest.py](https://github.com/CCI-MOC/hil/blob/master/hil/rest.py).  This tells the framework the URL path and
HTTP method which should be mapped to that function, and also specifies
how the arguments should be verified.

Please [see the documentation there](rest_api.html) for additional
information on the specifics, as well as [api.py]( https://github.com/CCI-MOC/hil/blob/master/hil/rest.py) for a number
of examples. Of special note is that every externally-visible function must
supply a `Schema` which explicitly specifies the method for verifying all URL
and body arguments. In HIL, all body arguments are required to be JSON.

## Often-used code
In certain cases, one will encounter heavily repeated code that gets run once per API call such as this:

```python
db = local.db
```

In these cases, it is preferred to keep a reference in "local", and use it directly. For example, instead of:
```python
db = local.db
db.delete(...)
```
one should prefer:
```python
local.db.delete(...)
```

## Submitting code / Pull Requests

Overall, HIL follows the [github fork & pull
model](http://scottchacon.com/2011/08/31/github-flow.html) to integrate
contributions, where users fork the [main HIL repository][repo], push changes
to their personal fork and then create a [Pull Request][pr](PR) to merge it
into the master branch of the HIL repository.

### Prior to the pull request
This summarizes what should be done prior to a pull request:

- [ ] If functionality could have architectural implications or controversial, have a discussion with the team. Ideally, prior to coding to save effort.
- [ ] Ensure any user, deployer or developer documentation is updated.
- [ ] If a change affects an external API, be sure to update docs/rest\_api.md.
- [ ] Testing:
  - [ ] Ensure tests pass after making your changes by running `py.test tests/unit tests/stress.py` from the top-level hil directory. Parallel testing can be used on multi-core systems by running `py.test tests/unit tests/stress.py -n auto`
  - [ ] Add unit tests in the corresponding file and create one if none are present.
  - [ ] If practical, bug fixes should have an reproducing test to ensure that the bug does not come back.
  - [ ] Run deployment tests if code could affect switches

#### Get agreement

The HIL project appreciates all ideas and submissions. In the past, we've
discussed several alternatives to how things currently work (which we're trying
to get better about writing down), and it would be good to have agreement that
includes input from these past discussions as well as the wisdom of the
community. The best way to do this is to [file an
issue](https://github.com/CCI-MOC/hil/issues) on github, email
hil-dev-list@bu.edu or speak with one of the core developers directly.

#### Documentation

* [Documentation listing](/README.html#documentation)

In HIL, we primarily have 3 types of users: end-users (API/CLI users),
deployers (HIL instance admins) and developers (you!). If your change affects
any of HIL's extensive documentation, please be sure to update the
accompanying documentation. For example, if an API call signature is changed or
added, please update [docs/rest_api.md](https://github.com/CCI-MOC/hil/blob/master/docs/rest_api.md).

While most end-user and developer documentation can be found in the documentation listing
(linked above), developer documentation may be found in the [docs
directory](https://github.com/CCI-MOC/hil/blob/master/docs/).

#### Testing

* [Testing document](testing.html)

Testing helps to ensure the quality of the code base. Every pull request
submitted should first be tested to ensure that all existing tests pass. If
changes could affect state external to HIL's DB (network switches and
headnodes), then deployment tests should also be run.

When introducing new functionality, new tests (both unit and more comprehensive)
should be added that provide adequate coverage.

If fixing a bug, a regression test should accompany the bug fix to ensure that
the bug does not return.

### Pull Requests

Once the checklist above has been met, issue a [pull request][pr] from your
personal fork to the [main HIL repo][repo].

Labels are the way we communicate github pull request and issue status. They should be assigned in line with the *Suggestions* section
of [this wiki
page](https://github.com/CCI-MOC/hil/wiki/Issue-Tracker-Proposal#suggestions).

### Code review

Code reviews help increase code quality by finding:
* mistakes that can oftentimes be overlooked by a single developer
* improving readability
* helping reviewers to learn about different areas of the code

Reviewers are the final guardians for good code quality. If you see a piece of
complex code, that is probably where you want to spend a lot of your review
time. Remember the 80/20 rule (80% of the bugs come from 20% of the code).

### Friendliness

We want the MOC HIL to be a pleasure to work with. Thus, while we want to
ensure a high level of code quality, we don't want new project contributors to
get overwhelmed. This should be kept in mind while conducting a review.  In
some cases, such as missing tests, it may help a new contributor for an
experienced reviewer to work closely or even write the initial tests
themselves.

As a practical matter, if feedback is lengthy and would take a longer time to
write up than simply to do, it can be considered a courtesy to check out the
submitter's branch, make the changes yourself, then submit a Pull Request
directly to the submitter's branch. This is especially helpful for
documentation PRs. When doing so, it can help to notify the submitter directly
as they may otherwise miss your pending PR (they likely won't be expecting it).

### Approval criteria

Pull Requests require at least 2 successful reviews, also known as "+1"'s, in
order to be merged, with at least 2 core developers being involved in some way:
either as a submitter or a reviewer.

The exception to this is documentation, where we are a little more lenient in
the interest of lowering the barrier to having better docs. For docs changes,
typically one +1 is sufficient.

Whomever provides the enabling +1 is responsible for clicking the merge button
on github. If you do not have commit access, then please add your +1 to the PR
and ask one of the Core Developers to complete the merge.

### Labels

Github labels are used to indicate the status of a Pull Request. Those that are relevant to PRs include:

* Easy (if the submitter or someone else thinks this would be good for someone new to the code base)
* Waiting on reviewer
* Waiting on submitter
* Waiting on other change
* Waiting on deployment tests
* Waiting on +2
* Do not merge yet

After updating a PR, it is good to apply/unapply labels as appropriate so that
it's easy for others to quickly scan the list of outstanding requests and
figure out which are in need of help.

## Core developers

Core developers are the trusted gatekeepers of the HIL codebase. They consist of:

* Jon Bell
* Ian Denhardt
* Jason Hennessey (PTL)
* Kyle Hogan
* Kristi Nikolla
* George Silvis
* Sahil Tikale

Anyone who has had a few successful commits is invited to speak to the PTL
(Project Team Lead) about being added as one.

[repo]: https://github.com/CCI-MOC/hil
[pr]: https://help.github.com/articles/using-pull-requests/
