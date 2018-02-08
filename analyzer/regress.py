import sys
import requests
import time
import argparse
import random
import os
import re
import glob
import pdb
import pymysql as mdb

import numpy as np
from pylab import *

import addr_utils
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
from sklearn.neighbors import NearestNeighbors

import pdb

class analyzer:
        
    def __init__(self, args):
        self.args = args
        self.db_init()
        #self.knn_k = args.knn_k
        #self.knn_nbrs = []
        #self.num_br = args.num_br
        self.listing_attrs = []



    #def plot(self):
    #    t = arange(0.0, 2.0, 0.01)
    #    s = sin(2*pi*t)
    #    plot(t, s)
    #    xlabel('time (s)')
    #    ylabel('voltage (mV)')
    #    title('About as simple as it gets, folks')
    #    grid(True)
    #    show()
                    
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
        listing['cl_filepath'] = row[0]
        listing['cl_listingid'] = row[1]
        listing['cl_lat'] = row[2]
        listing['cl_lon'] = row[3]
        listing['cl_price'] = row[4]
        listing['cl_num_br'] = row[5]
        listing['cl_num_ba'] = row[6]
        listing['cl_sq_ft'] = row[7]

        listing['cl_building'] = row[8]
        listing['cl_laundry'] = row[9]
        listing['cl_parking'] = row[10]
        listing['cl_catsok'] = row[11]
        listing['cl_catrent'] = row[12]
        listing['cl_dogsok'] = row[13]
        listing['cl_dogrent'] = row[14]
        listing['cl_nosmoking'] = row[15]
        listing['cl_wheelchair'] = row[16]
        listing['cl_furnished'] = row[17]
        listing['cl_area'] = row[18]

        listing['ws_addr'] = row[19]
        listing['ws_city'] = row[20]
        listing['ws_ws'] = row[21]
        listing['ws_ts'] = row[22]
        listing['ws_bs'] = row[23]
        listing['geo_cs'] = row[24]
        listing['geo_age'] = row[25]
        listing['geo_income'] = row[26]
        listing['cl_post_len'] = row[27]
        return listing
        
    def listing_to_features(self, listing):
        # throw away incomplete records and houses
        if (listing['cl_lat'] == -999.0 or
            listing['cl_num_br'] == -1 or
            listing['cl_price'] == -1 or
            listing['cl_sq_ft'] == -1 or
            listing['ws_ws'] == -1):
            #listing['cl_building'] == 'house'):
            return [-1, []]
        else:
            if (listing['cl_building'] in ['house', 'duplex', 'townhouse']):
                #print listing['cl_building']
                is_house = 1
            else:
                is_house = -1

            if (listing['cl_laundry'] == 'w/d in unit'):
                #print listing['cl_laundry']
                is_inunitlaundry = 1
            else:
                is_inunitlaundry = -1

            if (listing['cl_parking'] in ['attached garage', 'detached garage', 'carport']):
                #print listing['cl_parking']
                is_coveredparking = 1
            else:
                is_coveredparking = -1

            sq_ft = listing['cl_sq_ft']

            if sq_ft == -1:
                sq_ft = 0
            
            #features = [listing['cl_lat'],  listing['cl_lon'], listing['cl_num_br'],
            features = [\
                        listing['cl_num_br'],
                        sq_ft, 
                        #sq_ft * sq_ft, 
                        #is_house, 
                        is_inunitlaundry, 
                        #is_coveredparking, 
                        #listing['cl_furnished'], 
                        listing['cl_catsok'], 
                        #listing['cl_dogsok'], 
                        listing['ws_ws'],
                        listing['cl_post_len']
                        ]
             
            return [listing['cl_price'], features]


    def db_dump(self):
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("SELECT * FROM %s" % self.args.db_name)
            rows = cur.fetchall()
            for row in rows:
                listing = self.db_read(row)
                print listing


    def db_load(self):
        Y = []
        X = []
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("SELECT * FROM %s WHERE ws_city='%s'" % (self.args.db_name, self.args.city.lower()))
            rows = cur.fetchall()
            for row in rows:
                listing = self.db_read(row)
                # If this is a valid row, use it
                [price, features] = self.listing_to_features(listing)                
                if (price != -1):
                    Y.append(price)
                    X.append(features)  
                    #self.listing_attrs.append(attrs)
                    # removing duplicates
                    #for row in self.listing_features:
                        #if (cmp(row, attrs) == 0):
                            #break
                    #else:
                        #self.listing_attrs.append(attrs)

        #print self.listing_attrs
        #print "Loaded %d valid listings." % len(self.listing_attrs)
        #print hstack((np.array(Y)[:,np.newaxis], np.array(X)))
        return [np.array(X), np.array(Y)]


    def lin_regress_train(self, X, Y):
        X_train = X[:-20,:]
        X_test = X[-20:,:]

        #pdb.set_trace()
        Y_train = Y[:-20]
        Y_test = Y[-20:]

        # Create linear regression object
        regr = linear_model.LinearRegression(normalize=True)

        # Train the model using the training sets
        regr.fit(X_train, Y_train)

        # The coefficients
        print('Intercept: \n', regr.intercept_)
        print('Coefficients: \n', regr.coef_)
        # The mean square error
        print("Residual sum of squares: %.2f"
              % np.mean((regr.predict(X_test) - Y_test) ** 2))

        # Explained variance score: 1 is perfect prediction
        print('Variance score: %.2f' % regr.score(X_test, Y_test))

        Y_predict = regr.predict(X)
        np.set_printoptions(linewidth=300, precision=4, edgeitems=10)

    def lin_regress(self, X, Y):

        # Create linear regression object
        regr = linear_model.LinearRegression(normalize=True)

        # Train the model using the training sets
        regr.fit(X, Y)

        # The coefficients
        print('Intercept: \n', regr.intercept_)
        print('Coefficients: \n', regr.coef_)
        # The mean square error
        print("Residual sum of squares: %.2f"
              % np.mean((regr.predict(X) - Y) ** 2))

        # Explained variance score: 1 is perfect prediction
        print('Variance score: %.2f' % regr.score(X, Y))

        #Y_predict = regr.predict(X)
        np.set_printoptions(linewidth=300, precision=4, edgeitems=10)

        #print np.around(hstack((Y_predict[:,np.newaxis], Y[:,np.newaxis], X)))

        # Plot outputs
        #plt.scatter(X_test, Y_test,  color='black')
        #plt.plot(X_test, regr.predict(X_test), color='blue',
                 #linewidth=3)

        #plt.xticks(())
        #plt.yticks(())

        #plt.show()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download listing pages')
    parser.add_argument("-c", dest='city', help='City name.')
    parser.add_argument("-d", dest='db_name', default='CleanListing', help='Database name.')
    parser.add_argument("-b", dest='num_br', type=int, default=1, metavar='num_bedroom', help='Desired no. of bedrooms.')
    #parser.add_argument("-a", dest='num_ba', type=int, default=1, metavar='num_bathroom', help='Desired no. of bathrooms.')
    parser.add_argument("-s", dest='sq_ft', type=int, default=800, metavar='size', help='Desired size of apartment in square ft.')
    parser.add_argument("-w", dest='ws', type=int, metavar='walkscore', choices=xrange(0, 100), default=50, help='Desired walkscore')
    #parser.add_argument("-t", dest='ts', type=int, metavar='transitscore', choices=xrange(0, 100), default=50, help='Desired transit score')
    #parser.add_argument("-u", dest='is_house', action='store_true', default=False,  help='Desire a house, not a condo or an apartment.')
    parser.add_argument("-l", dest='is_house', action='store_true', default=False,  help='Desire a house, not a condo or an apartment.')
    parser.add_argument("-p", dest='is_covered_parking', action='store_true', default=False,  help='Desire carport or garage.')

    parsed_args = parser.parse_args()
    analyzer = analyzer(args=parsed_args)

    #analyzer.db_dump()
    [X, Y] = analyzer.db_load()
    #analyzer.lin_regress_train(X,Y)
    analyzer.lin_regress(X,Y)
    #analyzer.plot_knn()
    #analyzer.find_knn()
    #print len(listings)

    # Download the links that haven't been downloaded
    #loader.save_listings(listings)
 
