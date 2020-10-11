from flask import Flask, render_template, redirect, url_for, Response, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
import requests
import json
from pymongo import MongoClient
from gridfs import GridFS
from bson import objectid, json_util, BSON
import census as ce
import csv 



#years= ['1986','1988','1990','1992','1994','1996','1998','2000','2002','2004','2006','2008','2010','2012','2013','2014','2015','2016','2017','2018']
#recent_years= ['2012', '2013','2014','2015','2016','2017','2018']
years_wanted= ['1986','1988','1990','1992','1994','1996','1998','2000','2002','2004','2006','2008','2010','2012','2013','2014','2015','2016','2017','2018']
recent_years_wanted= ['2012','2013','2014','2015','2016','2017','2018']

years_nc = []
years_pop = []
recent_years = []

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

app.config['Mongo_URI'] = 'mongodb+srv:'

# run in debug mode
app.debug = True

mongo = PyMongo(app)

db = MongoClient().mygrid 
fs = GridFS(db)

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
      
        
#This is not recommended in production
#What would happen is every time you visit the root route it would load the DB again with all the data

@app_route("/",methods=['GET','POST'])
def root():
    # return render_template('index.html')
    return app.send_static_file("index.html")


# get the GEOJSON information from mongodb
@app.route("/get_geo", methods=["GET"])
def get_geo():

    #to acces the data first we need to get the colletion in where the files are stored
    col = db.fs.files.find_one()

    if col == None:
        print("GeoJSON is still loading please wait and reselect year")
        data = {}
    else:
    # once we have the object storing the file information, we can get the data and read it
        bsdata = fs.get(col["_id"]).read()

        # since the data was encode, we need to decode it back
        data = BSON.decode(bsdata)

    return jsonify(data)

# call the API to load the nc geo JSON and store into Mongo DB if not there.
@app.route("/reload_geo", methods=["GET"])
def reload_geo():
    # check to see if there is an exisitng file.  If so than do not reload
    col = db.fs.files.find_one()

    if col == None:
        # if the geojson file is not stored, call the API.
        response = requests.get("https://opendata.arcgis.com/datasets/d192da4d0ac249fa9584109b1d626286_0.geojson")

        # GridFS stored BSON binary files, the fucntion to do that is BSON.encode
        geojson = BSON.encode(response.json())

        # then we store it with the put()
        fs.put(geojson)

    return get_geo()

# call the API to load the nc employment and store into Mongo DB if not there.
@app.route("/reload_census", methods=["GET"])
@cross_origin()
def reload_census():
 
    # access the census collection
    censuscol = mongo.db.census

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
                censuscol.insert(censusyear)
                years_nc.append(year)
                result = "new"

        else:  # don't refresh if we have the data.  Eventually we would want to change this
            result = "existing"
            years_nc.append(year)
    print(years_nc)
    return result

# call the API to load the nc population and store into Mongo DB if not there.
@app.route("/reload_nccensus", methods=["GET"])
@cross_origin()
def reload_nccensus():
 
    # access the nccensus collection
    censuscol = mongo.db.nccensus
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
                censuscol.insert(censusyear)
                years_pop.append(year)
                result = "new"
        else:  # don't refresh if we have the data.  Eventually we would want to change this
            result = "existing"
            years_pop.append(year)
    print(years_pop)
    return result


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
