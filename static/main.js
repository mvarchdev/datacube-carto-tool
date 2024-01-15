$(document).ready(function(){
    $('#colorPalette').change(function() {
        if ($(this).val() === 'custom') {
            $('#customColorInput').show();
        } else {
            $('#customColorInput').hide();
        }
    });

    $('#generateButton').click(function(){
        var districtCode = $('#districtSelect').val();
        var numClasses = $('#numClasses').val();
        var colorPalette = $('#colorPalette').val();

        if (colorPalette === 'custom') {
            colorPalette = $('#customColor').val();
        }

        $('#loading').show();
        $('#mapResult').empty();
        $('#data-container').empty();
        $('#error-message').empty();

        $.post('/generate_map', {
            district_code: districtCode,
            num_classes: numClasses,
            color_palette_name: colorPalette
        }, function(response){
            if (response.status === 'Accepted') {
                checkMapStatus(districtCode, numClasses, colorPalette);
            } else {
                showError(response.message);
                $('#loading').hide();
            }
        }).fail(function(){
            showError('Failed to initiate map generation.');
            $('#loading').hide();
        });
    });
});

function showError(message) {
    $('#error-message').text(message).show();
}

function checkMapStatus(districtCode, numClasses, colorPalette) {
    $.get('/map_status', {district_code: districtCode, num_classes: numClasses, color_palette_name: colorPalette}, function(data) {
        if (data.status === 'Completed') {
            $('#mapResult').html('<img src="/maps/' + districtCode + '/' + numClasses + '/' + colorPalette + '" alt="Generated Map" class="img-fluid">');
            $('#loading').hide();
            fetchData(districtCode);
        } else if (data.status.includes('Error')) {
            $('#loading').hide();
            showError('Error in map generation: ' + data.status);
        } else {
            setTimeout(function() { checkMapStatus(districtCode, numClasses, colorPalette); }, 2000);
        }
    }).fail(function() {
        $('#loading').hide();
        showError('Error checking map status.');
    });
}

function fetchData(districtCode) {
    $.get('/get_data', {district_code: districtCode}, function(response) {
        if (response.status === 'Success') {
            populateTable(response.table);
        } else {
            showError(response.message);
        }
    }).fail(function() {
        showError('Error fetching land data.');
    });
}

function populateTable(tableHtml) {
    $('#data-container').html(tableHtml);
    $('#data-container table').addClass('table table-bordered table-hover');
}
