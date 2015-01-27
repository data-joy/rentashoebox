import sys
import requests
import time
from bs4 import BeautifulSoup
import argparse
import random
import os
import re
import glob
import pdb
import pymysql as mdb


class analyzer:
    
    def __init__(self, args):
        self.db_init()


    def db_init(self):
        self.dbcon = mdb.connect('localhost', 'root', '', 'listingdb') #host, user, password, #database


#    def db_read(self, listing):
#        with self.dbcon:
#            cur = self.dbcon.cursor()
#            cur.execute("INSERT INTO Listings VALUES('%s', %d, %.6f, %.6f, %d, %d, "
#                        "%d, %d, '%s', %d, %d, %d)" %
#                        (listing['cl.filepath'],
#                         listing['cl.listingid'],
#                         listing['cl.lat'],
#                         listing['cl.lon'],
#                         listing['cl.price'],
#                         listing['cl.num_br'],
#                         listing['cl.num_ba'],
#                         listing['cl.sq_ft'],
#                         listing['ws.addr'],
#                         listing['ws.ws'],
#                         listing['ws.ts'],
#                         listing['ws.bs']))


    def db_dump(self):
        with self.dbcon:
            cur = dbcon.cursor()
            cur.execute("SELECT * FROM Listings")
            rows = cur.fetchall()
            for row in rows:
                print row

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download listing pages')

    analyzer = analyzer()

    # Extract list of links to download
    analyzer.db_dump()

    #print len(listings)

    # Download the links that haven't been downloaded
    #loader.save_listings(listings)
 
