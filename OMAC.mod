/*********************************************
 * OPL 12.6.2.0 Model
 * Author: i_khedhe
 * Creatlocationsn Date: 12 déc. 2015 at 19:32:41
 *********************************************/
/*********************************************
 *
 *  ### Modified by Ignaclocations Tamayo to separate Data from Model
 * 
 * 	Ignaclocations Tamayo, TSP, 2016
 *	Verslocationsn 1.3
 *	Date: August 2016
 *	
 * [Reference](http://www.ibm.com/support/knowledgecenter/SSSA5P_12.6.2/ilog.odms.ide.help/OPL_Studlocations/opllangref/topics/opl_langref_data_init_arrays.html?view=embed)
 * 
 **********************************************/

/****************
Range parameters 
****************/

int S=...; 	//number of POPs
int N=...; 	//numbe of clients
int F=...; 	//number of vCDNs
int L=...; 	//number of locatlocationsns/clients

range servers=1..S; 		// POPs
range clients=1..N; 		// clients
range vcdns=1..F; 			// vCDNs 
range locations=1..L; 		// index for representing a locatlocationsn


/**********************
 Array and Vertor parameters 
 **********************/
 
int clientLocation[clients] = ...; 					// Location where the client can be found
int serverLocation[servers] = ...;  					// Location where the POP can be found

int serverOf[vcdns] = ... ;							// POP where the vCDN is initially. Use for the `c` calculation 

float d[clients][vcdns]=...; 						// debit du film "vcdns" dans node "clients"
float C[locations][locations] = ...; 				// link capacity of any i,j edge 
float D[servers] = ... ;							// Streaming capacity of the Server
int hopcount[servers][servers] = ...;				// Topologie hop counts for the shortest path
float migrationCostK[servers][servers] = ...;		// Migration cost Multipliers defined by the Operator

int size_of[vcdns] = ... ;							// Size requiered in a POP to host a vCDN
int volume[servers] = ... ;							// Total storage capacity for a POP


float c[servers][vcdns] ; 							//cost of migrating f to servers, calculated
	
	 
/****************** Initializatlocationsn Instructlocationsns ***********/

// Initialisatlocationsn of the maximum server streaming
//
//execute 
//{
//	for(var i in servers)
//	{
//		if (i<=2)
//			D[i] = 200; // in GB/S
//		else
//			D[i] = 200; // in GB/S
//	}
//}
//
//// Initializatlocationsn of capacity's links inside the network'.
//
//execute 
//{
//	for(var i in locations)
//	{
//		for (var j in locations)
//	{
//	C[i][j] = 0;  // in GB/S
//	}
//}
//}
//
//// Decalaratlocationsn and initialisatlocationsn of vCDN parameters (size), it can be also CPU, RAM or any system parameters.
//
//execute 
//{
//	for(var i in vcdns) 
//	{
//		size_of[i] = 8; // in GB
//	}
//}
//
//// Decalaratlocationsn and initialisatlocationsn of the maximum storage size of each server.
//
//execute 
//{
//	for(var i in servers) 
//	{
//		volume[i] = 200;  // in GB
//	}
//}
//
//// Virtual CDN toplogy graph (virtual CDN, PoP server) à t0
//
//execute
//{
//	
//}
// 
// Migratlocationsn cost.

execute 
{
	for(var f in vcdns)
	{
		for(var s in servers)
			c[s][f]=   hopcount[ serverOf[f]  ][s]*size_of[f] * migrationCostK[ serverOf[f] ][ s ];
			   
	}
}

/****************** END Instructlocationsns ***********/


/**********************
 Decislocationsn Binary Variables 
 ***********************/

  int x_t0[servers][vcdns] =... ; 
  int y_t0[servers][clients][vcdns]=...;  
  float z_t0[clients][vcdns][locations][locations]=...; 				////////// Float ??????????????????????
 
 dvar int x[servers][vcdns]  ; 			// variable de placement du CDN
 dvar int y[servers][clients][vcdns]; 	//variable de cout de streaming
 dvar float z[clients][vcdns][locations][locations];				////////// Float ??????????????????????


/*************************
Intialization for Desicion Variables
***************************/


/********************
Objective functlocationsn which is the total migratlocationsn cost
**********************/

minimize sum(s in servers, f in vcdns) x[s][f]*c[s][f];

/******************
 Les contraintes
 ******************/
 
subject to 
{
	forall(s in servers, f in vcdns)
		const01:
			0 <= x[s][f] <=1;

	forall(op_s in servers, v in clients, f in vcdns)
		const02:
			0 <= y[op_s][v][f] <= 1;

	forall(op_s in servers, v in clients, f in vcdns)
		const03:
			y[op_s][v][f] <= x[op_s][f];
 
 	forall(v in clients, f in vcdns)
		const04:
		{
			if (d[v][f]!= 0)
				sum(op_s in servers) y[op_s][v][f] == 1;
		} 
		
	forall(op_s in servers)
		const05:
			sum(v in clients, f in vcdns) y[op_s][v][f] * d[v][f] <= D[op_s];

	forall(op_s in servers)   
		const06:
			sum(f in vcdns) x[op_s][f] * size_of[f]<= volume[op_s]; 

	forall(op_s in servers, v in clients, f in vcdns, i in locations, j in locations)
		const07:
			if (C[i][j]!=0)
			{
				if (i == clientLocation[v] ) 
					sum(j in locations) z[v][f][i][j] - sum(j in locations) z[v][f][j][i] == -1;
				else if (i == serverLocation[op_s] ) 
					sum(j in locations) z[v][f][i][j] - sum(j in locations) z[v][f][j][i] == y[op_s][v][f];
				else 
					sum(j in locations) z[v][f][i][j] - sum(j in locations) z[v][f][j][i] == 0;
			}
  
	forall(i in locations, j in locations)
		const08:
			sum(v in clients, f in vcdns) z[v][f][i][j] * d[v][f] <= C[i][j];
}

 
 
 main {
 	thisOplModel.generate();
 	cplex.solve();
  	var ofile = new IloOplOutputFile("RESULTS.txt");
 	ofile.writeln(thisOplModel.printSolution());
  	ofile.writeln("");
	ofile.writeln("Optimal objective value="+cplex.getObjValue());
	ofile.writeln("");
 	ofile.writeln("Optimal migrations are:");
  	for(s in thisOplModel.servers)
  	{
  	  	for(v in thisOplModel.vcdns)
  	  	{
  	  		if  (thisOplModel.x[s][v] == 0)
				ofile.writeln("x["+ s +"]["+ v +"]");
		}		
	}
} 

  
