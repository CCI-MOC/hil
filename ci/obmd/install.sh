#!/usr/bin/env sh
set -ex

# The version of Go available in trusty by default is too old; install
# a newer one from PPA. See also:
#
# https://github.com/golang/go/wiki/Ubuntu
sudo add-apt-repository -y ppa:gophers/archive
sudo apt-get update
sudo apt-get -y install golang-1.10-go

# Set environment variables to point at the new Go installation:
export GOROOT=/usr/lib/go-1.10
export PATH="$HOME/go/bin:/usr/lib/go-1.10/bin:$PATH"

# Just in case, forget any cached command locations:
hash -r

# Download and build obmd:
go get -v github.com/CCI-MOC/obmd

# Copy obmd to somewhere global; this way we don't have to mess with $PATH
# for every test that uses it:
sudo cp ~/go/bin/obmd /usr/local/bin/
