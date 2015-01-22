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


class loader:
    
    def path_to_url(self, path):
        return 'http://sfbay.craigslist.org'+path

    #def pathlist_to_urllist(self, path_list):
    #    return map(lambda x: 'http://sfbay.craigslist.org/'+x, path_list)

    def __init__(self, args):
        #self.region = args.region
        self.page_delay = args.page_delay
        self.page_limit = args.page_limit
        self.do_simulate = args.do_simulate
        self.indir = args.indir
        if self.indir and args.infiles:
            print "Warning: can't specify both input dir and input files."
            print "Using only the input directory."
            self.infiles = None
        else:
            self.infiles = args.infiles

        self.db_init()

    def extract_listings(self):
        if (self.indir):
            # read all html files in dir
            for filename in glob.glob(self.indir + "/*.html"):
                with open(filename, 'r') as f:
                    listing = self.parse_listing(f)
                    if listing:
                        self.db_insert(listing) 
                    else:
                        print "Skip corrupted file:", f.name
        else:
            for f in self.infiles:
                listing = self.parse_listing(f)
                if listing:
                    self.db_insert(listing) 
                else:
                    print "Skip corrupted file:", f.name


    def get_scores(self, lat, lon):
         url = "https://www.walkscore.com/score/loc/lat=" + str(lat)
         url += "/lng=" + str(lon)
         url += "/?utm_source=redfin.com&amp;utm_medium=ws_api&amp;utm_campaign=ws_api"

         resp = requests.get(url)
         # slow down the downloads
         rand_delay = 2.0 + random.expovariate(1.0/self.page_delay)
         print "Sleeping ", rand_delay, "seconds ..."
         time.sleep(rand_delay)


         bytes = resp.text
         m = re.search('walk/score/(\d+)\.', bytes)
         if m:
             ws = int(m.group(1))
         else:
             ws = -1

         m = re.search('transit/score/(\d+)\.', bytes)
         if m:
             ts = int(m.group(1))
         else:
             ts = -1

         m = re.search('bike/score/(\d+)\.', bytes)
         if m:
             bs = int(m.group(1))
         else:
             bs = -1

         m = re.search('<title>(.+) - Walk Score</title>', bytes)
         if m:
             addr = m.group(1)
         else:
             addr = ""

         #pdb.set_trace()

         return [addr, ws, ts, bs]


    def db_init(self):
        self.dbcon = mdb.connect('localhost', 'root', '', 'listingdb') #host, user, password, #database
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("DROP TABLE IF EXISTS Listings")
            #cur.execute("CREATE TABLE Listings(Id INT PRIMARY KEY AUTO_INCREMENT,"
            cur.execute("CREATE TABLE Listings("
                        "cl_filepath VARCHAR(128),"
                        "cl_listingid INT,"
                        "cl_lat       FLOAT,"
                        "cl_lon       FLOAT,"
                        "cl_price     INT,"
                        "cl_num_br    INT,"
                        "cl_num_ba    INT,"
                        "cl_sq_ft     INT,"
                        "ws_addr      VARCHAR(256),"
                        "ws_ws        INT,"
                        "ws_ts        INT,"
                        "ws_bs        INT"
                        ")")


    def db_insert(self, listing):
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("INSERT INTO Listings VALUES('%s', %d, %.6f, %.6f, %d, %d, "
                        "%d, %d, '%s', %d, %d, %d)" %
                        (listing['cl.filepath'],
                         listing['cl.listingid'],
                         listing['cl.lat'],
                         listing['cl.lon'],
                         listing['cl.price'],
                         listing['cl.num_br'],
                         listing['cl.num_ba'],
                         listing['cl.sq_ft'],
                         listing['ws.addr'],
                         listing['ws.ws'],
                         listing['ws.ts'],
                         listing['ws.bs']))

    def db_print(self):
        with self.dbcon:
            cur = dbcon.cursor()
            cur.execute("SELECT * FROM Listings")
            rows = cur.fetchall()
            for row in rows:
                print row


    def parse_listing(self, f):
        print "----------------"
        print f.name

        bytes = f.read()
        parsed = BeautifulSoup(bytes)
        #listings = parsed.find_all('p', class_='row')

        listing = {}
        listing['cl.filepath'] = f.name
        m = re.search('/(\d+)\.', f.name)
        listing['cl.listingid'] = int(m.group(1))

        # Extract lat, long
        # e.g., <div id="map" class="viewposting" data-latitude="37.536908" 
        #        data-longitude="-121.998000" data-accuracy="0"></div>
        map = parsed.find('div', id="map")
        if map:
            listing['cl.lat'] = (float(map['data-latitude']))
            listing['cl.lon'] = (float(map['data-longitude']))
            # Given lat, lon, get Walk/Transit/Bike scores
            [addr, ws, ts, bs] = self.get_scores(listing['cl.lat'], listing['cl.lon'])
            listing['ws.addr'] = addr
            listing['ws.ws'] = ws
            listing['ws.ts'] = ts
            listing['ws.bs'] = bs
        else:
            listing['cl.lat'] = -999.0
            listing['cl.lon'] = -999.0
            # Given lat, lon, get Walk/Transit/Bike scores
            listing['ws.addr'] = ''
            listing['ws.ws'] = -1
            listing['ws.ts'] = -1
            listing['ws.bs'] = -1

        # Extract price
        # <h2 class="postingtitle">
        #  <span class="star"></span>
        #  &#x0024;1695 / 1br - 560ft^2 - :::::: We have Gas Stoves :::::: (fremont / union city / newark)
        # </h2>
        postingtitle = parsed.find('h2', class_="postingtitle")
        if postingtitle:
            title = postingtitle.text
            price = re.search('\$(\d+)', title)
            #br = re.search(' (\d+)br', title)
            #ba = re.search(' (\d+)ba', title)
            #ft = re.search(' (\d+)ft\^2', title)
            #print title

            #print "price =", price.group(0)
            listing['cl.price'] = (int(price.group(1)))
            #print "#BR =", br
            #print "#BA =", ba
            #print "#FT =", ft
        else:
            listing['cl.price'] = -1

           
        # Extract #BR / # Bath / Size 
        # Extract Price / Size / 
        # e.g.,  <p class="attrgroup">
        #          <span><b>1</b>BR / <b>1</b>Ba</span> 
        #          <span><b>560</b>ft<sup>2</sup></span> 
        #          <span>apartment</span> 
        #          <span class="housing_movein_now property_date" date="2015-01-24" today_msg="available now">available jan 24</span><br>
        #          <span>laundry on site</span> 
        #          <span>carport</span><br>
        #          <span>cats are OK - purrr</span></p>
        #         <p class="attrgroup"></p>

        listing['cl.num_br'] = -1
        listing['cl.num_ba'] = -1
        listing['cl.sq_ft'] = -1

        atg = parsed.find('p', class_='attrgroup')
        if atg:
            atg_spans = atg.find_all('span')
            # e.g., <span><b>2</b>BR / <b>2</b>Ba</span>, <span><b>946</b>ft<sup>2</sup></span>
        
            for span in atg_spans:
                text = span.text
    
                m = re.search('(\d+)BR', text)
                if m:
                    num_br = int(m.group(1))
                    listing['cl.num_br'] = num_br
                    #print "# BR =", num_br
                    # Note: don't break yet because #Ba is next, if avail.
    
                    m=re.search('(\d+)Ba', text)
                    if m:
                        num_ba = int(m.group(1))
                        listing['cl.num_ba'] = num_ba
                        #print "# Ba =", num_ba
                    continue
    
                m = re.search('(\d+)ft2', text)
                if m:
                    sq_ft = int(m.group(1))
                    #print "Size =", m.group(1)
                    listing['cl.sq_ft'] = sq_ft
                    continue
    
                #print "XXX: " + text

        print listing
        return listing

