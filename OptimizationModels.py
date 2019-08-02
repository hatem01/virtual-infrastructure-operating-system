"""

Modeling for Optimization
===================================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

This is the main Model of vCDN Infrastructure Optimization (HMAC/OMAC)


It builds graphs based on topology information, and runs HMAC and OMAC on top of those
The Topology is made of the locations and the network links. This should reflet a 2-tier or 3-tier architecture
Over this topology, clients are located at the Edge nodes and POPs are located anywhere

HMAC runs over this structure and determines the migrations to make. 
The results are placed back in the DB with the updated timestamp

In the original paper it is said that every node holds a POP for possible migration. In this Demo, for extensibility, the nodes can or cannot have an OpenStack DC. HmacResult only happens to nodes that do have an OpenStack DC

.. note:: Install python-igraph

.. note:: This module does not interact directly with the DB, the Optimizer module does

	
### Original code note:

> Author: Hatem IBN KHEDHER, Makhlouf HADJII, Emad ABD-ELRAHMAN, Hossam AFIFI, and Ahmed.E KAMAL
> Date:15/02/2015
> This source code attempt to resolve the vCDN migration using Gomory-Hu tree for large scale scenario
> Import the required packages

"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from  igraph import Graph, plot as iPlot
from random import sample, randint, random			
#Use to generate random graph Model
from  math import exp, log
#Exponential function
import sys
import os
import logging

from DataModels import HmacResult,  NetworkLink, Demand, AlteredDemand
import SettingsFile
import Messages
import Optimizer

logger = logging.getLogger(__name__)


INI_Section = "graph"
""" This is the INI file section where we expect to find our values """

_flow_attr = "flow"
""" In the Gomuri Tree graph; this edge attribute contains the minimum flow calculated
"""

_capacity_attr = "capacity"
""" In the Topology graph; this edge attribute contains the link capacity
"""

_capacityUnits = "Mbps"
""" In the Topology graph; the edge capacity attribute has this units. Used to write the label
"""


_CPLEX_DAT_FILENAME = "../CPLEX/OMAC.dat"
""" Relative route to the CPLEX data file, from the vIOSLib folder """

_location_attr = "name"
""" In the Topology graph; this vertex attribute contains the location name
"""

_saturatedLinkDelay = 9999
"""	In a migration Gomory-Hu Tree, if the migration path has 0 o Negative Flow/Capacity, this delay is informed, meaning "A very high delay"
"""

LAYOUT = "fruchterman_reingold"
""" Layout used to draw the Topologie .png file in the Web Interface, both the Graph and the Gomuri Tree
"""

BOX_SIZE = 1000
""" 	Size of the PNG file, in pixels, when drawing the Topologie """

DEFAULT_NODE_COLOR = "white"
POP_NODE_COLOR = "blue"
CLIENT_NODE_COLOR = "green"
NEGATIVE_CAPACITY_COLOR = "red"

CLIENT_NODE_SIZE = 10
POP_NODE_SIZE = 20
POP_NODE_SIZE_INC = 10


networkTreeChildren = 3
"""	In the TREE Random Graph; the amount of children for a given node
"""

networkMaxCapacity = 100
"""	In the TREE Random Graph; the maximum random Capacity given to a Link
"""

NCUPM_alpha = 1.25
""" Coefficient for the NCUPM model """
NCUPM_beta = 6.8
""" Coefficient for the NCUPM model """
NCUPM_gamma = 1.67
""" Coefficient for the NCUPM model """

def readSettingsFile():
	"""
		This function asks the INI file parser module, that must have read the INI file, to look for the options in the sections and variables that are of interest for this module.
		
		If the options are not present in the INI file, the existing values are not modified
		
		This is so that we add or remove options from the INI file just by mofiying this functions. Also, the same INI entry can be read by many modules
		
		.. note:: Make sure that the SettingsFile module has been initialized and read a valid file
		
		::Example::
			SettingsFile.read(INI_file)
			OptimizationModels.readSettingsFile()
		
	"""
	global DEFAULT_NODE_COLOR
	global POP_NODE_COLOR
	global CLIENT_NODE_COLOR
	global CLIENT_NODE_SIZE
	global POP_NODE_SIZE
	global POP_NODE_SIZE_INC
	global NEGATIVE_CAPACITY_COLOR
	global BOX_SIZE
	global LAYOUT
	global networkTreeChildren 
	global networkMaxCapacity 
	global NCUPM_alpha
	global NCUPM_beta
	global NCUPM_gamma
	
	# This is the INI file section where we expect to find our values
	
	if SettingsFile.getOptionString(INI_Section,"DEFAULT_NODE_COLOR"):
		DEFAULT_NODE_COLOR = SettingsFile.getOptionString(INI_Section,"DEFAULT_NODE_COLOR")
	if SettingsFile.getOptionString(INI_Section,"POP_NODE_COLOR"):
		POP_NODE_COLOR = SettingsFile.getOptionString(INI_Section,"POP_NODE_COLOR")
	if SettingsFile.getOptionString(INI_Section,"CLIENT_NODE_COLOR"):
		CLIENT_NODE_COLOR = SettingsFile.getOptionString(INI_Section,"CLIENT_NODE_COLOR")
	if SettingsFile.getOptionInt(INI_Section,"CLIENT_NODE_SIZE"):
		CLIENT_NODE_SIZE = SettingsFile.getOptionInt(INI_Section,"CLIENT_NODE_SIZE")
	if SettingsFile.getOptionInt(INI_Section,"POP_NODE_SIZE"):
		POP_NODE_SIZE = SettingsFile.getOptionInt(INI_Section,"POP_NODE_SIZE")
	if SettingsFile.getOptionInt(INI_Section,"POP_NODE_SIZE_INC"):
		POP_NODE_SIZE_INC = SettingsFile.getOptionInt(INI_Section,"POP_NODE_SIZE_INC")
	if SettingsFile.getOptionString(INI_Section,"NEGATIVE_CAPACITY_COLOR"):
		NEGATIVE_CAPACITY_COLOR = SettingsFile.getOptionString(INI_Section,"NEGATIVE_CAPACITY_COLOR")
	if SettingsFile.getOptionInt(INI_Section,"GRAPHBOX_SIZE"):
		BOX_SIZE = SettingsFile.getOptionInt(INI_Section,"GRAPHBOX_SIZE")
	if SettingsFile.getOptionString(INI_Section,"GRAPH_LAYOUT"):
		LAYOUT = SettingsFile.getOptionString(INI_Section,"GRAPH_LAYOUT")
	
	if SettingsFile.getOptionFloat("DEFAULT","network_tree_branches"):
		networkTreeChildren = SettingsFile.getOptionFloat("DEFAULT","network_tree_branches")
	if SettingsFile.getOptionFloat("DEFAULT","network_link_capacity"):
		networkMaxCapacity = SettingsFile.getOptionFloat("DEFAULT","network_link_capacity")
	
	if SettingsFile.getOptionFloat("DEFAULT","NCUPM_alpha"):
		NCUPM_alpha = SettingsFile.getOptionFloat("DEFAULT","NCUPM_alpha")
	if SettingsFile.getOptionFloat("DEFAULT","NCUPM_beta"):
		NCUPM_beta = SettingsFile.getOptionFloat("DEFAULT","NCUPM_beta")	
	if SettingsFile.getOptionFloat("DEFAULT","NCUPM_gamma"):
		NCUPM_gamma = SettingsFile.getOptionFloat("DEFAULT","NCUPM_gamma")	
	#endif
#enddef

	


def graphConsumeBW(graph, node_src_name, node_dst_name, capacity , bw):
	"""
		Given any graph and 2 nodes (Node's name to find them), the bw value is substracted from the SPT path between the nodes
		The attribute `capacity` is expected to be in the graph's edges and it is here where `bw` is substracted
		
		:param graph: A Graph
		:type graph: Graph
		:param node_src_name: Name of the source Node. This is checked against the `name` attribute of the Vertex
		:type node_src_name: String
		:param node_dst_name: Name of the destination Node. This is checked against the `name` attribute of the Vertex
		:type node_dst_name: String
		:param capacity: Name of the Edge attribute to substract the `bw` from
		:type capacity: String
		:param bw: value to be substracted from all the edges in the SPT path
		:type bw: float
	"""
	try:		
		#First we get the location node of the POP of the client demanding.
		node_src = graph.vs.find(name = node_src_name)
		
		# We need to know the POP node of the demanded instance
		node_dst = graph.vs.find(name = node_dst_name)
				
		#Initial SPT lenght = all nodes, so it is big as initial value and the minimal path lenght is found
		#SPT is a set of nodes, to the biggest is the total number of nodes. This is to have an absolute max
		SPT_len = graph.vcount()    
			
		#We get the Shortest path from client to server, and we check each link in the path
		SPT = graph.get_shortest_paths(node_src,to = node_dst, output="epath" )[0];

		#logger.debug( Messages.ShortestPath_S % str(SPT))
			
		for e in SPT:
			
			graph.es[e][capacity] = graph.es[e][capacity] - bw
			if (graph.es[e][capacity] < 0):
				graph.es[e]['color'] = NEGATIVE_CAPACITY_COLOR
		
		return True
	
	except:
		return False
	
#enddef
	
def drawGraph(g, filename="graph.png"):
	"""
		
		Draws the Graph to the file passed as parameter. This method returns when the file is done.
		
		The Graphical options set either by default or via the INI file
		
		:param filename: PNG filename where to store the graph. Valid formats is PNG or PDF, the file must have .PNG or .PDF ending
		:type filename: String with an absoute path and ending in .PNG of .PDF
		
		:returns: True if all was OK.
		
	"""
	
	try:
		iPlot(g, filename , layout=g.layout( LAYOUT), bbox=(BOX_SIZE,BOX_SIZE), margin=BOX_SIZE*.1  )
		logger.info (Messages.Draw_File_S % filename)
		return True
	except:
		logger.exception("")
		return False
#enddef

def subgraph(graph, filter_dict = None ):
	""" Returns a subgraph of an existing one, where the Nodes matching the atrributes in the FILTER are removed.

    @param filter: Dictionary of attributes such that if a node matches any of them, it is discarded from the subgraph
    
    @return: Graph with only the nodes that were not catched by the Filter
    
    Used when calculating the Gomory-Hu Tree. Because the Model's graph has Clients as nodes (to draw it), we first filter the Client Nodes before building the Tree
    Another aproach could have been to have 2 graphs internally, one for drawing and one for operating, but then changes would need appropriate coordination and that is harder than just filtering
    
	"""
	g = graph.copy()
	
	for key, value in filter_dict.items():
		to_delete_ids = []
		to_delete_ids = [ v.index for v in g.vs if value == v[key] ]
		g.delete_vertices(to_delete_ids)
	return g



class Model(object):
	"""
		
		The model just holds the information from the infrastructure into structures for the 2 optimization algorithms:
		
		HMAC is based on Graph Theory
		OMAC on Linear-Programming
		
		The model has, internally, a Graph that holds some information about the topologie and its state. 
		This Graph can be drawn to a file or screen (using Cairo lib)
		
		The Graph is created with these attributes
		> Vertex:Name = Location
		> Vertex:label = Location or Pop.name where there is a POP
		> Edge:capacity = NetworkLink.capacity
		> Edge:label = NetworkLink.capacity
		
		> Vertex:pop = POP Object; None if there is none
		
		Internally a Gomury Ho Tree is also constructed based on the Topologie Capacity (does not include the clients)
		
		The Tree is created with these attributes
		> Vertex:Name = Location
		> Vertex:label = Location or Pop.name where there is a POP
		> Edge:capacity = Gomory-Hu Tree flow
		
		The Graph can have the links' capacities reduced or consumed by a set of Demands, leaving a Graph of the consumed topologie
		
		:Example:
		
		1) Having update the list of Locations (nodes) and NetworkLinks (edged), create a Model 
			aModel = HMAC(Locations, NetworkLinks)
		
		2) Put information about the POPs, the ClientGroups, etc and build the Gomory-Hu Tree
			aModel.setPOPs(ListOfPOPs)
			aModel.setClientGroups(ListOfClients)
			aModel.buildGomoryTree()
			
		3) Draw the Graph 
			aModel.drawTopologie() 
			aModel.drawCapacity() 
			aModel.drawGomoryTree() 
			
		4) Consume the Graph with a set of Demands
			aModel.consumeDemands(ListOfDemands)
			
		5)  Draw the Graph with the reduced capacity
			aModel.drawCapacity() 
			aModel.drawGomoryTree() 
	"""
	
	capacityGraph = Graph()
	topologieGraph = Graph()
	gomoryTree = Graph()
	
	def __init__(self, Locations, Links):
		"""
			This load the Node/Vertex information from the Locations. The nodes on the Graph are the Locations
			
			Then the Edges information from the NetworkLinks. The edges on the Graph have the capacity of the link
			
			By default, all nodes are White Circles of size 15, having as LABEL its Location name
			
			:param Locations: is a list of Locations (List of nodes)
			:type Locations: Location[]
			
			:param Links: is a list of NetworkLinks (Listo of edges)
			:type Links: NetworkLink[]
			
			:raises:  any error from the internals, catch everything
			
		"""

		self.topologieGraph= Graph()
		self.capacityGraph= Graph()
		
		##This is an internal class that holds all the ARRAYS of values needed to provide to CPLEX engine
		# As these arrays are used only and exclusively by CPLEX/OMAC, they belong to OMAC class only
		self.omac = OMAC()				
		self.omac.setTopologie(Locations,Links)
		
		for l in Locations:
			#Graph Node with attributes
			self.topologieGraph.add_vertex(name=l.name, 
											label=l.name, pop=None, 
											color=DEFAULT_NODE_COLOR)
			self.capacityGraph.add_vertex(name=l.name, 
											label=l.name, 
											pop=None , 
											color=DEFAULT_NODE_COLOR)
			
		#endfor
			
		for l in Links:
			self.topologieGraph.add_edge(	l.locationA.name,
											l.locationB.name,
											capacity=l.capacity,
											label=  ( "%.2f" % l.capacity),  
										)
			self.capacityGraph.add_edge(	l.locationA.name,
											l.locationB.name,
											label=( "%.2f" % l.capacity),  
											capacity= 1.0*l.capacity
										)
			
			logger.debug(Messages.Added_Link_S_to_S_of_D % (l.locationA.name,l.locationB.name,l.capacity))
			
		#endfor
		
		logger.info(Messages.Built_Model_D_locations_D_links % (len(Locations),len(Links)))
		
		
		
	#enddef
	
	def setPOPs(self,pops):
		"""
			:param pops: List of POPs to be placed in the nodes. According to the model, they can be placed in any layer of the topology
			:type pops: POP[]
			
			:raises:  any error on the internals
			
			The Graph Vertex has some attributes changed
			> Vertex:label = Pop.name where there is a POP
			> Vertex:popId = POP:id
			> Vertex:color = blue
			> Vertex:size = 15 + cantidad de Instancias
		
		"""

		for p in pops:
					
			i = self.topologieGraph.vs.find(name=p.location.name).index
			self.topologieGraph.vs[i]['color'] = POP_NODE_COLOR
			self.topologieGraph.vs[i]['size'] = POP_NODE_SIZE + POP_NODE_SIZE_INC*len(p.instances)
			self.topologieGraph.vs[i]['label'] = p.name
			
			i = self.capacityGraph.vs.find(name=p.location.name).index
			self.capacityGraph.vs[i]['color'] = POP_NODE_COLOR
			self.capacityGraph.vs[i]['size'] = POP_NODE_SIZE + POP_NODE_SIZE_INC*len(p.instances)
			self.capacityGraph.vs[i]['label'] = p.name
			self.capacityGraph.vs[i]['popId'] = p.id
			
			
			
			logger.debug( Messages.Added_Pop_S_in_S % (p.name, p.location.name) )
		#endfor
		
		self.omac.setPOPs(pops)
		# Add this information to the OMAC model too
		
		logger.info(Messages.Added_D_POPs % len(pops))
		
	#enddef
	

	
	def setClientGroups(self,clientGroups):
		"""
			:param clientGroups: List of ClientGroups to be placed in the nodes. 
			:type pops: ClientGroup[]
			
			:raises:  any error on the internals
			
			The Graph has some vertex and edges added.
			> Vertex.name = Vertex.label = ClientGroup.name
			> Vertex.color = CLIENT_NODE_COLOR
			> Vertex.size = CLIENT_NODE_SIZE
			> Vertex.isClient = True
			
			Edge from ClientGroup to Location
			> Edge.color = CLIENT_NODE_COLOR
			> Edge.capacity = ClientGroup.connectionBW
			> Edge.label = ClientGroup.connectionBW + ClientGroup.connectionBWUnits
		
		"""

		for c in clientGroups:
			i = self.topologieGraph.vs.find(name=c.location.name).index
			self.topologieGraph.add_vertex(name=c.name, 
											label=c.name, 
											color=CLIENT_NODE_COLOR,
											size=CLIENT_NODE_SIZE)
			self.topologieGraph.add_edge(c.location.name,
										c.name,capacity=c.connectionBW,
										color=CLIENT_NODE_COLOR,
										label=str(c.connectionBW)+c.connectionBWUnits)
			
			logger.debug( Messages.Added_Client_S_in_S % (c.name , c.location.name))
		#endfor
	
		self.omac.setClientGroups(clientGroups)
		# Add this information to the OMAC model too
		
		logger.info(Messages.Added_D_Clients % len(clientGroups))
		
	#enddef
	
	def buildGomoryTree(self):
		"""
			From the Capacity Graph of the Model, make a Gomory-Hu Tree
			
		
			Calculates the Gomory-Hu tree of the given graph, assuming that the edge capacities are given in `capacity` property.

			This implementation uses Gusfield's algorithm.
			
			Copy the graph and vertex attributes of the original graph into the returned one
			
			The label property of the Gomuri Tree edges is set to the same value as the Gomuri Flow  
			
			.. note:: If the Capacity has been affected by consumeDemands(), the Gomory-Hu Tree will be calculated on the new capacity values
			
			.. note:: Call this before drawGomoryTree()  
    
		"""
		n = self.capacityGraph.vcount()
		
		# Initialize the tree: every edge points to node 0
		neighbors = [0] * n
		flows = [0.0] * n

		# For each source vertex except vertex zero...
		for s in xrange(1, n):
		# Find its neighbor.
			t = neighbors[s]

		# Find the minimum cut between s and t
			cut = self.capacityGraph.mincut(s, t, _capacity_attr)
			flows[s] = cut.value
			side_of_s = cut[cut.membership[s]]

			# Update the tree
			for u in side_of_s:
				if u > s and neighbors[u] == t:
					neighbors[u] = s

		# Construct the tree, putting as a LABEL of the edge the _flow_attr value
		edges = [(i, neighbors[i]) for i in xrange(1, n)]
		
		self.gomoryTree = Graph(n, edges, directed=False, edge_attrs={_flow_attr: flows[1:],_capacity_attr: flows[1:], 'label': flows[1:]})
		
		for attr in self.capacityGraph.attributes():
			self.gomoryTree[attr] = self.capacityGraph[attr]
		for attr in self.capacityGraph.vertex_attributes():
				self.gomoryTree.vs[attr] = self.capacityGraph.vs[attr]
		
	#enddef
	
	def drawTopologie(self, filename=None):
		"""
		..seealso:: drawGraph()
		"""
		return drawGraph(self.topologieGraph ,filename)
	#enddef
	
	def drawCapacity(self, filename=None):
		"""
		..seealso:: drawGraph()
		"""
		return drawGraph(self.capacityGraph ,filename)
	#enddef
	
	def drawGomory(self, filename=None):
		"""
		..seealso:: drawGraph()
		"""
		return drawGraph(self.gomoryTree,filename)
	#enddef

	
	def consumeDemands(self,demands):
		"""
			
			The set of Demands is consumed/substracted from the Model's Topology Graph and Gomory-Hu Tree
			
			:param demands: A list of Demands to consume the model from
			:type demands: Demands[]
			
			:returns: True if all OK; False if there were errors
			
			The Demands passed as parameter are assumed to be VALID
			
		"""
		
		DemandCounter = 0
		errors = False
	
		# For each Demand
		for d in demands:
			try:
				DemandCounter = DemandCounter +1
			
				clientLocation = d.clientGroup.location
				pop = d.pop
				vcdn = d.vcdn
				Demanded_BW = d.bw
			
				logger.debug( Messages.ClientLocation_S_requests_S_from_S_TotalBW_F % (clientLocation.name, vcdn.name,pop.name ,Demanded_BW))
				
				#First we get the location node of the POP of the client demanding.
				node_src_name = clientLocation.name
				
				# We need to know the POP node of the demanded instance
				node_dst_name = pop.location.name
				
				graphConsumeBW(self.capacityGraph,node_src_name,node_dst_name,capacity = _capacity_attr,bw = Demanded_BW)
				graphConsumeBW(self.gomoryTree,node_src_name,node_dst_name,capacity = _flow_attr,bw = Demanded_BW)
				
			except:
				logger.exception( Messages.Exception_Consuming_Demand_D_Graph % d.id )
				errors = True
				continue
		#endfor
		
		#Updating the Link Labels
		for e in self.capacityGraph.es:
			e['label'] = ( "%.2f" % e[_capacity_attr]) # +_capacityUnits
		for e in self.gomoryTree.es:
			e['label'] = ( "%.2f" % e[_flow_attr])
	
		logger.info( Messages.Graph_Consume_D_Demands % DemandCounter)
		return not errors
	#enddef

	def consumeFakeDemands(self,fakeDemands):
		"""
		
			The set of FakeDemands is consumed/substracted from the Model's Topology Graph and Gomory-Hu Tree
			
			This is used for the simulation(), in order not to use real DB objects.
		
			:param fakeDemans: A list of FakeDemands to consume the model from
			:type fakeDemans: FakeDemands[]
			
			:returns:  True if all OK; False if there were errors
			
			The Demands passed as parameter are simulated, so their type has to be FakeDemands
			
		"""
		
		DemandCounter = 0
		errors = False
	
		# For each Demand
		for d in fakeDemands:
			try:
				DemandCounter = DemandCounter +1
			
				logger.debug( Messages.ClientLocation_S_requests_from_S_TotalBW_F % (d.clientGroupLocationName,d.popName, d.bw))
				
				#First we get the location node of the POP of the client demanding.
				node_src_name = d.clientGroupLocationName
				
				# We need to know the POP node of the demanded instance
				node_dst_name = d.popLocationName
				
				graphConsumeBW(self.capacityGraph,node_src_name,node_dst_name,capacity = _capacity_attr,bw = d.bw)
				graphConsumeBW(self.gomoryTree,node_src_name,node_dst_name,capacity = _flow_attr,bw = d.bw)
				
			except:
				logger.exception( Messages.Exception_Consuming_Fake_Demand )
				errors = True
				continue
		#endfor
		
		#Updating the Link Labels
		for e in self.capacityGraph.es:
			e['label'] = ( "%.2f" % e[_capacity_attr]) # +_capacityUnits
		for e in self.gomoryTree.es:
			e['label'] = ( "%.2f" % e[_flow_attr])
	
		logger.info( Messages.Graph_Consume_D_Demands % DemandCounter)
		return not errors
	#enddef
	
	def updateFakeInstances(self,fakeInstances):
		"""
			This takes a list of fakeInstances in order to adjust the Graph's drawing to reflect the proper amount of instances per POP
			
			..seealso:: Optimizer.simulate()
			
			:param fakeInstances: List if fakeInstance to check
			:type fakeInstances: FakeInstance[]
			
		"""
		
		if fakeInstances != None or fakeInstances != []:
			
			popCounter = dict()
			
			for i in fakeInstances:
				
				if i.popLocationName not in popCounter.keys():
					popCounter[i.popLocationName] = 1
					# Counting starst in 1 as there is a first instance for this to be listed in the fakeInstances list
				else:
					popCounter[i.popLocationName] = popCounter[i.popLocationName] + 1
		
			
			for POPnode in self.gomoryTree.vs:
				if POPnode['pop'] != None:
					POPnode['size'] = POP_NODE_SIZE
			
			for popLocationName,instances in popCounter.items():
				i = self.gomoryTree.vs.find(name=popLocationName).index
				self.gomoryTree.vs[i]['size'] = POP_NODE_SIZE + POP_NODE_SIZE_INC*instances
				
				i = self.capacityGraph.vs.find(name=popLocationName).index
				self.capacityGraph.vs[i]['size'] = POP_NODE_SIZE + POP_NODE_SIZE_INC*instances
				
				
				
		#endif
	#enddef

	def optimizeHMAC(self, demands):
		"""
			The results of the optimization are a list of recommended migrations
			
			HMAC works on the Gomuri Tree, where it is assumed that the Flow/Capacity is the remaining Link BW.
			HmacResults are triggerd by saturated links, having 0 or negative Flow/Capacity in the Gomuri Tree
			If all the Gomory Tree shows links with positive Flow/Capacity, it means that the Topologie can very well suppor the Demands the way they are, so no migrations
			
			The HmacResults would indicate the Cost as vCDN.vDisk * (migration path hops in graph)
			The HmacResults would indicate the Delay as vCDN.vDisk / (minimal BW in the migration path) or _SaturatedLinkDelay
			
			.. warning:: Calling this function should happen after calling consumeDemands(). Otherwise, the full Topologie capacity is considered as not used and fully available (less migrations will be triggered)
			
			At the end of the optimization process, the Demands will be linked to the corresponding Migration or Alteration to Perform.
			At the end of the optimization process, the Demands will have this `invalidInstance` field updated. 
			If needed, update the DB to have this modification registered.
			
			:param demands: List of Demand Objects taken from the DB
			:type demands: Demand[]
			
			:returns:  A List of HmacResults to perform, a List of Demands Alterations
			:rtype:  HmacResult[], AlteredDemand[]
			
			:raises:  All internal errors
			
		"""
		
		migrationList = []
		alteredDemandList = []
		
		invalidDemads = 0
				
		# For each Demand
				
		for d in demands:
			
			instance = Optimizer.getInstance(d.pop,d.vcdn)
			if instance == None:
				
				logger.error(Messages.Invalid_Demand_Client_S_vCDN_S_POP_S %  (d.clientGroup.location.name, d.vcdn.name, d.pop.name) )
				d.invalidInstance = True
				invalidDemads = invalidDemads+1
				continue   
				# Get next Demand to work with
			
			d.invalidInstance = False
			Demanded_BW = d.bw
			
			if Demanded_BW == 0.0:
				continue   
				# Get next Demand to work with, a Demand that does not take BW is not worth analyzing
			
			srcPop = instance.pop
			demandedvCDN =  instance.vcdn
			clientLocation = d.clientGroup.location
			
			logger.debug( Messages.ClientLocation_S_requests_S_from_S_TotalBW_F % (clientLocation.name, demandedvCDN.name,srcPop.name ,Demanded_BW))
			
			#First we get the location node of the POP of the client demanding.
			node_client = self.gomoryTree.vs.find(name = clientLocation.name)
			
			# We need to know the POP node of the demanded instance
			node_pop = self.gomoryTree.vs.find(name = srcPop.location.name)
			
						
			#Initial SPT lenght = all nodes, so it is big as initial value and the minimal path lenght is found. The SPT is a set of nodes
			SPT_len = self.gomoryTree.vcount()    
			
			#We get the Shortest path from client to server. The SPT is using Node/Vertex because there is the need to differenciate which node faces the client and which faces the vCDN
			SPT = self.gomoryTree.get_shortest_paths(node_client, to = node_pop )[0];
			
			logger.debug( Messages.ShortestPath_S % str(SPT))
			
			# SPT is a set of nodes like [8, 2, 0, 1]; 8 is the demand's client node and 1 the demand's vCDN node
			#We take the links on the path to the server; one by one; starting from the client
			
			migrate=False
			dstPopId = None
			
			if len(SPT) > 2:
			# It makes sense to migrate if the client is not just in front of the original POP. 
			# The path client->POP must be bigger than 1 link (2 nodes)
				
				for k in range(0,len(SPT)-1):
					
					# We take the SPT link by link, in pairs, from the client to the vCDN.
					# nodeSouth faces the Client, nodeNorth faces the vCDN
					# The closest POP to the Client is kept in dstPop
					# The migration is triggered if there is a saturated link
					
					nodeSouth = SPT[k]
					nodeNorth = SPT[k+1]
					
					egde_id = self.gomoryTree.get_eid(nodeSouth, nodeNorth,directed=False, error=False)
					
					if (egde_id == -1):
						break
						#no link; so the SPT Path is invalid
					
					
					
					if (self.gomoryTree.vs['popId'][nodeSouth]) and self.gomoryTree.es[_flow_attr][egde_id] < 0:
						dstPopId = self.gomoryTree.vs['popId'][nodeSouth]
						migrate = True
						break
				
				#endFor
				
				# The path from the Client to the vCDN has been checked. There would be a migration if there was a saturated link
				
				if migrate and dstPopId  :

					try:
						
						dstPop = Optimizer.DBConn.getPOPbyId(dstPopId)
						
						logger.debug( Messages.Migration_check_PopSrc_S_PopDts_S  %  ( srcPop.name, dstPop.name ))
						
						#Look for Minimal BW left on the migrated path from the srcPOP to the dstPOP
						
						minBWCapacity = srcPop.totalNetBW
						accumHops = 0
						
						for j in range(k,len(SPT)-1):
							nodeSouth = SPT[j]
							nodeNorth = SPT[j+1]
							
							#This time the Gomory Tree SPT is run on the remaining path, because this is where the migration would run
							
							egde_id = self.gomoryTree.get_eid(nodeSouth, nodeNorth,directed=False, error=False)
							if (egde_id != -1):
																
								accumHops = accumHops+1
								if minBWCapacity > self.gomoryTree.es[_capacity_attr][egde_id]:
									minBWCapacity = self.gomoryTree.es[_capacity_attr][egde_id]
						#end for
						
						logger.debug( Messages.Migration_path_D_Hops_F_BW %  ( accumHops, minBWCapacity ))
						
						if (Optimizer.getInstance(dstPop, demandedvCDN) == None):
								
							#If there is no Instance of the vCDN in the Destination POP; this is a HmacResult
							if dstPop.canHostVCDN(demandedvCDN) and ( (dstPop.totalNetBW  - dstPop.curNetBW) > Demanded_BW):
								
								# If there are some other Demands that because of the Migration would take more BW that the one saved by the migration, then no migration
								Redirected_BW = 0
								for dx in demands[:]:
									if dx.vcdnId == demandedvCDN.id and dx.popId == srcPop.id and dx.id != d.id:
										
										node_client = self.gomoryTree.vs.find(name = dx.clientGroup.location.name)
										node_pop = self.gomoryTree.vs.find(name = dstPop.location.name)
										
										SPT = self.gomoryTree.get_shortest_paths(node_client, to = node_pop,  output="epath" )[0];
										
										for l in SPT:
											if l == egde_id:
												Redirected_BW = Redirected_BW + dx.bw
												
												break
										#endfor
								#endfor
								
								if Redirected_BW < Demanded_BW:
									
									if minBWCapacity > 0:
										migDelay = demandedvCDN.vDisk * 1024* 8  * ( accumHops ) / (minBWCapacity  *60)
										# vDisk in GB, link capacity in Mbps. Result in [mins]
									else:
										migDelay = _saturatedLinkDelay 
										# A high value becase the division over 0 should yield Infinite, and Negative BW means saturation
									
									
									migCost = demandedvCDN.vDisk * ( accumHops )
									# The internal cost is bigger with a longer path and a bigger vCDN
								
									# Check if this Migration was already triggered by another demand
									found = False
									for mig in migrationList:
										if mig.dstPopId == dstPop.id and mig.instanceId == instance.id:
											found = True
											break
									
									
									# Add this Demand to the list of Demands optimized by this migration
									if found:
										mig.demandsIds.append(d.id)
									else:
										hmacRes = HmacResult(dstPop.id , instance.id, delay = migDelay, cost = migCost, minBW = minBWCapacity)
										hmacRes.demandsIds.append(d.id)
										migrationList.append( hmacRes )
									
									logger.info( Messages.Migrate_vCDN_S_srcPOP_S_dstPOP_S % (demandedvCDN.name , srcPop.name, dstPop.name) )
								else:
									logger.info( Messages.Migrate_vCDN_S_srcPOP_S_dstPOP_S_RedirectionBW % (demandedvCDN.name , srcPop.name, dstPop.name) )
							else:
								logger.debug( Messages.Migration_Condition_Hold_B_NetCapacity_D_Mbps %  ( dstPop.canHostVCDN(demandedvCDN), (dstPop.totalNetBW  - dstPop.curNetBW - Demanded_BW) ))
								logger.debug(dstPop.canHostVCDN_String(demandedvCDN))
						else:
								
								#If there is an Instance of the vCDN in the Destination POP; this is a Scale-Out ane the Demands could be altered to be optimally served
								
								if ( (dstPop.totalNetBW  - dstPop.curNetBW) > Demanded_BW):
						
									alteredDemandList.append( 
														AlteredDemand(d.id, dstPop.id ) 
									)
									
									logger.info( Messages.Redirect_Demand_Client_S_vCDN_S_srcPOP_S_dstPOP_S % (d.clientGroup.name, demandedvCDN.name , srcPop.name, dstPop.name))
								else:
									logger.debug( Messages.Scale_Condition_NetCapacity_D_Mbps %  (  (dstPop.totalNetBW  - dstPop.curNetBW - Demanded_BW) ))
						#Endif
					except:
						raise
						logger.exception( Messages.Exception_Migrating_vCDN_S_PopSrc_S_PopDts_S %  ( demandedvCDN.name, srcPop.name, dstPop.name ))
						continue
				#endIf - migrate == True and dstPop != None :
				
			#endif - If Len(STP) > 2
		# Get next Demand from DB and process
		#endfor
		logger.info( Messages.HMAC_optimized_D_migrations_D_invalidDemands % (len(migrationList),invalidDemads))
		
		#return (migrationList, invalidDemands)
		return migrationList , alteredDemandList
		
	#enddef
	
	
	
class FakeDemand(object):
	"""
		This object is used in the Simulation of the Migrations
		
		Because while simulating the Demands are placed according to the Migrations, if the Demands objects are used for analysis the changes will impact the DB
		This is because in the internal methods the DataModel relationships are used to get related objects; requiring the relationship to be effectively existing in the DB
		In our case, if a Demand is deplaced, before using any other method the ORM will try to update the DB  to get the new relationships.
		So, to avoid that, we use a fake object that has per separate the 3 elements of a Demand
		
	"""
	
	
	def __init__(self, clientGroupLocationName = "", clientGroupName = "",clientGroupId = 1,popLocationName= "", popName = "",popId = 1, vcdnName = "", vcdnId=1,  bw = 0, volume = 0):
		
		self.clientGroupLocationName = clientGroupLocationName
		self.clientGroupName = clientGroupName
		self.clientGroupId = clientGroupId
		self.popLocationName = popLocationName
		# POP and Client Location to find the node!
		self.popName = popName
		self.popId = popId
		self.vcdnName = vcdnName
		self.vcdnId = vcdnId
		self.bw = bw
		self.volume = volume
	#enddef
	
class FakeRedirect(object):
	"""
		This object is used in the Simulation
		
		Because a Demand would need to be redirected when the vCND is migrated
		
	"""
	
	def __init__(self, fakeDemand, dstPopName = "",dstPopId = 1 ):
		
		self.clientGroupLocationName = fakeDemand.clientGroupLocationName
		self.clientGroupName = fakeDemand.clientGroupName
		self.popName = fakeDemand.popName
		
		self.vcdnName = fakeDemand.vcdnName
		
		self.dstPopId = dstPopId
		self.dstPopName = dstPopName
		
		self.bw = fakeDemand.bw
		self.volume = fakeDemand.volume
	#enddef
	
class FakeInstance(object):
	"""
		This object is used in the Simulation of the Migrations
		
		..seealso:: FakeDemand
		
	"""
	
	def __init__(self, popName = "",popId = 1, vcdnName = "", vcdnId=1 , popLocationName= ""):
		self.popName = popName
		self.popId = popId
		self.vcdnName = vcdnName
		self.vcdnId = vcdnId
		self.popLocationName = popLocationName
	#enddef	
		
	

	
class Random(object):
	"""
		
		This is an auxiliary model used to create a random infrastructure,
		
		The Random Graph Vertex are created with this attributes
		Vertex:name = Location.name
		Vertex:location = Location object
		
		The edge has a property that represents the capacity
		Edge:capacity = NetworkLink.capacity
		
		Once created, pull the NetworkLinks objects using aModel.getLinkList()
		Once created, pull the border Locations using aModel.getAccessLocations()
		
		:Example:
		
			aModel = OptimizationModes.Random( locations )
			listLinks = aModel.getLinkList()
			listLocations = aModel.getAccessLocations()
		
	"""
	
	topologieGraph = Graph()
	
	def __init__(self,  Locations):
		"""
			This model creates a Random Graph with the random probability, with as many nodes as Locations
			
			Then the Locations are linked to the nodes in the random Graph
						
			Then the Edges are set a random Capacity BW, in a range [0 , maxLinkCapacity]
			
			.. note:: The objects in Locations array are attached to this Model, do not delete unless when the complete model is deleted
			
			:param Locations: List of existing locations
			:type Locations: Locations[]
		"""
		
		g = Graph()
		
		logger.debug(Messages.RandomGraph_locationsD_maxCapaD % ( len(Locations), networkMaxCapacity )  )
		
		self.topologieGraph = Graph.Tree( len(Locations) , networkTreeChildren)
		
		
		i = 0
		for l in Locations:		
		# Attaching the Location object to the nodes of the random Graph
			self.topologieGraph.vs[i]['location'] = l
			i = i+1
		#endfor
		
		i=0
		for edge in self.topologieGraph.es:		
		# Setting a random Link Capacity to the links
			edge['capacity']  = random() * networkMaxCapacity 
			i = i+1
		#endfor
		
		logger.info(Messages.RandomGraph_locationsD % ( len(Locations) )  )
	#enddef
	
	def getLinkList(self):
		"""
		Creates a list of NetworkLink objects taken from the graph
		
		:returns:  a list of NetworkLink objects taken from the graph
		:rtype: NetworkLink[]
		"""
		
		netLinks = []
		for edge in self.topologieGraph.es:
			source_vertex = self.topologieGraph.vs['location'][edge.source]
			target_vertex = self.topologieGraph.vs['location'][edge.target]
			netLinks.append ( NetworkLink( source_vertex.id, target_vertex.id, edge['capacity'] ) )
			
			
		#endfor
		return netLinks
	#enddef
	
	def listSortedLocations(self):
		"""
		Creates a sorted list of the Locations objects, ordered from higher to lower node degree
		
		:returns:  a list of Locations objects taken from the graph, ordered from higher degree to less degree
		:rtype: Location[]
		"""
		locsList = []
		degrees = self.topologieGraph.degree()
		while( len(degrees) > 0):
			max_degree_node = degrees.index(max(degrees))
			locsList.append( self.topologieGraph.vs['location'][max_degree_node] )
			del degrees[max_degree_node]	
				
		return locsList
	#enddef
			
	def getAccessLocations(self):
		"""
		Creates a list of the Locations that are Access in the topologie graph.
		Access Locations are nodes with degree 1
		
		:returns:   a list of the Locations that are Access in the Topologie
		:rtype: Location[]
		"""
		locsList = []
		for node in self.topologieGraph.vs:
			if self.topologieGraph.degree(node) == 1:
				locsList.append( node['location'] )
		 #endfor
		return locsList
	#enddef
	
#endclass


class OMAC(object):
	"""
		Class defining and contaning arrays values used for the CPLEX OMAC implementation 
		
			
		This class produces a .DAT file that is compatible with the .MOD file in CPLEX IDE
		
		Possibility to gererate directly a LP notation problem
		
		Get the CPLEX files from the folder ../CPLEX. These .mod and .dat folder can be imported into CPLEX to run the OMAC exact optimization
		
		:Example:
		
			omacModel = new OMAC()
			omacModel.setTopologie(Locations, NetLinks)
			omacModel.setPOPs(POPs)
			omacModel.setvCDNs(vCDNs)
			omacModel.setClientGroups(clientGroups)
			omacModel.setDemands(clientGroups)
			omacModel.setMigrationCost(clientGroups)
			omacModel.optimize()	
		
		By running the Model's function, some of these functions are already executed and the execution path changes a bit:
		
		:Example:
		
			model = new Model(Locations, NetLinks)
			model.setPOPs()
			model.setClientGroups(POPs)
			model.omac.setvCDNs(vCDNs)
			model.omac.setDemands(clientGroups)
			model.omac.setMigrationCost(clientGroups)
			model.omac.optimize()
		
	"""
	"""
		Running CPLEX on command line with .mod et .dat files
		
		$ export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/Documents/ibm/ILOG/CPLEX_Studio_Community1263/opl/bin/x86-64_linux
		$ ~/Documents/ibm/ILOG/CPLEX_Studio_Community1263/opl/bin/x86-64_linux/oplrun  -h
		$ ~/Documents/ibm/ILOG/CPLEX_Studio_Community1263/opl/bin/x86-64_linux/oplrun -o OMAC.opl OMAC.mod OMAC.dat
		$ ~/Documents/ibm/ILOG/CPLEX_Studio_Community1263/opl/bin/x86-64_linux/oplrun -e OMAC.lp OMAC.mod OMAC.dat
		oplrun -e OMAC.lp OMAC.mod OMAC.dat
		
		REF:
		http://www.ibm.com/support/knowledgecenter/SSSA5P_12.2.0/ilog.odms.cplex.help/Content/Optimization/Documentation/CPLEX/_pubskel/CPLEX32.html
		file:///home/rsm/Documents/ibm/ILOG/CPLEX_Studio_Community1263/doc/html/en-US/refpythoncplex/html/index.html
		
	"""
	
	#All these arrays are used in OMAC CPLEX
	
	topologieGraph = Graph()
	
	def __init__(self):
		"""
			
		"""
		
	#enddef
	
	def setPOPs(self, listPOPs):
		"""
			:param listPOPs: List of POPs.
			:type listPOPs: POP[]
			:raises:  any error on the internals
			
			The values POP.maxDisk and POP.maxNetBW are used for OMAC Model
	
		"""
		self.POPs = 0
		self.POP_id = []
		self.POP_name = []
		self.POP_location = []
		self.POP_netBW = []
		self.POP_storage = []
		
		for pop in listPOPs:
			
			self.POP_id.append(pop.id)
			self.POP_netBW.append(pop.maxNetBW)
			self.POP_storage.append(pop.maxDisk)
			self.POP_name.append(pop.name)
			self.POP_location.append ( self.Location_id.index( pop.locationId  ) )
			self.POPs = self.POPs + 1
			
			
		#endfor
		
		self.hops = [ [0 for x in range(self.POPs) ] for y in range(self.POPs)]
		
		for popA in listPOPs:
			for popB in listPOPs:
				node_src = self.topologieGraph.vs.find(name = (popA.location.name))
				node_dst = self.topologieGraph.vs.find(name = (popB.location.name))
			
				SPT = self.topologieGraph.get_shortest_paths(node_src,to = node_dst, output="epath" )[0];
			
				self.hops[self.POP_id.index(popA.id)][self.POP_id.index(popB.id)] = len(SPT)
		
		
	#enddef
	

	
	def setvCDNs(self, listvCDNs):
		"""
			:param listvCDNs: List of vCDNs in the Infra
			:type listvCDNs: vCDN[]
			:raises:  any error on the internals
	
		"""
		self.vCDNs = 0
		self.vCDN_id = []
		self.vCDN_name = []
		self.vCDN_pop = []
		self.vCDN_size = []
		
		##### OMAC assumes that a vCDN is located only in 1 server, so there is only 1 Instance per vCDN
		##### But HMAC allows for multiple Instances of the same vCDN
		
		for v in listvCDNs:
			self.vCDN_id.append(v.id)
			self.vCDN_size.append(v.vDisk)
			self.vCDN_name.append(v.name)
			if v.instances:
				firstInstance = v.instances[0]
				self.vCDN_pop.append (  self.POP_id.index(firstInstance.popId)  )
			else:
				self.vCDN_pop.append (0)
				
			
			self.vCDNs = self.vCDNs + 1
			
	#enddef
	
	def setClientGroups(self,clientGroups):
		"""
			:param clientGroups: List of ClientGroups
			:type pops: ClientGroup[]
			:raises:  any error on the internals
		"""
		self.Clients = 0
		self.Client_id = []
		self.Client_name = []
		self.Client_location = []
		
		for c in clientGroups:
			self.Client_id.append(c.id)
			self.Client_name.append(c.name)
			self.Client_location.append ( self.Location_id.index( c.locationId  ) )
			self.Clients = self.Clients + 1
	#enddef
	
	
	def setDemands(self,listDemands):
		"""
			:param demands: List of Demands
			:type demands: Demand[]
			:raises:  any error on the internals
						
			.. note:: The list of Demands are assumed to be valid, they are not checked in this function.
		"""
		
		self.DemandsBW = [ [0 for x in range(self.vCDNs) ] for y in range(self.Clients)]
		self.Y = [ [[0 for z in range(self.vCDNs) ] for x in range(self.Clients) ] for y in range(self.POPs)]
		self.Z =  [ [ [[0 for z in range(self.Clients) ] for x in range(self.vCDNs) ] for y in range(self.Locations)]  for w in range (self.Locations)]
		
		for dem in listDemands:
			try:
				self.DemandsBW [ self.Client_id.index(dem.clientGroupId) ][ self.vCDN_id.index(dem.vcdnId) ] = dem.bw
				
				self.Y [ self.POP_id.index(dem.popId) ] [ self.Client_id.index(dem.clientGroupId) ][ self.vCDN_id.index(dem.vcdnId) ]= 1
			except IndexError:
				continue
			
			node_src = self.topologieGraph.vs.find(name = (dem.clientGroup.location.name))
			node_dst = self.topologieGraph.vs.find(name = (dem.pop.location.name))
			
			SPT = self.topologieGraph.get_shortest_paths(node_src,to = node_dst)[0];
			
			for k in range (0 , len(SPT) -1):
		
				LocationAName = self.topologieGraph.vs['name'][SPT[k]]
				LocationBName = self.topologieGraph.vs['name'][SPT[k+1]]
				try:
					self.Z[self.Client_id.index(dem.clientGroupId)][self.vCDN_id.index(dem.vcdnId)][ self.Location_name.index(LocationAName) ] [self.Location_name.index(LocationBName)] = 1
				except IndexError:
					continue
	#enddef
	
	def setTopologie(self, locationsList, linksList):
		"""
			:param locationsList: List of Locations as defined by the Operator's Infrastructure
			:type locationsList: Location[]
			:param linksList: List of NetLinks as defined by the Operator's Infrastructure
			:type linksList: NetLink[]
		"""
		
		self.topologieGraph = Graph()
		
		for l in locationsList:
			self.topologieGraph.add_vertex(name=(l.name))
			
		for l in linksList:
			self.topologieGraph.add_edge((l.locationA.name),(l.locationB.name))
		#endfor
		
		self.Locations = 0
		self.Location_id = []
		self.Location_name = []
		
		for l in locationsList:
			self.Location_id.append(l.id)
			self.Location_name.append(l.name)
			self.Locations = self.Locations + 1
			
		self.Capacity = [ [0 for x in range(self.Locations) ] for y in range(self.Locations)]
		
		for l in linksList:
			try:
				self.Capacity [ self.Location_id.index(l.locationAId) ][ self.Location_id.index(l.locationBId) ] = l.capacity
				self.Capacity [ self.Location_id.index(l.locationBId) ][ self.Location_id.index(l.locationAId) ] = l.capacity
			except IndexError:
				continue
	

	#enddef
	
	def setMigrationCost(self,migCosts):
		"""
			:param migCosts: List of MigrationCostMultiplier as defined by the Operator's Infrastructure
			:type migCosts: MigrationCostMultiplier[]
		"""
		self.MigCosts = [ [1.0 for x in range(self.POPs) ] for y in range(self.POPs)]
		
		
		for c in migCosts:
			try:
				self.MigCosts [ self.POP_id.index(c.popAId) ][ self.POP_id.index(c.popBId)  ] = c.costMultiplier
				self.MigCosts [ self.POP_id.index(c.popBId) ][ self.POP_id.index(c.popAId)  ] = c.costMultiplier
			except IndexError:
				continue
			
	#enddef
	
	def optimize(self):
		"""
			Writes a .dat file for CPLEX engine to run next to the .mod file already prepared
			
			At the end of the execution, get the 2 CPLEX files from '../CPLEX/*'
			
			:returns: True is all went OK, False if it was unable to write the file.
			 
		"""
		try:
			
			directory = os.path.dirname(os.path.abspath(__file__))
			path = os.path.join(directory, '../CPLEX/OMAC.dat')
			f = open(path, 'w')
			
		except IOError:
			logger.exception(Messages.Unable_Write_File_S % str(path))
			return False
		
		f.write("//OMAC CPLEX Data file\n\n")
		
		#Dimensions
		f.write("S = %d ;\n" % self.POPs)
		f.write("N = %d ;\n" % self.Clients)
		f.write("F = %d ;\n" % self.vCDNs)
		f.write("L = %d ;\n" % self.Locations)
		f.write("\n\n")
		
		f.write("servers_Names = " + str(self.POP_name) + ";\n")
		f.write("clients_Names = " + str(self.Client_name) + ";\n")
		f.write("vcdns_Names = " + str(self.vCDN_name) + ";\n")
		f.write("locations_Names = " + str(self.Location_name) + ";\n")
		f.write("\n\n")
		
		#Array values
		
		#Python prints an L at the end of long integers, but CPLEX does not get them. So they are removed
		f.write("D = " + str(self.POP_netBW).replace("L","") + ";\n")
		f.write("\n\n")
		f.write("volume = " + str(self.POP_storage).replace("L","") + ";\n")
		f.write("\n\n")
		f.write("size_of = " + str(self.vCDN_size).replace("L","") + ";\n")
		f.write("\n\n")
		f.write("serverLocation = " + str(self.POP_location) + ";\n")
		f.write("\n\n")
		f.write("clientLocation = " + str(self.Client_location) + ";\n")
		f.write("\n\n")
		f.write("serverOf = " + str(self.vCDN_pop) + ";\n")
		f.write("\n\n")
		
		
		#Matrix values
		f.write("d = " + matrix2string(self.DemandsBW) + ";\n")
		f.write("\n\n")
		f.write("C = " + matrix2string(self.Capacity) + ";\n")
		f.write("\n\n")
		f.write("hopcount = " + matrix2string(self.hops) + ";\n")
		f.write("\n\n")
		f.write("migrationCostK = " + matrix2string(self.MigCosts) + ";\n")
		
		f.close()
		
		logger.debug(Messages.OMAC_DAT_S % str(path))
		
		return True
		
		
	#enddef

#endclass

class NCUPM(object):
	"""
		
		This model represents the exponential law relating a Demand BW with a QoE metric
		
		This is a realization of NCUPM part of the thesis "Qualite d'Experience et Adaptation de services video" of M. Mamadou Tourad DIALLO
		
		Ref: http://samovar.telecom-sudparis.eu/spip.php?article824&lang=fr
		
		:raises: ValueError
	"""
	
	def __init__(self):
		"""
			
			The Model is initiated from the global variables (NCUPM_alpha,NCUPM_beta,NCUPM_gamma)
			These variables are read from the INI file, or taken from default values
			
		"""
		self.alpha = NCUPM_alpha
		self.beta = NCUPM_beta
		self.gamma = NCUPM_gamma
	
		self.minMOS =  self.alpha 
		self.maxMOS =  self.alpha + self.beta*exp( self.gamma * (-1.0) )
	
	def x(self,mos):
		"""
		 For a given 'MOS' value to achieve, there is a BW adjustment coefficient 'x' given by the model
		
		This coefficient x is to be divided by the original BW to have the adjusted one.
		
		:param mos: a MOS value to achieve with the adjusted BW
		:type mos: float
		
		:returns: A coefficient x in the interval [1,10]
		:rtype: float
		
		:raises: ValueError in case of exception in the math formulae
		
		"""
		
		try:
			x = log( self.beta / (mos - self.alpha) ) / self.gamma
		except :
			raise ValueError
		
		if x<1 :
			x = 1
		if x>10 :
			x = 10
		
		return x
		

#endclass

def matrix2string(matrix):
	"""
		From a 2d matrix; a string is returned in the form of a print
		
		This is to agree with the CPLEX array notation
		
		>>> matrix[rows][columns]
		
		Becomes
		
		[\n
		[ columns ],\n
		[ columns ],
		[ columns ],
		... rows ...\n
		]
		
		:param matrix: a 2d matrix
		:type matrix: int or float or String
		
	"""
	ret = "[\n"
	for r in matrix:
		ret = ret + str(r).replace("L","") + " ,\n"
		#Python prints an L at the end of long integers, but CPLEX does not get them. So they are removed
	ret = ret + "]"
	return ret
#enddef

def  str_array( listString):
	"""
		Becase the way tha Python prints an array is different from CPLEX,
			this function goes the proper CPLEX writing of Arrays
			
		:param listString: A list of values
		:type listString: List[]
		
		:returns: The String printing of the array, in CPLEX format
		:rtype: String
		
	"""
	ret = "{"
	for i in range(0, len(listString)-1):
		ret = ret + "\"" + listString[i] + "\","
	ret = ret + "\"" + listString[i] + "\"}"
	return ret
