
cd "$(dirname $0)"

cp testsuite.cfg ../../
cp site-layout.json ../../

cd ../..
py.test --cov=hil --cov-append tests/deployment/*_networks.py
