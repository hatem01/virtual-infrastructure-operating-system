-- \brief Database Description
--
-- \author Ignacio Tamayo, TSP, 2016
-- \version 1.4
--
-- \seealso DataModels.py
--
-- \internal 
-- Limit the access scope according to security policy or system access


-- 
-- vIOSimulator
-- Copyright (c) 2016 Telecom SudParis - RST Department
-- Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
-- The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
--

DROP DATABASE IF EXISTS vios;
CREATE DATABASE vios;
GRANT ALL PRIVILEGES ON vios.* TO 'vios'@'localhost' IDENTIFIED BY 'vIOS_DBPASS';
GRANT ALL PRIVILEGES ON vios.* TO 'vios'@'%' IDENTIFIED BY 'vIOS_DBPASS';

USE vios

-- \table Locations
-- UNIQUE = name; To avoid confusion on the related tables (A location name is unique in a certain area; and if not it can be made so)
-- \related NetLinks, ClientGroups, POPs

DROP TABLE IF EXISTS Locations;

CREATE TABLE Locations(
	id int AUTO_INCREMENT,
	name varchar(60) not null,
	geo varchar(200)  null,
	created_at DATETIME     ,
	modified_at DATETIME      ,
	PRIMARY KEY (id),
	unique(name)
);

-- \table NetLinks
-- UNIQUE = (locationAId,locationBId) as not to have 2 entries for the same link. At DB it is CHECKED that (locationAId <> locationBId) to avoid loops
-- Birectionality is not checked in DB, so (locationAId,locationBId) and (locationBId,locationAId) can happen
-- `capacity` is in Mbps
-- \related Locations
-- On UPDATE/DELETE a Location, if there is a NetworkLink to or from those locations, the UPDATE/DELETE is stopped and an error happens. Delete the NetworkLinks first

DROP TABLE IF EXISTS NetLinks;

