// gear-slider.js requires jQuery UI slider
// Make sure https://code.jquery.com/ui/1.13.2/jquery-ui.min.js is loaded before this file
$(function() {
  // Check if jQuery UI slider is available
  if (typeof $.fn.slider === 'undefined') {
    console.error('gear-slider.js: jQuery UI slider is required. Please load https://code.jquery.com/ui/1.13.2/jquery-ui.min.js before this file.');
    return;
  }

  const $slider = $('#slider-range');
  if ($slider.length === 0) {
    return; // Slider element not found
  }

  const min = parseInt($slider.data('min')) || 0;
  const max = parseInt($slider.data('max')) || 100;
  const step = parseInt($slider.data('step')) || 1;
  
  // Parse values từ string "2015, 2025" hoặc array
  var valuesData = $slider.data('values');
  var values;
  if (typeof valuesData === 'string') {
    values = valuesData.split(',').map(function(v) {
      return parseInt(v.trim());
    });
  } else if (Array.isArray(valuesData)) {
    values = valuesData;
  } else {
    values = [min, max];
  }

  // Initiate Slider
  $slider.slider({
    range: true,
    min: min,
    max: max,
    step: step,
    values: values
  });
  
  // Update label với giá trị ban đầu
  var updateYearLabel = function(vals) {
    $('#yearMin').text(vals[0]);
    $('#yearMax').text(vals[1]);
  };
  
  // Apply initial values
  updateYearLabel($slider.slider("values"));

  // Slide event
  $slider.on('slide', function(event, ui) {
    updateYearLabel(ui.values);
  });
});