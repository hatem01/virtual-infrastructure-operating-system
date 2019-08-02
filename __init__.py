"""
vIOSLib
===========

Package containing all the modules and elements for the OMAC/HMAC Demo on OpenStack cloud
	
> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

###Folders:

 * /static/ is used for Flask HTTP Server to serve static files (the .PNG file of the Topologie)
 * /templates/ is used for Flask HTTP Server to have the Web pages to parse and dynamically serve

:Example:
	
	vIOSLib.SettingsFile.read(INI_file)
	vIOSLib.readSettingsFile()
	vIOSLib.setDebug()
	vIOSLib.initialize()
	
	
With this, any module can inherit the logger by doing

	import logging
	logger = logging.getLogger(__name__)

"""

"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""


import logging
from logging.handlers import  RotatingFileHandler

import SettingsFile

_FORMAT = '%(asctime)s %(name)s %(levelname)s : %(message)s'
""" Format used by the logging facility"""

INI_Section = "log"
""" This is the INI file section where we expect to find our values """

logging.basicConfig(format=_FORMAT,level=logging.INFO)
logger = logging.getLogger(__name__)
""" Name of the logger; to be used by other modules when they create their logger objects """

logfile = None
""" File where to write the Logs """

backupCount = 2
""" Amount of backup log files to keep """

maxBytes = 1024000
""" Amount of bytes for a log file to have before being backed-up and rotated """

debug = False
""" Defalt verbose mode """


def initializeLogging():
	"""
		This initialize the logging service, by default on INFO level. This configures the logger object used by all the modules in the package.
		
		If there is a filename set, the logger2file handler is configured.
		
		:raises:  Internal Exceptions
		
		..Example::
			vIOSLib.readSettingsFile()
			vIOSLib.initialize()
	"""
	global debug
	
	
	if debug:
		logger.setLevel(logging.DEBUG)
	if logfile:
		hdlr = RotatingFileHandler(logfile, maxBytes, backupCount)
		formatter = logging.Formatter(_FORMAT)
		hdlr.setFormatter(formatter)
		hdlr.setLevel(logging.INFO)
		if debug:
			hdlr.setLevel(logging.DEBUG)
		logger.addHandler(hdlr)
		hdlr.doRollover()


def setDebug():
	"""
		Sets the logging level to DEBUG. This overrides or can be overriden by readSettingsFile()
	"""
	global debug
	debug = True
	
def setLogFile(filename):
	"""
		Sets the Filename where to write the logs. This overrides or can be overriden by readSettingsFile()
	
		:param filename: A valid filename where to write the logs
		:type filename: String
	"""
	global logfile
	logfile = filename

	
def readSettingsFile():
	"""
		This function asks the INI file parser module, that must have read the INI file, to look for the options in the sections and variables that are of interest for this module.
		
		If the options are not present in the INI file, the existing values are not modified
		
		This is so that we add or remove options from the INI file just by mofiying this functions. Also, the same INI entry can be read by many modules
		
		Options set: logfile, backupCount, maxBytes, debug
		
		.. note:: Make sure that the SettingsFile module has been initialized and read a valid file
		
		:Example:
		
			SettingsFile.read(INI_file)
			Messages.readSettingsFile()
			
		
	"""
	global logfile
	global backupCount
	global maxBytes
	global debug
	
	if SettingsFile.getOptionString(INI_Section,"logfile"):
		logfile = SettingsFile.getOptionString(INI_Section,"logfile")
	if SettingsFile.getOptionInt(INI_Section,"maxBytes"):
		maxBytes = SettingsFile.getOptionInt(INI_Section,"maxBytes")
	if SettingsFile.getOptionInt(INI_Section,"backupCount"):
		backupCount = SettingsFile.getOptionInt(INI_Section,"backupCount")
	if SettingsFile.getOptionBoolean(INI_Section,"debug"):
		debug = SettingsFile.getOptionBoolean(INI_Section,"debug")
	#endif
	
