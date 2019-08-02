# vCDN Infrastructure Optimization Simulator

> IBN KHEDHER Hatem
>
> Version 1.4
>
> Date: Sept 2016

This is a demo implementation of HMAC algorithm for Optimal vCDN Migration on an OpenStack environment. 

HMAC is an Optimal VM migration algorithm that uses topologie information, live OpenStack statistics and metrics and the Demand for a vCDN Service as inputs. These input information can come from Operator's systems or, in our case, from manual input.

The objective of HMAC is to determine where to migrate a VM in order not to saturate the network links capacity neither the OpenStack capacity, minimizing the migration cost. This is an heuritic algorithm, it not an exact solution.

From the selected Optimal operations, a simulation is run to determine the impact on the Infrastructure.

This demo integrated also OMAC algorithm, which is an exact solution algorithm that uses IBM CPLEX. In this case, both the .mod and .dat files are generated by this tool and could be imported into a licensed version of CPLEX to obtain the results.

This demo makes use of an exponential law to simulate the reduction in the BW demands in the infrastructure, based on QoE values

This demo triggers some instantiations and snapshot migrations in the OpenStack Data Centers, in background. These operations are to be checked either via the OpenStack Controllers or via the logs left by the simulator.

This version of vIOSimulator is designed and adjusted for the DVD2C project, on which Telecom SudParis has a participating role.

### References:

 *  http://ieeexplore.ieee.org/document/7500390/?reload=true&arnumber=7500390
 
 * http://arxiv.org/pdf/1608.08365.pdf 
 
 * http://samovar.telecom-sudparis.eu/spip.php?article824&lang=en

## Requirements

 * Python 2.7
 * MySQL Database

These Python modules are needed: 

		docutils (0.12)
		Flask (0.11.1)
		Flask-Admin (1.4.2)
		Jinja2 (2.8)
		keystoneauth1 (2.4.0)
		keystonemiddleware (4.4.0)
		mysql-connector-python (2.0.4)
		mysql-utilities (1.6.1)
		mysqlclient (1.3.7)
		python-ceilometerclient (2.4.0)
		python-igraph (0.7.1.post6)
		python-keystoneclient (2.3.1)
		python-novaclient (3.3.1)
		simplejson (3.8.1)
		SQLAlchemy (1.0.13)


## Environment Open Stack

This demo operates in an OpenStack distributed environment, tested using both `OpenStack Icehouse` and `OpenStack Mitaka`. 

This demo supports also `Regions`, where a single `Horizon` and `Keystone` service is shared among different DataCenters.

An OpenStack DataCenter, to operate with this demo, must have a `Nova` and `Ceilometer` service installed.

The OpenStack DataCenters should have given `Tenants` created, associating each to a `vCDN` client.

> **NOTE:** Make sure the `endpoints` set in the `Keystone` service are properly reachable and point to the appropriate API HTTP url.


## Structure

 * SQL scripts and database description.
 
 * CPLEX files are left after OMAC is run. These files are to be imported into a
 
 * Python code, the main library package is `vIOSLib` and the executable Demo is `vIOSimulator.py`.
  
 * Bash scripts for testing the initial deployment.
 
## Installl Instructions

> **NOTE:** These instructions are given for Ubuntu systems, please modify they commands according to your system

Once dowloaded the repository, first create a DataBase by executing the SQL script

		mysql -u root -p [-h <server>] <  vIOS_db.sql

Test the connectivity by

		mysql -u vios -p  [-h <server>]  vios

Install python, pip, and the Python dependencies
	
		sudo apt-get install python python-pip python-ceilometerclient  python-novaclient python-keystoneclient 
		pip install python-igraph, mysqlclient, Flask-Admin, Flask, SQLAlchemy
	
Adjust the desired configurations in `config_demo.ini`, at least the MySQL DB url


## Execution

Adjust the desired configurations in `config_demo.ini`

#### To launch the Demo in the CLI:

		bin/vIOSimulator.py -f config_demo.ini

Connect to the HTTP Server, on the IP and Port set in `config_demo.ini`

#### To lauch the Demo as a Service;

 * Ubuntu 14.04
 
Create a file `/etc/init/vIOS.conf`:

		description "Running vIOS (vCDN Infrastructure Optimization Simulator)"
		author "Jose Ignacio Tamayo - Telecom SudParis 2016"
		start on runlevel [2345]
		stop on runlevel [!2345] 
		# Respawn and stop respawning if it got respawned 10 time in 10 seconds
		respawn limit 2 2 
		# prepare environment
		pre-start script
				mkdir /var/log/vIOS
		end script
		script 
		cd <installation folder>
				/usr/bin/python bin/vIOSimulator.py -f <config file> -l <log file>
		end script

Restart the Service Daemon

		$ sudo initctl reload-configuration
		$ sudo init-checkconf /etc/init/vIOS.conf
		$ sudo service vIOS start|stop|status
 
  * Ubuntu 16.04
 
Create a file `/lib/systemd/system/vIOS.service`, replacing the simbols by the appropriate values:

		[Unit]
		Description=Running vIOS (vCDN Infrastructure Optimization Simulator)
		[Service]
		Type=simple
		Environment=statedir=<installation folder>
		Environment=PYTHONPATH=<python packages folder>
		WorkingDirectory=<installation folder>
		ExecStartPre=/bin/mkdir -p /var/log/vIOS
		ExecStart=/usr/bin/python bin/vIOSimulator.py -f <config file> -l <log file>
		[Install]
		WantedBy=multi-user.target

Restart the Service Daemon

	$ sudo systemctl daemon-reload
	$ sudo systemctl status vIOS


## Version Changelog

 * Call the actual migration of VMs on OpenStack, via snapshot-copy or VM-cloning.
 * Demand BW adjustment by QoE, for the Operator to consider this.
 * All options possible are in the INI file

### Feature Pipeline

 * Deployer les Types de vCDNs
 * Test coverage program, Decision Coverage.
 * Use of Client's connection BW and hosting capacities. ClientGroups connections integrated in the Gomuri Tree. Check migration to client
 * Insert Logic for handling individual VMs


## Authors and license

Author: IBN KHEDHER Hatem, France
Email: ibnkhedherhatem@gmail.com


This code is delivered AS IS, no warranty is provided neither support nor maintenance.

This code is free, under MIT licence [Reference](http://choosealicense.com/licenses/) [MIT](http://www.tawesoft.co.uk/kb/article/mit-license-faq).

--------------------------------
vIOS (vCDN Infrastructure Optimization Simulator)

Copyright (c) 2016 Telecom SudParis - RST Department

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

----------------------------------
