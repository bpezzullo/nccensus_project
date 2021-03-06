from flask import Flask, render_template, Response, jsonify
from bson import json_util
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
import requests
import json
import census as ce
import csv 


#----- Import API key ---------------
from config import username, password, dbname



#years= ['1986','1988','1990','1992','1994','1996','1998','2000','2002','2004','2006','2008','2010','2012','2013','2014','2015','2016','2017','2018']
#recent_years= ['2012', '2013','2014','2015','2016','2017','2018']
years_wanted= ['1986','1988','1990','1992','1994','1996','1998','2000','2002','2004','2006','2008','2010','2012','2013','2014','2015','2016','2017','2018']
recent_years_wanted= ['2012','2013','2014','2015','2016','2017','2018']

years_nc = []
years_pop = []

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app, resources={
    r"/*": {
        "origins": "*"
    }
})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CORS_ORIGINS'] = '*'

# Use flask_pymongo to set up mongo connection

# temporary mongo DB
#app.config["MONGO_URI"] = "mongodb://localhost:27017/censusdb"

app.config['MONGO_URI'] = 'mongodb+srv://' + username + ':' + password + '@cluster0.jvrf7.mongodb.net/' + dbname + '?retryWrites=true&w=majority'

# run in debug mode
#app.debug = True

mongo = PyMongo(app)


#   Name: deter_county  
#   Description: This populates the pop-up when the county is selected 
#   Input:
#     result - json file with the state information
#     county - country name
#     year - year to be displayed
#   Returns:
#     none
def deter_county(result,county,year):
    size = 0
    ind = 1
    name_ind = 0
    cnty = ""
    first_data_row = 1
    code = "none"
    split_char = ' '
    year_int = int(year)
    if (year_int >= 2017):
        code = '00'
    elif (year_int >= 2012):
        code = '00'
    elif (year_int > 2007):
        name_ind = 1
        ind=2
    elif (year_int >= 2002):
        name_ind = 1
        ind=2
        split_char = ','
    elif (year_int > 1997):
        name_ind = 1
        ind=2

    cnty = county + split_char + result[first_data_row][name_ind].split(split_char,1)[1]
    for county_d in result:
        if (code == "none"):
            if(cnty == county_d[name_ind]):
                size = int(county_d[ind])
                break
        elif (cnty == county_d[name_ind] and code == county_d[2]):
            size = int(county_d[ind])
            break

    return size



def m_insert(name,data):
    geocol = mongo.db.geo
    dataset = {"type": name, "result" : data}
    geocol.insert(dataset)
    return
      
        

@app.route('/', methods=["GET", "POST"])
@app.route("/home")
def root():
    # return render_template('index.html')
    return app.send_static_file("index.html")


# get the GEOJSON information from mongodb
@app.route("/get_geo", methods=["GET"])
@cross_origin()
def get_geo():

    # access the geo collection
    geocol = mongo.db.geo

    myquery = { "type": "counties" }

    #Are the documents there?
    x = geocol.count_documents(myquery)
    data = {}
    if x == 0:
        print("GeoJSON is still loading please wait and reselect year")

    else:
        geodoc = geocol.find_one(myquery)
        # print(geodoc)
        geocounty = json.loads(json_util.dumps(geodoc))
        counties = geocounty['result']
        counties_data = []
        for county in counties:
            myquery = {"type": county}
            geodoc = geocol.find_one(myquery)
#            print(county , geodoc['result'])
            counties_data.append(geodoc['result'])
        # print(counties_data)
        # recreate the geojson file from the mongodb.
        data['crs'] = geocol.find_one({"type":'crs'})['result']
        data['name'] = geocol.find_one({"type":'name'})['result']
        data['type'] = geocol.find_one({"type":'type'})['result']
        data['features'] = counties_data

    return jsonify(data)

