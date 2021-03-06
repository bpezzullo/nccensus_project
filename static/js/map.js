console.log(local);

console.log("map.js");
/* function to generate initial pull of the data to be stored in Mongodb.   
  Input:
    None

  Returns:
    None
*/
function init_data() {

  console.log("init");
    
    url = local + "/reload_geo"
  // Perform an API call to the get the data into MongoDB
  d3.json(url, function (call_status) {
    console.log('geo' , call_status);

  });
    console.log("geo called");
      url = local + "/reload_census"
      // Perform an API call to the get the data into MongoDB
      d3.json(url, function(cen_data) {
        console.log('census',cen_data);
        // while (call_status == null) {
        //   console.log("loop")
        // }


        url = local + "/reload_nccensus"
        // Perform an API call to the get the data into MongoDB
        d3.json(url, function (nc_data) {
          console.log("nc", nc_data);

          url = local + "/get_years"
          // Perform an API call to the get the years stored from MongoDB
          d3.json(url, function (data) {
            console.log('years', data)
            //Create the drop down list of subject IDs
            document.getElementById("selDataset").innerHTML = generatetxt(data);
            var init_year = parseInt(data[0]);
            console.log(init_year);
            cursor_wait();
            waiting(init_year);
            buildMap(init_year);
            empNCbar(init_year);
            empNCtimeline(init_year);
          });
      });
    });


  return;
}

//init_data();

init_data();

/* Name: fill_in_popup.  
  Description: This populates the pop-up when the county is selected 
  Input:
    name - county name
    numb - county number as seen by NC
    pop - key dataset of the population number for the counties
    county_d - array dataset of the census showing county data

  Returns:
    pop_html - text string with html encoding for the pop-up
*/
function fill_in_popup(name, numb, pop, county_d) {
  pop_html = "<h5>" + name + " (" + numb + ") </h5> <hr> <h6>Employment: ";
  var c_emp = determine_size(name, county_d);

  pop_html = pop_html + commaSeparateNumber(c_emp) + "</h6> <br> <h6>Total Population: ";
  pop_html = pop_html + commaSeparateNumber(pop[name]) + "</h6> <br> <h6>Employment: "
  var pop_d = (c_emp * 100 / pop[name]).toFixed(2);
  pop_html = pop_html + pop_d + "%</h6>";
  return pop_html;
}

/* Name: commaSeparateNumber
  Description:  Adds comma(s) to a number
  Input:
    val - number to be updated
  Returns
    val - string with commas
    */

function commaSeparateNumber(val){
  while (/(\d+)(\d{3})/.test(val.toString())){
    val = val.toString().replace(/(\d+)(\d{3})/, '$1'+','+'$2');
  }
  return val;
}

/* Name: waiting
  Description: When the map is loading provide information to keep the user entertained 
  Input:
    year - year

  Returns:
    None
*/
function waiting(year) {
  var data = '<h5 class="blink blink-one"> Map for year ' + year + ' is loading </h5>'
  document.getElementById("wait").innerHTML = data;
  return 
}

/* Name: map_comp
  Description: Map is completeed loading return display to normal 
  Input:
    year - year

  Returns:
    None
*/
function map_comp(year) {
  var data = 'Total Emplopyed by County Map in year ' + year
  document.getElementById("wait").innerHTML = data;
  return 
}

/* Name: optionChanged  
  Description: User has selected a year from the drop down.  Call the routines to populate the map
  and the panels. 
  Input:
    value - year from the drop down

  Returns:
    none
*/
function optionChanged(value) {
  cursor_wait();
  waiting(value);
  buildMap(value);
  empNCbar(value);
  empNCtimeline(value);

}

/* Name: generatetxt  
  Description:  to generate the text for the drop downs.  This function creates a text string
  used to populate the drop down. 
  Input:
    keylist - array of strings containing the year

  Returns:
    text - text string with html encoding with the format of 
      <option> year </option>
*/
function generatetxt(keylist) {
  // set up variables being used in function.
  var text = [], i;

  // loop through array to populate the drop down.
  for (i = 0; i < keylist.length; i++) {
    text += "<option>" + keylist[i] + "</option>";
  }
  return text
}


// Creating map object
var myMap = L.map("map", {
  //center: [35.787743, -78.644257],
  center: [35.22, -79.17],
  zoom: 7
});

// Adding tile layer
L.tileLayer("https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}", {
  attribution: "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>",
  tileSize: 512,
  maxZoom: 18,
  zoomOffset: -1,
  id: "mapbox/streets-v11",
  accessToken: API_KEY
}).addTo(myMap);

/* Name: change_panels  
  Description: Controls the selection of a county on the screen.  
  Input:
    county - county name
    year - year selected
    year_emp - array dataset of the census showing county data

  Returns:
    None
*/
function change_panels(county, year, year_emp) {

  // holding function to change the side panels.
  console.log(county);
  countyCharts(year, county, year_emp);

  return;
}

