#!/usr/bin/env sh
set -ex

# download the obmd v0.1 binary
wget https://github.com/CCI-MOC/obmd/releases/download/v0.1/obmd
chmod +x obmd
sudo mv obmd /usr/local/bin
