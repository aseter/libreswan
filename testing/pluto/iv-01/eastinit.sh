TESTNAME=iv-01
source /testing/pluto/bin/eastlocal.sh

ipsec start
/testing/pluto/bin/wait-until-pluto-started

ipsec auto --add westnet-eastnet
ipsec whack --name westnet-eastnet --impair sa-fail --debug control --debug controlmore --debug crypt

