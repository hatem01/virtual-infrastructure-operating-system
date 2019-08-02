
""" 

Module to interact with the Nova, Ceilometer, Glance and Keystone API
=====================================================================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

.. warning: This uses Keystone API v2.0, Endpoints should use this API Version

.. note:: This module does not interact directly with the DB, the Optimizer module does


:Example:
	
	OsConn = OpenStackConnection()
	OsConn.setURL( url, region)
	OsConn.setCredentials(...)
	if OsConn.connect():
		if OsConn.connectMetrics():
			lims = OsConn.getLimits()
			met = OsConn.getMetrics()
			OsConn.disconnect()
	
	OsConn = OpenStackConnection()
	OsConn.setURL( url, region)
	OsConn.setCredentials(...)
	if OsConn.connect():
		servers = getServers()
		for s in servers:
			Thread(OsConn.migrate(s))
			s.pause()
			snapID = s.snapshot()
			OsConn.DownloadImg(snapID)
			OsConn.UploadImg(snapID)
			OsConn.UploadImg(snapID)
			met = OsConn.getMetrics()
			OsConn.disconnect()
	
	
"""

"""
References:

	https://albertomolina.wordpress.com/2013/11/20/how-to-launch-an-instance-on-openstack-iii-python-novaclient-library/
	
	http://www.ibm.com/developerworks/cloud/library/cl-openstack-pythonapis/
"""

"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from novaclient import client as NovaApiClient
from keystoneclient.auth.identity import v2
from keystoneclient import session
from ceilometerclient import client as CielClient
import glanceclient.v2.client as GlanceClient
import glanceclient.exc as GlanceExceptions
import novaclient.exceptions as NovaExceptions
from datetime import datetime, timedelta			### Needed for time formating and time calculations
import logging

import time


import Messages
import SettingsFile

logger = logging.getLogger(__name__)

INI_Section = "openstack" 
""" This is the INI file section where we expect to find our values """
	
TIMEOUT = 5				
""" HTTP API Connection timeOut. In Seconds """
CEILOMETER_PERIOD = 600	
"""  Ceilometer, by default, takes samples every 600 seconds. This is the most granular the default Ceilometer gets """

IMG_TIMEOUT = 60
""" Seconds to wait before polling the Glance Service to check if an Image is ready"""
IMG_RETRIES = 5
""" Max times to poll the Glance Service to check if an Image is ready"""
SERVER_TIMEOUT = 30
""" Seconds to wait before polling the Nova Service to check if an VM is ready"""
SERVER_RETRIES = 5
""" Max times to poll the Nova Service to check if an VM is ready"""

def readSettingsFile():
	"""
		This function takes an INI file parser object, that must have read the INI file, and starts looking for the options in the sections and variables that are of interest for this module.
		
		If the options are not present in the INI file, the default values are kept
		
		This is so that we add or remove options from the INI file just by mofiying this functions. Also, the same INI entry can be read by many modules
		
		.. note:: Make sure to pass a valid ConfigParser object
		
		:param SettingsParser: A SettingsParser object that starts from SettingsFile.py
		:type SettingsParser: SettingsParser
		
		
	"""
	
	global TIMEOUT
	global CEILOMETER_PERIOD
	global IMG_TIMEOUT
	global IMG_RETRIES
	global SERVER_TIMEOUT
	global SERVER_RETRIES
	
	if SettingsFile.getOptionInt(INI_Section,"connection_timeout"):
		TIMEOUT = SettingsFile.getOptionInt(INI_Section,"connection_timeout")
	if SettingsFile.getOptionInt(INI_Section,"ceilometer_period"):
		CEILOMETER_PERIOD = SettingsFile.getOptionInt(INI_Section,"ceilometer_period")
	if SettingsFile.getOptionInt(INI_Section,"glance_poll_timeout"):
		IMG_TIMEOUT = SettingsFile.getOptionInt(INI_Section,"glance_poll_timeout")
	if SettingsFile.getOptionInt(INI_Section,"nova_poll_timeout"):
		SERVER_TIMEOUT = SettingsFile.getOptionInt(INI_Section,"nova_poll_timeout")	
	if SettingsFile.getOptionInt(INI_Section,"glance_poll_retries"):
		IMG_RETRIES = SettingsFile.getOptionInt(INI_Section,"glance_poll_retries")	
	if SettingsFile.getOptionInt(INI_Section,"nova_poll_retries"):
		SERVER_RETRIES = SettingsFile.getOptionInt(INI_Section,"nova_poll_retries")	
		
	#endif

	
