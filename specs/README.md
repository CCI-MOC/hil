# Overview

This directory contains specifications for different aspects/features of HIL.

The idea is that if a feature could be controversial or require significant
effort, a specification gives the HIL team a place to come to consensus on the
design before significant effort is expended. A spec also documents the feature
and rationale for future developers/users.

A spec does not have to be lengthy: Try to capture enough info that people can
make an informed decision.

# When not needed

- Bug fixes/minor features do not require a spec, and should be submitted
  directly as a Pull Request (PR).

- If there is extensive discussion/debate in an issue/PR that could suffice.
  In that case, please be sure to write `Implements #<ISSUE_NUM>` or
  `Implements #<PR_NUM>` in your first commit message or PR description to
  allow the two to be correlated.

If you are wondering whether your effort requires a spec, please ask one of the
core team members.

# Procedure

To create a spec:
1. Create a new file in this directory using the template below.
2. Submit a Pull Request with that change.
3. When/if the spec is accepted, be sure to include `Implements #<SPEC_PR>` in
the body of the implementing PR to ensure that reviewers can refer back to the
specification.

# Template

Please include at least these entries in your specification, adding others if
you think them necessary:

```
# Problem
-----------

Please describe the problem you are trying to address

# Solution
-----------

What is your proposed solution?

# Alternative Solutions
-----------------------

If there are alternative ways of doing this, what are the tradeoffs?

# Arch Impact
-----------------

Are there any new architectural assumptions we are now making?

# Security
----------

Does this impact security?
```
