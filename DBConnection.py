""" 

Module to interact with the DB for vIOSimulator
=======================================
	
> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

Uses sqlalchemy. Uses any DB backend supported by SQLAlchemy.

No method prints messages, no exceptions raised, no logging performed. These methods are silent.

"""

"""

For methods that take parameters; the parameters are expected to be Values, not complete objects. 
This is to detach any change in the Model values of attributes from the DB operations (DB only cares about indexes and values)

A single Session object is used internally, and it is renewed/recreated 

"""

"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy import and_

from  DataModels import *

class DBConnection(object):
	"""
	
	Connection to the DB that is able to produce directly the appropriate Models
	
	.. seealso:: DataModels
	
	This is done as a object so that different modules or packages can have its own independent connection to the DB.
	
	The interactions with the DB are thought to be performed in blocks delimited by
	
		DBConnection.start()
			# Query, update, add, drop
			DBConnection.applyChanges() or DBConnection.cancelChanges()
		DBConnection.end()
	
	:Example:

	DBobj = DBConnection.DBConnection(url)
	if DBobj.connect:
		DBobj.start()
			
			# Operations getting objects from the Model.
			DBobj.getPOPs()
			DBobj.getvCDNbyId(2)
			
			# Alterations or updates of the objets
			
			# Either write the changes to the objects or discard them
			DBobj.applyChanges()
			DBobj.cancelChanges()
		DBobj.end()
		
	DBString = ""
	"""
		
	DBString = ""
	
	def __init__(self, connString):
		""" 
			Constructor, does not connect
			
			:param connString: Connection string to use, just like the ones in nova.conf for SqlAlchemy
			:type connString: String
		"""
		self.DBString = connString
		self.SessionClass = sessionmaker()
		self.engine = create_engine(self.DBString)
		self.SessionClass.configure(bind=self.engine)
		
		self.DBSession = self.SessionClass()
			
	#enddef
	
	def connect(self):
		""" 
			Connects to the DB
			
			:returns:  True if the connection was OK, False if not
			:rtype: boolean
		"""
		try:
			conn = self.engine.connect()
			conn.execute("SHOW TABLES;")
			conn.close()
			return True
		except:
			return False
	#enddef
	
	def toString(self):
		""" 
			:returns:  connection String + CONNECTED/NOT
			:rtype: String
		"""
		string = self.DBString
		if (self.DBSession) :
			string = string + " - CONNECTED"
		else:
			string = string + " - NOT Connected"
		return string
	#enddef
	
	def getLocations(self):
		"""  
		Returns a list of all the available Locations.
		
			:returns: list of Location class
			:rtype: Location[] or None
		"""
		try:
			return self._getArray(Location)
		except LookupError:
			return None
	#enddef
	
	def getNetworkLinks(self):
		"""  
		Returns a list of all the Network Links. 
		
			:returns: list of NetworkLink class
			:rtype: NetworkLink[] or None
		
		"""
		try:
			return self._getArray(NetworkLink)
		except LookupError:
			return None
	#enddef	

	def getMigrationCostMultiplierList(self):
		""" 
		 Get all the HmacResult Costs Multipliers 
		 
			:returns: list of MigrationCostMultiplier class
			:rtype: MigrationCostMultiplier[] or None
		"""
		try:
			return self._getArray(MigrationCostMultiplier)
		except LookupError:
			return None
	#enddef	

	def getHmacResults(self):
		""" 
		 Get all the HmacResult 
		 
			:returns: list of HmacResult class
			:rtype: HmacResult[] or None
		"""
		try:
			return self._getArray(HmacResult)
		except LookupError:
			return None
	#enddef	
	
	
	def getMigrationsSorted(self,field = "id"):
		"""  
			Get all the HmacResult entries in the DB that have the `migrate` field set to True, sorted by the argument field.
			
			Sorting field can be {"vcdn","fromPOP","toPOP","cost", "delay" }. 
			
			If any else, the results are sorted by ID
			
			:param field: A Field of the HmacResult table to sort the results, 
			:type field: String 
			
			:returns:  list of HmacResult class, sorted
			:rtype: HmacResult[] or None
		"""
		dataset = []
		try:
			if field=="vcdn":
				
				for element in self.DBSession.query(HmacResult).join(Instance,HmacResult.instanceId == Instance.id).order_by(Instance.vcdnId):
					dataset.append(element)
				
			elif field=="fromPOP":
				
				for element in self.DBSession.query(HmacResult).join(Instance,HmacResult.instanceId == Instance.id).order_by(Instance.popId):
					dataset.append(element)
				
			elif field=="toPOP":
				
				for element in self.DBSession.query(HmacResult).join(POP,HmacResult.dstPopId == POP.id).order_by(POP.name):
					dataset.append(element)
				
			elif field=="cost":
				
				for element in self.DBSession.query(HmacResult).order_by(HmacResult.cost):
					dataset.append(element)
				
			elif field=="delay":
				
				for element in self.DBSession.query(HmacResult).order_by(HmacResult.delay):
					dataset.append(element)
				
			
				
			else:
				
				for element in self.DBSession.query(HmacResult).order_by(HmacResult.id):
					dataset.append(element)
				
			return dataset 
		except:
			return None
	#enddef	
	
	def getRedirectsSorted(self,field = "id"):
		"""  
			Get all the AlteredDemand entries in the DB, sorted by the argument field.
			
			Sorting field can be {"vcdn","fromPOP","toPOP", "demand"}. 
			
			If any else, the results are sorted by ID
			
			:param field: A Field of the list ["vcdn","fromPOP","toPOP", "demand"]
			:type field: String 
			
			:returns:  list of AlteredDemand class, sorted
			:rtype: AlteredDemand[] or None
		"""
		dataset = []
		try:
			if field=="vcdn":
				
				for element in self.DBSession.query(AlteredDemand).join(Demand, Demand.id == AlteredDemand.demandId).order_by(Demand.vcdnId):
					dataset.append(element)
				
			elif field=="fromPOP":
				
				for element in self.DBSession.query(AlteredDemand).join(Demand, Demand.id == AlteredDemand.demandId).order_by(Demand.popId):
					dataset.append(element)
				
			elif field=="toPOP":
				
				for element in self.DBSession.query(AlteredDemand).join(POP,AlteredDemand.dstPopId == POP.id).order_by(POP.name):
					dataset.append(element)
					
			elif field=="demand":
				
				for element in self.DBSession.query(AlteredDemand).join(Demand,AlteredDemand.demandId == Demand.id).order_by(Demand.volume.desc()):
					dataset.append(element)
				
			else:
				
				for element in self.DBSession.query(AlteredDemand).order_by(AlteredDemand.id):
					dataset.append(element)
				
			return dataset 
		except:
			return None
	#enddef	
	
	def getPOPList(self):
		"""  Get a list of the POPs
			:returns: list of POP class, or None if not found
			:rtype: POP[] or None if error
			
		"""
		try:
			return self._getArray(POP)
		except LookupError:
			return None
	#enddef	

	def getPOPbyId(self,id):
		"""  
		Get a certain POP based on the ID.
		
		:returns: a POP object, or None if not found
		:rtype: POP or None if error
			
		"""
		try:
			return self._getItemById(POP,id)
		except LookupError:
			return None
	#enddef	
	
	def getvCDNbyId(self,id):
		"""  
		Get a certain vCDN based on the ID.
		
		:returns: a vCDN object, or None if not found
		:rtype: vCDN or None if error
			
		"""
		try:
			return self._getItemById(vCDN,id)
		except LookupError:
			return None
	#enddef	
	
	def getMetricList(self):
		"""  
		Get a list of the POPs.
		
		:returns: list of POP class
		:rtype: Metric[] or None
		"""
		try:
			return self._getArray(Metric)
		except LookupError:
			return None
	#enddef	

	def getInstanceList(self):
		"""  
		Get a list of the Instances.
		
		:returns: list of Instances class
		:rtype: Instance[] or None
		"""
		try:
			return self._getArray(Instance)
		except LookupError:
			return None
	#enddef	
	
	def getInstanceById(self,id):
		"""  
		Get a certain Instance based on the ID.
		
		:returns: an Instance object, or None if not found
		:rtype: Instance or None if error
			
		"""
		try:
			return self._getItemById(Instance,id)
		except LookupError:
			return None
	
	def getInstanceOf(self,vcdnId ,popId ):
		"""
		For a given pair of vCDN and POP (their ids), returns the instance that matches the pair; or None if not found
		
		:param vcdnId: Id of the vCDN to look for instances
		:type vcdnId: int
		:param popId: Id of the POP to look for instances
		:type popId: int
		
		:returns:   the Instance object or None if not found
		:rtype: Instance or None
		
		"""
		try:
			InstaceEntry = self.DBSession.query(Instance).filter(Instance.vcdnId == vcdnId, Instance.popId == popId).one()
			return InstaceEntry
		except NoResultFound, MultipleResultsFound:
			return None
			
	#enddef
	
	def getMigrationCostMultiplier(self,srcPOPId ,dstPOPId ):
		"""  
			Get the HmacResult Cost Multiplier for a given pair of POPs, identified by their IDs.
			
			:param srcPOPId:  Source POP for the Operation
			:type srcPOPId: int
			:param dstPOPId: Target POP for the Operation
			:type dstPOPId: int
			
			:returns: the MigrationCostMultiplier value found for a given pair of values, or 1.0 if not found
			:rtype: float
			
		"""
		
		ret = 1.0
		
		try:
			
			MigCostEntry = self.DBSession.query(MigrationCostMultiplier).filter( or_ (
				and_( MigrationCostMultiplier.popAId == srcPOPId, MigrationCostMultiplier.popBId == dstPOPId),
				and_( MigrationCostMultiplier.popBId == srcPOPId, MigrationCostMultiplier.popAId == dstPOPId))
				).one()
			ret = MigCostEntry.costMultiplier
		except NoResultFound:
			pass
		return ret
	#enddef	
	
	
	
	def getDemands(self):
		"""  
		Get a list of the current Demands
		
			:returns: list of Demand class, or None
			:rtype: Demand[] or None
		"""
		try:
			return self._getArray(Demand)
		except LookupError:
			return None
	#enddef	
	
	def getAlteredDemands(self):
		"""  
		Get a list of the current AlteredDemands, caused by the simulation
		
			:returns: list of AlteredDemand class, or None
			:rtype: AlteredDemand[] or None
		"""
		try:
			return self._getArray(AlteredDemand)
		except LookupError:
			return None
	#enddef	
	
	def getDemandById(self, id):
		"""
			Get the Demand identified by the id
			
			:param id: id of the Demand
			:type id: int
			
			:returns:  The Demand object or None
			:rtype: Demand or None
		"""
		try:
			return self._getItemById(Demand, id)
		except LookupError:
			return None
	#enddef
	
	
	def getMigrationById(self, id):
		"""
			Get the HmacResult identified by the id
			
			:param id: id of the HmacResult
			:type id: int
			
			:returns:  The HmacResult object or None
			:rtype: HmacResult or None
		"""
		
		try:
			return self._getItemById(HmacResult, id)
		except LookupError:
			return None

		
	#enddef
	
	
	def getAlteredDemandById(self, id):
		"""
			Get the AlteredDemand identified by the id
			
			:param id: id of the AlteredDemand
			:type id: int
			
			:returns:  The AlteredDemand object or None
			:rtype: AlteredDemand or None
		"""
		
		try:
			return self._getItemById(AlteredDemand, id)
		except LookupError:
			return None
	
	
	def getInvalidDemandsSorted(self, field = "id"):
		"""  
		Get a list of the  Demands that have set the field `invalidInstance` to True, sorted by the parameter field
		
			:param field: Any of the fields in the list {"demand","pop","vcdn"}
			:type field: String
			
			:returns: list of Demand class, or None
			:rtype: Demand[] or None
		"""
		dataset = []
		try:
			if field=="vcdn":
				
				for element in self.DBSession.query(Demand).join(vCDN,Demand.vcdnId == vCDN.id).filter(Demand.invalidInstance==True).order_by(vCDN.name):
					dataset.append(element)
				
			elif field=="demand":
				
				for element in self.DBSession.query(Demand).filter(Demand.invalidInstance==True).order_by(Demand.volume.desc()):
					dataset.append(element)
				
			else:
				
				for element in self.DBSession.query(Demand).filter(Demand.invalidInstance==True).order_by(Demand.id):
					dataset.append(element)
		except:
			return None
		return dataset 
	#enddef	
	
	def getvCDNs(self):
		""" 
		Get a list of the vCDNs
		
			:returns: list of vCDN class
			:rtype: vCDN[] or None
		"""
		try:
			return self._getArray(vCDN)
		except LookupError:
			return None
	#enddef	

	def getClientGroups(self):
		"""  
		Get a list of the ClientGroups. 
		
			:returns: list of ClientGroup class
			:rtype: ClientGroup[] or None
		"""
		try:
			return self._getArray(ClientGroup)
		except LookupError:
			return None
	#enddef	


	### Internal Functions ###

	def _getArray(self,ModelClass):
		"""  
		Gets all the values in the DB of a model class
		
			:param ModelClass: is the Table/Class to lookup and get the values
			
			:returns: list of elemenst of the ModelClass class
			:rtype: ModelClass[]
			
			:raises:  LookupError
		"""
		Array = []
		try:
			for element in self.DBSession.query(ModelClass).order_by(ModelClass.id):
				Array.append(element)
		except:
			raise LookupError
		return Array
	#enddef
	
	def _getArraySorted(self,ModelClass,ModelField):
		"""  
		Gets all the values in the DB of a model class
		
			:param ModelClass: is the Table/Class to lookup and get the values
			:param ModelField: is the Table/Class field to sort this. 'Must be ModelClass.x'
		
			:returns: list of elemenst of the ModelClass class
			:rtype: ModelClass[]
		
			:raises:  LookupError
		"""
		Array = []
		try:
			for element in self.DBSession.query(ModelClass).order_by(ModelField):
				Array.append(element)
		except:
			raise LookupError
		return Array
	#enddef			

	def _getItemById(self,ModelClass,id):
		"""  
		Gets the value in the DB of a model class that matches the id
		
			:param ModelClass: is the Table/Class to lookup and get the values
			:param id: the ID
			
			:returns: an object ModelClass class
			:rtype: ModelClass
			
			:raises:   LookupError
		"""
		item = None
		try:
			item =  self.DBSession.query(ModelClass).filter(ModelClass.id==id).one()
		except:
			raise LookupError
		return item
	#enddef		
	
	### AddDrop Operations ###
	
	def add(self,ModelClass):
		""" 
		Adds the new element to the DB
		
			:param ModelClass: is the Table/Class to add
			
			:raises:  internal errors
			
		"""
		self.DBSession.add(ModelClass)
		self.DBSession.commit()
	#enddef

	def drop(self,ModelClass):
		""" 
		Drops the element from the DB
		
			:param ModelClass: is the Table/Class to add
			
			:raises:  internal errors
			
		"""
		self.DBSession.delete(ModelClass)
		self.DBSession.commit()
	#enddef
	
	### DB Connnection cleanness Operations ###
	
			
	def applyChanges(self):
		""" 
		Commits the DB memory, if there is something to commit
		
			:raises:  internal errors
		"""
		#try:
		self.DBSession.commit()
			#self.DBSession.close()
		#except InvalidRequestError:
			##There is nothing to do
			#pass
		
	#enddef
	
	def cancelChanges(self):
		""" 
			Undoes all pending changes done to any of object obtained from the DB
		
			:raises:  internal errors
		"""
		self.DBSession.rollback()
	
	def start(self):
		""" 
			Start a new transaction block, closing the previous.
			All pending changes not applied are undone.
		"""
		self.DBSession.rollback()
		self.DBSession.close()
		self.DBSession = self.SessionClass()
		
	def end(self):
		""" 
			Ends the transaction block
		"""
		self.DBSession.close()
		
	#enddef
