""" 
OMAC/HMAC WEB interface
======================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

This is the WEB interface of OMAC demo. 

Use this sequence to operate this module

	:Example:
		WebAdmin.initialize()
		if WebAdmin.connect(DB URL):
			WebAdmin.build()
			WebAdmin.start()
			
Site Map:
	/ 			/index.html				
	/POPs		/pops.html				List the POPs, Update POP button
	/POP/<id>	/popDetail.html			View instances in a POP
	/vCDNs		/vcdns.html				List the vCDN Clients
	/vCDN/<id>	/vcdnDetail.html		View the Instances of a vCDN 
	/Topologie	/topologie.html			View the Locations, ClientGroups and NetworkLinks. See a Network Graph. Button to make Random Link Changes
	/Demands	/demands.html			View the current Demands taken from the DB. Button to make Randon Demands. Button to run HMAC/OMAC
	/Migrations	/migrations.html		View the current Migrations in the DB.
	/Simulation /simulation.html		Shows the effects of the selected Migrations in the Topologie capacity Graph
	/Execution  /execution.html			Shows the executed Migrations and Instantiations from the Simulation page.
	/admin								Flask Admin application

	All the pages are taken from basic HTML files in the /templates/ folder. Editing this HTML changes the Web Pages
	/templates/layout.html is the basic Web Page skeleton
	
	All the static content is in the /static/ folder. This is where the PNG images are left for the Web Server to pick them up
	/templates/layout.html is the basic Web Page skeleton
	
	.. seealso:: Optimizer.py Messages.py

	.. note:: install flask package from `pip install flask`
	.. note:: install flask-admin package from `pip install flask-admin`
	.. note:: This module does not modify or alter directly with the DB, only does queries
"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""


from flask import Flask, render_template, redirect, request, url_for, flash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin
import SettingsFile
import logging

import uuid							
#To have a random secret

import os							
# To operate with the Topologie map graph PNG file

from DataModels import *
import DBConnection
import Messages 
#from Optimizer import getQoSBWforDemand
import Optimizer

logger = logging.getLogger(__name__)

DBConn = None
""" 
	Object holding the connection to the Database
	:type DBConn: DBConnection class
"""

admin = None
""" 
	Object holding the definitions and pages of the WebServer
"""

app = None
""" 
	Object holding the connection to the HTTP Server
