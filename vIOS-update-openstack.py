#!/usr/bin/python
#Execute using python 2.7

"""
OMAC Demo daemon
================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

OMAC Daemon to be run in the Crontab (or similar)

This daemon automatically loads the configuration file, connects to the DB, connects to all OpenStack POPs and updates the information. This is intended not to leave any output or trace.

.. note:: This is an executable file, make sure permissions are in place

:Example:
	python vIOS-update-openstack.py -f|--config-file <INI configuration file>	
	python vIOS-update-openstack.py -h|--help Help

Reads a Config file in INI Format. The only compulsory value is:

----------------------
[database]
url = ""
-----------------------

.. seealso::  Optimizer.py

"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

### Importing system libraries ###
import sys
import getopt

### Importing local libraries ###
import vIOSLib
import vIOSLib.SettingsFile as SettingsParser
import vIOSLib.Optimizer as Optimizer
import vIOSLib.Messages as LibMessages

import Messages


def main(argv):
	""" 
		Main program to execute if this file is called as executable
		
		:param argv: This is sys.argv[1:] to get the CLI options passed at call
		:type argv: String[]
		
	"""
	db_url = ""  
	log_file_override = "" 
	debug_override = False
		 
	try:                                
		opts, args = getopt.getopt(argv, "hdf:l:", ["help","debug", "config-file=", "log-file="])		
		#<!> "config-file=" works both for CLI "--config-file=X" and "--config-file X" 
	except : 
		print Messages.ERROR_in_options                         
		sys.exit(2)                     
	
	#<?> There most be at least 1 option in the command
	if not opts:
		print Messages.ERROR_in_options
		usage()                         
		sys.exit(2)
	
	for opt, arg in opts:   #<!> opts is a tuple (option, value)             
		if opt in ("-h", "--help"):      
			usage()                     
			sys.exit(0)                  
		elif opt in ("-f", "--config-file"): 
			print (Messages.READING_OPTIONS % arg)
			try:
				SettingsParser.read(arg)
				if SettingsParser.getDBString():
					db_url = SettingsParser.getDBString()
				
				#<?> Some modules will need options taken from the config-file.
				vIOSLib.readSettingsFile()
				Optimizer.readSettingsFile()
				
			except :
				print(Messages.ERROR_Reading_File )
				
				sys.exit(6)
			
		elif opt in ("-l", "--log-file"): 
			print (Messages.USING_LOG % arg)
			log_file_override = arg
		elif opt in ("-d", "--debug"): 
			debug_override = True
		else:
			print Messages.ERROR_in_options
			usage()                     
			sys.exit(2) 
	
	del opts[:]
	#<?> To free memory; we kill the objects
	
	try:
		if log_file_override:
			vIOSLib.setLogFile(log_file_override)
		if debug_override:
			vIOSLib.setDebug()
		vIOSLib.initializeLogging()
		vIOSLib.logger.info(Messages.STARTING)
	except:
		print(Messages.ERROR_Logging)
		
		sys.exit(7)
		
	### Reading settings and conneting to DB ###
	if not Optimizer.connect( db_url ):
		print(Messages.ERROR_Connecting_to_DB_in_File %  db_url )
		sys.exit(4)
	
	### Update the OpenStack values in the DB
	Optimizer.updatePOPs()
	Optimizer.updateMetrics()
	sys.exit(0)

	
#enddef

# If this .PY is called as executable, run this		
if __name__ == "__main__":
    main(sys.argv[1:])
