-- Create the database
CREATE DATABASE sinvcapture;

-- Switch to the database 
USE sinvcapture;

-- View data from each table
SELECT * FROM INVENTORYCAPTURE;
SELECT * FROM USERMASTER;
SELECT * FROM NEXTUPNUMBER;
SELECT * FROM DOWNLOADINVENTORY;

-- Update number of lines in NEXTUPNUMBER table
UPDATE NEXTUPNUMBER SET NUMBEROFLINES = 10;

-- Update PREFIX to empty (use single quotes, not double)
UPDATE NEXTUPNUMBER SET PREFIX = 'ASN';