CREATE TABLE NetLinks(
	id int AUTO_INCREMENT,
	locationAId int not null,
	locationBId int not null,
	capacity int,
	created_at DATETIME      ,
	modified_at DATETIME      ,
	PRIMARY KEY (id),
	unique(locationAId,locationBId),
	check (locationAId <> locationBId),
	FOREIGN KEY (locationAId) REFERENCES Locations(id)  ON UPDATE RESTRICT ON DELETE RESTRICT,
	FOREIGN KEY (locationBId) REFERENCES Locations(id)  ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- \table POPs
-- UNIQUE = (region,url,region,tenant,loginUser) as not to have 2 entries for the OpenStack controller. If the Same OpenStack server is used, either there must be a different user/tenant/region
-- UNIQUE = (name) as to have single identifiable names
-- UNIQUE = (locationId) as to keep a single POP in each location. This assumtion might change, but it will impact most of the OPAC/HMAC implementation code (and break the foreing key)
--
-- `url`,`region`,`loginUser`,`loginPass`,`tenant`  are the same credentials used by the Nova CLI client, ussually put in Enviroment Variables
-- `url` to be the Public Keystone Endpoint, versioned
-- `region` can be NULL
-- `url` is expected to be the Public/Admin Keystone
-- `totalDisk`,`totalRAM`,`totalCPU`, `totalNetBW` are parameters set by the Optimizer, based on their installation and knowledge of the Infra
-- `maxDisk`,`maxRAM`,`maxCPU` are parameters calculated by OpenStack, by summing the capacities of the Hypervisors member of this POP
-- `curDisk`,`curRAM`,`curCPU`,,`curInstances` are parameters calculated by OpenStack, by summing the usage of the Hypervisors member of this POP
-- `curNetBW` is calculated by OpenStack, by summing the network statistics of all the Instances in the POP
-- `xDisk` in GB,`xRAM` in MB,`xCPU` in units, `xNetBW` in Mbps
--
-- \related Locations, Instances, Hypervisors, Flavors, HmacResults
-- On UPDATE/DELETE a Location, if there is a PoP associated, the change is PREVENTED and an ERROR given. First delete/update the POP

DROP TABLE IF EXISTS POPs;

CREATE TABLE POPs(
	id int AUTO_INCREMENT,
	name varchar(20) not null,
	locationId int not null,
	url varchar(100),
	region varchar(60),
	tenant varchar(60),
	loginUser varchar(60),
	loginPass varchar(60),
	totalDisk int,
	totalRAM int,
	totalCPU int,
	totalNetBW int,
	maxDisk int,
	maxRAM int,
	maxCPU int,
	maxNetBW int,
	curDisk int,
	curRAM int,
	curCPU int,
	curNetBW int,
	curInstances int,
	created_at DATETIME  ,
	modified_at DATETIME,
	PRIMARY KEY (id),
	unique(name),
	unique(url,region,tenant,loginUser),
	unique(locationId),
	FOREIGN KEY (locationId) REFERENCES Locations(id)  ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- \table Hypervisors
-- UNIQUE = (name,popId). 2 Hypervisors can belong to a single POP, as long as they have different names. 2 Hpervisors can have the same name, but on different POPs. This reflects OpenStack characteristics
--
-- `xDisk` in GB,`xRAM` in MB,`xCPU` in units, `xNetBW` in Mbps
--
-- \related POP
-- On UPDATE/DELETE a POP, if there is an Hypervisor associated, the Hypervisor is also UPDATE/DELETE

DROP TABLE IF EXISTS Hypervisors;

CREATE TABLE Hypervisors(
	id int AUTO_INCREMENT,
	name varchar(20) not null,
	popId int not null,
	model varchar(20),
	maxDisk int,
	maxRAM int,
	maxCPU int,
	maxNetBW int,
	curDisk int,
	curRAM int,
	curCPU int,
	curNetBW int,
	curInstances int,
	created_at DATETIME  ,
	modified_at DATETIME,
	PRIMARY KEY (id),
	unique(name,popId),
	FOREIGN KEY (popId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE
);


-- \table Flavors
-- UNIQUE = (osId,popId). 2 POP can have the same Flavor ID in OpenStack, coincidence. 1 POP has unique Flavors. This reflects OpenStack characteristics
--
-- `xDisk` in GB,`xRAM` in MB,`xCPU` in units
-- `osId` is the OpenStack ID given to this flavor
--
-- \related POP
-- On UPDATE/DELETE a POP, if there is an Flavor associated, then it is also UPDATE/DELETE

DROP TABLE IF EXISTS Flavors;

CREATE TABLE Flavors(
	id int AUTO_INCREMENT,
	name varchar(20) not null,
	popId int not null,
	osId varchar(60),
	rootDisk int,
	RAM int,
	CPU int,
	ephemeralDisk int,
	swapDisk int,
	isPublic boolean,
	created_at DATETIME  ,
	modified_at DATETIME,
	PRIMARY KEY (id),
	unique(osId,popId),
	FOREIGN KEY (popId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE
);

-- \table Metrics
-- From OpenStack Ceilometer
--
-- `sampletime` is the OpenStack Ceilometer timestamp. This is in STRING as not to mix the timestamps of the DB with the Python host with the Ceilometer DB
--
-- \related Instance
-- On UPDATE/DELETE an Instance, if there is a Metric associated, then it is also UPDATE/DELETE

DROP TABLE IF EXISTS Metrics;

CREATE TABLE Metrics (
	id int AUTO_INCREMENT,
	instanceId  int not null,
	durationHours int not null,
	cpuUtil_min float, cpuUtil_max float, cpuUtil_avg float, cpuUtilUnits varchar(20),
	diskrootsize_min float, diskrootsize_max float, diskrootsize_avg float,diskrootsizeUnits varchar(20),
	instance_min float, instance_max float, instance_avg float,instanceUnits varchar(20),
	memory_min float, memory_max float, memory_avg float,memoryUnits varchar(20),
	networkInBytes float, networkOutBytes float, networkBytesUnits varchar(20),
	networkInbps_min float, networkInbps_max float, networkInbps_avg float,networkbpsUnits varchar(20),
	networkOutbps_min float, networkOutbps_max float, networkOutbps_avg float,
	vcpu_min float, vcpu_max float, vcpu_avg float,vcpuUnits varchar(20),
	sampletime varchar(40),
	modified_at DATETIME, 
	PRIMARY KEY (id),
	unique(instanceId),
	FOREIGN KEY (instanceId) REFERENCES Instances(id)  ON UPDATE CASCADE ON DELETE CASCADE
);


-- \table MigrationCostMultipliers
-- Values of the Migration decision, the value is multiplied to the calculated cost to tune the Migration decision
-- UNIQUE = (popAId,popBId) as not to have 2 entries for the same migration. At DB it is CHECKED that (popAId <> popBId) to avoid loops
-- Birectionality is not checked in DB, so (popAId,popBId) and (popBId,popAId) can happen
--
-- `costMultiplier` is a value that could be used as cost multiplier.
--
-- \related Locations
-- On UPDATE/DELETE a POP, if there is a MigrationCostMultiplier associated, then it is also UPDATE/DELETE

DROP TABLE IF EXISTS MigrationCostMultipliers;

CREATE TABLE MigrationCostMultipliers(
	id int AUTO_INCREMENT,
	popAId int not null,
	popBId int not null,
	costMultiplier float,
	created_at DATETIME ,
	modified_at DATETIME,
	PRIMARY KEY (id),
	unique(popAId,popBId),
	check (popAId <> popBId),
	FOREIGN KEY (popAId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (popBId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE
);



-- \table ClientGroups
-- UNIQUE = (name). As the Clients can be placed in any location, the name must be unique to be able to identify them
-- `connectionBW` is the BW in Mbps that the client groups has to the location
-- \related Location, QOSMaps
-- On UPDATE/DELETE a Location, if there is a ClientGroups associated, the change is restricted and ERROR happens. First delete/update the ClientGroups

DROP TABLE IF EXISTS ClientGroups;

CREATE TABLE ClientGroups(
	id int AUTO_INCREMENT,
	locationId int not null,
	name varchar(20) not null,
	connectionBW int,
	created_at DATETIME     ,
	modified_at DATETIME      ,
	PRIMARY KEY (id),
	unique(name),
	FOREIGN KEY (locationId) REFERENCES Locations(id)  ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- \table vCDNs
-- UNIQUE = (name). Because each vCDN is identified by a single name. This allows, later; so associate a vCDN to a file in ObjectStorage or a specific VM Image
--
-- `url`,`loginUser`,`loginPass`,`tenant`  are the same credentials used by the Nova CLI client, ussually put in Enviroment Variables (via a file)
-- `xDisk` in GB,`xRAM` in MB,`xCPU` in units
-- `xNetBW` is not used for now, NULL
-- `defaultQosBW` is the BW in kbps to be given ClienGroups connecting to this vCDN, by default. BW in kbps
--
-- \related Instance, QOSMaps

DROP TABLE IF EXISTS vCDNs;

CREATE TABLE vCDNs(
	id int AUTO_INCREMENT,
	name varchar(20) not null,
	tenant varchar(20) not null,
	loginUser varchar(20) not null,
	loginPass  varchar(20) not null,
	vDisk int,
	vRAM int,
	vCPU int,
	vNetBW int,
	vInstances int,
	
	defaultQosBW int,
	
	created_at DATETIME     ,
	modified_at DATETIME      ,
	unique(name,tenant,loginUser),
	PRIMARY KEY (id)
);

-- \table QOSMaps
-- UNIQUE = (clientGroupId,vcdnId). A QOSMap entry is an SLA entry set by the vCDN to serve the Clients in a specific way. Otherwise the vCDNs.defaultQosBW is assumed
--
-- `bw` is the BW in kbps to be given to a specific ClienGroup connecting to this vCDN. BW in kbps
--
-- \related vCDNs, ClientGroups
-- On UPDATE/DELETE a ClientGroup, if there is a QOSMap associated, the change is restricted and ERROR happens
-- On UPDATE/DELETE a vCDN, if there is a QOSMap associated, the change is restricted and ERROR happens

DROP TABLE IF EXISTS QOSMaps;

-- CREATE TABLE QOSMaps(
	-- id int AUTO_INCREMENT,
	-- clientGroupId int not null,
	-- vcdnId int not null,
	-- bw int,
	-- created_at DATETIME    ,
	-- modified_at DATETIME      ,
	-- PRIMARY KEY (id),
	-- unique(clientGroupId,vcdnId),
	-- FOREIGN KEY (clientGroupId) REFERENCES ClientGroups(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
	-- FOREIGN KEY (vcdnId) REFERENCES vCDNs(id) ON UPDATE RESTRICT ON DELETE RESTRICT
-- );


-- \table Instances
-- UNIQUE = (popId,vcdnId). 1 server that holds several vCDNs inside, and a vCDN can be in many POPs, but the pair is unique ()
--
-- `xRAM` in MB,`xCPU` in units
--
-- \related POPs, vCDNs, Demands
-- On UPDATE/DELETE a POP, if there is an Instance associated, the Instance is also UPDATE/DELETE
-- On UPDATE/DELETE an vCDN, if there is an Instance associated, the Instance is also UPDATE/DELETE

DROP TABLE IF EXISTS Instances;

CREATE TABLE Instances(
	id int AUTO_INCREMENT,
	popId int not null,
	vcdnId int not null,
	maxRAM int,
	maxCPU int,
	curRAM int,
	curCPU int,
	curInstances int,
	maxInstances int,
	created_at DATETIME  ,
	modified_at DATETIME,
	PRIMARY KEY (id),
	unique(popId,vcdnId),
	FOREIGN KEY (popId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (vcdnId) REFERENCES vCDNs(id)  ON UPDATE CASCADE ON DELETE CASCADE
);



-- \table HmacResults
-- Results of HMAC optimization algorithm
-- UNIQUE = (demandId) as a migration HMAC responds to a single Demand.
-- 
-- 
-- `cost` is a value that is produced by HMAC, calculated as the vCDN.size * migration path hops
-- `delay` is a value that is produced by HMAC, calculated as the vCDN.size / minimum link capacity
-- `minBW` is the minimum link BW found on the gomory Tree for this migration. Used to know the liminit BW for the migration. In Mbps
-- `migrate` indicates that the entry is an effective Migration. If false, the entry is a Redirect (the dstPOP has already an Instance of the vCDN)
--
-- \related Demands, POPs, Instances
-- On UPDATE/DELETE a POP, if there is a Migration associated, then it is also UPDATE/DELETE
-- On UPDATE/DELETE an Instance, if there is a Migration associated, then it is also UPDATE/DELETE

DROP TABLE IF EXISTS HmacResults;

CREATE TABLE HmacResults(
	id int AUTO_INCREMENT,
	instanceId int not null,
	dstPopId int not null,
	
	delay float,
	cost float,
	minBW float,
	-- migrate boolean,
	created_at DATETIME,
	PRIMARY KEY (id),
	
	unique (instanceId,dstPopId),
	
	FOREIGN KEY (dstPopId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (instanceId) REFERENCES Instances(id)  ON UPDATE CASCADE ON DELETE CASCADE
);





-- \view Migrations
-- 
-- This view has the actual Migrations
-- 
-- \related HmacResults

DROP VIEW IF EXISTS Migrations;

CREATE VIEW Migrations as
SELECT * from HmacResults WHERE migrate = True;

-- \view Redirects
-- 
-- This view has the Redirections, meaning that the Result of HMAC is a Migration but the destination POP already has the vCDN
-- 
-- \related HmacResults

DROP VIEW IF EXISTS Redirects;

-- CREATE VIEW Redirects as
-- SELECT id,instanceId, dstPopId, demandId, migrate,created_at  from HmacResults WHERE migrate = False;












-- \table Demands
-- UNIQUE = (ClientGroupId,popId,vcdnId). As only 1 optimal server is to supply the demand for a vCDN,
-- This should ideally associate a Demand to an Instance, but not necessarily as the Instance can just have disappeared when the Demand was calculated or measured
--
-- `volue` is a number presenting the demand volume, concurrent demans, demand's importance, etc. This value is only used for sorting
-- `bw` is the total BW required for this Demand, in Mbps.
-- `validInstance` is True if the demanded pair (vCDN,POP) is actually an exiting Instance or not
--
-- \related POPs, ClientGroups, HmacResults, vCDNs
-- On UPDATE/DELETE a ClientGroup, if there is a Demands associated, it is also UPDATE/DELETE
-- On UPDATE/DELETE an POP, if there is a Demand associated, it is also UPDATE/DELETE
-- On UPDATE/DELETE an vCDN, if there is a Demand associated, it is also UPDATE/DELETE

DROP TABLE IF EXISTS Demands;

CREATE TABLE Demands(
	id int AUTO_INCREMENT,
	clientGroupId int not null,
	popId int not null,
	vcdnId int not null,
	volume int,
	bw float,
	invalidInstance boolean,
	hmacResultId int,
	created_at DATETIME  ,
	PRIMARY KEY (id),
	unique(clientGroupId,popId,vcdnId),
	FOREIGN KEY (clientGroupId) REFERENCES ClientGroups(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (popId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (vcdnId) REFERENCES vCDNs(id)  ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (hmacResultId) REFERENCES HmacResults(id)  ON UPDATE SET NULL ON DELETE SET NULL
);

-- \view InvalidDemands
-- 
-- This view has the Demands that do not have a valid Instance demanded
-- 
-- \related Demands

DROP VIEW IF EXISTS InvalidDemands;

CREATE VIEW InvalidDemands as
SELECT * from Demands WHERE invalidInstance = True;



-- \table AlteredDemands
-- UNIQUE = (demandId). As only 1 demand is to be altered per line
--
--
-- \related POPs, Demands
-- On UPDATE/DELETE a Demand, this is also UPDATE/DELETE
-- On UPDATE/DELETE an POP, if there is a Demand associated, it is also UPDATE/DELETE


DROP TABLE IF EXISTS AlteredDemands;

CREATE TABLE AlteredDemands(
	id int AUTO_INCREMENT,
	demandId int not null,
	dstPopId int not null,
	created_at DATETIME  ,
	PRIMARY KEY (id),
	unique(demandId),
	FOREIGN KEY (demandId) REFERENCES Demands(id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (dstPopId) REFERENCES POPs(id)  ON UPDATE CASCADE ON DELETE CASCADE
);




INSERT INTO 
Locations(name) 
VALUES ("Evry"),("Paris"),("Saclay"),("Issy"),("Chatillon"),("Boulogne"),("Versailles"),("Antony"),("Palaiseau"),("Orly"),("Melun"),("Corbeille"),("Argenteuil"),("Creteil"),("Ivry-sur-Seine"),("Poissy"),("Limours"),("Sarcelles")
;



INSERT INTO 
ClientGroups(locationId,name,connectionBW) 
VALUES 
(12,"Clients12",10),
(1,"Clients11",10),
(10,"Clients10",10),
(8,"Clients8",10),
(7,"Clients7",10),
(9,"Clients9",10),
(6,"Clients6",10),
(5,"Clients5",10)
;


INSERT INTO  vCDNs(name, tenant, loginUser, loginPass, vDisk ,vRAM ,vCPU ,	vNetBW, vInstances,defaultQosBW )
VALUES 	
("NetFlix","tenant_netflix","user_netflix","USER_PASS",60,4,2,100,1,10),
("TF1","tenant_tf1","user_tf1","USER_PASS",20,4,1,10,1,10),
("HBO","tenant_hbo","user_hbo","USER_PASS",20,4,1,10,1,10)
;


-- INSERT INTO QOSMaps( clientGroupId , vcdnId ,	bw)
-- VALUES (6,1,200),(1,1,20),(2,2,600),(4,3,50),(7,1,100),(1,2,100)
-- ;

INSERT INTO POPs( 	name ,	locationId , 	url ,	tenant, loginUser ,	loginPass ,  totalDisk , totalRAM , totalCPU , totalNetBW  )
VALUES 
("PopSaclay",1,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("PopEvry",2,"http://controller-evry:35357/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("PopParis",3,"http://controller-saclay:35357/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000)
;

INSERT INTO POPs( 	name ,	locationId , 	url ,region,	tenant, loginUser ,	loginPass ,  totalDisk , totalRAM , totalCPU , totalNetBW  )
VALUES 
("PopOrly",4,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000)
;


