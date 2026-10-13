DELETE FROM `exepPart2` WHERE `partNo` LIKE '%12345%' ;
DELETE FROM `egproBOM2` WHERE `typeID` LIKE 'UR-1234' ;
INSERT INTO `egproBOM2` (`typeID`, `partNo_egpro`, `qty`, `plant`, `regDate`) 
VALUES 
('UR-1234','012345',1,0,'2021-06-25 10:25:34'), 
('UR-1234','123451',3,0,'2021-06-25 10:25:34'), 
('UR-1234','123452A',10,0,'2021-06-25 10:25:34') ;
DELETE FROM `bossBOM2` WHERE `typeID` LIKE 'UR-1234' ;
INSERT INTO `bossBOM2` (`typeID`, `orderNumber`, `partNo`, `qty`, `regDate`) 
VALUES 
('UR-1234', '110000001', '012345', '1', CURRENT_TIMESTAMP), 
('UR-1234', '110000001', '123451', '3', CURRENT_TIMESTAMP),
('UR-1234', '110000001', '123452A', '10', CURRENT_TIMESTAMP),
('UR-1234', '110000001', '123453C', '1', CURRENT_TIMESTAMP),
('UR-1234', '110000001', '123454', '1', CURRENT_TIMESTAMP),
('UR-1234', '110000001', '123455', '1', CURRENT_TIMESTAMP),
('UR-1234', '110000001', '123456', '1', CURRENT_TIMESTAMP) ;
DELETE FROM `liveOrder_sub2` WHERE `orderNumber` LIKE '110000001' ;
INSERT INTO `liveOrder_sub2` 
(`orderNumber`, `typeID`, `orderQty`, `reg_date`, `start_date`, `finish_date`, `prod_result`, `plant_ID`, `sashizu_type`, `update_date`, `LINE`) 
VALUES 
('110000001', 'UR-1234', '45', '2021-05-17', '2021-06-20', '2021-06-27', '0', 'B020', 'ZP11', '2021-05-17', 'R02') ;