/* Name: determine_size
  Description: This returns the size of the county based on the identified year
  in the census.  
  Input:
    county - county name
    county_d - array dataset of the census showing county data

  Returns:
    size - This provides size of the county employees
*/
function determine_size(county, county_d) {


  var size = 0;
  var ind = 1;
  var name_ind = 0;
  // determine the type of data that we are looking at.  check to see the codes being used.
  if (county_d[0][2] == 'NAICS2012' || county_d[0][2] == 'NAICS2017') {
    // if the latest data formats then we see the number of employees, plus the number of employees
    // per sector.  See charts.js for the break down in the sectors.  In this case we want to look for
    // a sector of 00 which is for the whole county.

    county = county + " County, North Carolina";
    for (var i = 1; i < county_d.length - 1; i++) {
      // loop through the data and pull the information from the census document in memory
      if (county === county_d[i][name_ind] && '00' === county_d[i][2]) {
        size = parseInt(county_d[i][ind]);
      }
    }
  }
  else {
    if (county_d[0][0] == 'NAICS1997_TTL' || county_d[0][0] == 'NAICS2002_TTL' || county_d[0][0] == 'NAICS2007_TTL') {
      //  The older years only have the total number per county and have multiple formats.  Set up
      // the variables - ind which is the index to where the employment number is
      // - name_ind is the index for the name of the county
      // - county is the format of the county name
      ind += 1;
      name_ind += 1;
      suffix = county_d[1][name_ind].split(" ");
      if (suffix.length == 3) {
        county = county + " County, NC";
      }
      else if (suffix.length == 4) {
        county = county + ' County, North Carolina'
      }
      else {
        county = county + ", NC";
      }
    }
    else {
      county = county + " County, NC";
    }

    // once the needed variables are configured, find the population for the county.
    for (var i = 1; i < county_d.length - 1; i++) {
      if (county === county_d[i][name_ind]) {
        size = parseInt(county_d[i][ind]);
      }
    }
  }
  return size;
}


/* Name: chooseColor  
  Description: This populates the color for the county based on the size identified
  in the census.
  Input:
    county - county name
    county_info - array dataset of the census showing county data

  Returns:
    result - color of the county
*/
function chooseColor(county, county_info) {
  var result;
  var temp;
  var red = 0;
  var green = 0;
  var blue = 255;
  var mod;
  size = determine_size(county, county_info);
  // if (size <= 1000) {
  //   red = parseInt(size / 392);
  //   green = red;
  // }
  // else {
  //   if (size >= 600000) {
  //     blue = 16
  //   }
  //   mod = parseInt((size % 10000) / 1000) 
  //   blue = 255- (parseInt(size / 10000) + 1 * 40)
  //   red = mod;
  //   green = mod;
  // }
  // console.log(red,green,blue);
  temp = 0xFFFF00 - (0xf * parseInt(size / 10));
  result = '#' + temp.toString(16);
  // result = `rgb(${red},${green},${blue})`;
  return result;
}
/* Name: buildMap  
  Description: This populates the pop-up when the county is selected 
  Input:
    year - year to be displayed

  Returns:
    none
*/
function buildMap(year) {

  //empNCtimeline(year);

  // Use this link to get the geojson data.
  var link = local + "/get_geo"

  // Grabbing our GeoJSON data..
  d3.json(link, function (data) {

    url = local + "/get_census/" + year
    // Perform an API call to get the census daa for the year idnetified

    d3.json(url, function (county_data) {

      url = local + "/get_pop/" + year
      // Perform an API call to get the census daa for the year idnetified
  
      d3.json(url, function (pop_data) {

      var county_info = county_data.result;

      //empNCbar(county_info);

      // Creating a geoJSON layer with the retrieved data
      L.geoJson(data, {
        // Style each feature (in this case a neighborhood)
        style: function (feature) {
          return {
            color: "white",
            // Call the chooseColor function to decide which color to color our neighborhood (color based on borough)
            fillColor: chooseColor(feature.properties.NAME, county_info),
            fillOpacity: 0.5,
            weight: 1.5
          };
        },
        // Called on each feature
        onEachFeature: function (feature, layer) {
          // Set mouse events to change map styling
          layer.on({
            // When a user's mouse touches a map feature, the mouseover event calls this function, that feature's opacity changes to 90% so that it stands out
            mouseover: function (event) {
              layer = event.target;
              layer.setStyle({
                fillOpacity: 0.9
              });
            },
            // When the cursor no longer hovers over a map feature - when the mouseout event occurs - the feature's opacity reverts back to 50%
            mouseout: function (event) {
              layer = event.target;
              layer.setStyle({
                fillOpacity: 0.5
              });
            },
            // When a county is clicked, present the county information in a pop-up.
            // Also, change the lower panels to show county information
            click: function (event) {
              change_panels(this.feature.properties.CountyName, year, county_info);
            }
          });
          // Giving each feature a pop-up with information pertinent to it
          layer.bindPopup(fill_in_popup(feature.properties.CountyName, feature.properties.CNTY_NBR, pop_data,county_info));
        }
      }).addTo(myMap);
      cursor_clear();
      map_comp(year);
    });
  });
});
}
