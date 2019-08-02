#!/bin/bash


#vIOSimulator Command Line Test
#==============================
#
#> Ignacio Tamayo, TSP, 2016
#> Version 1.4
#> Date: Sept 2016
#
# Run as:
#	./tests/vIOS-CLI.sh
#


function DoTest {
echo "-------------------------"
echo  $*
$*
ret=$?
echo "-------------------------"
echo "Test return code:" $ret
echo "Press Enter"
read I
}
           
PYTHON=""
CMD="./bin/vIOSimulator.py"
CONFIG="./config_demo.ini"
CONFIG2="./config_graph.ini"

echo "Test1: No Options "
DoTest  ${CMD}

echo "Test2: Invalid Option "
DoTest  ${CMD} -x

echo "Test3: Help text"
DoTest ${CMD} --help

echo "Test4: Empty INI config file"
DoTest ${CMD} -f 

echo "Test4: Invalid INI config file"
echo LALALA > LALALA.ini
DoTest  ${CMD} -f LALALA.ini
rm LALALA.ini

echo "Test5: Logging Error"
DoTest  ${CMD}  -d -f ${CONFIG} -l /dev/log.txt

echo "Test6: DB connection Error"
DoTest  ${CMD}  --debug --config-file ${CONFIG2} 
 
echo "Test7: WebInterface Exception"
iperf -s -p 5000 &
DoTest ${CMD}  -d -f ${CONFIG} 
for i in $(ps -u | awk '/iperf/ {print $2}') ; do kill -9 $i; done;
