 // Closes the sidebar menu
$("#menu-close").click(function(e) {
    e.preventDefault();
    $("#sidebar-wrapper").toggleClass("active");
});
// Opens the sidebar menu
$("#menu-toggle").click(function(e) {
    e.preventDefault();
    $("#sidebar-wrapper").toggleClass("active");
});
// Scrolls to the selected menu item on the page
$(function() {
    $('a[href*=#]:not([href=#],[data-toggle],[data-target],[data-slide])').click(function() {
        if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') || location.hostname == this.hostname) {
            var target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            if (target.length) {
                $('html,body').animate({
                    scrollTop: target.offset().top
                }, 1000);
                return false;
            }
        }
    });
});
//#to-top button appears after scrolling
var fixed = false;
$(document).scroll(function() {
    if ($(this).scrollTop() > 250) {
        if (!fixed) {
            fixed = true;
            // $('#to-top').css({position:'fixed', display:'block'});
            $('#to-top').show("slow", function() {
                $('#to-top').css({
                    position: 'fixed',
                    display: 'block'
                });
            });
        }
    } else {
        if (fixed) {
            fixed = false;
            $('#to-top').hide("slow", function() {
                $('#to-top').css({
                    display: 'none'
                });
            });
        }
    }
});

// result markers
var news_markers = new Map();
var current_result = {};
var articles_source_id = "articles";
var current_user_location = new Array();
var current_filters = {};
var current_sources = new Array();
var current_layers = new Array();
// mapbox 
// L.mapbox.accessToken = 'pk.eyJ1IjoiYWJkZWxyYWhtYW5odXNzZWluIiwiYSI6ImE1NTdkM2NjNzBlYWViZDZlYzg3ODVjNDZkYTk4MTJiIn0.94E8T4tbJCKrPIdyQL-TzQ';
// var map = L.mapbox.map('map', 'mapbox.streets')
// .setView([51.029007, 13.736552], 13);

// mapbox gl
mapboxgl.accessToken = 'pk.eyJ1IjoiYWJkZWxyYWhtYW5odXNzZWluIiwiYSI6ImE1NTdkM2NjNzBlYWViZDZlYzg3ODVjNDZkYTk4MTJiIn0.94E8T4tbJCKrPIdyQL-TzQ';
var map = new mapboxgl.Map({
    container: 'map',
    // style: 'mapbox://styles/mapbox/light-v9'
    style: 'mapbox://styles/abdelrahmanhussein/civ307qxk000u2iozvu6xz1rx'
});

// Add zoom and rotation controls to the map.
map.addControl(new mapboxgl.NavigationControl());

// current location control
var geolocation_control = new mapboxgl.GeolocateControl();
map.addControl(geolocation_control);

// on load handler
map.on('load', function(){
    getLocation();
    map.scrollZoom.disable();
});

// on zoom handler
var zoom_threshold = 13;
var building_3d_layer = false;
var building_3d_layer_id = '3d-buildings';
map.on('zoom', function(){
    if (map.getZoom() >= zoom_threshold){
        if (building_3d_layer == false){
            map.addLayer({
                'id': building_3d_layer_id,
                'source': 'composite',
                'source-layer': 'building',
                'filter': ['==', 'extrude', 'true'],
                'type': 'fill',
                'minzoom': 15,
                'paint': {
                    'fill-color': '#aaa',
                    'fill-extrude-height': {
                        'type': 'identity',
                        'property': 'height'
                    },
                    'fill-extrude-base': {
                        'type': 'identity',
                        'property': 'min_height'
                    },
                    'fill-opacity': .6
                }
            });
            building_3d_layer = true;
        }
        map.setLayoutProperty(building_3d_layer_id, 'visibility', 'visible');
    }else{
        if (building_3d_layer == true){
            map.setLayoutProperty(building_3d_layer_id, 'visibility', 'none');
        }
    }
});

// get the current user location 
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition);
    }
}
function create_marker(marker_type, map_obj, marker_data){
    // create a DOM element for the marker
    var el = document.createElement('div');
    el.className = 'marker';
    el.id = 'marker_current_location'
    el.style.backgroundImage = 'url(./img/location_marker.png)';
    if (marker_type == 'article'){
        el.className += ' marker_article'
        el.id = marker_data.id
        el.style.backgroundImage = 'url(./img/article_marker.png)';
    }
    el.style.width = marker_data.size[0] +'px';
    el.style.height = marker_data.size[1] + 'px';

    // add marker to map
    return new mapboxgl.Marker(el, {offset: [-marker_data.size[0] / 2, -marker_data.size[1] / 2]})
        .setLngLat([marker_data.position.longitude, marker_data.position.latitude])
        .addTo(map_obj); 
}

