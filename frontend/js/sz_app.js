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
// mapbox 
// L.mapbox.accessToken = 'pk.eyJ1IjoiYWJkZWxyYWhtYW5odXNzZWluIiwiYSI6ImE1NTdkM2NjNzBlYWViZDZlYzg3ODVjNDZkYTk4MTJiIn0.94E8T4tbJCKrPIdyQL-TzQ';
// var map = L.mapbox.map('map', 'mapbox.streets')
// .setView([51.029007, 13.736552], 13);

// mapbox gl
mapboxgl.accessToken = 'pk.eyJ1IjoiYWJkZWxyYWhtYW5odXNzZWluIiwiYSI6ImE1NTdkM2NjNzBlYWViZDZlYzg3ODVjNDZkYTk4MTJiIn0.94E8T4tbJCKrPIdyQL-TzQ';
var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v9'
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


    // call the basic disatnce filter
    jQuery.ajax( {
        url: 'http://185.69.164.90:8090/api',
        type: 'post',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({ filters: {location: {source: [position.coords.longitude, position.coords.latitude], distance: 1500}} }),
        // test with berlin as a center point
        // data: JSON.stringify({ filters: {location: {source: [52.513728, 13.409660], distance: 500}} }),
        // traditional: true,
        success: function( response ) {
            // reponse
            console.log(response)
            if (response.count == 0){
                return
            }
            for (var item in response.response){
                item = response.response[item]
                item.marker_size = [24, 24]
                marker_data = {
                    size: item.marker_size,
                    position: {
                        longitude: item.address.coordinates[0],
                        latitude: item.address.coordinates[1]
                    },
                    id: item.dialog_id
                }
                news_markers.set(item.dialog_id, create_marker('article', map, marker_data));
            }
        },
        error: function (data){
            // error
            console.log(data)
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