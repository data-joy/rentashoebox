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
#import addr_utils

class loader:
    
    # address to city
    def addr_to_city(self, addr):
        m = re.search(', (\w[\w\s]+) CA', addr)
        if m:
            return m.group(1).lower()

        m = re.search('(\w[\w\s]+) CA', addr)
        if m:
            return m.group(1).lower()
        else:
            return 'unknown city'    
        
    def path_to_url(self, path):
        return 'http://sfbay.craigslist.org'+path

    # store parsed options into class variables
    # load database
    def __init__(self, args):
        #self.addr_utils = addr_utils.addr_utils()
        #self.addr_utils.load_cities_list()

        self.args = args
        if self.args.indir and self.args.infiles:
            print "Warning: can't specify both input dir and input files."
            print "Using only the input directory."
            self.args.infiles = None

        self.db_init()

    def process_listing(self, f):
        listing = self.parse_listing(f)

        if not listing:
            print "Skip corrupted listing:", f.name
            return 

        if loader.db_exists(listing['cl_listingid']):
            print "Skip existing listing:", f.name
            return
            
        [addr, city, ws, ts, bs] = self.get_scores(listing)
        print "Inserting into databse."
        self.db_insert(listing) 


    def process_listings(self):
        if (self.args.indir):
            # read all html files in dir
            for filename in glob.glob(self.args.indir + "/*.html"):
                with open(filename, 'r') as f:
                    self.process_listing(f)
        else:
            for f in self.args.infiles:
                self.process_listing(f)

    def get_scores(self, listing):

        lat = listing['cl_lat']
        lon = listing['cl_lon']

        # Given lat, lon, get Walk/Transit/Bike scores
        #[addr, city, ws, ts, bs] = self.get_scores(listing['cl_lat'], listing['cl_lon'])

        url = "https://www.walkscore.com/score/loc/lat=" + str(lat)
        url += "/lng=" + str(lon)
        url += "/?utm_source=redfin.com&amp;utm_medium=ws_api&amp;utm_campaign=ws_api"

        resp = requests.get(url)
        # slow down the downloads
        if self.args.page_delay < 0.5:
            self.args.page_delay = 0.5
        rand_delay = 0.5 + random.expovariate(1.0/self.args.page_delay)
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

        city = self.addr_to_city(addr)
        print "City = '%s'" % city
        #cities = self.addr_utils.extract_cities(addr)
        #if len(cities) > 0:
            # last one is likely the right one since the city appears later
        #    city = cities[-1]
        #else:
        #    city = ''

        listing['ws_addr'] = addr
        listing['ws_city'] = city 
        listing['ws_ws'] = ws
        listing['ws_ts'] = ts
        listing['ws_bs'] = bs
        
        return [addr, city, ws, ts, bs]


    def db_init(self):

        self.dbcon = mdb.connect('localhost', 'root', '', 'listingdb') #host, user, password, #database

        if not self.args.do_erase:
            return

        # Erase database and create table
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("DROP TABLE IF EXISTS %s" % self.args.table_name)
            cur.execute("CREATE TABLE %s("
                        "cl_filepath  VARCHAR(128),"
                        "cl_listingid LONG,"
                        "cl_lat       FLOAT,"
                        "cl_lon       FLOAT,"
                        "cl_price     INT,"
                        "cl_num_br    INT,"
                        "cl_num_ba    INT,"
                        "cl_sq_ft     INT,"
                        "cl_building VARCHAR(32),"
                        "cl_laundry   VARCHAR(32),"
                        "cl_parking   VARCHAR(32),"
                        "cl_catsok    INT,"
                        "cl_catrent   INT,"
                        "cl_dogsok    INT,"
                        "cl_dogrent   INT,"
                        "cl_nosmoking INT,"
                        "cl_wheelchair INT,"
                        "cl_furnished INT,"
                        "cl_area      VARCHAR(32),"
                        "ws_addr      VARCHAR(256),"
                        "ws_city      VARCHAR(32),"
                        "ws_ws        INT,"
                        "ws_ts        INT,"
                        "ws_bs        INT,"
                        "geo_cs       INT,"
                        "geo_age      INT,"
                        "geo_income   LONG,"
                        "cl_post_len  INT"
                        ")" % self.args.table_name )
            cur.close()

    def db_exists(self, listingid):

        result = False
        with self.dbcon:
            cur = self.dbcon.cursor()
            cmd = "SELECT * FROM %s WHERE cl_listingid=%d" \
                   % (self.args.table_name, listingid)
            #print "Command = " , cmd
            cur.execute("SELECT * FROM %s WHERE cl_listingid=%d" \
                        % (self.args.table_name, listingid))

            rows = cur.fetchall()
            for row in rows:
                print row
                # found, so it exists
                result = True
                break
            cur.close()
        return result

    def db_insert(self, listing):
        if self.args.do_simulate:
            return

        with self.dbcon:
            cur = self.dbcon.cursor()
            cmd = "INSERT INTO %s VALUES("\
                  "'%s', %d, %.6f, %.6f, %d, %d, "\
                  "%d, %d, '%s', '%s', '%s', %d, "\
                  "%d, %d, %d, %d, %d, %d, "\
                  "'%s', '%s', '%s', %d, %d, %d, "\
                  "%d, %d, %d, %d)" %\
                  (self.args.table_name,
                   listing['cl_filepath'],
                   listing['cl_listingid'],
                   listing['cl_lat'],
                   listing['cl_lon'],
                   listing['cl_price'],
                   listing['cl_num_br'],

                   listing['cl_num_ba'],
                   listing['cl_sq_ft'],
                   listing['cl_building'],
                   listing['cl_laundry'],
                   listing['cl_parking'],
                   listing['cl_catok'],

                   listing['cl_dogok'],
                   listing['cl_catrent'],
                   listing['cl_dogrent'],
                   listing['cl_nosmoking'],
                   listing['cl_wheelchair'],
                   listing['cl_furnished'],

                   listing['cl_area'],
                   listing['ws_addr'],
                   listing['ws_city'],
                   listing['ws_ws'],
                   listing['ws_ts'],
                   listing['ws_bs'],

                   listing["geo_p1"],
                   listing["geo_p2"],
                   listing["geo_p3"],
                   listing['cl_post_len'])

            print cmd
            cur.execute(cmd)
            cur.close()

    def db_print(self):
        with self.dbcon:
            cur = self.dbcon.cursor()
            cur.execute("SELECT * FROM %s" % self.args.table_name)
            rows = cur.fetchall()
            for row in rows:
                print row
            cur.close()

    def new_listing(self):
        listing = {}
        # Init w/ default bogus values
        listing['cl_filepath'] = ''
        listing['cl_listingid'] = -1
        listing['cl_lat'] = -999.0
        listing['cl_lon'] = -999.0
        listing['cl_price'] = -1.0
        listing['cl_num_br'] = -1.0

        listing['cl_num_ba'] = -1
        listing['cl_sq_ft'] = -1
        listing['cl_building'] = ''
        listing['cl_laundry'] = ''
        listing['cl_parking'] = ''
        listing['cl_catok'] = -1

        listing['cl_dogok'] = -1
        listing['cl_catrent'] = -1
        listing['cl_dogrent'] = -1
        listing['cl_nosmoking'] = -1
        listing['cl_wheelchair'] = -1
        listing['cl_furnished'] = -1

        listing['cl_area'] = ''
        listing['ws_addr'] = ''
        listing['ws_city'] = ''
        listing['ws_ws'] = -1
        listing['ws_ts'] = -1
        listing['ws_bs'] = -1

        listing["geo_p1"] = -1
        listing["geo_p2"] = -1
        listing["geo_p3"] = -1
        listing['cl_post_len'] = -1.0

        return listing


    def parse_listing(self, f):
        print "----------------"
        print f.name

        bytes = f.read()
        parsed = BeautifulSoup(bytes)

        listing = self.new_listing()

        listing['cl_filepath'] = f.name

        m = re.search('/(\d+)\.', f.name)
        listing['cl_listingid'] = int(m.group(1))

        #postingbody = parsed.find('section', id_='postingbody').text
        m = parsed.find('section', id='postingbody')
        if not m:
            return

        postingbody = m.text 
        print "Body len = %d" % len(postingbody)
        #print postingbody
        listing['cl_post_len'] = len(postingbody)
 
        # Extract lat, long
        # e.g., <div id="map" class="viewposting" data-latitude="37.536908" 
        #        data-longitude="-121.998000" data-accuracy="0"></div>
        mapinfo = parsed.find('div', id="map")
        if mapinfo:
            listing['cl_lat'] = (float(mapinfo['data-latitude']))
            listing['cl_lon'] = (float(mapinfo['data-longitude']))
        else:
            return

        # Extract price
        # <h2 class="postingtitle">
        #  <span class="star"></span>
        #  &#x0024;1695 / 1br - 560ft^2 - :::::: We have Gas Stoves :::::: (fremont / union city / newark)
        # </h2>
        postingtitle = parsed.find('h2', class_="postingtitle")
        if postingtitle:
            title = postingtitle.text
            price = re.search('\$(\d+)', title)
            if not price:
                return

            listing['cl_price'] = (int(price.group(1)))

            # Area name is inside parenthesis
            area = re.search('\(([\w\.\s]+)\)\s*$', title)
            #pdb.set_trace()
            if area:
                listing['cl_area'] = area.group(1)
            else:
                listing['cl_area'] = 'unknown area' 

            is_studio = ( 'studio' in title.lower() )
            
           
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

        atg = parsed.find('p', class_='attrgroup')
        if atg:
            atg_spans = atg.find_all('span')
            # e.g., <span><b>2</b>BR / <b>2</b>Ba</span>, <span><b>946</b>ft<sup>2</sup></span>
        
            for span in atg_spans:
                text = span.text
    
                m = re.search('(\d+\.\d+)BR', text)
                if not m:
                    m = re.search('(\d+)BR', text)

                if m:
                    num_br = round(float(m.group(1))+0.5)
                    listing['cl_num_br'] = num_br
                    # Heuristic to distinguish studios from 1BR
                    if num_br == 1 and is_studio:
                        print "It's likely a studio"
                        listing['cl_num_br'] = 0
                    
                    #print "# BR =", num_br
                    # Note: don't break yet because #Ba is next, if avail.
    
                    m=re.search('(\d+)Ba', text)
                    if m:
                        num_ba = int(m.group(1))
                        listing['cl_num_ba'] = num_ba
                        #print "# Ba =", num_ba
                    continue
    
                m = re.search('(\d+)ft2', text)
                if m:
                    sq_ft = int(m.group(1))
                    #print "Size =", m.group(1)
                    listing['cl_sq_ft'] = sq_ft
                    continue
    
                # Look for additional details and insert into listing
                #print "XXX: " + text
                self.parse_listing_details(listing, text)

        print listing
        return listing

    def parse_listing_details(self, listing, text_orig):
        text = text_orig.lower()
        building_types = [ 'apartment', 'condo', 'cottage/cabin', 'duplex', 
                   'flat', 'house', 'in-law', 'loft', 'manufactured', 'townhouse'];

        laundry_types = ['w/d hookups', 'w/d in unit', 'laundry in bldg', 'laundry on site'];

        parking_types = ['attached garage','carport','detached garage', 
                         'off-street parking','street parking'];

        boolean_labels = {'cats are ok - purrr' : 'cl_catok',
                          'dogs are ok - wooof' : 'cl_dogok',
                          'no smoking' : 'cl_nosmoking',
                          'wheelchair accessible' : 'cl_wheelchair',
                          'furnished' : 'cl_furnished'}

        for keyword in building_types:
            if keyword in text:
                listing['cl_building'] = keyword
                break
    
        for keyword in laundry_types:
            if keyword in text:
                listing['cl_laundry'] = keyword
                break
    
        for keyword in parking_types:
            if keyword in text:
                listing['cl_parking'] = keyword
                break

        for keyword in boolean_labels:
            if keyword in text:
                listing[boolean_labels[keyword]] = 1

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download listing pages')

    parser.add_argument("-t", dest='table_name', default="Listings_test", help="Table name in database")
    #parser.add_argument("-o", dest='output_file', default="data.csv", help="Output file")

    parser.add_argument("-y", dest='page_delay', type=float, default=1.0, help='Delay (in secs) between requests')
    #parser.add_argument("-l", dest='page_limit', type=int, default=1, help='Limit number of index pages to pull')
    parser.add_argument("-e", dest='listingid', type=int, help="check if listingid is already in databse")
    parser.add_argument("-n", dest='do_simulate', action='store_true', help="Don't actually change database, just simulate.")
    parser.add_argument("-i", dest='indir', help="Directory where HTML files are stored.")

    parser.add_argument("--erase", dest='do_erase', action='store_true', help="ERASE DATABASE!!! before adding new entries.")

    parser.add_argument("-p", dest='do_print_db', action='store_true', help="Just print contents of database")
    parser.add_argument(dest='infiles', nargs='*', type=argparse.FileType('r'),
                        metavar='listing_html', help='listing HTML file to parse and scrape')


    parsed_args = parser.parse_args()

    # Loader inits databases
    loader = loader(args=parsed_args)


    if parsed_args.listingid:
        if loader.db_exists(parsed_args.listingid):
            print "Listing %d exists." % parsed_args.listingid       
        else:
            print "Listing %d doesn't exist." % parsed_args.listingid       
        sys.exit(0)

    # For each listing, parse data
    # Get additional data from Internet
    # Store results in database 
    loader.process_listings()


    # Download the links that haven't been downloaded
    #loader.save_listings(listings)

    # Print an exit
    if (parsed_args.do_print_db):
        loader.db_print()
 
