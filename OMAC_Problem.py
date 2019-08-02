"""
/*********************************************
 * OPL 12.6.2.0 Model
 * Author: i_khedhe
 * Creation Date: 12 dec. 2015 at 19:32:41
 *********************************************/
 
"""
"""
	As it is not clear how to express the OMAC problem in the CPLEX Python librariy (also being unable to run it because of licence constraints)
	This module generates a .dat file that is to be executed in CPLEX IDE or via CLI on an appropriate server
	
	In theory the problem could be expressed in  .LP format, but the amount of variables make this difficult (could be tried later)
	
	[REF](http://www.ibm.com/support/knowledgecenter/SSSA5P_12.6.1/ilog.odms.cplex.help/CPLEX/GettingStarted/topics/tutorials/Python/eg_lpex1.html)
	[Reference](http://www.ibm.com/support/knowledgecenter/SSSA5P_12.2.0/ilog.odms.cplex.help/Content/Optimization/Documentation/CPLEX/_pubskel/CPLEX32.html)
	
	LP notation:
	
		Maximize
		x1  + 2x2 + 3x3
		subject to
		-x1 +  x2 + x3 < = 20
		 x1 - 3x2 + x3 < = 30
		with these bounds
		0 <= x1 <= 40
		0 <= x2 <= infinity
		0 <= x3 <= infinity
	
	Python Example:
	
		# data common to all populateby functions
		my_obj      = [1.0, 2.0, 3.0]
		my_ub       = [40.0, cplex.infinity, cplex.infinity]
		my_colnames = ["x1", "x2", "x3"]
		my_rhs      = [20.0, 30.0]
		my_rownames = ["c1", "c2"]
		my_sense    = "LL"
	
	Simpler libraries [like PyPCX http://www.stat.washington.edu/~hoytak/code/pycpx/, pycplex, docplex ] that use numpy matrix
	
	
"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

#"""
 #//parameters
 #int S=...; //number of servers
 #int N=...; //numbe of nodes
 #int F=...; //number of file VNF
 #int L=...; //number of edges/links
 
 #range servers=1..S; // virtual serveers
 #range nodes=1..N; // clients
 #range files=1..F; // videos/vCDNs/services
 #range jo=1..L; // index for representing links
 #range io=1..L; // links's index

#"""

#Params initalization
#POPs are the Servers
S = 0
obj_S = []
DbId_S = []
debit_max = []
volume = []
for pop in listPOPs:
	obj_S.append(pop)
	DbId_S.append(pop.id)
	debit_max.append(pop.totalNetBW)
	volume.append(pop.totalDisk)
	S = S+1

F = 0
obj_F = []
DbId_F = []
size_of = []
for v in listVCDNs:
	obj_F.append(v)
	DbId_F.append(v.id)
	size_of.append(v.vDisk)
	F = F+1

N = 0
obj_N = []
DbId_N = []
for c in listClientGroups:
	obj_N.append(c)
	DbId_N.append(c.id)
	N = N+1

L = 0
obj_L = []
DbId_L = []
C = []
for l in listNetworkLinks:
	obj_L.append(l)
	DbId_L.append(l.id)
	C.append(l.capacity)
	L = L+1


"""
	int d[nodes][files]; // debit du film "files" dans node "nodes""
	int C[io]; // link capacity of any  edge 
	int debit_max[servers];
	int z[nodes][files][io]; ///network flow parameters
	int volume[servers];	//maximum storage size of each server
	int size_of[files];	// vCDN parameters (size)
	float c[servers][servers][files];		//cost
 
"""
d = [ [0 for x in range(N) ] for y in range(N)]
for dem in listDemands:
	d [ DbId_N.index(dem.ClientGroupId) ][ DbId_F.index(dem.vCDNId) ] = dem.qowBW

c  = [ [ [0 for x in range(S) ] for y in range(S)] for z in range(F)]
for cost in CostPopXPopXvCDN:
	c [ DbId_L.index(cost.locationAId) ][ DbId_L.index(cost.locationBId) ] = cost.cost

z  = [ [ [0 for x in range(N) ] for y in range(F)] for z in range(L)]