"""

INI_Section = "web" 
""" This is the INI file section where we expect to find our values"""

ListenIp = "127.0.0.1"
""" Ip where the HTTP server would listen to"""
TCPport = 5000
""" TCP Port where the HTTP server will listen"""


def initialize():
	"""
		Prepares the Flask object before anything
		
		:raises:  any internal exception
		
	"""
	
	global app
	global admin
	
	_TEMPLATE = 'bootstrap3'		
	#This is the CSS Style for the Web Site.
	
	app = Flask(__name__)
	admin = Admin(app, name= Messages.AdminPageTitle, template_mode= _TEMPLATE)
	app.config['SECRET_KEY'] = uuid.uuid4().hex	

	## Needed for the session to work. Make this key really secret

#enddef

def connect(url):
	""" Connects to the provided DB String
	
		:param url is a sqlalchemy string, just like the ones in nova.conf [database]
		:type url String
		:returns: True if connection OK, False if not
		
	"""
	global DBConn	
	DBConn = DBConnection.DBConnection(url)
	return DBConn.connect()
#enddef

def build():
	""" 
		Prepares the different tabs and DataViews of the Interface
		
		Here is where the Site Map is constructed; using Route Rules. This implements the Site schema as shown above
		
		.. warning:: Under /admin there is a FlaskAdmin app, so please do not route anything to /admin/*
		
		:raises:  Any internal exception

	"""
	
	global admin
	
	if (admin):
		"""
			For the Admin app, it works based on View objects. There is a View for every editable element
			
			This section builds a simple Web Interface to alter the DB information for OMAC/HMAC optimization
		
			When user deletes an element, error might appear because of Foreign-Key restrictions. Check vIOS_db.sql
			
			The models in use must have a String method __unicode()__ so that the "<Object xABCED>" does not appear on the web page, but some useful text (returned by __unicode__())
				
			The DB Models to edit by the operator are:
			+--------------------------+
			| ClientGroups             |
			| Demands                  |
			| Locations                |
			| MigrationCostMultipliers |
			| NetLinks                 |
			| POPs                     |
			| vCDNs                    |
			+--------------------------+
		
		"""
		admin.add_view( LocationView(Location, DBConn.DBSession) )
		admin.add_view( NetworkLinkView(NetworkLink, DBConn.DBSession) )
		admin.add_view( MigrationCostView(MigrationCostMultiplier, DBConn.DBSession) )
		admin.add_view( POPView(POP, DBConn.DBSession) )
		admin.add_view( vCDNView(vCDN, DBConn.DBSession) )
		admin.add_view( ClientGroupView(ClientGroup, DBConn.DBSession) )
		admin.add_view( DemandView(Demand, DBConn.DBSession) )
	
		
	if (app):
		"""
			The Web intervace is built based on Route rules; to render the .html templates found in /templates
		"""
		
		Flash_msg_error = "error"
		# In layout.html; the Flash messages of this category are painted red. Check templates/layout.html
		
		Topologie_Graph_filename = "topologie.png"
		Topologie_Gomuri_filename = "gomory.png"
		Topologie_Graph_Demanded_filename = "demanded_topologie.png"
		Topologie_Gomuri_Demanded_filename = "demanded_gomory.png"
		Topologie_Gomuri_Simulated_filename = "simulated_gomory.png"
		
		@app.route('/')
		def index():
			return render_template('index.html')
		#enddef
		
		@app.route('/image')
		def image():
			imageTitle=request.args.get('imageTitle')
			imageFilename=request.args.get('imageFilename')
			return render_template('image.html', imageTitle = imageTitle, imageFilename = imageFilename )
		#enddef
		
		@app.route('/POPs' , methods = ['POST','GET'])
		def popsTable():
			if request.method == 'POST':
				if  'updatePOPs' in request.form:	
				#Button name found in the form of pops.html
					if not Optimizer.updatePOPs():
						flash(Messages.Errors_updating_POPs,Flash_msg_error)
					if not Optimizer.updateMetrics():
						flash(Messages.Errors_updating_Metrics,Flash_msg_error)
					flash(Messages.Updated_POPs)
					
			#endif
			DBConn.start()							
			popList = DBConn.getPOPList()
				
			if (popList):
				return render_template('pops.html', popList = popList)
			else:
				flash(Messages.NoPOPs,Flash_msg_error)
				return redirect(url_for('index'))
				
		@app.route('/vCDNs')
		def vcdnsTable():
			DBConn.start()
			vcdnList = DBConn.getvCDNs()
			
			if (vcdnList):
				return render_template('vcdns.html', vcdnList = vcdnList)
			else:
				flash(Messages.NovCDNs,Flash_msg_error)
				return redirect(url_for('index'))
		#enddef
		
		@app.route('/POP/<int:popId>')
		def popDetails(popId):
			pop = None
			DBConn.start()
			pop = DBConn.getPOPbyId(popId)
			
			if (pop):
				return render_template('popDetails.html', pop = pop  )
			else:
				flash(Messages.POP_not_found,Flash_msg_error)
				return redirect(url_for('popsTable'))
				
		@app.route('/vCDN/<int:vcdnId>')
		def vCDNDetails(vcdnId):
			vCDN = None
			DBConn.start()
			vCDN = DBConn.getvCDNbyId(vcdnId)
		
			if (vCDN):
				return render_template('vCDNDetails.html', vcdn = vCDN )
			else:
				flash(Messages.vCDN_not_found,Flash_msg_error)
				return redirect(url_for('vcdnsTable'))
		#enddef
		
		@app.route('/Topologie', methods = ['POST','GET'])
		def topologieTable():
			draw = False
			if request.method == 'POST':
				if  'createRandomLinks' in request.form :			
				#Used this way as; when submitting; either 'createRandomLinks' or 'drawTopologie' will be present in the POST message
					
					if Optimizer.createRandomInfrastructure():
						
						flash(Messages.Updated_Topo_Random)
					else:
						flash(Messages.Errors_random_links,Flash_msg_error)
				#endif
				
				#if ('drawTopologie' in request.form)  or draw:  
			
			#endif	
			
			try:
				os.remove(os.path.join(app.static_folder,Topologie_Graph_filename ))
				os.remove(os.path.join(app.static_folder,Topologie_Gomuri_filename ))
			except OSError:
				pass
			
			if Optimizer.buildModel():
				
				if Optimizer.OptimizationModel.drawTopologie( filename= app.static_folder + "/" + Topologie_Graph_filename ) and \
							Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_filename ) :
					flash(Messages.Updated_Graph)
				else:
					flash(Messages.Exception_drawing_Topologie,Flash_msg_error)
			else:
				flash(Messages.Error_building_Topologie,Flash_msg_error)
		

			DBConn.start()
			
			clientsList = DBConn.getClientGroups()
			locationsList = DBConn.getLocations()
			netlinksList = DBConn.getNetworkLinks()
			migcostsList = DBConn.getMigrationCostMultiplierList()
			
			return render_template('topologie.html', 
										clientsList = clientsList, 
										locationsList = locationsList, 
										netlinksList = netlinksList, 
										migcostsList=migcostsList ,
										Topologie_Graph_filename=Topologie_Graph_filename,
										Topologie_Gomuri_filename=Topologie_Gomuri_filename )

			
		
		@app.route('/Demands' , methods = ['POST','GET'])
		def demandsTable():
			draw = False
			if request.method == 'POST':
				if  'createRandomDemands' in request.form : 
					if Optimizer.createRandomDemands():
						flash(Messages.Created_Demands)
						
						
					else:
						flash(Messages.ERROR_creating_Demands,Flash_msg_error)
				
				# if adjusting QoE
				if "updateDemandsBW" in request.form : 
					if Optimizer.updateDemandsQoE(request.form.get('operatorQoE')):
						flash(Messages.Adjusted_Demands)
						
					else:
						flash(Messages.ERROR_adjusting_Demands,Flash_msg_error)
				
				# if reset QoE
				if "resetQoE" in request.form : 
					Optimizer.resetQoE()
					flash(Messages.QoE_reset)
				
				#if  ('drawTopologieDemands' in request.form) or draw:
			
			#endif		 
			
			try:
				os.remove(os.path.join(app.static_folder,Topologie_Gomuri_filename ))
				os.remove(os.path.join(app.static_folder,Topologie_Gomuri_Demanded_filename ))
			except OSError:
				pass
			
			if Optimizer.buildModel():
				
				Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_filename )
				
				if Optimizer.consumeDemands():
					
					if Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_Demanded_filename ) :
						flash(Messages.Updated_Graph)
						
				else:
					flash(Messages.ERROR_consuming_Demands,Flash_msg_error)
			else:
				flash(Messages.Exception_Building_Model,Flash_msg_error)
			
			
			DBConn.start()
			demandsList = DBConn.getDemands()
			
			
			if (demandsList == None):
				demandsList = []
				flash(Messages.NoDemands,Flash_msg_error)
			
			ModelMinQoE,ModelMaxQoE = Optimizer.minMaxDemandsQoE()
			
			return render_template('demands.html', 
										demandsList = demandsList,
										Topologie_Gomuri_filename=Topologie_Gomuri_filename,
										Topologie_Gomuri_Demanded_filename=Topologie_Gomuri_Demanded_filename,
										operatorQoE = Optimizer.operatorQoE,
										ModelMinQoE = ModelMinQoE,
										ModelMaxQoE = ModelMaxQoE)
		#enddef
		
		@app.route('/Migrations', methods = ['POST','GET'])
		def migrationsTable():
			if request.method == 'POST':
				if 'optimize' in request.form:
					
					try:
						os.remove(os.path.join(app.static_folder,Topologie_Graph_Demanded_filename ))
						os.remove(os.path.join(app.static_folder,Topologie_Gomuri_Demanded_filename ))
					except OSError:
						pass
							
					if Optimizer.buildModel():
						
						if Optimizer.optimize():
						
							Optimizer.OptimizationModel.drawCapacity( filename= app.static_folder + "/" + Topologie_Graph_Demanded_filename )
							Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_Demanded_filename ) 
							flash(Messages.Optimized)
						else:
							flash(Messages.ERROR_optimizing,Flash_msg_error)
							
					else:
						flash(Messages.Error_building_Topologie,Flash_msg_error)
				
			DBConn.start()
			
			if  request.args.get('sort'):
				migrationsList = DBConn.getMigrationsSorted(request.args.get('sort'))
				redirectsList = DBConn.getRedirectsSorted(request.args.get('sort'))
				invalidDemandList = DBConn.getInvalidDemandsSorted(request.args.get('sort'))
			else:
				migrationsList = DBConn.getMigrationsSorted()
				redirectsList = DBConn.getRedirectsSorted()
				invalidDemandList = DBConn.getInvalidDemandsSorted()
		
			
			if not migrationsList:
				flash(Messages.NoMigrations,Flash_msg_error)
				migrationsList = []
			if not invalidDemandList:
				invalidDemandList = []
			if not redirectsList:
				redirectsList = []
			
			return render_template('migrations.html', 
									migrationsList = migrationsList ,
									redirectsList = redirectsList,
									invalidDemandList = invalidDemandList)
		#enddef
		
		@app.route('/Simulation', methods = ['POST','GET'])
		def simulationTable():
			if request.method == 'POST':
				if 'simulate' in request.form:
					
					#Build a list of Migrations, Redirections and Demands based on the selected elements
					
					selectMigrations = request.form.getlist('migrations')
					selectRedirects = request.form.getlist('redirections')
					selectInstantiations = request.form.getlist('invalidDemands')
					
					migrationsList = []
					instantiationList = []
					redirectsList = []
					alteredDemandsList = []
					
					DBConn.start()
					
					for did in selectInstantiations:
						instantiationList.append( DBConn.getDemandById(did) )
					
					for rid in selectRedirects:
						redirectsList.append( DBConn.getAlteredDemandById(rid) )
					
					for mid in selectMigrations:
						migrationsList.append( DBConn.getMigrationById(mid) )
						
				
					
					# First a New Model is built from the Infrastructure, as to take into account any changes in the Topologie information
					# Then do pass the Demands as before to show how the Infrastructure is before optimization
					# Finally, call the simulation routine that will update the Model, and at the end the Gomory-hu Tree can be drawn
					
					if Optimizer.buildModel():
						
						try:
							os.remove(os.path.join(app.static_folder,Topologie_Gomuri_filename ))
							os.remove(os.path.join(app.static_folder,Topologie_Gomuri_Demanded_filename ))
							os.remove(os.path.join(app.static_folder,Topologie_Gomuri_Simulated_filename ))
						except OSError:
							pass
							
						Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_filename )
						if Optimizer.consumeDemands():
							Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_Demanded_filename ) 
							
							alteredDemandsList = Optimizer.simulate(
													migrationList = migrationsList,
													redirectList = redirectsList, 
													instantiationList = instantiationList
													)
																					
							if alteredDemandsList is not None :
								Optimizer.OptimizationModel.drawGomory( filename= app.static_folder + "/" + Topologie_Gomuri_Simulated_filename )
							else:
								flash(Messages.Errors_simulating,Flash_msg_error)
					else:
						flash(Messages.Error_building_Topologie,Flash_msg_error)
					
				
				
					return render_template('simulation.html', 
									migrationsList = migrationsList ,
									instantiationList = instantiationList,
									alteredDemandsList = alteredDemandsList,
									Topologie_Gomuri_filename = Topologie_Gomuri_filename,
									Topologie_Gomuri_Demanded_filename = Topologie_Gomuri_Demanded_filename,
									Topologie_Gomuri_Simulated_filename = Topologie_Gomuri_Simulated_filename
									)
				#endif
			return redirect(url_for('migrationsTable'))
		#enddef
		@app.route('/Execution', methods = ['POST','GET'])
		def executionTable():
			if request.method == 'POST':
				if 'execute' in request.form:
					
					#Build a list of Migrations and Instantiations
					
					selectMigrations = request.form.getlist('migrations')
					selectInstantiations = request.form.getlist('instantiations')
					
					migrationsList = []
					instantiationList = []
					
					DBConn.start()
					
					for did in selectInstantiations:
						instantiationList.append( DBConn.getDemandById(did) )
					
					for mid in selectMigrations:
						migrationsList.append( DBConn.getMigrationById(mid) )
						
					# Call the Execution routine that will trigger the Threads for the Migrations/Instantiations to run
					
					if Optimizer.triggerMigrations(migrationsList) and Optimizer.triggerInstantiations(instantiationList):
						flash(Messages.Executing)
					else:
						flash(Messages.Error_executing,Flash_msg_error)
					
					return render_template('execution.html', 
									migrationsList = migrationsList ,
									instantiationList = instantiationList
									)
				#endif
			return redirect(url_for('migrationsTable'))
		#enddef
		
#enddef

def start():
	""" 
		Starts the Web Server at TCP 5000
		
		:returns:  When the server has finished; either normally or abnormally
		
		:raises:  any internal exception
	"""
	
	app.run(host=ListenIp,port=TCPport, debug=False)
	
#enddef

def readSettingsFile():
	"""
		This function asks the INI file parser module, that must have read the INI file, to look for the options in the sections and variables that are of interest for this module.
		
		If the options are not present in the INI file, the existing values are not modified
		
		This is so that we add or remove options from the INI file just by mofiying this functions. Also, the same INI entry can be read by many modules
		
		.. note:: Make sure that the SettingsFile module has been initialized and read a valid file
		
		::Example::
			SettingsFile.read(INI_file)
			WebAdmin.readSettingsFile()
		
	"""
	global ListenIp
	global TCPport
	

	
	if SettingsFile.getOptionString(INI_Section,"listen_ip"):
		ListenIp = SettingsFile.getOptionString(INI_Section,"listen_ip")
	if SettingsFile.getOptionInt(INI_Section,"listen_port"):
		TCPport = SettingsFile.getOptionInt(INI_Section,"listen_port")
	#endif

### Views used in the Admin Site. Check Flask-Admin documentation ###

class LocationView(ModelView):
	""" 
		In Locations page, Location and POP associated can be altered
		If the location name is left blanc when editing or adding, error because of DB constraint
		
		.. seealso:: DataModels.py
		
	"""
	column_exclude_list = ['id','created_at','clientGroups' ]					# hide these fields when viewing
	form_excluded_columns = ['id','created_at','modified_at','clientGroups'] 	# hide these fields when editing
	column_labels = dict(geo='Geo coordinates')  								# Rename the field in the DB by a better text
#endclass


class NetworkLinkView(ModelView):
	""" 
		In the NetLinks page, only the NetLinks are altered
		If any of the locations is left blanc when editing or adding, error because of DB constraint
		
		.. seealso:: DataModels.py
	"""
	column_exclude_list = ['id','created_at']																			# hide these fields when viewing
	column_sortable_list = (('locationA','locationA.name'),('locationB','locationB.name'),'capacity','modified_at') 		# The only fields that clicking on the Header allow to sort
	column_labels = dict(locationA='Location A',locationB='Location B' , capacity = "Capacity [Mbps]") 					# Rename the title of the fields
	form_excluded_columns = ['id','created_at','modified_at',] 															# hide these fields when editing
#endclass


class MigrationCostView(ModelView):
	""" 
		In the NetLinks page, only the Migrations Costs are altered
		If any of the locations is left blanc when editing or adding, error because of DB constraint
		
		.. seealso:: DataModels.py
		
	"""
	column_exclude_list = ['id','created_at']											# hide these fields when viewing
	column_sortable_list = (('popA','popA.name'),('popB','popB.name'),'costMultiplier') 		# The only fields that clicking on the Header allow to sort
	column_labels = dict(popA='Pop A',popB='Pop B',costMultiplier="Cost Coeficient") 			# Rename the title of the fields
	form_excluded_columns = ['id','created_at','modified_at',] 							# hide these fields when editing because are filled automatically by the application in the DB
#endclass

class POPView(ModelView):
	""" 
		In the POPs page, the location can be altered also
		DB errors if the location chosed for the POP is already used by another POP (DB constraints)
		
		.. seealso:: DataModels.py
		
		
	"""
	column_exclude_list = ['id','created_at','loginPass','maxDisk','maxRAM','maxCPU','maxNetBW','curDisk','curRAM','curCPU','curNetBW','curInstances','demands']	
	# hide these fields when viewing
	form_excluded_columns = ['id','created_at','modified_at','maxDisk','maxRAM','maxCPU','maxNetBW','curDisk','curRAM','curCPU','curNetBW','curInstances','flavors','hypervisors','demands','instances','migrations','redirects'] 	
	# hide these fields when editing
	column_sortable_list = ('name',('location','location.name'),'totalRAM','totalDisk','totalCPU','totalNetBW') 
	# The only fields that clicking on the Header allow to sort
	column_labels = dict(loginUser = "OpenStack Admin",loginPass = "OpenStack Admin Password", totalNetBW='Installed Net BW [Mbps]',totalDisk='Installed Storage[GB]' , totalRAM = "Installed memory [MB]",totalCPU = "Installed CPUs") 
	# Rename the title of the fields
#endclass


class vCDNView(ModelView):
	""" 
		Defines the vCDNs. 		
		.. seealso:: DataModels.py
		
	"""

	column_exclude_list = ['id','created_at','loginPass']	# hide these fields when viewing
	form_excluded_columns = ['id','created_at','modified_at','instances','demands'] 	# hide these fields when editing
	column_labels = dict(loginUser = "OpenStack User", vNetBW='Needed Net BW [Mbps]',vDisk='Needed Storage[GB]' , vRAM = "Needed memory [MB]",vCPU = "Needed CPUs" ,vInstances = "Needed VMs", defaultQosBW = "Default BW for clients [kbps]" ) # Rename the title of the fields
#endclass

class ClientGroupView(ModelView):
	""" 
		Defines the ClientGroups page. The QOSMaps can be edited from here
		
		.. seealso:: DataModels.py
		
	"""
	
	column_exclude_list = ['id','created_at']			# hide these fields when viewing
	form_excluded_columns = ['id','created_at','modified_at','demands'] 	# hide these fields when editing
	column_sortable_list = (('location','location.name'),'name')
	column_labels = dict(connectionBW = "Connection BW [Mbps]",) # Rename the title of the fields
#endclass


class DemandView(ModelView):
	""" 
		Defines the Demands page. The associated Migrations are not  shown
		
		.. seealso:: DataModels.py
		
	"""
	
	column_exclude_list = ['id','created_at','invalidInstance']			# hide these fields when viewing
	form_excluded_columns = ['id','created_at','modified_at','redirect','migration','invalidInstance'] 	# hide these fields when editing
	column_labels = dict(volume = "Volume" ,bw = "BW [Mbps]") # Rename the title of the fields
	column_sortable_list = (('vCDN','vcdn.name'), ('POP','pop.name'),('clientGroup','clientGroup.name'),'volume','bw')
#endclass