function showPosition(position) {
    current_user_location = [position.coords.longitude, position.coords.latitude];
    map.flyTo({
        center: [position.coords.longitude, position.coords.latitude],
        // test with berlin as a center point
        // center: [13.409660, 52.513728],
        zoom: 12,
        bearing: 0,
        pitch: 0,

        // These options control the flight curve, making it move
        // slowly and zoom out almost completely before starting
        // to pan.
        speed: 0.5, // make the flying slow
        curve: 1.42, // change the speed at which it zooms out

        // This can be any easing function: it takes a number between
        // 0 and 1 and returns another number between 0 and 1.
        easing: function (t) {
            return t;
        }
    });


    map.on('moveend', function(eventData){
        marker_data = {
                        size:[24, 24],
                        position: {
                            longitude: position.coords.longitude,
                            latitude: position.coords.latitude
                            // test with berlin as a center point
                            // longitude: 13.409660,
                            // latitude: 52.513728
                        },
                       }
        create_marker('location', map, marker_data)
        // create a DOM element for the marker
        // var el = document.createElement('div');
        // el.className = 'marker';
        // el.id = 'marker_current_location'
        // el.style.backgroundImage = 'url(./img/location_marker.png)';
        // el.style.width = '40px';
        // el.style.height = '40px';

        // // add marker to map
        // new mapboxgl.Marker(el, {offset: [-40 / 2, -40 / 2]})
        //     .setLngLat([position.coords.longitude, position.coords.latitude])
        //     .addTo(map);
    });

    // call the default distance filter
    // default_filter = { filters: {location: {source: [position.coords.longitude, position.coords.latitude], distance: 1500}}, 
    //                     user_location: current_user_location }
    update_filters({location: {source: [position.coords.longitude, position.coords.latitude], distance: 1500}})
    query_server(current_filters, null, null)

}

// Create a popup, but don't add it to the map yet.
var popup = new mapboxgl.Popup({
    closeButton: false,
    closeOnClick: false
});

// When a click event occurs near a place, open a popup at the location of
// the feature, with description HTML from its properties.
map.on('click', function (e) {
    var features = map.queryRenderedFeatures(e.point, { layers: [articles_source_id] });

    if (!features.length) {
        return;
    }

    var feature = features[0];

    // Populate the popup and set its coordinates
    // based on the feature found.
    var div = window.document.createElement('div');
    var text = feature.properties.text.slice(0, 200) + "...";
    div.innerHTML = `<h5>${feature.properties.heading}</h5><p>${text}</p><a href='http://www.sz-online.de/' target="_blank">Read more</a>`;
    var popup = new mapboxgl.Popup()
        .setLngLat(feature.geometry.coordinates)
        // .setHTML(feature.properties.text.slice(0, 200) + "...")
        .setDOMContent(div)
        .addTo(map);
});

// Use the same approach as above to indicate that the symbols are clickable
// by changing the cursor style to 'pointer'.
map.on('mousemove', function (e) {
    var features = map.queryRenderedFeatures(e.point, { layers: [articles_source_id] });
    map.getCanvas().style.cursor = (features.length) ? 'pointer' : '';
});


// create mapbox sources from the news article data
function create_source(data){
    map.addSource(articles_source_id, {
        "type": "geojson",
        "data": {
            "type": "FeatureCollection",
            "features": data.response
        },
        "cluster": true,
        "clusterRadius": 10
    });
    current_sources.push(articles_source_id);
}

// function to update the map with the latest filte rresults
function update_map(data){
    // cleaar the map source and layer
    current_layers.forEach(function(layer_id){
        map.removeLayer(layer_id);
    });
    current_sources.forEach(function(source_id){
        map.removeSource(source_id)
    });
    current_layers = new Array();
    current_sources = new Array();
    
    if (data.count == 0){
        return
    }
    // create/update mapbox source
    create_source(data);
    // add layer
    map.addLayer({
        "id": articles_source_id,
        "type": "symbol",
        "source": articles_source_id,
        "filter": ["!has", "point_count"],
        "layout": {
            "icon-image": "newspaper",
            "icon-allow-overlap": true
        }
    });
    current_layers.push(articles_source_id)
    // Display the earthquake data in three layers, each filtered to a range of
    // count values. Each range gets a different fill color.
    var layers = [
        [10, '#f28cb1'],
        [5, '#f1f075'],
        [0, '#51bbd6']
    ];

    layers.forEach(function (layer, i) {
        layer_id = "cluster-" + i 
        map.addLayer({
            "id": layer_id,
            "type": "circle",
            "source": articles_source_id,
            "paint": {
                "circle-color": layer[1],
                "circle-radius": 18
            },
            "filter": i === 0 ?
                [">=", "point_count", layer[0]] :
                ["all",
                    [">=", "point_count", layer[0]],
                    ["<", "point_count", layers[i - 1][0]]]
        });
        current_layers.push(layer_id)
    });

    // Add a layer for the clusters' count labels
    var cluster_count_layer_id = "cluster-count";
    map.addLayer({
        "id": cluster_count_layer_id,
        "type": "symbol",
        "source": articles_source_id,
        "layout": {
            "text-field": "{point_count}",
            "text-font": [
                "DIN Offc Pro Medium",
                "Arial Unicode MS Bold"
            ],
            "text-size": 12
        }
    });
    current_layers.push(cluster_count_layer_id)
}

