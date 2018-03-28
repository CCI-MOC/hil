#!/usr/bin/env sh
set -ex

# The version of Go available in trusty by default is too old; install
# a newer one from PPA. See also:
#
# https://github.com/golang/go/wiki/Ubuntu
sudo add-apt-repository ppa:gophers/archive
sudo apt-get update
sudo apt-get -y install golang-1.10-go
