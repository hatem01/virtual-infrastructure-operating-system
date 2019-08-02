#!/usr/bin/python
# -*- coding: latin-1 -*-

#Execute using python 2.7

"""
vIOSimulator WEB main module
===========================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

HMAC/OMAC Demo on a live Open Stack cloud deployment

This module does:

	 * Reads a Config file in INI Format. Loads the options from the config files and pass them to the respective modules
	On error reading the config File, program exits
	
	 * Gets the DB URL for initial connection and connects to the DB
	On error, program exits
	
	 * Writes a simple log message to STDOUT (and the logging file, if set).
	On error, program exits
	
	 * Launch a Web Interface in http//<local IP>:<TCP Port>/
	On error, program exits
	
	
.. note:: Main interactions happen in the WEB interface. Modules print DEBUG and ERROR messages to LOG.

.. note:: Check vIOSLib.Messages for settings on the log file. Logging happens to STDOUT, additionally a log file can be used

.. warning:: For every config file passed as parameter, they are processed sequentially and overriden.

.. warning:: Debug and LogFile command-line options override the settings in the configuration files

:Example:

	python vIOSimulator.py [-d|--debug] -f|--config-file <INI configuration file>  [-f|--config-file <INI configuration file>] [-l|--log-file <LOG file>]
	python vIOSimulator.py -h|--help 

.. seealso:: Optimizer.py, WebAdmin.py

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
import vIOSLib.WebAdmin as WebAdmin
import vIOSLib.Messages as LibMessages
import vIOSLib.OptimizationModels as OptimizationModels
import vIOSLib.OpenStackConnection as OpenStackConnection

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
		usage()                         
		sys.exit(2)                     
	
	#<?> There most be at least 1 option in the command
	if not opts:
		print Messages.ERROR_in_options
		usage()                         
		sys.exit(2)
	
	for opt, arg in opts:   #<!> opts are parsed into a tuple (option, value)             
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
				OptimizationModels.readSettingsFile()
				Optimizer.readSettingsFile()
				WebAdmin.readSettingsFile()
				OpenStackConnection.readSettingsFile()
				
			except :
				print(Messages.ERROR_Reading_File )
				if debug_override: 
					raise  ### <<< DEBUG >>>
				sys.exit(6)
			
		elif opt in ("-l", "--log-file"): 
			print (Messages.USING_LOG % arg)
			log_file_override = arg
		elif opt in ("-d", "--debug"): 
			debug_override = True
		else:
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
		if debug_override: 
			raise  ### <<< DEBUG >>>
		sys.exit(7)
		
	### Reading settings and conneting to DB ###
	if not Optimizer.connect( db_url ):
		print(Messages.ERROR_Connecting_to_DB_in_File %  db_url )
		sys.exit(4)
	
	### Try to brin up the WEB interface ###
	try:
		WebAdmin.initialize()
		if WebAdmin.connect(db_url):
			print Messages.Web_URL_S_port_D % (WebAdmin.ListenIp , WebAdmin.TCPport)
			WebAdmin.build()
			WebAdmin.start()
			#<?> This gets blocked here until the end of the Web Server
	except:
		print Messages.ERROR_Web
		if debug_override: 
			raise  ### <<< DEBUG >>>
		sys.exit(99)
	
	banner()
	
#enddef


def usage():
	""" Prints how to use this tool """
	print("Usage: \t vIOSimulator.py  [-d] -f <INI configuration file> [-f <INI configuration file>] [-l <LOG file>]")	
	print("\t -d|--debug                                   Enables DEBUG logging, overrides the configuration file option")
	print("\t -f|--config-file <INI configuration file>    This is one or more configuration files, read sequentially.")
	print("\t -l|--log-file <LOG file>                     This is the file where log messages will be writen, in addition to STDOUT/STDERR. This overrides the configuration file option ")	
	print("\n\t vIOSimulator.py -h|--help")
	print("")
	banner()
#enddef	


def banner():
	"""  Prints a banner"""
	print("\nTelecom SudParis - 2016")	
	print("Ver 1.3\n")
	
#enddef	


		
# If this .PY is called as executable, run this		
if __name__ == "__main__":
    main(sys.argv[1:])
