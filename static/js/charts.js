/*
Define the Business sector codes and names
*/
const naics_codes = {
    //"00": "Total for all sectors",
    "11": "Agri-Food",
    "21": "Mining",
    "22": "Utilities",
    "23": "Construction",
    "42": "Wholesale trade",
    "51": "Information",
    "52": "Finance & insurance",
    "53": "Real estate",
    "54": "Professional",
    "55": "Securities Management",
    "56": "Waste Management",
    "61": "Educational services",
    "62": "Human Services",
    "71": "Recreation Services",
    "72": "Service Industry",
    "81": "Other services",
    "95": "Auxiliary Establishments",
    "99": "Unclassified" };

console.log("charts.js");
local = '';    // for running with Heroku
// local = 'http://127.0.0.1:5000';           // for running with Flask local

/**  Chart styling functions */
function ncColor(op) {
    // op: opacity [0,1]
    return `rgba(21, 67, 96, ${op})`
}

function countyColor(op) {
    // op: opacity
    return `rgba(255,12,32,${op})`
}

/*---------- Initialize Charts -----------------------------------*/
// Create new Bar Chart (blank data)
var ctx = document.getElementById('barChart').getContext('2d');
var myBarChart = new Chart(ctx, {
    type: 'horizontalBar',
    data: {
        labels: '',
        datasets: [{
            label: '',
            data: []
        }]
    },
    options: {
        legend: { 
            display: false
        },
        title: {
            display: true,
            text: "Employees of Sectors"
        }
    }
});
// Create new Line Chart (blank data)
ctx = document.getElementById('lineChart').getContext('2d');
var myLineChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: '',
        datasets: [{
            label: '',
            data: []
        }]
    },
    options: {
        legend: { 
            display: false
        },
        title: {
            display: true,
            text: "Employees of NC since 1986"
        }
    }
});
/*------- End of Initialization -----*/

//======= Functions ======================
/* Name: empNCbar
  Description: This updates the bar chart with the NC employment data of the year.
  Input:
    year - year (string)
  Returns:
    none
*/
function empNCbar(year) {

    var eind = 1 // emp index
    var nind = 2 // naics-code index

    url = local + "/get_nc_data/" + year;

    d3.json(url, function(data) {

        
        // Remove the first row - column names and second row-total number
        ncInfo = data.result.slice(2);

        // Sort the array by emp numbers
        ncInfo.sort( (a,b) =>  parseInt(b[eind]) - parseInt(a[eind]) );

        // Set labels as naics codes    
        codes = ncInfo.map( (x) => naics_codes[x[nind]] );

        // Set values as emp numbers
        values = ncInfo.map( (x) => parseInt(x[eind]) );

        // Updating chart with new data
        myBarChart.data.labels = codes.map( (c) => c);
        myBarChart.data.datasets.forEach((dataset) => {
            dataset.label = 'NC statewide';
            dataset.data = values.map( (d) => d);
            dataset.backgroundColor = codes.map( (d) => ncColor(0.6) )
        });
        myBarChart.options.legend.display = true;
        myBarChart.options.title.text = 'Employees of Sectors in '+year;
        myBarChart.update();
    });
}

// Line chart of .


/* Name: empNCtimeline
  Description: This updates the line chart with employment and population of years from 1986 to the given year
  Input:
    year - year (string)
  Returns:
    none
*/
function empNCtimeline(year) {

    url = local + "/get_nc_total/" + year;

    d3.json(url, function(data){
        values = data.size;
        years = data.year;

        while (myLineChart.data.datasets.length > 0) {
            myLineChart.data.datasets.pop()
        }
        
        console.log("in NCtimeline", myLineChart.data.datasets)

        myLineChart.data.labels = years;
        myLineChart.data.datasets.push({
            label : 'NC Employees',
            data : values.map( (d) => d),
            borderColor : ncColor(1),
            backgroundColor:  ncColor(0.5),
            fill : false
        })

        console.log("in NCtimeline", myLineChart.data.datasets)

        myLineChart.options.legend.display = true;
        myLineChart.update();

        // Updating chart with new data - population data
        pop_url = local + "/get_population/" + year + "/STATE"
        d3.json(pop_url, function(population){

            // Default is population data 'on'
            updateLinePopulation(myLineChart,population,'STATE');

            // Option whether show population on or off
            var myToggle = d3.select("#myToggle-NC");
            d3.select("#myToggle-CT").html("");
            myToggle.html('<label class="switch"><input type="checkbox" > <span class="slider2 round"></span></label>')

            var isDefault = true;

            myToggle.select(".switch").on("change", function(){
                if (isDefault == true) {
                    console.log("in true", myLineChart.data.datasets);
                    myLineChart.data.datasets.pop();
                    myLineChart.update();
                    isDefault = false;
                }
                else {

                    console.log("in false", myLineChart.data.datasets);
                    isDefault = true;
                    updateLinePopulation(myLineChart,population,'STATE');
                    console.log("in false", myLineChart.data.datasets);
                }
            });
        });
    });  
}