#    def parse_listing(self, listing):
#        try:
            #print(listing.prettify())
            #house_type = listing.find('span', class_='housing').text
            #price = listing.find('span', class_='price').text
            #area = listing.find('span', class_='pnr').find('small').text
            #housing = listing.find('span', class_='housing').text
#            path = listing.find('a', class_='i')['href']
            #print area, "|", price, "|", house_type
#        except:
#            print("Parsing error:", sys.exc_info()[0])
#            print(listing.prettify())
#            path = None
#        return path

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download listing pages')

    #parser.add_argument("-d", dest='data_dir', default="./data", help="Base dir of data")
    parser.add_argument("-o", dest='output_file', default="data.csv", help="Output file")

    parser.add_argument("-y", dest='page_delay', type=float, default=2.0, help='Delay (in secs) between requests')
    parser.add_argument("-l", dest='page_limit', type=int, default=1, help='Limit number of index pages to pull')
    parser.add_argument("-n", dest='do_simulate', action='store_true', help="Don't actually download, just simulate.")
    parser.add_argument("-d", dest='indir', help="Directory where HTML files are stored.")

    parser.add_argument(dest='infiles', nargs='*', type=argparse.FileType('r'),
                        metavar='listing_html', help='listing HTML file to parse and scrape')

    parsed_args = parser.parse_args()

    loader = loader(args=parsed_args)

    # Extract list of links to download
    loader.extract_listings()

    #print len(listings)

    # Download the links that haven't been downloaded
    #loader.save_listings(listings)
 
