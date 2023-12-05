$(document).ready(function(){
    // Show custom color input when 'Custom' is selected
    $('#colorPalette').change(function() {
        if ($(this).val() == 'custom') {
            $('#customColorInput').show();
        } else {
            $('#customColorInput').hide();
        }
    });

    $('#generateButton').click(function(){
        var selectedDistrict = $('#districtSelect').val();
        var numClasses = $('#numClasses').val();
        var colorPalette = $('#colorPalette').val();

        if (colorPalette === 'custom') {
            colorPalette = $('#customColor').val();
        }

        $('#loading').show();
        $('#mapResult').empty();
        $('#data-container').empty();

        $.post('/generate_map', {
            district_code: selectedDistrict,
            num_classes: numClasses,
            color_palette_name: colorPalette
        }, function(data){
            checkMapStatus(selectedDistrict, numClasses, colorPalette);
        });
    });
});

function showError(message) {
    $('#error-message').text(message).show();
}

function checkMapStatus(district_code, num_classes, color_palette_name) {
    $.get('/map_status', {district_code: district_code, num_classes: num_classes, color_palette_name: color_palette_name}, function(data) {
        if (data.status === 'Completed') {
            $('#mapResult').html('<img src="/maps/' + district_code + '/'+num_classes+'/'+color_palette_name+'" alt="Generated Map" class="img-fluid">');
            $('#loading').hide();
            fetchData(district_code);
        } else if (data.status.includes('Error')) {
            $('#loading').hide();
            showError('Error in map generation: ' + data.status);
        } else {
            setTimeout(function() { checkMapStatus(district_code, num_classes, color_palette_name); }, 2000);
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