/* Name: countyCharts
  Description: This updates, for the county,
    the bar chart with the employment data of the year and
    the line chart with the employment and population of years from 1986 to the given year
  Input:
    year - year (string)
    county - county name (string)
    census - employment data of county
  Returns:
    none
*/

function countyCharts(year, county, census) {

    //-- Update the bar chart

    var cind = 4 // county index
    var eind = 1 // emp index
    var nind = 2 // naics-code index

    console.log("in countyCharts", year)

    d3.json(local + "/get_combined_codes", function(codes){
        //console.log(codes,county)
        // Get the county number for census and adjust the length of string
        var countyNbr = codes[county].Census_NBR;
        if (countyNbr.length < 3) { countyNbr = "0"+countyNbr; }

        // Get the info for the county
        var countyInfo = census.filter( (dt) => dt[cind] == countyNbr );
    
        // Sort the info by emp number in descending orger
        countyInfo.sort( (a,b) => b[eind] - a[eind] );
    
        // Set labels as naics codes    
        codes = countyInfo.map( (x) => naics_codes[x[nind]] );
    
        // Set values as emp numbers
        values = countyInfo.map( (x) => parseInt(x[eind]) );
    
        // Remove the entry for total '00'
        codes = codes.slice(1);
        values = values.slice(1);
        
        // Set a new dataset with the county info
        var newDataset = {
            label: county+' County',
            backgroundColor:  codes.map( (d) => countyColor(0.6) ),
            data: values
        }
        // Updating chart with new employment data
        myBarChart.data.datasets.pop();
        myBarChart.data.labels = codes;
        myBarChart.data.datasets.push(newDataset);
        myBarChart.options.legend.display = true;
        myBarChart.options.title.text = 'Employees of Sectors in '+year;
        myBarChart.update();
    })

    //- Update the line chart
    var url = local + "/get_county_data/"+county;
    d3.json(url, function(data) {

        while (myLineChart.data.datasets.length > 0) {
            myLineChart.data.datasets.pop()
        }

        // Set a new dataset with county data       
        var newDataset = {
            label: 'Employees',
            fill: false,
            fillColor: countyColor(0.5),
            backgroundColor: countyColor(0.5),
            borderColor:  countyColor(0.6), 
            data: data.size
        }
        myLineChart.data.datasets.push(newDataset);



        // Updating chart with new data - population data
        pop_url = local + "/get_population/" + year + "/" + county

        d3.json(pop_url, function(population){

            console.log("for pop", county, population)

            // Default is population data on
            updateLinePopulation(myLineChart,population,county);

            // Option whether show population or not
            var myToggleCT = d3.select("#myToggle-CT");
            d3.select("#myToggle-NC").html("");
            myToggleCT.html('<label class="switch"><input type="checkbox" > <span class="slider round"></span></label>')


            var isDefault = true;
            
            myToggleCT.select(".switch").on("change", function(){
                if (isDefault == true) {
                    console.log("in true-CT", myLineChart.data.datasets.length);                   
                    myLineChart.data.datasets.pop();
                    console.log("in --", myLineChart.data.datasets[0]);
                    myLineChart.update();
                    isDefault = false;
                }
                else {
                    console.log("in false-CT", myLineChart.data.datasets.length);
                    isDefault = true;
                    updateLinePopulation(myLineChart,population,county);
                    console.log("in false-CT", myLineChart.data.datasets);
                }
            });


        });   
    });
}

/* Name: updateLinePopulation
  Description: This updates the line chart
    after adding the dataset with the population data
  Input:
    myLine - pointer to chart
    population - population data
    county - county name
  Returns:
    none
*/

function updateLinePopulation(myLine,population,county){

    if (county == 'STATE') {
        titleArea = 'NC '
    }
    else {
        titleArea = county + ' County '
    }

    var newDataSet = {
        label: 'Population',
        data: population.size,
        borderwidth: 0.2,
        borderColor : 'rgba(128, 128, 128, 0.1)',
        backgroundColor:  'rgba(128, 128, 128, 0.1)',
        pointRadius: 0,
        fill: true,
        cubicInterpolationMode: 'monotone'
    }
    console.log("in update function,", myLine.options.title)

    myLine.data.datasets.push(newDataSet);

    console.log("in update function,", myLine.data.datasets)

    myLine.options.legend = {
        display : true,
        fillStyle: 'rgba(255,255,255, 0.5)'
    }
    myLine.options.title = {
        display : true,
        text: titleArea + 'Employees since 1986'
    }

    myLine.update();
}
