
cd "$(dirname $0)"

cp testsuite.cfg ../../
cp site-layout.json ../../

cd ../..
py.test tests/deployment/*_networks.py