# call the API to load the nc geo JSON and store into Mongo DB if not there.
@app.route("/reload_geo", methods=["GET"])
@cross_origin()
def reload_geo():
    # access the geo collection
    geocol = mongo.db.geo

    myquery = { "type": "counties" }

    #Are the documents there?
    x = geocol.count_documents(myquery)

    if x == 0:
        # if col == 0:
        # if the geojson file is not stored, call the API.
        response = requests.get("https://opendata.arcgis.com/datasets/d192da4d0ac249fa9584109b1d626286_0.geojson")

        # need to chunk up the geojson file to allow it to be stored in Mongodb
        result = response.json()

        # call function to insert each type
        m_insert('crs',result['crs'])
        m_insert('name',result['name'])
        m_insert('type',result['type'])

        # for the couties break-up the features portion of the json and store each county separatedly.
        counties = []
        for coord in result['features']:
            # for each county store the county boarder information.
            counties.append(coord['properties']['CountyName'])
            m_insert(coord['properties']['CountyName'],coord)

        m_insert('counties',counties)

    return get_geo()

# call the API to load the nc employment and store into Mongo DB if not there.
@app.route("/reload_census", methods=["GET"])
@cross_origin()
def reload_census():
 
    # access the census collection
    censuscol = mongo.db.census

    global years_nc
    years_nc = []

    # loop through the years to pull the information in.
    for year in years_wanted:
        myquery = { "year": year }
        x = censuscol.count_documents(myquery)

        # check to see if the year exists in collection.  If so skip otherwise pull into
        # database from the census API
        if x == 0:
            # using functions in census.py, call the API for the year.
            responseJson = ce.emp_by_year(int(year))
            if responseJson == 'error':
                result = 'error'                
            else:
                censusyear = {"year": year, "result" : responseJson}
                censuscol.insert_one(censusyear)
                years_nc.append(year)
                result = "new"

        else:  # don't refresh if we have the data.  Eventually we would want to change this
            result = "existing"
            years_nc.append(year)
    final_year = years_nc[-1]
    return get_nc_data(final_year)


# call the API to load the nc population and store into Mongo DB if not there.
@app.route("/reload_nccensus", methods=["GET"])
@cross_origin()
def reload_nccensus():
 
    # access the nccensus collection
    censuscol = mongo.db.nccensus
    global years_pop 
    years_pop = []
        # loop through the years to pull the information in.
    for year in years_wanted:
        myquery = { "year": year }
        x = censuscol.count_documents(myquery)

        # check to see if the year exists in collection.  If so skip otherwise pull into
        # database from the census API
        if x == 0:
            # using functions in census.py, call the API for the year.
            responseJson = ce.emp_by_year_NC(int(year))
            if responseJson == 'error':
                result = 'error'
            else:    
                censusyear = {"year": year, "result" : responseJson}
                censuscol.insert_one(censusyear)
                years_pop.append(year)
                result = "new"
        else:  # don't refresh if we have the data.  Eventually we would want to change this
            result = "existing"
            years_pop.append(year)
    final_year = years_pop[-1]
    return get_nc_data(final_year)



# These routes are used to populate the information from the database or files.

# return the nc information for the year.
@app.route("/get_census/<year>", methods=['GET'])
@cross_origin()
def get_census(year):

    # access the census collection given an year
    censuscol = mongo.db.census
    myquery = { "year": year }
    x = censuscol.count_documents(myquery)
    if x == 0:  # need to change to call refresh
        result = "none"
    else:
        censusdoc = censuscol.find_one(myquery)
        censusjson = json.loads(json_util.dumps(censusdoc))
        result = jsonify(censusjson)
    return result

# route that returns the county employment information
@app.route("/get_county_data/<county>", methods=['GET'])
@cross_origin()
def get_county_data(county):
    result = []

    # loop through the years
    for year in years_nc:
        censuscol = mongo.db.census
        myquery = { "year": year }
        x = censuscol.count_documents(myquery)
        if x == 0:  # pull the county information
            result.append(0)
        else:
            censusdoc = censuscol.find_one(myquery,{ "_id": 0, "result": 1 })
            censusjson = json.loads(json_util.dumps(censusdoc))
            result.append(deter_county(censusjson['result'],county,year))
    county_info = {"year" : year,
                    "size": result}
    return jsonify(county_info)

