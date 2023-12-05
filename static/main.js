$(document).ready(function() {
    $('#district-form').submit(function(event) {
        event.preventDefault();
        var districtCode = $('#district-select').val();
        $('#loading').show();
        $.post('/generate_map', { district_code: districtCode }, function(response) {
            waitForMapGeneration(districtCode);
        });
    });
});

function waitForMapGeneration(districtCode) {
    $.get('/get_data/' + districtCode, function(data) {
        if (data.status === 'completed') {
            $('#loading').hide();
            // Display map and data
            displayMap(data.map_url);
            displayData(data.land_data);
        } else {
            setTimeout(function() { waitForMapGeneration(districtCode); }, 2000);
        }
    });
}

function displayMap(mapUrl) {
    $('#map').html('<img src="' + mapUrl + '" alt="Generated Map">');
}

function displayData(landData) {
    // Populate table with land data
}
