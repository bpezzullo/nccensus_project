# Dependencies and Setup
import pandas as pd
import numpy as np
import requests
import json
# import time

#----- Import API key ---------------
from config import census_api_key

#----- Define functions
## Set a naics code query to restrict the API call only for 2-digit business codes
def set_naics_query(year):
    
    # The NAICES codes for higher level business
    NAICS_codes = ['00', '11', '21', '22', '23', '42', '51', '52', '53', '54', '55', '56', '61', '62', '71', '72', '81', '95', '99']
    code_query = ""
    for code in NAICS_codes:
        if (year >= 2017):
            code_query += f'&NAICS2017={code}'
        elif (year >= 2012):
            code_query += f'&NAICS2012={code}'
    return code_query

## Set a url for given year to retrieve employee data for all counties.
def set_url(year):
    
    cbp_url = f'https://api.census.gov/data/{year}/cbp?get='
    
    ## The quary variables vary in years
    if (year >= 2017):
        variables = "NAME,EMP"
    elif (year >= 2012):
        variables = "GEO_TTL,EMP"
    elif (year > 2007):
        variables = "NAICS2007_TTL,GEO_TTL,EMP"
    elif (year > 2002):
        variables = "NAICS2002_TTL,GEO_TTL,EMP"
    elif (year > 1997):
        variables = "NAICS1997_TTL,GEO_TTL,EMP"
    else:
        variables = "GEO_TTL,EMP"
    
    url = cbp_url+variables+"&for=county:*&in=state:37&key="+census_api_key
    
    # From 2012, there are subcategories upto 2~6 digits in NAICS codes. We collect only 2 digits codes.
    if (year >= 2012):
        url += set_naics_query(year)
    
    return url

## Function: County data for all years
#     returns a table of given county with total employees for 1986~2018
def county_all_years(county):
    census = []
    for year in np.arange(1986,2018):
        
        #print(year)
        
        cbp_url = f'https://api.census.gov/data/{year}/cbp?get='
        if (year >= 2017):
            variables = "NAICS2017,EMP"
        elif (year >= 2012):
            variables = "NAICS2012_TTL,EMP"
        elif (year > 2007):
            variables = "NAICS2007_TTL,EMP"
        elif (year > 2002):
            variables = "NAICS2002_TTL,EMP"
        elif (year > 1997):
            variables = "NAICS1997_TTL,EMP"
        else:
            variables = "GEO_TTL,EMP"
            
        url = cbp_url+variables+f'&for=county:{county}&in=state:37&key='+census_api_key
        if (year >= 2017):
            url = url + "&NAICS2017=00"
            
        #print(url)
        
        try:
            response = requests.get(url)
            #print(response)
            year_data = response.json()
            #print(json.dumps(year_data, indent=4))
            census.append(year_data[1][1])
        except:
            print(f"Found error")    

    return census


## Set a url to query State-wide data
def set_url_NC(year):
    
    cbp_url = f'https://api.census.gov/data/{year}/cbp?get='
    
    ## The quary variables vary in years
    if (year >= 2017):
        variables = "NAME,EMP"
    elif (year >= 2012):
        variables = "GEO_TTL,EMP"
    elif (year > 2007):
        variables = "NAICS2007_TTL,GEO_TTL,EMP"
    elif (year > 2002):
        variables = "NAICS2002_TTL,GEO_TTL,EMP"
    elif (year > 1997):
        variables = "NAICS1997_TTL,GEO_TTL,EMP"
    else:
        variables = "GEO_TTL,EMP"
    
    url = cbp_url+variables+"&for=state:37&key="+census_api_key
    
    # From 2012, there are subcategories upto 2~6 digits in NAICS codes. We collect only 2 digits codes.
    if (year >= 2012):
        url += set_naics_query(year)
    
    return url

#---- Perform API calls

## For given year, collect EMP data for all counties

def emp_by_year(year):
    
    url = set_url(year)

    try:
        response = requests.get(url)
        #print(response)
        census_data = response.json()
        #print(json.dumps(census_data, indent=4))
    except:
        print(f"Found error")
        census_data = "error"   
    #df = pd.DataFrame(census_data, columns=census_data[0])
    #emp_df=df.drop(0).drop("state",axis=1)

    return census_data


# ## For given county, collect EMP data for all years
# # example: Wake county = '183'
# def emp_by_county(county):
#     emp_ct = county_all_years(county)
#     emp_ct_df = pd.DataFrame({
#         "County" : [county]*len(emp_ct),
#         "Year" : np.arange(1986,2018),
#         "EMP" : emp_ct
#     })
#     return emp_ct_df

def emp_by_year_NC(year):
        
    url = set_url_NC(year)

    try:
        response = requests.get(url)
        #print(response)
        census_data = response.json()
        #print(json.dumps(census_data, indent=4))
    except:
        print(f"Found error")
        census_data = "error"   
        
    #df = pd.DataFrame(census_data, columns=census_data[0])
    #emp_df=df.drop(0).drop("state",axis=1)

    return census_data