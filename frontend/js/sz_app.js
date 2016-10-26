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
    marker = new mapboxgl.Marker(el, {offset: [-marker_data.size[0] / 2, -marker_data.size[1] / 2]})
        .setLngLat([marker_data.position.longitude, marker_data.position.latitude])
        .addTo(map_obj);    

}
function showPosition(position) {

    map.flyTo({
        center: [position.coords.longitude, position.coords.latitude],
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
        data: JSON.stringify({ filters: {location: {source: [position.coords.latitude, position.coords.longitude], distance: 500}} }),
        // traditional: true,
        success: function( response ) {
            // reponse
            console.log(response)
            for (var item in response.response){
                item = response.response[item]
                marker_data = {
                    size: [24, 24],
                    position: {
                        longitude: item.address.coordinates[1],
                        latitude: item.address.coordinates[0]
                    },
                    id: item.dialog_id
                }
                create_marker('article', map, marker_data);
            }
        },
        error: function (data){
            // error
            console.log(data)
        }
    } );

}