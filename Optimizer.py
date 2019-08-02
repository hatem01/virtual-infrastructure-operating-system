
""" 
vCDN Infrastructure Optimization Controller
=======================================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

This is the main controller of OMAC demo

..note:: When updating the items in the DB, do not set the date/time by localfunctions; Let the DB handle all timestamps using ONUPDATE and DEFAULT

All messages and logs are in Messages.py. This is to make it easy to change languages and to have unified messages

For  DB operations, mostly queries and listing, destroy the objects after use with del ARRAY[:] and end the Transaction with DBConn.endTransaction() 
For  DB modifications, update/add/deletes queries, end the Transaction with DBConn.endTransaction() before moving to another Query o listing

.. seealso:: DataModels.py Messages.py
	
	
	This version includes a Demand BW adjustment mechanism that follows an exponential law, and is representative of the Operator's Infrastructure as a whole

:Example:

	connect( db_url ) # Connect to the DB
	
	createRandomInfrastructure()  #Create a random topology and build a model
	buildModel()
	
	updatePOPs()   # update the latest OpenStack data
	updateMetris()
	
	createRandomDemands()  # Create a Random set of Demands and optimize based on them
	consumeDemands()
	optimize()
	
	simulate()  # Simulate the impact on the Infrastructure of the selected changes
	
"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from random import random, seed			
#Used to randomize the Demands and the Infrastructure
import time								
#Used to calculate the time of decision making
import logging

import os

import thread
# Use to have the OpenStack operations on separate Threads

from  DataModels import Hypervisor,Flavor,Instance, Metric, Demand, Demand
import Messages
import DBConnection 
import OpenStackConnection as OpenStack
from OpenStackConnection import ServerMetadata
from OptimizationModels import Model, FakeDemand, FakeInstance, FakeRedirect, Random, NCUPM
import SettingsFile


logger = logging.getLogger(__name__)

# Options read from the Config File somewhere else
# These options are read from the config file and are expected to be overriden

meterDurationHours = 6
"""Default 6 hours to sample Metrics on the Telemetry"""
demandProbability = 0.5			
"""Default probability of a client v demand a vcdn f. Values in the range [0,1]"""
demandAmplitude = 100.0				
"""Maximum value for a Demand bw, in Mbps. Values > 0"""

IMG_FOLDER = "/tmp"
""" Local folder used for Snapshot Migration """

_MAX_QoE = 5
""" Maximum MOS value for the Quality of Experience """
_MIN_QoE = 1
""" Maximum MOS value for the Quality of Experience """

operatorQoE = _MAX_QoE
"""	Global value used for the Operator to reduce the BW for all demands according to an Exponential law """



INI_Section = "openstack" 
""" This is the INI file section where we expect to find our values"""


DBConn = None
""" 
	Object holding the connection to the Database
	:type DBConn: DBConnection class
"""


OptimizationModel = None
""" Object holding the connection to the HMAC Model for the calculations to take place
	:type HMAC class
