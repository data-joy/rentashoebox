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

from sklearn.neighbors import NearestNeighbors
import numpy as np
from pylab import *


class analyzer:
    
    def __init__(self, args):
        self.db_init()
        self.knn_k = args.knn_k
        self.knn_nbrs = []
        self.num_br = args.num_br
        self.listing_attrs = []
        self.sq_ft = args.sq_ft

    def plot(self):
        t = arange(0.0, 2.0, 0.01)
        s = sin(2*pi*t)
        plot(t, s)
        xlabel('time (s)')
        ylabel('voltage (mV)')
        title('About as simple as it gets, folks')
        grid(True)
        show()
                    
    def plot_knn(self):
        y_vec = []
        x_vec = []
        ws_vec = []
        for listing_vec in self.listing_attrs:
            num_br = listing_vec[3]
            if num_br == self.num_br:
                # this is a useful data point
                sq_ft = listing_vec[5]
                if sq_ft == -1:
                    continue
                ws = listing_vec[4]
                price = listing_vec[2]
                x_vec.append(sq_ft)
                y_vec.append(price)
                ws_vec.append(ws)

        print "%d valid listings." % len(x_vec)
        print ws_vec
        plot(x_vec, y_vec, '+')
        #xlabel('Walk Score')
        xlabel('Square Footage')
        ylabel('Rent')
        title('%d Bedroom Aparments' % self.num_br)
        grid(True)
        show()

    def find_knn(self):
        y_vec = []
        x_vec = []
        ws_vec = []
        for listing_vec in self.listing_attrs:
            num_br = listing_vec[3]
            if num_br == self.num_br:
                # this is a useful data point
                sq_ft = listing_vec[5]
                if sq_ft == -1:
                    continue
                ws = listing_vec[4]
                price = listing_vec[2]
                x_vec.append(sq_ft)
                y_vec.append(price)
                ws_vec.append(ws)

        temp = []
        for x in x_vec:
            #print x
            temp.append([x])

        Y = np.array(temp)
        nbrs = NearestNeighbors(n_neighbors=self.knn_k, algorithm='ball_tree').fit(Y)
        distances, indices = nbrs.kneighbors(self.sq_ft) 

        #print distances
        #print indices
        sum = 0
        x_res = []
        y_res = []
        for i in range(self.knn_k):
            #print "Nearest %d:  Size=%d Price=%d" % (i, x_vec[indices[i]][0], y_vec[indices[i]][0])
            #print i, x_vec[indices[i]]
            x_res.append(x_vec[indices[0][i]])
            y_res.append(y_vec[indices[0][i]])
            print "Nearest %d: SampleId=%d Size=%d Price=%d" %\
                   (i, indices[0][i], x_vec[indices[0][i]], y_vec[indices[0][i]])
            sum += y_vec[indices[0][i]]
        avg_price = sum/self.knn_k
        print "Avg price: %d" % avg_price

        print [avg_price, x_res, y_res]
        return [avg_price, x_res, y_res]
    def find_knn2(self):
        #X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
        relevant_vec = []
        ws_vec = []
        for listing_vec in self.listing_attrs:
            num_br = listing_vec[3]
            if num_br == self.num_br:
                # this is a useful data point
                ws = listing_vec[4]
                price = listing_vec[2]
                ws_vec.append([ws])
                relevant_vec.append(listing_vec)
        Y = np.array(ws_vec)
        print Y
        nbrs = NearestNeighbors(n_neighbors=self.knn_k, algorithm='ball_tree').fit(Y)
        distances, indices = nbrs.kneighbors(Y)
        print distances
        print indices



    def db_init(self):
        self.dbcon = mdb.connect('localhost', 'root', '', 'listingdb') #host, user, password, #database


    def db_read(self, row):
        listing = {}
        listing['cl.filepath'] = row[0]
        listing['cl.listingid'] = row[1]
        listing['cl.lat'] = row[2]
        listing['cl.lon'] = row[3]
        listing['cl.price'] = row[4]
        listing['cl.num_br'] = row[5]
        listing['cl.num_ba'] = row[6]
        listing['cl.sq_ft'] = row[7]
        listing['ws.addr'] = row[8]
        listing['ws.ws'] = row[9]
        listing['ws.ts'] = row[10]
        listing['ws.bs'] = row[11]
        return listing
        
    def listing_to_attrs(self, listing):
        if (listing['cl.lat'] == -999.0 or
            listing['cl.num_br'] == -1 or
            listing['cl.price'] == -1 or
            listing['ws.ws'] == -1):
            return None
        else:
            return [listing['cl.lat'], 
                    listing['cl.lon'],
                    listing['cl.price'],
                    listing['cl.num_br'],
                    listing['ws.ws'],
                    listing['cl.sq_ft']]


    def db_dump(self):
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("SELECT * FROM Listings")
            rows = cur.fetchall()
            for row in rows:
                listing = self.db_read(row)
                print listing


    def db_load(self):
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("SELECT * FROM Listings")
            rows = cur.fetchall()
            for row in rows:
                listing = self.db_read(row)
                attrs = self.listing_to_attrs(listing)                
                if (attrs):
                    for row in self.listing_attrs:
                        if (cmp(row, attrs) == 0):
                            break
                    else:
                        self.listing_attrs.append(attrs)
        #print self.listing_attrs
        #print "Loaded %d valid listings." % len(self.listing_attrs)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download listing pages')
    parser.add_argument("-g", dest='region', help='Region such as eby sby etc.')
    parser.add_argument("-k", dest='knn_k', type=int, default=5, metavar='num_nbrs', help='No. of nearest neighbors.')
    parser.add_argument("-b", dest='num_br', type=int, default=1, metavar='num_BR', help='Desired no. of bedrooms.')
    parser.add_argument("-s", dest='sq_ft', type=int, default=800, metavar='size', help='Desired size of apartment in square ft.')
    parser.add_argument("-w", dest='ws', type=int, metavar='walkscore', choices=xrange(0, 100), help='Desired walkscore')

    parsed_args = parser.parse_args()
    analyzer = analyzer(args=parsed_args)

    #analyzer.db_dump()
    analyzer.db_load()

    #analyzer.plot_knn()
    analyzer.find_knn()
    #print len(listings)

    # Download the links that haven't been downloaded
    #loader.save_listings(listings)
 
