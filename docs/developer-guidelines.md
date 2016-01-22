# Overview

This document represents the developer policies and procedures for maintaining Hardware as a Service (HaaS).

Welcome! Overall, we follow the [github fork & pull
model](http://scottchacon.com/2011/08/31/github-flow.html), where users fork
the [main HaaS repository][repo], push changes to their personal fork and then
create a [Pull Request][pr](PR) to merge it back to the master branch of the
HaaS repository.

## Communicating

* IRC: The MOC team hangs out on #moc on [freenode](https://www.freenode.net/)
* IRL: The MOC group office is on the BU campus, at 3 Cummington Mall, Boston, MA room 451. Anyone interested in HaaS is welcome to drop in and work there.
* Email: HaaS developers should subscribe to haas-dev-list@bu.edu by sending a plain text email to majordomo@bu.edu with "subscribe haas-dev-list" in the body.

# Prior to a pull request

This short list summarizes what should be done prior to a pull request:

- [ ] If functionality could have architectural implications or controversial, have a discussion with the team. Ideally, prior to coding to save effort.
- [ ] Ensure any user, deployer or developer documentation is updated
- [ ] Testing:
  - [ ] Ensure existing tests pass.
  - [ ] Run deployment tests if code could affect switches
  - [ ] Implement any new tests.

## Get agreement

The HaaS effort appreciates all ideas and submissions. In the past, we've
discussed several alternatives to how things currently work (which we're trying
to get better about writing down), and it would be good to have agreement that
includes input from these past discussions as well as the wisdom of the
community. The best way to do this is to [file an
issue](https://github.com/CCI-MOC/haas/issues) on github, email
haas-dev-list@bu.edu or speak with one of the "core developers".

## Documentation

* [Documentation listing](../README.rst#documentation)

In HaaS, we primarily have 3 types of users: end-users (API/CLI users),
deployers (HaaS instance admins) and developers (you!). If your change affects
any of HaaS's extensive documentation, please be sure to update the
accompanying documentation.

While most end-user and developer documentation can be found in the documentation listing
(linked above), developer documentation may be found in the [docs
directory](./).

## Testing

* [Testing document](testing.md)

Testing helps to ensure the quality of the code base. Every pull request
submitted should first be tested to ensure that all existing tests pass. If
changes could affect state external to HaaS's DB (network switches and
headnodes), then deployment tests should also be run.

When introducing new functionality, new tests (both unit and more comprehensive)
should be added that provide adequate coverage.

If fixing a bug, a regression test should accompany the bug fix to ensure that
the bug does not return.

# Code reviews / pull requests

Once the checklist above has been met, issue a [pull request][pr] from your
personal fork to the [main HaaS repo][repo]. 

Labels are the way we communicate github pull request and issue status. They should be assigned in line with the *Suggestions* section
of [this wiki
page](https://github.com/CCI-MOC/haas/wiki/Issue-Tracker-Proposal#suggestions).

## Code review


## Friendliness

We want the MOC HaaS to be a pleasure to work with. Thus, while we want to
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
as they may otherwise your pending PR.

## Approval criteria

Pull Requests require at least 2 successful reviews, also known as "+1"'s, in
order to be merged, with at least 2 core developers being involved in some way:
either as a submitter or a reviewer.

The exception to this is documentation, where we are a little more lenient in
the interest of lowering the barrier to having better docs. For docs changes,
typically one +1 is sufficient.

Whomever provides the enabling +1 is responsible for clicking the merge button
on github. If you do not have commit writes, then please add your +1 to the PR
and ask one of the Core Developers to complete the merge.

## Labels

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

# Core developers

Core developers are the trusted gatekeepers of the HaaS codebase. They consist of:

* Jon Bell
* Ian Denhardt
* Jason Hennessey (PTL)
* George Silvis
* Sahil Tikale

Anyone who has had a few successful commits is invited to speak to the PTL
about being added as one.

[repo]: https://github.com/CCI-MOC/haas
[pr]: https://help.github.com/articles/using-pull-requests/