"""

def readSettingsFile():
	"""
		This function asks the INI file parser module, that must have read the INI file, to look for the options in the sections and variables that are of interest for this module.
		
		If the options are not present in the INI file, the existing values are not modified
		
		This is so that we add or remove options from the INI file just by mofiying this functions. Also, the same INI entry can be read by many modules
		
		.. note:: Make sure that the SettingsFile module has been initialized and read a valid file
		
		::Example::
			SettingsFile.read(INI_file)
			Optimizer.readSettingsFile()
		
	"""
	global demandProbability
	global demandAmplitude
	global meterDurationHours
	global IMG_FOLDER
		
	if SettingsFile.getOptionFloat("DEFAULT","demand_probability"):
		demandProbability = SettingsFile.getOptionFloat(INI_Section,"demand_probability")
	if SettingsFile.getOptionFloat("DEFAULT","demand_amplitude"):
		demandAmplitude = SettingsFile.getOptionFloat(INI_Section,"demand_amplitude")
	if SettingsFile.getOptionInt("DEFAULT","sample_period_hours"):
		meterDurationHours = SettingsFile.getOptionInt(INI_Section,"sample_period_hours")
	if SettingsFile.getOptionFloat(INI_Section,"local_tmp_dir"):
		IMG_FOLDER = SettingsFile.getOptionInt(INI_Section,"local_tmp_dir")
	
#enddef

def connect(url):
	""" 
	Connects to the provided DB String
	
		:param url is a sqlalchemy string, just like the ones in nova.conf [database]
		:type url String
		
		:returns: True if connection OK, False if not
	"""
	global DBConn	
	logger.debug(Messages.ConnectDB_S % url)
	DBConn = DBConnection.DBConnection(url)
	return DBConn.connect()
#enddef

def consumeDemands():
	"""
		Gets the Demands from the Database and, one by one; removes the Demanded BW from the Capacity Graph of the Model
		
		Invalid demands are ignored. Demands that request a pair (vCDN,POP) that does not exist are IGNORED. 
		
		A new model is created here, taking fresh information from the DB. This is because the Operator can be working on the Demands, alters or receives a change it the Topologie information (clientGroups, Locations, NetLinks, POPs, etc)
		and would like to re-run the Demands on top. So a new fresh Model is needed in this case to include the possible backend changes
		
		..seealso:: OptimizationModel.consumeDemands()
		
		:returns:  True if all OK; False if there were some errors
				
	"""
	
	ret = True
	
	## Start from a Fresh model from the DB information
	if buildModel():
		try:
			DBConn.start()
			
			demandsList = DBConn.getDemands()
			
			logger.info(Messages.Consuming_Demands)
			
			if (demandsList):
				for d in demandsList[:]:
					
					# Check Valid demands, invalids are removed
					instance = getInstanceforDemand(d)
					if  instance == None:
						demandsList.remove(d)
						logger.error(Messages.Invalid_Demand_Client_S_vCDN_S_POP_S % (d.clientGroup.name, d.vcdn.name, d.pop.name ))
					
				#endfor
			
				return OptimizationModel.consumeDemands(demandsList)
			
			#endif
		except:
			logger.exception(Messages.Exception_optimizing)
			return False
		finally:
			del demandsList[:]
			DBConn.cancelChanges()
			DBConn.end()
	else:
		logger.error(Messages.NoModel)
		return False
#enddef

def createRandomInfrastructure():
	""" 
		Updates values from the Infrastructure, non-OpenStack
	
		These values are parameters set by the Operator and its systems, in the production case.
		In this DEMO, this is a fake function to generate values and put them in the OMAC DB.
		
		Changes produced: ClientGroups.location and NetworkLinks table are shuffled ar random
		
		:returns:  True if all ok; False if there were some errors
		
		This is done by mapping the Model to a Random Tree graph
		
	"""
	
	#.. warning:: It has proven difficult to shuffle the POPs.location field, to move the POPs randomly. Even if we do a full shuffle and avoid repetitions, because of the constraint UNIQUE(POP.location); when the table is being updated it can happen that for an instant the location is duplicated. 
	#This triggers an error, the proper way would be to add a dummy location to start using is as a token for swapings locations.... or to remove the lock of Unique location.
	
	logger.info(Messages.Consuming_Demands)
	DBConn.start()
	LocationList = DBConn.getLocations()
	if (LocationList):
		try:
			# Make a random Graph with the locations in DB, and get the Links in the graph
			# The Location objects are linked to the Graph, do not delete them
			
			erg = Random(LocationList)
			
			
			linksList = erg.getLinkList()
			
			# Clear all the Network links, and take them from the ER Graph
			for nl in DBConn.getNetworkLinks():
				DBConn.drop(nl)
			DBConn.applyChanges()
			
			for nl in linksList:
				DBConn.add(nl)
			DBConn.applyChanges()

			logger.info(Messages.Updated_NetworkLinks)
			
			# Assign the ClientGroup locations at will, only on the access layer
			borderLocations = erg.getAccessLocations()
			clients = DBConn.getClientGroups()
			for c in clients:
				index = int(random() * len(borderLocations))
				c.locationId = borderLocations[ index].id
			#endfor
			DBConn.applyChanges()
			
			logger.info(Messages.Updated_ClientLocations)
			return True
		except:
			logger.exception( Messages.Exception_updating_Infrastructure)
			DBConn.cancelChanges()
			return False
	else:
		logger.error( Messages.No_Locations)
		return False
	DBConn.end()
	
#enddef


def createRandomDemands():
	""" 
		Updates values from the Demand registers, non-OpenStack.
		These values are parameters set by the Operator and its systems.
		
		In this DEMO, this is a fake function to generate values and put them in the OMAC DB.
		
		A demand, in OMAC paper; is said to be d[v][f], but as only 1 server is to supply this demand, and q vCDN can be in more than 1 server, this leads to associate a demand to an Instance, which is 1 server that holds a vCDN inside
		
		The Demands are created via a random number and a threshold
		For all Clients and all Instances: There is a demand if a random probability is bigger than 'demandProbability' value.
		If so, the bw of the demand is set in the range of values [0 ; demandAmplitude] aproximately.
		
		:returns:  True if all ok; False if there were some errors.
		
	"""
	global operatorQoE
	
	logger.info(Messages.Create_Random_Demands)
	
	try:
		
		DBConn.start()
		
		# Get all instances of all Instances. Get all clientGroups
		vCDNList = DBConn.getvCDNs()
		ClientGroupList = DBConn.getClientGroups()
		
		if vCDNList  and ClientGroupList  :
			
			logger.debug(Messages.CreatingRandomDemands_D_probaF_amplitudeD % (len(vCDNList) *len(ClientGroupList),demandProbability,demandAmplitude))
			
			# Remove all Demands.
			demands = DBConn.getDemands()
			if demands:
				for d in demands:
					DBConn.drop(d)
				DBConn.applyChanges()
				
				logger.info(Messages.Deleted_Demands)
			
			# Make random associations
			accum = 0
			for v in vCDNList:
				seed()
				
				for clientGroup in ClientGroupList:
					rnd = random()
					instancesList = v.instances
					if instancesList:
						for i in instancesList:
							if rnd < demandProbability:
								d = Demand(clientGroupId = clientGroup.id, 
											popId = i.popId,vcdnId=i.vcdnId, 
											volume =  (demandProbability - rnd) * 2 * 100, 
											bw =  (demandProbability - rnd) * 2 * demandAmplitude 
											)  
								
								
								# (demandProbability - rnd) gives a number  in the interval [0,demandProbability]; demandProbability < 1
								# (demandProbability - rnd) * 2 * demandAmplitude gives a number in the desired range
								DBConn.add(d)
								accum = accum+1
								break
							#endif
						#endfor
					#endif
				#endfor
			
			# Update DB
			DBConn.applyChanges()
				
			logger.info(Messages.Created_D_Demands % accum )
		
		else:
			logger.error( Messages.NoInstances)
			return False
		#endif
		
		DBConn.end()
		operatorQoE = _MAX_QoE
		return True
		
	except:
		logger.exception( Messages.Exception_updating_Demand)
		DBConn.end()
		return False
#enddef



def simulate( migrationList = [],redirectList = [], instantiationList = []):
	"""
		This functions simulates that the Migrations/Redirections/Instantiations were actually executed; changed the Data in the Systems and would be reflected as changes in the Model
		
		This procedure starts from a new Model, having fresh Topologie information from the DB.
		
		Then the requested changes are simulated, altering the list of Instances in the Model, and also altering the list of Demands. 
		This is because the simulation suposes that the CDN system performs all the needed changes so that the Demands will point to where the vCDN were Migrated or Instantiated or Redirected.
		So the Model now works on a simulated list of Instances and updated Demands
		
		Then the Model is asked to check the representation of the number of Instances, from the new list of simulated instances
		
		The simulated Demands are checked against the simulated list of Instances; as the moving of Instances could have caused some Demands to now become invalid
		
		Finally, the Model is asked to consume the simulated list of Demands to have an updated Gomory-Hu Tree of remaining capacity. Hopefully, a better scenario that the original
		
		All simulated objects and elements are deleted, the DB is not altered in any way
		
		
		:param migrationsList: List of Migrations to execute
		:type migrationsList: HmacResult[]
		:param redirectsList: List of Redirects to execute
		:type redirectsList: Redirect[]
		:param invalidDemandList: List of Demands to instantiate
		:type invalidDemandList: Demands[]
		
		:returns:  FakeRedirect[] or None
		
		..note:: This function updates/Changes the Model's Gomory-Hu Tree.
				
	"""
	
	global DBConn
	global Model
	
	logger.info(Messages.Simulating_Migrations) 
	
	try:
		
		# Build model, first
		buildModel()
		
		DBConn.start()
		realInstances = DBConn.getInstanceList()
		realDemands = DBConn.getDemands()
		
		fakeInstances = []
		fakeDemands = []
		fakeRedirects = []
		
		
		for i in realInstances:
			fakeInstances.append( FakeInstance( popName = i.pop.name, 
														popId = i.popId, 
														vcdnName = i.vcdn.name , 
														vcdnId = i.vcdnId ,
														popLocationName = i.pop.location.name)
								)
		for d in realDemands:
			fakeDemands.append(	FakeDemand(clientGroupLocationName = d.clientGroup.location.name, 
													clientGroupName = d.clientGroup.name,
													clientGroupId = d.clientGroupId,
													popLocationName = d.pop.location.name,
													popName = d.pop.name, 
													popId = d.popId, 
													vcdnName = d.vcdn.name , 
													vcdnId = d.vcdnId,
													volume = d.volume,
													bw=d.bw)
								)
		
		#Delete all the Objects not to affect the DB, as this is a simulations and the DB should not change
		
		del realInstances[:]
		del realDemands[:]
		DBConn.cancelChanges()
		DBConn.end()
		
		
		# Place new fake instances where needed, from Migrations and Instantiations
		# Get the Demands and adjust the targets to go to the Redirected/Migrated/Instantiated
		
		logger.info(Messages.Adjusting_Instances_Demands) 
		
		for m in migrationList:
			
			logger.debug(Messages.Simulate_Migration_vCDN_S_from_POP_S_to_POP_S % (m.instance.vcdn.name, m.instance.pop.name, m.dstPop.name))
			
			#found = False
			for f in fakeInstances[:]:
				if m.instance.vcdnId  == f.vcdnId and m.instance.popId == f.popId:
					#found = True
					fakeInstances.remove(f)
					logger.debug(Messages.Deleted_Fake_Instace_POP_S_vCDN_S % (m.instance.pop.name, m.instance.vcdn.name))
								
					newInstance = FakeInstance(  popName = m.dstPop.name, 
													popId = m.dstPopId , 
													popLocationName = m.dstPop.location.name,
													vcdnName = m.instance.vcdn.name , 
													vcdnId = m.instance.vcdnId
												)
					
					if newInstance not in fakeInstances:
						fakeInstances.append(newInstance)
						logger.debug(Messages.Added_Fake_Instace_POP_S_vCDN_S % (m.dstPop.name, m.instance.vcdn.name))
					else:
						del newInstance
					break
				#endif
			#endfor
			for fd in fakeDemands:
				if fd.vcdnId == m.instance.vcdnId and fd.popId == m.instance.popId:
					
					logger.debug(Messages.Update_Fake_Demand_fromPOP_S_toPOP_S % (fd.popName, m.dstPop.name) )
					
					fakeRedirects.append( FakeRedirect (
											fd, dstPopId = m.dstPopId, dstPopName = m.dstPop.name
											)
					 )
										
					fd.popId  = m.dstPopId
					fd.popName = m.dstPop.name
					fd.popLocationName = m.dstPop.location.name
						
			#endfor
		#endfor
		
		for r in redirectList:
			logger.debug(Messages.Simulate_Redirection_vCDN_S_from_POP_S_to_POP_S % (r.demand.vcdn.name, r.demand.pop.name, r.dstPop.name))
			for f in fakeDemands:
				if f.vcdnId == r.demand.vcdnId and f.popId == r.demand.popId and f.clientGroupName == r.demand.clientGroup.name and f.clientGroupLocationName == r.demand.clientGroup.location.name :
					
					logger.debug(Messages.Update_Fake_Demand_fromPOP_S_toPOP_S % (f.popName, r.dstPop.name) )
					
					fakeRedirects.append( FakeRedirect (
											f, dstPopId = r.dstPopId, dstPopName = r.dstPop.name
											)
					 )
					 
					f.popId  = r.dstPopId
					f.popName = r.dstPop.name
					f.popLocationName = r.dstPop.location.name
			#endfor
		#endfor
			
		for i in instantiationList:
			
			logger.debug(Messages.Simulate_Instantiation_vCDN_S_on_POP_S % (i.vcdn.name, i.pop.name))
			
			newInstance = FakeInstance(vcdnId = i.vcdnId , 
										popId = i.popId, 
										vcdnName = i.vcdn.name, 
										popName = i.pop.name ,
										popLocationName = i.pop.location.name)
			
			if newInstance not in fakeInstances:
				fakeInstances.append(newInstance)
				logger.debug(Messages.Added_Fake_Instace_POP_S_vCDN_S % (newInstance.popName, newInstance.vcdnName))
			else:
				del newInstance
			
			fd = FakeDemand(clientGroupLocationName = i.clientGroup.location.name, 
													clientGroupName = i.clientGroup.name,
													clientGroupId = i.clientGroupId,
													popLocationName = i.pop.location.name,
													popName = i.pop.name, 
													popId = i.popId, 
													vcdnName = i.vcdn.name , 
													vcdnId = i.vcdnId,
													volume = i.volume,
													bw=v.bw)
													
			fakeRedirects.append( FakeRedirect (
											fd, dstPopId = fd.popId, dstPopName = fd.popName
											)
								)
					 
		#endfor
		
		logger.info(Messages.Adjusting_Model) 
		
		#Adjust the POPs Sizes according to the new list of Instances after all the chagnes
		OptimizationModel.updateFakeInstances(fakeInstances)
		
		# Check Valid demands compared to the Instances after all the changes, invalids are removed
		for d in fakeDemands[:]:
			match = False
			for f in fakeInstances:
				if  d.vcdnId == f.vcdnId and d.popId == f.popId:
					match=True
					break
			#endfor
			if not match:
				fakeDemands.remove(d)
				
				logger.debug(Messages.Invalid_Demand_Client_S_vCDN_S_POP_S % (d.clientGroupLocationName, d.vcdnName, d.popName))
				
				d.vcdnName=""
				d.popName=""
		
		logger.info(Messages.Running_Demands)
		
		# Do consume the adjusted Demands
		OptimizationModel.consumeFakeDemands(fakeDemands)
			
		del fakeInstances[:]
		del fakeDemands[:]
		
	except:
		logger.exception(Messages.Exception_Simulating)
		return None
	# Done, the Gomory-Hu Tree and the Capacity can be drawn
	return fakeRedirects
	
	#enddef
	

def getInstanceforDemand(d):
	"""
		For a given Demand d, requesting a vCDN from a POP, this function checks if effectively there is any Instance of the vCDN in that POP
		
		:param d: demand to check for a valid Instance
		:type d: Demand
		
		:returns:   the Instance object or None if not found
		:rtype: Instance or None

	"""
	return DBConn.getInstanceOf(vcdnId = d.vcdnId, popId = d.popId )
#enddef

def getInstance(pop,vcdn):
	"""
		For a given POP and a vCDN, this function retuns the Instance of them both, if it exists
		
		:param pop: POP to check for a valid Instance
		:type pop: POP
		:param vcdn: vCDN to check for a valid Instance
		:type vcdn: vCDN
		
		:returns:   the Instance object or None if not found
		:rtype: Instance or None

	"""
	return DBConn.getInstanceOf(vcdnId = vcdn.id, popId = pop.id )
#enddef

#enddef

def updatePOPs():
	""" Reads values of the OpenStack APIs for the POPs
	
		With the login provided in the POP ( the provided user must have "admin" access)
			It updates the Hypervisors table, adding if new hypervisors are found. The total POP capacity values are the sum of all its hypervisors
			It updates the Flavors table, only with the Public Flavors (as Tenants should use these flavors). Only rootDisk information is captured
		
		With the login provided for each vCDN, a user with "_member_" access to the Tenant:
			It updates the limits found for the Tenant in the POPs
			It updates the number of instances for the Tenant in the POPs
						
		:returns:  True is all the POPs were updated; False if any of the POPs failed
			
	"""
	global DBConn
	
	
	_errors = False
	
	logger.info(Messages.Updating_OpenStack)
	
	OSMan = OpenStack.APIConnection()
	
	DBConn.start()
	
	popList = DBConn.getPOPList()
	if (popList):
		for pop in popList:
			OSMan.disconnect()
			
			OSMan.setURL(pop.url,pop.region)
			
			OSMan.setCredentials(pop.tenant,pop.loginUser,pop.loginPass)
			if not OSMan.connect():
				logger.error(Messages.NoConnect_Pop_S % pop.name)
				_errors = True
				continue
				#Not connect, log error and continue to NEXT POP
			
			#These are the accumulated values through the Hypervisors in the POP. The POP has resources equal to the sum of its Hypervisors
			found = False
			hyperDB = None
			accumCurCPU =0
			accumCurRAM =0
			accumCurDisk=0
			accumInstances =0
			accumMaxCPU =0
			accumMaxRAM =0
			accumMaxDisk =0
			
			
			
			try:
				for hyper in OSMan.getHypervisors():
					# First we see if there is alreay a Hypervisor entry for this POP in the DB. If there is not, we will create this new Hypervisor
					for hyperDB in pop.hypervisors:		
						if (hyperDB.name == hyper.hypervisor_hostname):		
							found=True
							break
					#endfor
					if not found:
						hyperDB = Hypervisor(hyper.hypervisor_hostname, pop.id)
						logger.debug(Messages.Created_Hypervisor_S_POP_S % (hyperDB.name,pop.name))
						DBConn.add(hyperDB)
						
					
					DBConn.applyChanges()
					
					#Update existing values	and increasing the counter for POP resources

					hyperDB.model = hyper.hypervisor_type
					accumCurCPU += hyper.vcpus_used
					accumCurRAM += hyper.memory_mb_used
					accumCurDisk += hyper.local_gb_used
					accumInstances += hyper.running_vms
					accumMaxCPU += hyper.vcpus
					accumMaxRAM += hyper.memory_mb
					accumMaxDisk += hyper.local_gb
					
					hyperDB.updateMaxValues (cpu = hyper.vcpus, ram = hyper.memory_mb, disk = hyper.local_gb)
					hyperDB.updateCurValues (cpu = hyper.vcpus_used, ram = hyper.memory_mb_used, disk = hyper.local_gb_used, instances= hyper.running_vms)
					
					logger.debug(Messages.Updated_Hypervisor_S_POP_S % ( hyperDB.name , pop.name))
					
					#As we have updated the Hypervisor in hyperDB, we must make this change permanent, by flushing the Session, before getting the next Hypervisor
					DBConn.applyChanges()
					
				#endfor
			
			except:
				logger.exception(Messages.Exception_Update_Hypervisor_S_POP_S % ( hyperDB.name , pop.name))
				_errors = True
				
			found=False
			flavorDB = None
			try:
				for flav in OSMan.getPublicFlavors():
					# First we see if there is alreay a Flavor entry for this POP in the DB. If there is not, we will create this new Flavor
					for flavorDB in pop.flavors:		
						if (flavorDB.osId == flav.id):		
							found=True
							break
					#endfor
					if not found:
						flavorDB = Flavor(flav.name, flav.id, pop.id)
						#flavorDB.created_at = datetime.
						logger.debug(Messages.Created_Flavor_S_POP_S % (flav.name,pop.name))
						DBConn.add(flavorDB)
					
					
					#Update existing values	 
					flavorDB.updateValues (name = flav.name,cpu = flav.vcpus, ram = flav.ram, disk = flav.disk, isPublic = True)
					logger.debug(Messages.Updated_Flavor_S_POP_S % ( flav.name , pop.name))
					
				#endfor
				DBConn.applyChanges()
			except:
				_errors = True
				logger.exception(Messages.Exception_Update_Flavor_S_POP_S % ( flav.name , pop.name))
				
				
			#Update existing values	 
			pop.updateMaxValues (cpu = accumMaxCPU, ram = accumMaxRAM, disk = accumMaxDisk , netBW = pop.totalNetBW)
			pop.updateCurValues (cpu = accumCurCPU, ram = accumCurRAM, disk = accumCurDisk, instances = accumInstances, netBW = 0)
		
			DBConn.applyChanges()
			# End of operations with AdminLogin
			
			logger.info(Messages.Updated_Pop_S % pop.name)
			
			### Starting operations with Tenant Login ###
			found=False
			InstanceDB = None
			
			vCDNList = DBConn.getvCDNs()
			
			
			if (vCDNList):
				for vcdn in vCDNList:
					try:
						OSMan.disconnect()
						OSMan.setCredentials(vcdn.tenant,vcdn.loginUser,vcdn.loginPass)
						if not OSMan.connect() or OSMan.getLimits()==None:
							logger.error(Messages.NoConnect_Pop_S % pop.name)
							_errors = True
							continue
							### Next tenant tries to login
						
						
						lim = OSMan.getLimits()
						
						found=False
						for InstanceDB in vcdn.instances:
							if (InstanceDB.popId == pop.id):
								found=True
								logger.debug(Messages.Found_Instance_S_at_POP_S_LimitsInstances_D % ( vcdn.name ,InstanceDB.pop.name,lim.curInstances))
								break
						#endfor
						
						
						
						if found and lim.curInstances ==0:		
							# There is an instance in the DB but not in the OpenStack, so it is deleted
							DBConn.drop(InstanceDB.metric)
							DBConn.drop(InstanceDB)
							logger.debug( Messages.Deleted_Instance_S_at_POP_S % (vcdn.name , pop.name))
							continue  
							 ### Next tenant tries to login
						elif not found and lim.curInstances > 0: 		
							# There no not an instance in the DB but it is in the OpenStack, so it is added
							InstanceDB = Instance(vcdn.id, pop.id)
							DBConn.add(InstanceDB)
							InstanceDB.updateMaxValues (cpu = lim.maxCPU, ram = lim.maxRAM, instances = lim.maxInstances)
							InstanceDB.updateCurValues (cpu = lim.curCPU, ram = lim.curRAM, instances = lim.curInstances)
							
							logger.debug(Messages.Added_Instance_S_at_POP_S % (vcdn.name, pop.name))
						elif found and lim.curInstances > 0:
							#Update existing values
							InstanceDB.updateMaxValues (cpu = lim.maxCPU, ram = lim.maxRAM, instances = lim.maxInstances)
							InstanceDB.updateCurValues (cpu = lim.curCPU, ram = lim.curRAM, instances = lim.curInstances)
							
							logger.debug( Messages.Updated_Instance_S_at_POP_S % (vcdn.name, pop.name))
						
						DBConn.applyChanges()	
						
					except:
						_errors = True
						logger.exception(Messages.Exception_Update_vCDN_S_POP_S % ( vcdn.name , pop.name))
						DBConn.cancelChanges()
						continue
				#endfor
			#endif 
				
			# End of operations with Tenant Login
			logger.info(Messages.Updated_Tenants_Pop_S % pop.name)
			
		#endfor
		DBConn.applyChanges()
	#endif
	DBConn.end()
	return not _errors
#enddef



def updateMetrics():
	""" Reads values of the OpenStack Telemetry APIs for all the Instances
		With the login provided for each vCDN, a user with "member" access to the Tenant and read access to Telemetry
		
		Better if executed after updatePOPs() to have up-to-date Instance information
			
		Starts looking for all Instances in a POP. 
			For this instance, the vCDN credentials are used to access the Telemetry of the vCDN
			The Metrics are updated for this Instance. If there is no Metrics, the next Instance in the loop is taken
			If the vCDN credentials do not login to the Telemetry, the next Instance is the look is taken
		
		Finished once checked all the POPs
		
		:returns:  True is all the POPs were updated; False if any of the POPs failed
		
	"""
	global DBConn
	
	global meterDurationHours			
	#Parameter read from config file
	
	_errors = False 
	
	logger.info(Messages.Updating_OpenStack_Metrics)
	
	OSMan = OpenStack.APIConnection()
	
	DBConn.start()
	
	popList = DBConn.getPOPList()
	
	if (popList):
		for pop in popList:
			
			PopCurNetBW = 0	
			## Summing all the curNetBW of all the instances in the POP gives the current BW used in the POP
			
			instanceList = pop.instances
			if (instanceList is not None) and (instanceList ):
				for i in instanceList:
					# Starting operations with to check the metrics of this instance
					OSMan.disconnect()
					OSMan.setURL(pop.url,pop.region)
					OSMan.setCredentials(i.vcdn.tenant,i.vcdn.loginUser,i.vcdn.loginPass)
					if not OSMan.connectMetrics():
						logger.error(Messages.NoConnect_Pop_S % pop.name)
						_errors = True
						continue
						### Next Instace tries to login
					
					logger.debug( Messages.Getting_Metric_Pop_D_tenant_S % (pop.name,i.vcdn.name))
					
					meter = OSMan.getMetrics(meterDurationHours)
						
					#try:
					metricDB = None
					metricDB = i.metric
					if metricDB == None or metricDB==[]:  
						#There are no metrics created for this instance, lets make one
						metricDB = Metric(i.id)
						DBConn.add(metricDB)
						logger.debug( Messages.Added_Metric_Instance_D % i.id)
					#except:
						#logger.error(Messages.ERROR_Update_DB_Metric )
						#continue  #Next Instance
				
					#either way; new or old; update
					metricDB.update(meterDurationHours, meter.sampletime, meter.todict() )
					PopCurNetBW = PopCurNetBW + meter.values["network.outgoing.bytes.rate"]._avg + meter.values["network.incoming.bytes.rate"]._avg
					logger.debug( Messages.Updated_Metric_Instance_D % i.id)
				#endfor
				# End of operations with Tenant Login
				
				
				logger.info( Messages.Updated_Metrics_Pop_S % pop.name )
				logger.info(Messages.Updated__D_OpenStack_Metrics % len(instanceList))
			#endif
			pop.curNetBW = PopCurNetBW / 1024	
			# Because meter.values["network.outgoing.bytes.rate"]._avg is on kbps and pop.curNetBW has to be in Mbps
			
			pop.maxNetBW = pop.totalNetBW	
			#Copy the manual-set value totalNetBW
			
			DBConn.applyChanges()  
			### This updates all the values found for a POP, puts all in the DB
			# if DBConn.endTransaction() is not done here; the Foreign keys POP - Instance - Metric might give errors. Please leave this call here
			

		#endfor
		
	#endif
	
	DBConn.applyChanges()		### This updates all the values left for update
	DBConn.end()
	return not _errors
	
#enddef


def optimize():
	""" 
		Gathers information from the DB and calls optimization with the information.
		
		This optimization is a Heurisitic approach, based on the Demands.
		
		The Global Model is built from fresh information from the DB, this is to include any backend changes made to the Topology or Demands.
		
		This stores the result in the DB
		
		:returns: True if all went ok
		
		.. seealso:: OptimizationModel.optimizeHMAC()
		
	"""
	global Model
	global DBConn
	
	logger.info(Messages.Optimizating)
	
	# This creates a new Model from the DB and passes the Demands to have a remaining capacity Graph
	if consumeDemands():
		
		#Delete the previous HmacResults Entries
		DBConn.start()
		migList = DBConn.getHmacResults()
		if (migList):
			for m in migList:
				DBConn.drop(m)
			DBConn.applyChanges()
			logger.info(Messages.Deleted_Migrations)
		DBConn.end()
		#endif
		
		#Delete the previous AlteredDemands Entries
		DBConn.start()
		altDemandsList = DBConn.getAlteredDemands()
		if (altDemandsList):
			for alt in altDemandsList:
				DBConn.drop(alt)
			DBConn.applyChanges()
			logger.info(Messages.Deleted_Redirections)
		DBConn.end()
		#endif
				
		try:
			
			DBConn.start()
			demands = DBConn.getDemands()
			vcdns =  DBConn.getvCDNs()
			migCostKList =  DBConn.getMigrationCostMultiplierList()
			
			migrationList = None
			invalidDemands = None
			
			if (demands):
				
				
				
				migrationList, alteredDemands  = OptimizationModel.optimizeHMAC(demands)
				
				logger.info(Messages.HMAC_optimized)
					
				#If as a result, there are HmacResults to make, they are written to the DB
				#This is done to Isolate the Modeling only from where and how is the result stored
				
				
				if (migrationList is not None and migrationList ):  
					for m in migrationList:
						DBConn.add(m)
					#DBConn.applyChanges()
				
				if (alteredDemands is not None and alteredDemands ):  
					for alt in alteredDemands:
						DBConn.add(alt)
					#DBConn.applyChanges()
				
				DBConn.applyChanges()
				
				### Update the list of Demands that are affected by a Migration
				### Update the Cost of migrations ###
				 
				for m in migrationList:
					
					migCostMultiplier = DBConn.getMigrationCostMultiplier(m.instance.popId, m.dstPopId)
					
					if migCostMultiplier :
						m.cost = m.cost * migCostMultiplier
						logger.debug(Messages.Updated_MigrationCost_MigrationId_D% (m.id) )
					
					
					for d in m.demandsIds:
					
						demand = DBConn.getDemandById(d)
						if demand:
							demand.hmacResultId = m.id
					
				DBConn.applyChanges()
				
								
				# Add the missing information for the OMAC model
				OptimizationModel.omac.setvCDNs(vcdns)
				OptimizationModel.omac.setMigrationCost(migCostKList)
				OptimizationModel.omac.setDemands(demands)
				
				# Write the .DAT file for OMAC Optimization
				if not OptimizationModel.omac.optimize():
					logger.error(Messages.No_OMAC_Optimize)
				else:
					logger.info(Messages.OMAC_optimized)
					
				
				DBConn.applyChanges()
				
				
				logger.info(Messages.Optimized)
				
				return True
				
			else:
				logger.error(Messages.NoDemands)
				
			DBConn.end()
		except:
			logger.exception(Messages.Exception_optimizing)
			
	else:
		logger.error(Messages.NoModel)
		
	
	return False
#enddef


def buildModel():
	""" 
		Gathers information from the DB and calls creates an HMAC/OMAC Model
		..note:: Call this before optimize()
		
		This resets/rebuils the global object Model
		
		:returns:  True if Model was built; False if not.
		
	"""
	
	global DBConn
	global OptimizationModel
	
	logger.info(Messages.Building_Model) 
	DBConn.start()
	try:
		
		#Build nodes with locations and links
		locations = DBConn.getLocations()
		netLinks = DBConn.getNetworkLinks()
		if (locations and netLinks ):
			OptimizationModel = Model(locations,netLinks)
		else:
			logger.error(Messages.Missing_Elements_to_Build_Model)
			return False  # No model, just quit
		del locations[:] 
		del netLinks[:] 
		DBConn.cancelChanges()
	except:
		logger.exception(Messages.Exception_Building_Model)
		return False
		# No model, just quit. The Global Model remains unchanged

	try:
		#Place POPs in infrastructure
		pops = DBConn.getPOPList()
		if (pops):
			OptimizationModel.setPOPs(pops)
		else:
			logger.error(Messages.NoPOPs)
			# If there were  no POPs; at least the Graphs can be built yet, so we continue
		### DO not call del pops[:]  as these objects are now linked to the Modele's Graphs
		DBConn.cancelChanges()
	except:
		logger.exception(Messages.Exception_Model_POPS)
		return False
	try:
		#Place ClientGroups in infrastructure
		clientGroups = DBConn.getClientGroups()
		if (clientGroups):
			OptimizationModel.setClientGroups(clientGroups)
		else:
			logger.error(Messages.NoClients)
			# If there were  no ClientGroups; at least the Graphs can be built yet, so we continue
		del clientGroups[:]
		DBConn.cancelChanges()
	except:
		logger.exception(Messages.Exception_Model_Clients)
		return False
	
	OptimizationModel.buildGomoryTree()
	DBConn.end()
	
	return True
#enddef


def _migrateInstance(instanceId, dstPopId):
	"""
		Migrates all the VMs from an instance into the Destination POP
		
		:param instanceId: an instance Id to be migrated
		:type instanceId: int
		:param dstPopId: Pop Id where to deploy the VMs
		:type dstPopId: int
	
		The instance and dstPop parameters cannot be None
			
		The Parameter is an Id because this function brings up its own connection to the DB
	"""
	
	
	aDBConn = DBConnection.DBConnection(DBConn.DBString)
	
	
	OSMan = OpenStack.APIConnection()
	DstOSMan = OpenStack.APIConnection()
	
	_errors = False 
	
	aDBConn.start()
	
	instance = aDBConn.getInstanceById(instanceId) 
	dstPop = aDBConn.getPOPbyId(dstPopId) 
			
	vCDN_Name = instance.vcdn.name
	srcPOP_Name = instance.pop.name
	dstPOP_Name = dstPop.name
		
	OSMan.setURL(instance.pop.url,instance.pop.region)
	OSMan.setCredentials(instance.vcdn.tenant,instance.vcdn.loginUser,instance.vcdn.loginPass)
	DstOSMan.setURL(dstPop.url,dstPop.region)
	DstOSMan.setCredentials(instance.vcdn.tenant,instance.vcdn.loginUser,instance.vcdn.loginPass)
					
	logger.info(Messages.Migrating_Instance_vCDN_S_POP_S_POP_S % (vCDN_Name,srcPOP_Name,dstPOP_Name))
	
	del instance
	del dstPop
	aDBConn.cancelChanges()
	aDBConn.end()
	
	if OSMan.connect() and OSMan.connectImages() and DstOSMan.connect() and DstOSMan.connectImages():
		
		for server in OSMan.getServers():
			
			try:
				
				originalServerData = OSMan.serverMetadata(server.id)
				
				if OSMan.isServerReady(server.id):
					server.pause()
					time.sleep(2)
				
				imageId = server.create_image(server.id + "_migration")
				
				logger.debug(Messages.Created_Snapshot_Server_S_POP_S % (server.id,srcPOP_Name) )
				
				OSMan.waitImageReady(imageId)
				
				try:
					server.unpause()
				except:
					logger.error(Messages.NotResumed_Server_S_POP_S % (server.id,srcPOP_Name) )
					pass
					# Not .resume() but unpause()
					
					
				if OSMan.isImageReady(imageId):
					
					
				
					### Download the image ###	
					fullpath = os.path.join(IMG_FOLDER,"%s.tmp" % (server.id + "_migration"))
					if OSMan.getSnapshotImage(imageId,fullpath):
					
						
						logger.debug(Messages.downloadedImageFile_S % (fullpath) )
						
						dstImageId = DstOSMan.putSnapshotImage(server.id + "_migration", fullpath)
						
						if DstOSMan.waitImageReady(dstImageId):
							
							logger.debug(Messages.uploadedImageFile_S % (fullpath) )
								
							originalServerData.imageName = server.id + "_migration"
							
							ServerId = DstOSMan.createServer(originalServerData)
							
							if DstOSMan.waitServerReady(ServerId):
									
								logger.debug(Messages.Created_Server_S_vCDN_S_POP_S % (ServerId,vCDN_Name, dstPOP_Name) )
								
								### Delete original Instance in the src POP
					
								if OSMan.deleteServer(server.id):
									logger.debug(Messages.Deleted_Server_S_POP_S % (server.id,srcPOP_Name) )
								else:
									logger.error(Messages.NotDeleted_Server_S_POP_S % (server.id,srcPOP_Name) )
									
							else:
								#Not able to start the server from the image
								logger.error(Messages.NoServerCreated_vCDN_S_POP_S % (vCDN_Name, dstPOP_Name))
								
							DstOSMan.deleteImage(dstImageId)
								
						else:
							#Not able to upload the image
							logger.error(Messages.NoUpload_ImgFile_S % (fullpath))
					else:
						### problem while downloading the img file ##
						logger.error(Messages.NoDownload_ImgFile_S % (fullpath))
						
					### Delete the local the img file ###
					try:
						os.remove(fullpath)	
					except:
						pass
				
				
				#endif	
				OSMan.deleteImage(imageId)
									
			except:
				logger.exception(Messages.Exception_Migrating_Server_S_POP_S_POP_S % (server.id,srcPOP_Name, dstPOP_Name) )
				continue
		#endfor	
	else:
		logger.error(Messages.NoConnect_Pops)
		return False
	
#enddef


def _cloneInstance(instanceId, dstPopId):
	"""
		Clones all the VMs from an instance into the Destination POP
		
		There is no actual migration or copy, a exact copy of the current VMs is built (if possible) on the destination POP
		
		:param instance: a Valid instance to be migrated
		:type instance: int
		:param dstPop: Pop where to deploy the VMs
		:type dstPop: int
	
		The instance and dstPop parameters cannot be None
		
		The Parameter is an Id because this function brings up its own connection to the DB
			
	"""
	
	aDBConn = DBConnection.DBConnection(DBConn.DBString)
	
	
	OSMan = OpenStack.APIConnection()
	DstOSMan = OpenStack.APIConnection()
	
	_errors = False 
	
	aDBConn.start()
	
	instance = aDBConn.getInstanceById(instanceId) 
	dstPop = aDBConn.getPOPbyId(dstPopId) 
			
	vCDN_Name = instance.vcdn.name
	srcPOP_Name = instance.pop.name
	dstPOP_Name = dstPop.name
		
	OSMan.setURL(instance.pop.url,instance.pop.region)
	OSMan.setCredentials(instance.vcdn.tenant,instance.vcdn.loginUser,instance.vcdn.loginPass)
	DstOSMan.setURL(dstPop.url,dstPop.region)
	DstOSMan.setCredentials(instance.vcdn.tenant,instance.vcdn.loginUser,instance.vcdn.loginPass)
					
	logger.info(Messages.Migrating_Instance_vCDN_S_POP_S_POP_S % (vCDN_Name,srcPOP_Name,dstPOP_Name))
	
	del instance
	del dstPop
	aDBConn.cancelChanges()
	aDBConn.end()
	
	if OSMan.connect() and DstOSMan.connect() :
		
		for server in OSMan.getServers():
			
			try:
				
				originalServerData = OSMan.serverMetadata(server.id)
				
				logger.info(Messages.Migrating_Server_S_vCDN_S_POP_S % (server.id,vCDN_Name,srcPOP_Name))
				
				ServerId = DstOSMan.createServer(originalServerData)
				
				if ServerId and DstOSMan.waitServerReady(ServerId):
					
					logger.info(Messages.Created_Server_S_vCDN_S_POP_S % (ServerId,vCDN_Name,dstPOP_Name) )
					
					### Delete original Instance in the src POP
					
					if OSMan.deleteServer(server.id):
						logger.info(Messages.Deleted_Server_S_vCDN_S_POP_S % (server.id,vCDN_Name,srcPOP_Name) )
					else:
						logger.error(Messages.NotDeleted_Server_S_vCDN_S_POP_S % (server.id,vCDN_Name,srcPOP_Name) )
					
				else:
					#Not able to start the server from the image
					logger.error(Messages.NoServerCreated_vCDN_S_POP_S % (vCDN_Name,dstPOP_Name))
					
			except:
				logger.exception(Messages.Exception_Cloning_Server_S_POP_S_POP_S % (server.id,srcPOP_Name, dstPOP_Name) )
				continue
		#endfor	
		logger.info(Messages.Migration_ended_Instance_vCDN_S_POP_S_POP_S % (vCDN_Name,srcPOP_Name,dstPOP_Name))
	else:
		logger.error(Messages.NoConnect_Pops)
#enddef

def _createInstance(demandId):
	"""
		Creates all the VMs from an Demand into the POP, by cloning it from another Instance of the same vCDN
		
		A copy of the current VMs is built (if possible) on the POP, based on all the parameters from the vCDN in another POP (if any)
		
		This is because it is assumed that the vCDN have a single size deployed in all the DataCenters and the Data Centers are configured similarly
		
		:param demand: a Demand  id to be instantiated
		:type demand: int

		The instance and dstPop parameters cannot be None
		The Parameter is an Id because this function brings up its own connection to the DB
	"""
	
	
	aDBConn = DBConnection.DBConnection(DBConn.DBString)
	
	
	aDBConn.start()
	
	demand = aDBConn.getDemandById(demandId) 
	modelInstance = aDBConn.getInstanceforDemand(demand)
	
	vCDN_Name = demand.vcdn.name
	POP_Name = demand.pop.name

	if modelInstance:
		
		logger.info(Messages.Instantiating_Instance_vCDN_S_POP_S % (vCDN_Name,POP_Name))
	
		_cloneInstance(modelInstance.id , demand.popId)
		
	else:
		logger.error(Messages.NoInstanceForvCDN_S % vCDN_Name )

	aDBConn.cancelChanges()
	aDBConn.end()
	
	logger.info(Messages.Instantiation_ended_Instance_vCDN_S_POP_S   % (vCDN_Name,POP_Name))
	
#enddef

def triggerMigrations(migrations):
	"""
		Does perform a set of Migrations on the OpenStack Data Centers.
		This triggers several Threads for the completion of the migration but does not wait for them.
		The Migrations operations are not controlled, they have to be followed in the OpenStack controllers or the log files left by vIOS
	
		:param migrationIds: A list of migrationsIds to do
		:type migrationIds: int[]
		
	"""
	
	if not _testWritableDir(IMG_FOLDER):
		logger.error(Messages.NoWritable_S % IMG_FOLDER)
		return False
	
	logger.info(Messages.Executing_D_Migrations % len(migrations) )

	for mig in migrations:
		try:
			thread.start_new_thread ( _migrateInstance, (mig.instanceId, mig.dstPopId) )
		except:
			logger.exception(Messages.Unable_Thread)
			continue
	#endfor
	
	return True
	#else:
		#logger.error(Messages.Error_migrating)
		#return False
	
#enddef


def triggerInstantiations(instantiations):
	"""
		Does perform a set of Instantiations on the OpenStack Data Centers.
		This triggers several Threads for the completion of the instantation but does not wait for them.
		The Instantation operations are not controlled, they have to be followed in the OpenStack controllers or the log files left by vIOS
		
		The instantiaton is a copy because when describing the vCDN, it can have many different VMs and of very different sizes.
			Describing such a structure is out of the scope of Optimization.
			So, as all vCDN Instances are assumed to be the same all over the Infrastructure, a new Instance of a vCDN is a copy
			of an already existing instance, with the proper amount of VMs, IPs, security Groups, etc
		
		:param instantiationIds: A list of demand ids to satisfy by creating the Instance
		:type instantiationIds: int[]
		
		..note:: Needed another DB session
		
	"""
	
	for i in instantiations:
		
		logger.info(Messages.Executing_Instantiation_vCDN_S_POP_S % (i.vcdn.name, i.pop.name) )
		
		if i.vcdn.instances:
			try:
				
				modelInstance = i.vcdn.instances[0]
			
				thread.start_new_thread ( _cloneInstance, (modelInstance.id, i.popId) )
			except:
				logger.exception(Messages.Unable_Thread)
				continue
			
		else:
			logger.exception(Messages.NoInstance)
			continue
		
	#endfor
	
	logger.info(Messages.Executing_D_Instantiations % len(instantiations) )
	return True
	#else:
		#logger.error(Messages.Error_instantiating)
		#return False
	
#enddef


def resetQoE():
	"""
		Without touching any Demand, the QoE value is set to the Max
		
		This is used when the Demands are updated externally and vIOS must considered that the Demands are expecting the best QoE possible
		
	"""
	global operatorQoE
	
	operatorQoE = maxQoE

def updateDemandsQoE(qoe):
	"""
		For the given QoE value, all the Demands have their BW updated.
		
		This is to simulate how much less BW can the Operator offer to the clients to have a desired/agreed QoE MOS level
		
		This is based on the TSP paper "Qualite d'Experience et Adaptation de services video" by  Mamadou Tourad DIALLO
		:param qoe: Value of the desired QoE to adjust the Demands
		:type qoe: float or int or String
	"""
	
	global operatorQoE
	
	qoe = float(qoe)
	
	
	if qoe is not None and  qoe <= _MAX_QoE or qoe >= _MIN_QoE:
		
		
		logger.info(Messages.Updating_Demand_BW_QoE_F % qoe)
		
		aNCUPMModel = NCUPM()
		
		DBConn.start()
		x = aNCUPMModel.x(operatorQoE)/aNCUPMModel.x(qoe)
		
		logger.info(Messages.Updating_Demand_BW_x_F % x)
		
		Demands = DBConn.getDemands()
		if Demands:
			for d in Demands:
				d.bw = x * d.bw
			#endfor
			DBConn.applyChanges()
		else:
			logger.error(Messages.NoDemands)
		
		operatorQoE = qoe
		DBConn.end()
		
		logger.info(Messages.Updated_Demand_BW)
		
		return True
		
		
	else:
		logger.error(Messages.Invalid_QoE_Value)
		
	return False
		
def minMaxDemandsQoE():
	"""
		Returns de minimum and maximum QoE values possible with the NCUPM parameters
		
		:returns: (min,max)
		:rtype: float
		
	"""
	aNCUPMModel = NCUPM()
	
	return (aNCUPMModel.minMOS, aNCUPMModel.maxMOS)
		

def _testWritableDir(folder):
	"""
		Tests if a folder does exists and if it is possible to write and delete files from it
		
		..note:: a file 'test.tmp' will be created and deleted from the folder
		
		:param folder: a folder to test
		:type folder: String
		
		:returns: True if the folder is valid and a test file was written and deleted. False else
		
	"""
	if os.path.isdir(folder):
		try:
			testfile = open(os.path.join(folder,"test.tmp"),"w+")
			testfile.close()
			os.remove(os.path.join(folder,"test.tmp"))
			return True
		except IOError:
			#unable to write files in the locations
			return False
	else:
		return False
