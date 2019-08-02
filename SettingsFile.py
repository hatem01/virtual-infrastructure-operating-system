""" 

INI config file parser
======================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

Some modules use default values or requiere config parameters set in the INI-format file. This module gets those values from the file

:Example:

	SettingsParser.read(arg)
	if SettingsParser.getDBString():
		db_url = SettingsParser.getDBString()
	Module.readSettingsFile()
	
		
Another module, trusting SettingsFile has read a valid INI file, can implement their own funtion to read their options on their own

:Example:

	def Module.readSettingsFile():
		if SettingsParser.getInt(MySection,MyOption):
			value = SettingsParser.getInt(MySection,MyOption)

This can then be changed to JSON or XML file, without altering the receving modules.

Also, the other modules are not aware of the Settings File mechanisms, they just ask for an optionName to be searched in a sectionName

------------------------------------
The config file is INI structure

[Section]
Option = Value

[database]
url = Value

[DEFAULT]
Option = Value
------------------------------------
"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import ConfigParser 

URL_Option = "url"
""" Option in the INI file to look for the DB String"""
Database_Section = "database"
""" Section in the INI file to look for the DB String"""

Config = ConfigParser.ConfigParser()
# Internal object

def read(filename):
	"""
		Reads the INI file passed as parameter. It is assumed that the file does exist and is readable
		
		:param filename: Filename to read
		:type filename: String
		
		:raises:  LookupError if unable to read the file
	"""
	
	try:
		
		Config.read(filename)
	except:
		raise LookupError

def getDBString():
	"""
		Gets the value of the option URL_Option in the config file. 
		If the option is not found, None is returned
		
		.. warning:: Call after read()
		
		:returns:  the String of the DB URL or None
		:rtype: String or None
	"""
	try:
		return Config.get(Database_Section,URL_Option,raw=True)
	except:
		return None

def getOptionString(sectionName,optionName):
	"""
		Looks for the optionName in the sectionName or the DEFAULT section. 
		If found, the value is returned. If not found, None is returned
		
		.. warning:: Call after read()
		
		:param sectionName: Name of the section in the INI file where the option is searched. The DEFAULT section is also checked
		:type sectionName: String
		:param optionName: name of the option to search
		:type optionName: String
		
		:returns:  The optionName String value, or None if not found
		:rtype: String or None
	"""
	try:
		return Config.get(sectionName,optionName,raw=True)
	except:
		return None
	
#enddef

def getOptionInt(sectionName,optionName):
	"""
		.. seealso:: getOptionString()
		
		:returns:  The optionName integer value, or None if not found
		:rtype: int or None
	"""
	
	try:
		return Config.getint(sectionName,optionName)
	except:
		return None
		
#enddef

def getOptionFloat(sectionName,optionName):
	"""
		.. seealso:: getOptionString()
		
		:returns:  The optionName float value, or None if not found
		:rtype: float or None
	"""
	try:
		return Config.getfloat(sectionName,optionName)
	except:
		return None
#enddef

def getOptionBoolean(sectionName,optionName):
	"""
		.. seealso:: getOptionString()
		
		:returns:  The optionName boolean value, or None if not found
		:rtype: boolean or None
	"""
	try:
		return Config.getboolean(sectionName,optionName)
	except:
		return None
#enddef

