-- \brief Database Data for simulation and testing
--
-- \author Ignacio Tamayo, TSP, 2016
-- \version 1.4
--
-- \seealso DataModels.py
--


-- 

-- vIOSimulator

-- Copyright (c) 2016 Telecom SudParis - RST Department

-- Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

-- The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

--


USE vios;

Delete  FROM MigrationCostMultipliers;

DELETE * FROM Hypervisors

DELETE * FROM Flavors

DELETE * FROM Instances

DELETE  FROM POPs;

DELETE  FROM NetLinks;

DELETE  FROM QOSMaps;

DELETE  FROM ClientGroups;

DELETE  FROM Locations;


INSERT INTO Locations(name) VALUES
('Location1'),('Location2'),('Location3'),('Location4'),('Location5'),('Location6'),('Location7'),('Location8'),
('Location9'),('Location10'),('Location11'),('Location12'),('Location13'),('Location14'),('Location15'),('Location16'),
('Location17'),('Location18'),('Location19'),('Location20'),('Location21'),('Location22'),('Location23'),('Location24'),
('Location25'),('Location26'),('Location27'),('Location28'),('Location29'),('Location30'),('Location31'),('Location32'),
('Location33'),('Location34'),('Location35'),('Location36'),('Location37'),('Location38'),('Location39'),('Location40'),
('Location41'),('Location42'),('Location43'),('Location44'),('Location45'),('Location46'),('Location47'),('Location48'),
('Location49'),('Location50'),('Location51'),('Location52'),('Location53'),('Location54'),('Location55'),('Location56'),
('Location57'),('Location58'),('Location59'),('Location60'),('Location61'),('Location62'),('Location63'),('Location64'),
('Location65'),('Location66'),('Location67'),('Location68'),('Location69'),('Location70'),('Location71'),('Location72'),
('Location73'),('Location74'),('Location75'),('Location76'),('Location77'),('Location78'),('Location79'),('Location80'),
('Location81'),('Location82'),('Location83'),('Location84'),('Location85'),('Location86'),('Location87'),('Location88'),
('Location89'),('Location90'),('Location91'),('Location92'),('Location93'),('Location94'),('Location95'),('Location96'),
('Location97'),('Location98'),('Location99'),('Location100'),('Location101'),('Location102'),('Location103'),('Location104'),
('Location105'),('Location106'),('Location107'),('Location108'),('Location109'),('Location110'),('Location111'),('Location112'),
('Location113'),('Location114'),('Location115'),('Location116'),('Location117'),('Location118'),('Location119'),('Location120'),
('Location121'),('Location122'),('Location123'),('Location124'),('Location125'),('Location126'),('Location127'),('Location128'),
('Location129'),('Location130'),('Location131'),('Location132'),('Location133'),('Location134'),('Location135'),('Location136'),
('Location137'),('Location138'),('Location139'),('Location140'),('Location141'),('Location142'),('Location143'),('Location144'),
('Location145'),('Location146'),('Location147'),('Location148'),('Location149'),('Location150')
;