// function to query the server and return the output
function query_server(filters, on_success, on_error){
    query = {filters: filters, user_location: current_user_location}
    console.log(`Querying server with query ${query}`)
    var url = 'http://185.69.164.90:8090/api';
    var type = 'post';
    var content_type = "application/json; charset=utf-8";
    var data = JSON.stringify(query)

    jQuery.ajax( {
        url: url,
        type: type,
        contentType: content_type,
        // data: JSON.stringify({ filters: {location: {source: [position.coords.longitude, position.coords.latitude], distance: 1500}} }),
        data: data,
        // test with berlin as a center point
        // data: JSON.stringify({ filters: {location: {source: [52.513728, 13.409660], distance: 500}} }),
        // traditional: true,
        success: function( response ) {
            // reponse
            console.log(response);
            current_result = response;
            // call the update map function
            update_map(response);
            // call the on_success callback 
            if (on_success){
                on_success(response)
            }
        },
        error: function (data){
            // error
            console.log(`Error: ${data}`);
            // call the on_error callback
            if (on_error){

            }
        }
    } );

}

// handle the click of the collapsing panel
jQuery(function ($) {
    $('.panel-heading span.clickable').on("click", function (e) {
        if ($(this).hasClass('panel-collapsed')) {
            // expand the panel
            $(this).parents('.panel').find('.panel-body').slideDown();
            $(this).removeClass('panel-collapsed');
            $(this).find('i').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
        }
        else {
            // collapse the panel
            $(this).parents('.panel').find('.panel-body').slideUp();
            $(this).addClass('panel-collapsed');
            $(this).find('i').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
        }
    });
});

function update_filters(filter){
    current_filters = Object.assign({}, current_filters, filter);
}

function on_search_button_clicked(){
    var search_text = document.getElementById("search_input").value
    update_filters({text: search_text})
    query_server(current_filters, null, null)
}

function on_distance_slider_change(distance){
    update_filters({location: {source: current_user_location, distance: parseInt(distance)}})
    query_server(current_filters, null, null)
}

$(document).ready(function(){
    document.getElementById("seach_button").onclick = on_search_button_clicked;
    var distance_slider = document.getElementById("distance_slider");
    noUiSlider.create(distance_slider, {
        start: 1500,

        // Disable animation on value-setting,
        // so the sliders respond immediately.
        animate: false,
        range: {
            min: 0,
            max: 10000
        }
    });
    distance_slider.noUiSlider.on('update', function(values, handle){
        document.getElementById("range").innerHTML = values[handle] + " m";
        
    });
    distance_slider.noUiSlider.on('change', function(values, handle){
        on_distance_slider_change(values[handle]);
    });

    var dateSlider = document.getElementById('time_slider');

    var today = new Date();
    var two_months_ago = new Date();
    two_months_ago.setDate(today.getDate() - 60);

    noUiSlider.create(dateSlider, {
    // Create two timestamps to define a range.
        range: {
            min: timestamp('June 1, 2016'),
            max: new Date().getTime()
        },

    // Steps of one day
        step: 1 * 24 * 60 * 60 * 1000,

    // Two more timestamps indicate the handle starting positions.
        start: [ two_months_ago.getTime(),  today.getTime()],

    // No decimals
        format: wNumb({
            decimals: 0
        })
    });
    var dateValues = [
        document.getElementById('event-start'),
        document.getElementById('event-end')
    ];

    dateSlider.noUiSlider.on('update', function( values, handle ) {
        dateValues[handle].innerHTML = formatDate(new Date(+values[handle]));
        var from_date = new Date(+values[0])
        from_date = from_date.getDate() + "." + (parseInt(from_date.getMonth()) + 1) + "." + from_date.getFullYear();
        var to_date = new Date(+values[1])
        to_date = to_date.getDate() + "." + (parseInt(to_date.getMonth()) + 1) + "." + to_date.getFullYear();
        update_filters({time: [from_date, to_date]});
    });
    dateSlider.noUiSlider.on('change', function( values, handle ) {
        query_server(current_filters, null, null);
    });
});


// Create a new date from a string, return as a timestamp.
function timestamp(str){
    return new Date(str).getTime();   
}

// Create a list of day and monthnames.
var
    weekdays = [
        "Sunday", "Monday", "Tuesday",
        "Wednesday", "Thursday", "Friday",
        "Saturday"
    ],
    months = [
        "January", "February", "March",
        "April", "May", "June", "July",
        "August", "September", "October",
        "November", "December"
    ];

// Append a suffix to dates.
// Example: 23 => 23rd, 1 => 1st.
function nth (d) {
  if(d>3 && d<21) return 'th';
  switch (d % 10) {
        case 1:  return "st";
        case 2:  return "nd";
        case 3:  return "rd";
        default: return "th";
    }
}

// Create a string representation of the date.
function formatDate ( date ) {
    return weekdays[date.getDay()] + ", " +
        date.getDate() + nth(date.getDate()) + " " +
        months[date.getMonth()] + " " +
        date.getFullYear();
}