# For given year(2012~), return state-wide employees of each sector
@app.route("/get_nc_data/<year>", methods=['GET'])
@cross_origin()
def get_nc_data(year):

    censuscol = mongo.db.nccensus
    myquery = { "year": year }

    # check to see if the year exists in collection.  
    x = censuscol.count_documents(myquery)
    if x == 0:  # If not future change to handle a call to refresh.
        result = "none"
    else:
        censusdoc = censuscol.find_one(myquery)
        censusjson = json.loads(json_util.dumps(censusdoc))
        result = jsonify(censusjson)
    return result

# Return total employee numbers of NC of from 1986 to the given year
@app.route("/get_nc_total/<year>", methods=['GET'])
@cross_origin()
def get_nc_total(year):
    # set the index
    # sector : sub sectors exist or not
    # cind : county index
    # ein : emp index
    # nind : nicas code index
    sector = False
    eind = 1
    nind = 2
    yrs = []
    result = []
    print('get_nc_total' , years_pop)
#    test = ['2002','2004']
    for yr in years_pop:
        
        if int(yr) > int(year):
            break

        censuscol = mongo.db.nccensus
        myquery = { "year": yr }
        x = censuscol.count_documents(myquery)
        if x == 0:  # pull the county information
            result.append(0)
        else:
            censusdoc = censuscol.find_one(myquery,{ "_id": 0, "result": 1 })
            censusjson = json.loads(json_util.dumps(censusdoc))

            if (int(yr) > 1997):
                eind = 2
            if (int(yr) >= 2012 ):
                sector = True
                eind = 1           
            
            if (sector):
                ncemp = censusjson['result']
                selData = list(filter(lambda d: d[nind] == '00', ncemp))
                result.append( selData[0][eind]  )
                #print("yr: ", yr, selData)
            else:
                selData = censusjson['result'][1]
                result.append( selData[eind]  )
                #print("yr: ", yr, selData)

            # Append data to array
            yrs.append(yr)
            

    nc_info = {"year" : yrs,
                "size": result}  

    return jsonify(nc_info)

# route to pull the years needed for the drop down
@app.route("/get_years", methods=['GET'])
@cross_origin()
def get_years():
    recent_years = []
    for year in recent_years_wanted:
        if (year in years_pop) and (year in years_nc):
            recent_years.append(year)

    # return the years that our common between the 2 data sets years_pop and years_nc
    return jsonify(recent_years)

# route to pull the county information for that year
@app.route("/get_population/<year>/<county>", methods=['GET'])
@cross_origin()
def get_population(year, county):

    with open("./datasets/counties_pop_1990_2019.csv") as cfile:
        pp_data = csv.reader(cfile)
        next(pp_data)
        sel_pop = list(filter(lambda d: (d[1] == county) & (int(d[0])<=int(year)), pp_data))
        sel_pop.sort(key=lambda d:d[0])
        yrs = []
        vls = []
        for yr in years_pop:
            if int(yr) > int(year):
                break
            if int(yr) < 1990:
                yrs.append(yr)
                vls.append(sel_pop[0][2])
            elif int(yr) < 2000:
                yrs.append(yr)
                vls.append(sel_pop[1][2])
            else:
                yrs.append(yr)
                yr_pop = list(filter(lambda d: d[0] == yr, sel_pop))
                vls.append(yr_pop[0][2])
        pop_info = {
            'year': yrs,
            'size': vls
        }
    return jsonify(pop_info)
        
# route to pull the population for the year identified.
@app.route("/get_pop/<year>", methods=['GET'])
@cross_origin()
def get_pop(year):
    # the data starts with year 2010 and the index of 1.  Subtract 2009 from the years to get index
    # into the list item.
    year_index = int(year) - 2009
    result = {}
    # opening the CSV file
    with open('./datasets/countytotals_2010_2019.csv', mode='r')as file:

        # reading the CSV file
        csvFile = csv.reader(file)

        # skip the initial 4 lines of data
        next(csvFile)
        next(csvFile)
        next(csvFile)
        next(csvFile)

        for lines in csvFile:

           #put the data into a dioctionary
           result[lines[0]] = lines[year_index]
            
    return jsonify(result)

@app.route("/get_combined_codes", methods=['GET'])
@cross_origin()
def get_combined_codes():

    with open('./datasets/combined_county_codes.json', mode='r')as file:

        # Reading from json file 
        json_object = json.load(file) 

    return json_object

if __name__ == "__main__":
    app.run()