class APIConnection(object):
	"""
		This class represents the connection with the Nova API, passing by authentication with KeyStone
		The values provided in setURL() and setCredentials() are the same as the ones used for CLI client
		Internally, the client will get the Nova API endpoint from Keystone, so make sure the Endpoints in Keystone are correct and reachable
	"""
	
	# Constants used on API connections
	NOVA_VERSION = "2"		# Invalid client version '2.0'. must be one of: 3, 2, 1.1
	CIEL_VERSION = "2"		# 
	GLANCE_VERSION = "2"

	def __init__(self):
		"""
			Starts with no connections, with no credentials to connect with. Empty start
		"""
		self.Session = None
		self.Nova = None
		self.Ceil = None
		self.Glance = None
	#enddef
	
		
	def connect(self):
		"""
			Connects to the Nova API Server after authenticating with Keystone
			 
			Execute after setURL() and setCredentials()
			 
			:returns: True if the connection went OK, False if errors
		"""
		try:
			auth = v2.Password( username=self.user, 
								password=self.passwd, 
								tenant_name=self.tenant, 
								auth_url=self.auth_url)
			
			logger.debug( Messages.AuthOS_url_S_user_s_tenant_S % (self.auth_url ,self.user ,self.tenant))
			
			## auth = v2.Password(username="user_hbo", password="USER_PASS", tenant_name="tenant_hbo", auth_url="http://controller-evry:35357/v2.0")
			
			self.Session = session.Session(auth=auth)
			
			self.Nova = NovaApiClient.Client(
								self.NOVA_VERSION,
								session = self.Session,
								timeout=TIMEOUT,
								region_name = self.region
								)
								
			# Nova = NovaApiClient.Client("2", session = Session)
								
			logger.debug( Messages.AuthOS_region_S % self.region)
			
			self.Nova.servers.list()
			
			logger.debug( Messages.Authenticated)
			
		except Exception, e:
			logger.error( Messages.Exception_Nova_url_S_region_S_user_S_tenant_S % (self.auth_url ,self.region,self.user ,self.tenant))
			logger.error(repr(e))
			return False
			
		#  Nova = NovaApiClient.Client("2", session = Session)
		
		return True
	#enddef
	
	
	def connectMetrics(self):
		"""
			Connects to the Ceilometer API Server after authenticating with Keystone
			
			Execute after connect()
			 
			Could return False in case of error.. for now errors are detected though Exceptions
			
			:returns: True if the connection went OK, False if errors
			
		"""
		try:
			auth = v2.Password(username= self.user, 
								password= self.passwd, 
								tenant_name= self.tenant, 
								auth_url= self.auth_url)
			
			logger.debug( Messages.AuthOS_url_S_user_s_tenant_S % (self.auth_url ,self.user ,self.tenant))
			
			## auth = v2.Password(username="admin", password="ADMIN_PASS", tenant_name="admin", auth_url="http://controller-saclay:35357/v2.0")
			
			self.Session = session.Session(auth=auth)
			self.Ceil = CielClient.get_client(
								self.CIEL_VERSION,
								session = self.Session,
								timeout=TIMEOUT,
								region_name = self.region
								)
			logger.debug( Messages.AuthOS_region_S % self.region)
			self.Ceil.meters.list()
			logger.debug( Messages.Authenticated)
		except Exception,e :
			logger.error( Messages.Exception_Ceilometer_url_S_region_S_user_S_tenant_S % (self.auth_url,self.region ,self.user ,self.tenant))
			logger.error(repr(e))
			return False
		#  Session = CielClient.get_client("2",username="admin", password="ADMIN_PASS",tenant_name="admin", auth_url="http://controller:35357/v2.0")
		return True
	#enddef
	
	def connectImages(self):
		"""
			Connects to the Glance API Server after authenticating with Keystone
			
			Execute after connect()
			 
			Could return False in case of error.. for now errors are detected though Exceptions
			
			:returns: True if the connection went OK, False if errors
			
		"""
		try:
			auth = v2.Password(username= self.user, 
								password= self.passwd, 
								tenant_name= self.tenant, 
								auth_url= self.auth_url)
			
			logger.debug( Messages.AuthOS_url_S_user_s_tenant_S % (self.auth_url ,self.user ,self.tenant))
			
			## auth = v2.Password(username="admin", password="ADMIN_PASS", tenant_name="admin", auth_url="http://controller-saclay:35357/v2.0")
			
			self.Session = session.Session(auth=auth)
			self.Glance = GlanceClient.Client(
								self.GLANCE_VERSION,
								session = self.Session,
								region_name = self.region
								)
			logger.debug( Messages.AuthOS_region_S % self.region)
			list(self.Glance.images.list())
			logger.debug( Messages.Authenticated)
			
			#Glance = GlanceClient.Client("2", session = Session)
			
		except Exception,e :
			logger.error( Messages.Exception_Glance_url_S_region_S_user_S_tenant_S % (self.auth_url,self.region ,self.user ,self.tenant))
			logger.error(repr(e))
			return False
		
		return True
	#enddef
	
	def disconnect(self):
		""" Disconnects from the Nova, Ceilometer and Keystone API Server """
		self.Nova = None
		self.Ceil = None
		self.Session = None
	#enddef
	
	def setURL(self,url,region = None):
		"""
			:param url: url is the KeyStone Auth
			:type url: String
			:param region: Region of the OpenStack services to use. Defaults to None
			:type region: String
			
			Same as the credentials file used in CLI
			
			.. note:: Make sure that the Nova API URL given in the Keysonte reply is reachable from this host. Do "nova --debug list" to verify where Keystone send the Api Call
		"""
		self.auth_url = url
		self.region = region
	#enddef
	
	def setCredentials(self,tenant,user,passwd):
		"""
			:param tenant: url is the Admin tenant
			:type tenant: String
			:param user: url is the Admin user
			:type user: String
			:param passwd: url is the Admin pass
			:type passwd: String
			
			Same as the credentials file used in CLI
		"""
		self.tenant = tenant
		self.user = user
		self.passwd = passwd
	#enddef	
	
	def getHypervisors(self):
		"""
		Gets a list of hypervisors
		
		:returns: List of novaclient.Hypervisors
		:rtype: novaclient.Hypervisor[]
		"""
		return self.Nova.hypervisors.list()
	#enddef

	def getPublicFlavors(self):
		""" Gets a list of flavors, only those marked as public 
		
		:returns: List of novaclient.Flavors
		:rtype: novaclient.Flavor[]
		"""
		
		return [f for f in self.Nova.flavors.list() if f.is_public]
	#enddef
	
	def getServers(self):
		"""Gets a list of servers
		
		:returns: List of novaclient.Servers
		:rtype: novaclient.Server[]
		"""
		return self.Nova.servers.list()
	#enddef
	
	def getSnapshotImage(self,imageId,filename):
		"""
		Downloads to the filename the Image file of the ImageId 
		
		:param imageId: Glance Id of the Image to download
		:type imageId: String as per Glance Id
		:param filename: Absolute path to filename to write
		:type filename: String
		
		:returns: True if image was downloaded OK, False else
		
		"""
		
		try:
			aImage = self.Glance.images.get(imageId)
			try:
				image_file = open(filename, 'w+')
				for chunk in self.Glance.images.data(imageId):
					image_file.write(chunk)
				image_file.close()
				return True
			except IOError:
				#Not able to open file
				return False
			
		except GlanceExceptions.HTTPNotFound:
			#Unable to retreive the Image
			return False
	#enddef
	
	def putSnapshotImage(self,imageName,filename):
		"""
			Uploads the filename the Image and creates the Image named as such 
			
			:param imageName: Glance name of the Image to create
			:type imageName: String
			:param filename: Absolute path to filename to read
			:type filename: String
		
			:returns: Image Id of the new Image created from the snapshot file
			:rtype: String as per Glance ID
		
		"""
		
		try:
			aImage = self.Glance.images.create(name = imageName, container_format = "bare", visibility = "private", disk_format="qcow2" )
			self.Glance.images.upload(aImage.id, open(filename, 'rb'))			
			return aImage.id
		except GlanceExceptions.HTTPNotFound, IOError:
			#Unable to upload the Image
			return False
	#enddef
	
		
	def serverMetadata(self,serverId):
		"""
			From a ServerId existing in a ComputeNode, a MetaData structure is extracted
			
			This data is usefull to describe the machine when instantiating in another DC
			
			..This is not the Nova Metadata, it is an internal call used to contain all parameters needed to create a clone VM
			
			:param serverId: String of the Server Id to read from
			:type serverId: String as per Nova Server Id
			
			:returns: The MetaData corresponding to the serverId
			:rtype: ServerMetadata
			
		"""
		try:
			
			server = self.Nova.servers.find(id = serverId)
			serverMeta = ServerMetadata(name = server.name)
			serverMeta.imageName = self.Nova.images.find(id = server.image['id']).name
			serverMeta.flavorName = self.Nova.flavors.find(id = server.flavor['id']).name
			serverMeta.NetworkNames =  server.addresses.keys()
			serverMeta.SecurityGroups = [ s.name for s in server.list_security_group()]
			
			
			for address in server.addresses.values():
				for ip in address:
					if ip['OS-EXT-IPS:type'] == "floating":
						serverMeta.floating_ip = True
			
			return serverMeta
		except:
			return None
	
	def createServer(self, serverMetadata):
		"""
		
		Given a ServerMetadata describing the desired parameters, a new VM is launched with these parameters
		
		:param serverMetadata: the server metadata description
		:type serverMetadata: ServerMetadata
		
		:returns: True if the VM was created OK; False else
		
		"""
		try:
			try:
				imageObj = self.Nova.images.find(name = serverMetadata.imageName)
				FlavorObj = self.Nova.flavors.find(name = serverMetadata.flavorName)
			except NovaExceptions.NoUniqueMatch:
				logger.error(Messages.Duplicated_element_S,serverMetadata.imageName )
				return None
			
			networksDict = []
			for netName  in  serverMetadata.NetworkNames:
				try:
					networksDict.append ( { 'net-id' : self.Nova.networks.find(label = netName).id } )
				except (NovaExceptions.NotFound, NovaExceptions.BadRequest):
					pass
			
			secGroups = []
			for secg  in  serverMetadata.SecurityGroups:
				try:
					if self.Nova.security_groups.find(name=secg) is not None:
						secGroups.append(secg)
				except (NovaExceptions.BadRequest, NovaExceptions.NotFound):
					pass
			
			try:
				server = self.Nova.servers.create( serverMetadata.name, 
													imageObj, 
													FlavorObj, 
													nics=networksDict, 
													security_groups = secGroups )	
			except NovaExceptions.BadRequest:
				logger.error(Messages.Invalid_Server_Parameters_S,serverMetadata.to_dict() )
				return None
			except NovaExceptions.OverLimit:
				logger.error(Messages.QuotaLimit )
				return None
						
			time.sleep(5)
			
			if serverMetadata.floating_ip:
				floating_ip = self.Nova.floating_ips.create(self.Nova.floating_ip_pools.list()[0].name)
				server.add_floating_ip(floating_ip)
			
			return server.id
			
		except (NovaExceptions.BadRequest, NovaExceptions.NotFound):
			
			return None
	#enddef	
	
	def deleteServer(self, serverId):
		"""
		
		Given a ServerId, it is deleted and its Floating IP returned to the Pool
		
		:param serverId: the server Id to be deleted
		:type serverId: String as in Nova Server Id
		
		:returns: True if the VM was deleted OK; False else
		
		"""
		try:
			
			server = self.Nova.servers.find(id = serverId)
			
			for address in server.addresses.values():
				for ip in address:
					if ip['OS-EXT-IPS:type'] == "floating":
						pass
						server.remove_floating_ip(ip['addr'])
						self.Nova.floating_ips.delete(ip['addr'])
			
			server.pause()
			
			return True
						
		except NovaExceptions.NotFound:
			logger.error(Messages.ServerId_S_NotFound % serverId )
			return False
	#enddef	
	
	def deleteImage(self, imageId):
		"""
		
		Given an imageId, it is deleted
		
		:param imageId: the image Id to be deleted
		:type imageId: String as in Glance Server Id
		
		:returns: True if the VM was deleted OK; False else
		
		"""
		try:
			
			aImage = self.Glance.images.get(imageId)
			
			aImage = self.Glance.images.delete(imageId)
			
			return True
						
		except GlanceExceptions.HTTPNotFound:
			logger.error(Messages.ImageId_S_NotFound % imageId )
			return False
	#enddef	
	
		
	def isServerReady(self,serverId):
		"""
		
		Checks is a VM is active or not
		
		:param serverId: Id of the server to check its status
		:type serverId: String as per Nova Server Id
		
		:returns: True if the server has 'ACTIVE' status, False else
		
		"""
		try:
			aServer = self.Nova.servers.find(id = serverId)
			return aServer.status.lower() == "active"
		except NovaExceptions.NotFound:
			#Unable to retreive the Server
			return False
	
	def isImageReady(self,imageId):
		"""
		
		Checks is an Image is active or not
		
		:param imageId: Id of the Glance Image to check its status
		:type imageId: String as per Glance Image Id
		
		:returns: True if the image has 'ACTIVE' status, False else
		
		"""
		try:
			aImage = self.Glance.images.get(imageId)
			return aImage.status.lower() == "active"
		except GlanceExceptions.HTTPNotFound:
			#Unable to retreive the Image
			return False
	
	def waitImageReady(self,imageId):
		""" 
			Wait for the Glance image to be ready. 
			It waits IMG_TIMEOUT seconds between each retry, and retries up to IMG_RETRIES times before quiting
		
			:param imageId: Id of the Glance Image to check its status
			:type imageId: String as per Glance Image Id
		
			:returns: True if the image has 'ACTIVE' status, False else
		"""
		retries = 0
		try:
			while( self.Glance.images.get(imageId).status.lower() != 'active') and retries < IMG_RETRIES:
				time.sleep(IMG_TIMEOUT)
				retries = retries + 1
		except GlanceExceptions.HTTPNotFound:
			logger.error(Messages.ServerId_S_NotFound % serverId )
			retries = SERVER_RETRIES
		if retries >= IMG_RETRIES:
			### The image is not ready ###
			return False
		else:
			return True
	
	def waitServerReady(self,serverId):
		""" 
			Wait for the Nova Server to be ready. 
			It waits SERVER_TIMEOUT seconds between each retry, and retries up to SERVER_RETRIES times before quiting
		
			:param serverId: Id of the Nova Server to check its status
			:type serverId: String as per Nova Server Id
		
			:returns: True if the image has 'ACTIVE' status, False else
		"""
		retries = 0
		try:
			
			while( self.Nova.servers.find(id = serverId).status.lower() != 'active') and retries < SERVER_RETRIES:
				time.sleep(SERVER_TIMEOUT)
				retries = retries + 1
				
		except NovaExceptions.NotFound:
			logger.error(Messages.ServerId_S_NotFound % serverId )
			retries = SERVER_RETRIES
			 
		if retries >= SERVER_RETRIES:
			### The server is not ready ###
			return False
		else:
			return True
	
	def getLimits(self):
		""" 
		Gets a list of the absolute limiting values for the connected tenant 
		
			> nova quota-show
			>nova quota-defaults

			:returns:  an Limits object with the limits
			:rtype: Limits class
			
			
		"""
		retLim = Limits()
		try:
			for l in self.Nova.limits.get().absolute:	
				
			#### HAS to be this way; with *for* because it is a Generator of AbsoluteLimit Objects, not a dictionary neither List
				if l.name == "maxTotalRAMSize":
					retLim.maxRAM = l.value
				elif l.name =="totalRAMUsed":
					retLim.curRAM  = l.value
				elif l.name == "maxTotalInstances":
					retLim.maxInstances = l.value
				elif l.name =="totalInstancesUsed":
					retLim.curInstances = l.value
				elif l.name =="maxTotalCores":
					retLim.maxCPU = l.value
				elif l.name =="totalCoresUsed":
					retLim.curCPU = l.value
				
		except:
			pass
		return retLim
	#enddef
	
	def getMetrics(self,durationHours):
		""" 
		
			Gets a list of the absolute limiting values for the connected tenant 
			
			:param durationHours: are the period to measure; in hours
			:type durationHours: int 
			:returns:  an Meter object with the metrics
			:rtype: Meter class
			
						
			 CLI equivalent: 
				> ceilometer  statistics -m vcpus -q 'timestamp>2016-06-14T00:00:00' -p 600
			
			Collects many samples, with the SUM of the values for each tenant. So te SUM of all disk/mem/cpu/net used every 10mins(600 secs, default sample rate)
			If the Sample Rate of Ceilometer is different; change the period. If there is different Sample Rate for each meter, change this function
			
			The logic is that every sampling (600 secs) we sum all the samples, grouped by Tenant. So if a Tenant has 3 VMs, each of 512 MB Ram; we would
			have a sample of 1512 MB or RAM representative of what the client was using in that period of time
			
			Then we collect this aggregated samples and to MIN/MAX/AVG on the aggregated
			
			This  logic is not done by the Statistics alone, as it aggregates the MIN/MAX over the total Samples. So the Tenant with 3 VMs of 265,512,512 MB Ram
			will show MIN=256, MAX=512 on each sample; which is not the intended data
			
			Then all this data is put in a list and we get the MIN/MAX/AVG
			
			'%Y-%m-%dT%H:%M:%S' is the Format of the DB result, please check this is coherent in all Ceiling Servers
			
			The minimum timeStamp of all the Meters is considered as the timestamp of the complete metric. So the metric is as recent as its oldest individual meter
			
			.. note:: It might get old data because it keeps history of killled/dead instances. This is how Ceiling works
			
		"""
		
		
		OS_CEILOMETER_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
		OS_CEILOMETER_TIME_FORMAT_USEC = '%Y-%m-%dT%H:%M:%S.%f'
		### Sometimes the DB adds the microseconds
		
		
		#Initial object to store our captured Metrics
		meter = Meter()
		minTimeStampValue = datetime.now()
		
		for m in meter.values.keys():
			#Get last sample timestamp. the Sample Api will order the samples; the first is the most recent one
			sample_set = self.Ceil.samples.list( meter_name = m, limit=1 )
			if sample_set != None and sample_set != []:
				timestamp = sample_set[0].timestamp
				logger.debug(Messages.LastSample_S_at_S % ( m ,str(timestamp)))
			else:
				logger.error(Messages.NoMetrics_Meter_S % ( m ))
				continue
			
			# Converting the DB Time into normal Python time. Put now() as a last resource
			try:
				time_value =  datetime.strptime(timestamp,OS_CEILOMETER_TIME_FORMAT)
			except:
				try:
					time_value =  datetime.strptime(timestamp,OS_CEILOMETER_TIME_FORMAT_USEC)
				except:
					time_value = datetime.now()
			
			if minTimeStampValue > time_value:
				minTimeStampValue = time_value
			
			# Now we calculate the time to start measuring; = last sample - X hours
			delta = timedelta(hours = durationHours)
			time_value = time_value - delta
			timestamp = time_value.strftime(OS_CEILOMETER_TIME_FORMAT)
			
			logger.debug(Messages.CollectSamples_S_since_S % (m,str(timestamp)))
			
			# Now we build the stats query to use only the last X hours; make a single value and use MIN/MAX/AVG
			query = []
			query.append({"field": "timestamp", "op": "gt", "value": timestamp})
					
			
			stats_set = self.Ceil.statistics.list( meter_name = m, q = query, period = CEILOMETER_PERIOD ,  groupby="project_id") 			
			
			#Building a list with the values
			values_list = []
			for data in stats_set:
				values_list.append(data.sum)
			
			#logger.debug( values_list )
			##Now we do the MIN/MAX/AVG on the aggregated data
			meter.values[m] = Stats(unit=stats_set[0].unit,**MinMaxAvg(values_list)) 
			# The values for the meter m have been read; next!
			logger.debug( Messages.Meter_Stats_minD_maxD_avgD % (meter.values[m]._min,meter.values[m]._max,meter.values[m]._avg) )
		#endfor
		meter.sampletime = str(minTimeStampValue)		
		## The oldest sample timestamp is used as a representative of the complete metric. 
		return meter
	#enddef
