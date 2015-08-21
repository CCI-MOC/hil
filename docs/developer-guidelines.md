# Overview

This document represents the developer policies and procedures for maintaining Hardware as a Service (HaaS).

Overall, we follow the [github
fork & pull model](http://scottchacon.com/2011/08/31/github-flow.html), where users fork
the [main HaaS repository][repo], push changes to
their personal fork and then create a [Pull Request][pr](PR) to merge it back to the
master branch of the HaaS repository. 


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
issue](https://github.com/CCI-MOC/haas/issues) on github.

## Documentation

* [Documentation listing](../README.rst#documentation)

In HaaS, we primarily have 3 types of users: end-users (API/CLI users),
deployers (HaaS instance admins) and developers (you!). If your change affects
any of HaaS's extensive documentation, please be sure to update the
accompanying documentation.

While most end-user and deployer documentation can be found in the README
(linked above), developer documentation may be found in the [docs
directory](./).

## Testing

* [Testing document](testing.md)

Testing helps to ensure the quality of the code base. Every pull request
submitted should first be tested to ensure that all existing tests pass. If
changes could affect state external to HaaS's DB (network switches and
headnodes), then deployment tests should also be run.

When introducing new functionality, new tests (both unit and more comprhensive)
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

As a practical matter, especially when it comes to detailed suggestions for 
ubmitting the code as a PR against the new contributor's forked
repo.


## Approval criteria

In every PR, at least 2 *core reviewers* must be involved in some way: either as a submitter or a reviewer.


[repo]: https://github.com/CCI-MOC/haas
[pr]: https://help.github.com/articles/using-pull-requests/
