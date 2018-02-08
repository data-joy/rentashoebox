USE listingdb;
DROP TABLE IF EXISTS CleanListing;


CREATE TABLE CleanListing LIKE Listing;
INSERT INTO CleanListing SELECT * FROM Listing;

DELETE FROM CleanListing WHERE cl_lat = -999;
DELETE FROM CleanListing WHERE cl_num_br = 0 AND cl_num_ba > 1;
DELETE FROM CleanListing WHERE cl_price > 10000;
DELETE FROM CleanListing WHERE cl_sq_ft > 5000 AND cl_num_ba < 4;