INSERT INTO 
ClientGroups(locationId,name,connectionBW) 
VALUES 
(1,'ClientGroup1',10),(2,'ClientGroup2',10),(3,'ClientGroup3',10),(4,'ClientGroup4',10),(5,'ClientGroup5',10),
(6,'ClientGroup6',10),(7,'ClientGroup7',10),(8,'ClientGroup8',10),(9,'ClientGroup9',10),(10,'ClientGroup10',10),
(11,'ClientGroup11',10),(12,'ClientGroup12',10),(13,'ClientGroup13',10),(14,'ClientGroup14',10),(15,'ClientGroup15',10),
(16,'ClientGroup16',10),(17,'ClientGroup17',10),(18,'ClientGroup18',10),(19,'ClientGroup19',10),(20,'ClientGroup20',10),
(21,'ClientGroup21',10),(22,'ClientGroup22',10),(23,'ClientGroup23',10),(24,'ClientGroup24',10),(25,'ClientGroup25',10),
(26,'ClientGroup26',10),(27,'ClientGroup27',10),(28,'ClientGroup28',10),(29,'ClientGroup29',10),(30,'ClientGroup30',10),
(31,'ClientGroup31',10),(32,'ClientGroup32',10),(33,'ClientGroup33',10),(34,'ClientGroup34',10),(35,'ClientGroup35',10),
(36,'ClientGroup36',10),(37,'ClientGroup37',10),(38,'ClientGroup38',10),(39,'ClientGroup39',10),(40,'ClientGroup40',10),
(41,'ClientGroup41',10),(42,'ClientGroup42',10),(43,'ClientGroup43',10),(44,'ClientGroup44',10),(45,'ClientGroup45',10),
(46,'ClientGroup46',10),(47,'ClientGroup47',10),(48,'ClientGroup48',10),(49,'ClientGroup49',10),(50,'ClientGroup50',10),
(51,'ClientGroup51',10),(52,'ClientGroup52',10),(53,'ClientGroup53',10),(54,'ClientGroup54',10),(55,'ClientGroup55',10),
(56,'ClientGroup56',10),(57,'ClientGroup57',10),(58,'ClientGroup58',10),(59,'ClientGroup59',10),(60,'ClientGroup60',10),
(61,'ClientGroup61',10),(62,'ClientGroup62',10),(63,'ClientGroup63',10),(64,'ClientGroup64',10),(65,'ClientGroup65',10),
(66,'ClientGroup66',10),(67,'ClientGroup67',10),(68,'ClientGroup68',10),(69,'ClientGroup69',10),(70,'ClientGroup70',10),
(71,'ClientGroup71',10),(72,'ClientGroup72',10),(73,'ClientGroup73',10),(74,'ClientGroup74',10),(75,'ClientGroup75',10),
(76,'ClientGroup76',10),(77,'ClientGroup77',10),(78,'ClientGroup78',10),(79,'ClientGroup79',10),(80,'ClientGroup80',10),
(81,'ClientGroup81',10),(82,'ClientGroup82',10),(83,'ClientGroup83',10),(84,'ClientGroup84',10),(85,'ClientGroup85',10),
(86,'ClientGroup86',10),(87,'ClientGroup87',10),(88,'ClientGroup88',10),(89,'ClientGroup89',10),(90,'ClientGroup90',10),
(91,'ClientGroup91',10),(92,'ClientGroup92',10),(93,'ClientGroup93',10),(94,'ClientGroup94',10),(95,'ClientGroup95',10),
(96,'ClientGroup96',10),(97,'ClientGroup97',10),(98,'ClientGroup98',10),(99,'ClientGroup99',10),(100,'ClientGroup100',10)
;

INSERT INTO POPs( 	name ,	locationId , 	url ,	tenant, loginUser ,	loginPass ,  totalDisk , totalRAM , totalCPU , totalNetBW  )
VALUES 
("POP3",3,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP2",2,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP1",1,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP5",5,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP9",9,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP10",10,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP14",14,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP19",19,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP21",21,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP23",23,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP35",35,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP39",39,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP47",47,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP51",51,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP59",59,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP67",67,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP78",78,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP81",81,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP89",89,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP95",95,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP105",105,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP114",114,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP128",128,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP131",131,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP135",135,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP139",139,"http://controller-saclay:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP141",141,"http://controller-evry:5000/v2.0","admin","admin","ADMIN_PASS", 1512,8096,4,10000)
;

INSERT INTO POPs( 	name ,	locationId , 	url , region,	tenant, loginUser ,	loginPass ,  totalDisk , totalRAM , totalCPU , totalNetBW  )
VALUES 
("POP11",11,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP22",22,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP33",33,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP44",44,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP55",55,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000),
("POP66",66,"http://controller-evry:5000/v2.0","regionTwo","admin","admin","ADMIN_PASS", 1512,8096,4,10000)
;


INSERT INTO  vCDNs(name, tenant, loginUser, loginPass, imagefile ,vDisk ,vRAM ,vCPU ,	vNetBW, vInstances,defaultQosBW )
VALUES 	
("NetFlix","tenant_netflix","user_netflix","USER_PASS","VideoServer",60,4,2,100,1,10),
("TF1","tenant_tf1","user_tf1","USER_PASS","VideoServer",20,4,1,10,1,10),
("TF1_HD","tenant_tf1_hd","user_tf1","USER_PASS","VideoServer",20,4,1,10,1,10),
("Hobo","tenant_tf1","user_tf1","USER_PASS","VideoServer",20,4,1,10,1,10),
("RFI","tenant_hbo","user_hbo","USER_PASS","VideoServer",20,4,1,10,1,10),
("HBO_Sport","tenant_hbo","user_hbo","USER_PASS","VideoServer",20,4,1,10,1,10),
("HBO_HD","tenant_hbo_hd","user_","USER_PASS","VideoServer",20,4,1,10,1,10),
("HBO","tenant_hbo","user_hbo","USER_PASS","VideoServer",20,4,1,10,1,10)
;



INSERT INTO MigrationCostMultipliers (popAId,popBId,costMultiplier) 
VALUES
(1 , 3, 2.5),
(1 , 5, 1.5),
(2 , 4, 0.5),
(3 , 6, 2.5),
(4 , 1, 1.5),
(6 , 2, 0.5),
(9 , 5, 3.5),
(11 , 7, 1.5),
(14 , 16, 0.5),
(16 , 1, 2.5)
;