#endclass

class Limits(object):
	""" 
		Class representing the absolute values that a Tenant has in a Nova Api. This is to avoid using the awful OpenStack AbsoluteLimit class
		
		> nova quota-show
		> nova quota-default
		
	"""
	def __init__(self, curCPU = 0, maxCPU = 0, curRAM = 0, maxRAM = 0, curInstances= 0, maxInstances= 0):
		self.curCPU = curCPU
		self.maxCPU = maxCPU
		self.curRAM = curRAM
		self.maxRAM = maxRAM
		self.curInstances = curInstances
		self.maxInstances = maxInstances
	#enddef
#endclass

def MinMaxAvg(data):
	"""
		Given a list of values, the MIN/MAX/AVG value is returned in a Dictionary
		
		:param data: List of data of the same kind
		:type data: int[] or float[]
		
		:returns: a dictionary { 'min':min,'max':max,'avg':average }
		:rtype: dictionary
		
		.. seealso:: Stats
		
	"""
	
	min_val = data[0]
	max_val = data[0]
	acc_val = 0
	count = 0
	for d in data:
		if (d < min_val ): min_val= d
		if (d > max_val ): max_val= d
		acc_val = acc_val + d
		count = count+1
	return { 'min':min_val,'max':max_val,'avg':acc_val/count }

