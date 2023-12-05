$(document).ready(function(){
    $('#generateButton').click(function(){
        var selectedDistrict = $('#districtSelect').val();
        $('#loading').show();
        $('#mapResult').empty();
        $('#data-container').empty();

        $.post('/generate_map', {district: selectedDistrict}, function(data){
            checkMapStatus(selectedDistrict);
        });
    });
});

function showError(message) {
    $('#error-message').text(message).show();
}

function checkMapStatus(district_code) {
    $.get('/map_status', {district_code: district_code}, function(data) {
        if (data.status === 'Completed') {
            $('#mapResult').html('<img src="/maps/' + district_code + '" alt="Generated Map" class="img-fluid">');
            $('#loading').hide();
            fetchData(district_code);
        } else if (data.status.includes('Error')) {
            $('#loading').hide();
            showError('Error in map generation: ' + data.status);
        } else {
            setTimeout(function() { checkMapStatus(district_code); }, 2000);
        }
    }).fail(function() {
        $('#loading').hide();
        showError('Error checking map status.');
    });
}

function fetchData(district_code) {
    $.get('/get_data', {district_code: district_code}, function(landData) {
        populateTable(landData);
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Error fetching data:', textStatus, errorThrown);
    });
}

function populateTable(data) {
    $('#data-container').empty();
    $('#data-container').html(data['table']);
    $('#data-container table').addClass('table table-bordered table-hover');
}