#enddef
	
class Stats(object):
	"""
		Class that wraps a statistical metric
		
		Each metric item is composed of 3 values taken from OpenStack Ceilometer (min,max,avg) and the units in which it is measured (unit)
		
		The Stats objects holds this values in a single object; with properties .unit ._min, ._max, ._avg
		The *_* is used to avoid confussions with the methods min() max()
		
		.. seealso:: MinMaxAvg
			
	"""
	def __init__(self,max=0,min=0,avg=0,unit=""):
		self._min = min
		self._max = max
		self._avg = avg
		self.unit = unit
	#enddef
		
#endclass

class Meter(object):
	""" 
		Class representing the metrics values that a Tenant has in a Ceilometer Api. 
		This is to avoid using the awful OpenStack Meter class
		
			> ceilometer meter-list
			> ceilometer statistics -m <meter>
		
		Inside the class; there is a dictionary of the Stats to pull from Ceilometer, and the sampletime attribute (when this metric was taken; in OpenStack time)
		
		Also, this object transforms in a dictionary that is compatible with the Metrics model object
		
		.. seealso:: DataModels.py
		
	"""
	def __init__(self):
		"""
			Starts an empty dictionary of Stats objects, for the desired Meters from OpenStack
			The Dictionary'keys are the text name of the meters in OpenStack
			
			Also, in a String, the timestamp of the metric is kept. 
			It is STRING as to keep the original Ceilometer value and not to mess with it (no calculations are expected with this value)

			.. seealso:: Stats
			
		"""
		# This is an dictionary of meters in the Ceilometer API. 
		# This way; it is easier to map/set what elements are taken from Ceilometer (there are plenty other meters)
		# Also the Stats object unifies the available information for all meters
		
		self.values = { 'network.incoming.bytes':Stats() , 
						'network.outgoing.bytes':Stats() , 
						'network.incoming.bytes.rate':Stats() , 
						'network.outgoing.bytes.rate':Stats(), 
						'cpu_util':Stats(), 
						'disk.root.size':Stats(), 
						'instance':Stats(), 
						'memory':Stats(),
						'vcpus':Stats()
						}
		
		# String value of the Stats timestamp, from Ceilometer API
		self.sampletime = ""
	#enddef

	
	def todict(self):
		"""
			Converts this object into a dictionary compatible with the DB, table Metrics
			
			.. seealso: DataModels.py
			
			This separation DB - Ojects - API is to be flexible on what we take from Ceilometer API, what is stored and how
			
		"""
		K = 1024
		octect = 8
		dictio = {}
		
		dictio["networkInBytes"] 	= self.values["network.incoming.bytes"]._max/K - self.values["network.incoming.bytes"]._min/K
		dictio["networkOutBytes"] 	= self.values["network.outgoing.bytes"]._max/K - self.values["network.outgoing.bytes"]._min/K 
		#dictio["networkBytesUnits"] 	= "kBytes"
		dictio["networkInBps_min"]    = self.values["network.incoming.bytes.rate"]._min*octect/K 	
		dictio["networkInBps_max"]    = self.values["network.incoming.bytes.rate"]._max*octect/K 	
		dictio["networkInBps_avg"]    = self.values["network.incoming.bytes.rate"]._avg*octect/K  	
		dictio["networkOutBps_min"]   = self.values["network.outgoing.bytes.rate"]._min*octect/K  	
		dictio["networkOutBps_max"]   = self.values["network.outgoing.bytes.rate"]._max*octect/K  	
		dictio["networkOutBps_avg"]   = self.values["network.outgoing.bytes.rate"]._avg*octect/K 	
		#dictio["networkBpsUnits"] 	= "kbps"
		dictio["cpuUtil_min"]         = self.values["cpu_util"]._min 		
		dictio["cpuUtil_max"]         = self.values["cpu_util"]._max 		
		dictio["cpuUtil_avg"]        = self.values["cpu_util"]._avg		
		#dictio["cpuUtilUnits"] 	= "%"
		dictio["diskrootsize_min"]    = self.values["disk.root.size"]._min 	
		dictio["diskrootsize_max"]    = self.values["disk.root.size"]._max 	
		dictio["diskrootsize_avg"]    = self.values["disk.root.size"]._avg 	
		#dictio["diskrootsizeUnits"]    = "GBytes"
		dictio["instance_min"]        = self.values["instance"]._min 		
		dictio["instance_max"]        = self.values["instance"]._max 		
		dictio["instance_avg"]        = self.values["instance"]._avg 		
		#dictio["instanceUnits"]		= "units"
		dictio["memory_min"]         =  self.values["memory"]._min 		
		dictio["memory_max"]         = self.values["memory"]._max			
		dictio["memory_avg"]         = self.values["memory"]._avg
		#dictio["memoryUnits"]		= "MBytes"
		dictio["vcpu_min"]         =  self.values["vcpus"]._min 		
		dictio["vcpu_max"]         = self.values["vcpus"]._max			
		dictio["vcpu_avg"]         = self.values["vcpus"]._avg
		#dictio["vcpuUnits"]		= "units"
		
		return dictio
	#enddef
#endclass


class ServerMetadata(object):
	"""
		These are the common parameters of a Server in the infrastructure
		
		This metadata is used for cloning VMs
		
		This assumes that all OpenStack controllers are uniform, having the same Flavors, Images, NetworkNames and SecurityGroups
		
	"""
	
	name = ""
	imageName = ""
	flavorName = ""
	NetworkName = [""]
	SecurityGroups = [""]
	floating_ip = False
	
	def __init__(self,name="",imageName = "", flavorName="",NetworkNames=[],SecurityGroups=[], floating_ip = False):
		self.name = name
		self.imageName = imageName
		self.flavorName = flavorName
		self.NetworkNames = NetworkNames
		self.SecurityGroups = SecurityGroups
		self.floating_ip = floating_ip
	
	def to_dict(self):
		
		d = dict()
		d['name'] = self.name
		d['imageName'] = self.imageName
		d['flavorName'] = self.flavorName
		d['nets'] = [ s for s in self.NetworkNames]
		d['secGroups'] = [ s for s in self.SecurityGroups ]
		d['floatingIp'] =  self.floating_ip
		
		
		return d
