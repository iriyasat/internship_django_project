var activeFilters = {};
var $filterResults = $('#filterResults');
var $filterTags = $('#filterTags'); 
var $filterDivider = $('#filterDivider');
var $btnClearAll = $('#btnClearAll');
var show = $filterResults.data('show');
var updateFilterResultsTimeout = null;

    // Filter tag HTML
    function createFilterTag(uniqueKey, filterValue, filterType, checkboxValue, isActive) {
        var activeClass = isActive ? 'active' : '';
        var iconSrc = isActive ? './assets/icons/plug.svg' : './assets/icons/X.svg';
        var iconAlt = isActive ? 'plug' : 'X';
        var hoverIconSrc = isActive ? './assets/icons/plug.svg' : './assets/icons/minus.svg';
        return '<p class="select-item ' + activeClass + '" data-filter-key="' + uniqueKey + '" data-filter-type="' + filterType + '" data-checkbox-value="' + checkboxValue + '" data-icon-src="' + iconSrc + '" data-hover-icon-src="' + hoverIconSrc + '">' +
               filterValue +
               '<img src="' + iconSrc + '" alt="' + iconAlt + '" class="filter-icon">' +
               '</p>';
    }

    // Update filter results (debounced to avoid multiple calls)
    function updateFilterResults() {
        // Clear existing timeout to prevent duplicate calls
        if (updateFilterResultsTimeout) {
            clearTimeout(updateFilterResultsTimeout);
        }
        
        // Debounce the update - wait 50ms before executing
        updateFilterResultsTimeout = setTimeout(function() {
            var filterCount = Object.keys(activeFilters).length;

            // Expose activeFilters cho các trang khác (ví dụ shop.js)
            window.shopActiveFilters = activeFilters;
            if (typeof $ !== 'undefined' && typeof $(document).trigger === 'function') {
                // Gửi bản copy để tránh bị sửa trực tiếp từ ngoài
                $(document).trigger('shopFiltersUpdated', [$.extend(true, {}, activeFilters)]);
            }

            $filterResults.removeClass('hidden');
            if (filterCount === 0) {
                $filterResults.hide();
                return;
            }
            
            if(show != false) {
                $filterResults.show();
            } else {
                $filterResults.hide();
                show = true;
            }

            $filterResults.removeAttr('data-show');

            $filterResults.removeAttr('style');
            $filterTags.empty();

            // Default: "No accidents", "Great Price"
            var noAccidentsFilter = null;
            var greatPriceFilter = null;
            var otherFilters = [];
            
            for (var key in activeFilters) {
                if (activeFilters.hasOwnProperty(key)) {
                    var filterData = activeFilters[key];
                    if (filterData.type === 'no-accidents') {
                        noAccidentsFilter = {key: key, data: filterData};
                    } else if (filterData.type === 'great-price') {
                        greatPriceFilter = {key: key, data: filterData};
                    } else {
                        otherFilters.push({key: key, data: filterData});
                    }
                }
            }
            
            // No accidents
            if (noAccidentsFilter) {
                var tag1 = createFilterTag(noAccidentsFilter.key, noAccidentsFilter.data.value, noAccidentsFilter.data.type, noAccidentsFilter.data.checkboxValue, false);
                $filterTags.append(tag1);
            }
            
            // Great Price
            if (greatPriceFilter) {
                var tag2 = createFilterTag(greatPriceFilter.key, greatPriceFilter.data.value, greatPriceFilter.data.type, greatPriceFilter.data.checkboxValue, true);
                $filterTags.append(tag2);
            }
            
            // filters default options
            otherFilters.forEach(function(item) {
                var isActive = item.data.isActive || false;
                var tag = createFilterTag(item.key, item.data.value, item.data.type, item.data.checkboxValue, isActive);
                $filterTags.append(tag);
            });

            // btnClearAll
            if (filterCount > 0) {
                $filterDivider.show();
                $btnClearAll.show();
            }
            
            // Apply filters to car listings after updating tags
            // Always call applyCarFilters - it will handle showing all items if no filters are selected
            if (typeof applyCarFilters === 'function') {
                applyCarFilters();
            }
        }, 50); // Debounce 50ms
    }

    // Add filter - unique key for each filter tag
    function addFilter(filterType, value, checkboxValue, isActive) {
        if (!value || value === 'undefined' || value === 'null' || value.trim() === '') {
            return;
        }
        
        // create unique key: filterType-checkboxValue ( filterType-all if checkboxValue "all")
        var keyValue = checkboxValue || value;
        var uniqueKey = filterType + '-' + keyValue.replace(/\s+/g, '-').toLowerCase();
        activeFilters[uniqueKey] = {
            type: filterType,
            value: value, 
            checkboxValue: checkboxValue || value,
            isActive: isActive || false 
        };
        updateFilterResults();
    }

    // Xóa filter
    function removeFilter(uniqueKey) {
        delete activeFilters[uniqueKey];
        updateFilterResults();
    }
    
    // Remove filter for type and value
    function removeFilterByTypeAndValue(filterType, checkboxValue) {
        for (var key in activeFilters) {
            if (activeFilters.hasOwnProperty(key)) {
                var filterData = activeFilters[key];
                if (filterData.type === filterType && filterData.checkboxValue === checkboxValue) {
                    delete activeFilters[key];
                    break;
                }
            }
        }
        updateFilterResults();
    }

    // Remove all filters
    function clearAllFilters() {
        activeFilters = {};
        updateFilterResults();
        
        // Uncheck all and reset "all"
        $('#filterSidebar input[type="checkbox"]').not('[value="all"]').not('[value="ALL Brand"]').prop('checked', false);
        $('#filterSidebar input[type="checkbox"][value="all"], #filterSidebar input[type="checkbox"][value="ALL Brand"]').prop('checked', true);
        
        // Reset radio buttons default value
        $('#filterSidebar input[type="radio"]').each(function() {
            if ($(this).is(':checked') && $(this).index() > 0) {
                $(this).closest('ul, div').find('input[type="radio"]').first().prop('checked', true);
            }
        });
        
        // Reset price range slider về giá trị mặc định
        var $slider = $('#slider-range');
        if ($slider.length > 0) {
            var defaultMin = parseInt($slider.data('min')) || 120;
            var defaultMax = parseInt($slider.data('max')) || 750;
            $slider.slider('values', [defaultMin, defaultMax]);
            $('#yearMin').text(defaultMin);
            $('#yearMax').text(defaultMax);
        }
    }

    function initializeCheckedFilters() {
        // Find filter container - check both #filterSidebar and .filter-sidebar-desktop
        var $filterContainer = $('#filterSidebar, .filter-sidebar-desktop').first();
        if (!$filterContainer.length) {
            $filterContainer = $('body'); // Fallback
        }
        $filterContainer.find('.filter-select-dropdown').each(function() {
            var $dropdown = $(this);
            var $allCheckbox = $dropdown.find('input[value="all"]:checked');
            
            if ($allCheckbox.length > 0 && $allCheckbox.is(':checked')) {
                var checkboxName = $allCheckbox.attr('name');
                var filterType = getFilterTypeFromName(checkboxName);
                
                if (filterType && show != false) {
                    var allLabel = formatAllLabel(filterType);
                    addFilter(filterType, allLabel, 'all');
                }
                return; 
            }
            
            $dropdown.find('input[type="checkbox"]:checked').not('[value="all"]').not('[value="ALL Brand"]').each(function() {
                var $checkbox = $(this);
                var checkboxName = $checkbox.attr('name');
                var checkboxValue = $checkbox.val() || '';
                // Lấy text từ span, loại bỏ em tag và trim
                var $span = $checkbox.closest('label').find('span');
                var displayText = $span.clone().children('em').remove().end().text().trim();
                
                if (!checkboxName) {
                    return;
                }
                
                // Lấy filter type từ name
                var filterType = getFilterTypeFromName(checkboxName);
                
                if (!filterType) {
                    return;
                }
                
                // Luôn ưu tiên dùng displayText từ span
                var finalValue;
                
                if (displayText && displayText !== '') {
                    // Có text trong span, dùng text đó
                    finalValue = displayText;
                } else if (checkboxValue === 'on' || checkboxValue === '') {
                    // Nếu checkboxValue là "on" (mặc định) hoặc rỗng, bỏ qua
                    return;
                } else {
                    // Dùng checkboxValue
                    finalValue = checkboxValue;
                }
                
                // Đảm bảo finalValue không phải "on"
                if (finalValue === 'on' || finalValue === '') {
                    return;
                }
                
                // Thêm filter vào activeFilters
                addFilter(filterType, finalValue, checkboxValue);
            });
        });

        // Find filter container - check both #filterSidebar and .filter-sidebar-desktop
        var $filterContainer = $('#filterSidebar, .filter-sidebar-desktop').first();
        if (!$filterContainer.length) {
            $filterContainer = $('body'); // Fallback
        }
        
        // Collect từ radio buttons (color, payment)
        $filterContainer.find('input[type="radio"]:checked').each(function() {
            var $radio = $(this);
            var filterValue = $radio.val();
            var radioName = $radio.attr('name');
            var displayText = $radio.closest('label').find('span').text().trim();
            
            if (radioName === 'exteriorColor' && filterValue && filterValue !== 'all') {
                // Format label: "Exterior Black"
                var displayLabel = filterValue;
                addFilter('color', displayLabel, filterValue);
            } else if (radioName === 'interiorColor' && filterValue && filterValue !== 'all') {
                // Format label: "Interior White"
                var displayLabel = 'Interior ' + filterValue;
                addFilter('interior-color', displayLabel, filterValue);
            } else if (radioName === 'payment2' && filterValue) {
                // Payment radio button
                var finalValue = displayText || filterValue;
                addFilter('payment', finalValue, filterValue);
            }
        });

        // Collect từ features checkboxes
        $filterContainer.find('.filter-features input[type="checkbox"]:checked').each(function() {
            var $checkbox = $(this);
            var checkboxValue = $checkbox.val();
            var filterType = $checkbox.attr('name');
            
            if (filterType && checkboxValue && show != false) {
                addFilter(filterType.toLowerCase(), checkboxValue, checkboxValue);
            }
        });
    }

    // Lắng nghe change từ checkbox trong select dropdowns
    $(document).on('change', '#filterSidebar .filter-select-dropdown input[type="checkbox"], .filter-sidebar-desktop .filter-select-dropdown input[type="checkbox"]', function() {
        var $checkbox = $(this);
        var checkboxName = $checkbox.attr('name');
        var checkboxValue = $checkbox.val() || '';
        // Lấy text từ span, loại bỏ em tag và trim
        var $span = $checkbox.closest('label').find('span');
        var displayText = $span.clone().children('em').remove().end().text().trim();
        
        // Đảm bảo có name và value
        if (!checkboxName || !checkboxValue || checkboxValue === 'undefined' || checkboxValue === 'null') {
            return;
        }
        
        // Lấy filter type từ name attribute
        var filterType = getFilterTypeFromName(checkboxName);
        
        if (!filterType) {
            return;
        }
        
        // Nếu value="all" được checked, hiển thị "ALL [field name]" trong filter tags
        if (checkboxValue === 'all') {
            if ($checkbox.is(':checked')) {
                // Xóa tất cả filters có type này trước
                for (var key in activeFilters) {
                    if (activeFilters.hasOwnProperty(key) && activeFilters[key].type === filterType) {
                        delete activeFilters[key];
                    }
                }
                // Thêm filter "ALL [field name]" (chữ hoa cho Brand và Model)
                var allLabel = formatAllLabel(filterType);
                addFilter(filterType, allLabel, 'all');
            } else {
                // Uncheck "all", xóa filter "ALL [field name]"
                removeFilterByTypeAndValue(filterType, 'all');
            }
            // Apply filters after updating tags
            setTimeout(function() {
                if (typeof applyCarFilters === 'function') {
                    applyCarFilters();
                }
            }, 50);
            return;
        }

        if (checkboxValue && checkboxValue.trim() !== '') {
            // Nếu "all" đang được checked, bỏ check nó trước khi thêm filter cụ thể
            var $allCheckbox = $checkbox.closest('.filter-select-dropdown').find('input[value="all"]');
            if ($allCheckbox.is(':checked')) {
                $allCheckbox.prop('checked', false);
                // Xóa filter "all [field name]"
                removeFilterByTypeAndValue(filterType, 'all');
            }
            
            // Luôn ưu tiên dùng displayText từ span
            var finalValue;
            
            if (displayText && displayText !== '') {
                // Có text trong span, dùng text đó
                finalValue = displayText;
            } else if (checkboxValue === 'on' || checkboxValue === '') {
                // Nếu checkboxValue là "on" (mặc định) hoặc rỗng, bỏ qua
                return;
            } else {
                // Dùng checkboxValue
                finalValue = checkboxValue;
            }
            
            // Đảm bảo finalValue không phải "on"
            if (finalValue === 'on' || finalValue === '') {
                return;
            }
            
            if ($checkbox.is(':checked')) {
                addFilter(filterType, finalValue, checkboxValue);
            } else {
                removeFilterByTypeAndValue(filterType, checkboxValue);
            }
        }
    });


    // Helper function để lấy filter type từ toggle ID (fallback)
    function getFilterType(toggleId) {
        var filterTypeMap = {
            'BrandSelectToggle': 'brand',
            'modelSelectToggle': 'model',
            'BodyStyleSelectToggle': 'body-style',
            'FuelStyleSelectToggle': 'fuel-type',
            'TransmissionSelectToggle': 'transmission',
            'DriveTypeSelectToggle': 'door-count',
            'CylindersSelectToggle': 'cylinders'
        };
        return filterTypeMap[toggleId] || '';
    }

    // Lắng nghe change từ radio buttons (color, payment)
    $(document).on('change', '#filterSidebar input[type="radio"], .filter-sidebar-desktop input[type="radio"]', function() {
        var $radio = $(this);
        var filterValue = $radio.val();
        var radioName = $radio.attr('name');
        var displayText = $radio.closest('label').find('span').text().trim();
        
        if (radioName === 'exteriorColor' || radioName === 'interiorColor') {
            var filterType = radioName === 'exteriorColor' ? 'color' : 'interior-color';
            
            // Xóa filter cũ trước
            for (var key in activeFilters) {
                if (activeFilters.hasOwnProperty(key) && activeFilters[key].type === filterType) {
                    delete activeFilters[key];
                }
            }
            
            if (filterValue && filterValue !== 'all') {
                // Format label: "Exterior Black", "Interior White"
                var labelPrefix = radioName === 'exteriorColor' ? 'Exterior' : 'Interior';
                var displayLabel = labelPrefix + ' ' + filterValue;
                addFilter(filterType, displayLabel, filterValue);
            }
            updateFilterResults();
        }
        // Xử lý payment2 radio buttons
        else if (radioName === 'payment2') {
            var filterType = 'payment';
            
            // Xóa filter cũ trước
            for (var key in activeFilters) {
                if (activeFilters.hasOwnProperty(key) && activeFilters[key].type === filterType) {
                    delete activeFilters[key];
                }
            }
            
            if (filterValue && $radio.is(':checked')) {
                // Sử dụng displayText từ span hoặc filterValue
                var finalValue = displayText || filterValue;
                addFilter(filterType, finalValue, filterValue);
            }
            updateFilterResults();
        }
        
        // Apply filters after updating tags
        setTimeout(function() {
            if (typeof applyCarFilters === 'function') {
                applyCarFilters();
            }
        }, 50);
    });

    // Lắng nghe change từ features checkboxes
    $(document).on('change', '#filterSidebar .filter-features input[type="checkbox"], .filter-sidebar-desktop .filter-features input[type="checkbox"]', function() {
        var $checkbox = $(this);
        var checkboxValue = $checkbox.val();
        var filterType = $checkbox.attr('name');
        
        // Lấy text từ span, loại bỏ em tag và trim
        var $span = $checkbox.closest('label').find('span');
        var displayText = $span.clone().children('em').remove().end().text().trim();
        
        if (filterType && checkboxValue) {
            filterType = getFilterTypeFromName(filterType.toLowerCase());
            
            if (!filterType) {
                return;
            }
            
            // Sử dụng displayText nếu có, nếu không dùng checkboxValue
            var finalValue = displayText && displayText !== '' ? displayText : checkboxValue;
            
            if ($checkbox.is(':checked')) {
                addFilter(filterType, finalValue, checkboxValue);
            } else {
                removeFilterByTypeAndValue(filterType, checkboxValue);
            }
            
            // Apply filters after updating tags
            setTimeout(function() {
                if (typeof applyCarFilters === 'function') {
                    applyCarFilters();
                }
            }, 50);
        }
    });



    // Xóa filter khi click vào filter tag
    $(document).on('click', '.select-item', function(e) {
        e.preventDefault();
        var $tag = $(this);
        var filterKey = $tag.data('filter-key');
        var filterType = $tag.data('filter-type');
        var checkboxValue = $tag.data('checkbox-value');
        
        if (filterKey) {
            removeFilter(filterKey);
            
            // Uncheck checkbox/radio tương ứng trong sidebar
            // Find filter container - check both #filterSidebar and .filter-sidebar-desktop
            var $filterContainer = $('#filterSidebar, .filter-sidebar-desktop').first();
            if (!$filterContainer.length) {
                $filterContainer = $('body'); // Fallback
            }
            
            // Tìm dropdown chứa checkbox có name = filterType
            if (filterType === 'color') {
                $filterContainer.find('input[name="exteriorColor"][value="' + checkboxValue + '"]').prop('checked', false);
                $filterContainer.find('input[name="exteriorColor"]').first().prop('checked', true);
            } else if (filterType === 'interior-color') {
                $filterContainer.find('input[name="interiorColor"][value="' + checkboxValue + '"]').prop('checked', false);
                $filterContainer.find('input[name="interiorColor"]').first().prop('checked', true);
            } else if (filterType === 'payment') {
                // Uncheck payment radio button
                $filterContainer.find('input[name="payment2"][value="' + checkboxValue + '"]').prop('checked', false);
            } else if (filterType === 'price') {
                // Reset price range slider về giá trị mặc định
                var $slider = $('#slider-range');
                if ($slider.length > 0) {
                    var defaultMin = parseInt($slider.data('min')) || 120;
                    var defaultMax = parseInt($slider.data('max')) || 750;
                    $slider.slider('values', [defaultMin, defaultMax]);
                    $('#yearMin').text(defaultMin);
                    $('#yearMax').text(defaultMax);
                }
            } else {
                // Tìm checkbox trong dropdown có name = filterType
                // Find filter container - check both #filterSidebar and .filter-sidebar-desktop
                var $filterContainer = $('#filterSidebar, .filter-sidebar-desktop').first();
                if (!$filterContainer.length) {
                    $filterContainer = $('body'); // Fallback
                }
                var $checkbox = $filterContainer.find('input[name="' + filterType + '"][value="' + checkboxValue + '"]');
                if ($checkbox.length) {
                    $checkbox.prop('checked', false);
                    
                    // Nếu không còn checkbox nào được chọn trong dropdown này, chọn "all"
                    var $dropdown = $checkbox.closest('.filter-select-dropdown');
                    var otherChecked = $dropdown.find('input[type="checkbox"]:checked').not('[value="all"]').not('[value="All Brand"]');
                    if (otherChecked.length === 0) {
                        var $allOption = $dropdown.find('input[value="all"], input[value="All Brand"]').first();
                        if ($allOption.length) {
                            $allOption.prop('checked', true);
                            // Trigger change event để hiển thị "ALL [field name]"
                            $allOption.trigger('change');
                        }
                    }
                }
            }
            
            // Apply filters after removing filter tag
            setTimeout(function() {
                if (typeof applyCarFilters === 'function') {
                    applyCarFilters();
                }
            }, 50);
        }
    });

    // Xóa tất cả filters
    $(document).on('click', '#btnClearAll', function() {
        clearAllFilters();
        // Apply filters after clearing all
        setTimeout(function() {
            if (typeof applyCarFilters === 'function') {
                applyCarFilters();
            }
        }, 100);
    });
    
    // Lắng nghe thay đổi từ price range slider
    $(document).on('slidechange', '#slider-range', function(event, ui) {
        var minPrice = ui.values[0];
        var maxPrice = ui.values[1];
        var defaultMin = parseInt($(this).data('min')) || 120;
        var defaultMax = parseInt($(this).data('max')) || 750;
        
        // Xóa filter price cũ nếu có
        removeFilterByTypeAndValue('price', 'price-range');
        
        // Nếu giá trị khác với giá trị mặc định, thêm filter tag
        if (minPrice !== defaultMin || maxPrice !== defaultMax) {
            var priceLabel = 'Price: $' + minPrice + ' - $' + maxPrice;
            addFilter('price', priceLabel, 'price-range');
        }
        
        // Apply filters after updating tags
        setTimeout(function() {
            if (typeof applyCarFilters === 'function') {
                applyCarFilters();
            }
        }, 50);
    });
    
    // Cũng lắng nghe slide event để cập nhật real-time
    $(document).on('slide', '#slider-range', function(event, ui) {
        var minPrice = ui.values[0];
        var maxPrice = ui.values[1];
        var defaultMin = parseInt($(this).data('min')) || 120;
        var defaultMax = parseInt($(this).data('max')) || 750;
        
        // Xóa filter price cũ nếu có
        removeFilterByTypeAndValue('price', 'price-range');
        
        // Nếu giá trị khác với giá trị mặc định, thêm filter tag
        if (minPrice !== defaultMin || maxPrice !== defaultMax) {
            var priceLabel = 'Price: $' + minPrice + ' - $' + maxPrice;
            addFilter('price', priceLabel, 'price-range');
        }
        
        // Apply filters after updating tags
        setTimeout(function() {
            if (typeof applyCarFilters === 'function') {
                applyCarFilters();
            }
        }, 50);
    });

    // Khởi tạo: collect và hiển thị các filters đã checked
    initializeCheckedFilters();
    
    // Khởi tạo price range filter nếu giá trị khác mặc định
    setTimeout(function() {
        var $slider = $('#slider-range');
        if ($slider.length > 0 && typeof $slider.slider === 'function') {
            try {
                var currentValues = $slider.slider('values');
                var defaultMin = parseInt($slider.data('min')) || 120;
                var defaultMax = parseInt($slider.data('max')) || 750;
                
                if (currentValues && (currentValues[0] !== defaultMin || currentValues[1] !== defaultMax)) {
                    var minPrice = currentValues[0];
                    var maxPrice = currentValues[1];
                    var priceLabel = 'Price: $' + minPrice + ' - $' + maxPrice;
                    addFilter('price', priceLabel, 'price-range');
                }
            } catch (e) {
                // Slider not initialized yet, skip
                console.log('Timeout: $e');
            }
        }
    }, 100); // Delay để đảm bảo slider đã được khởi tạo
    
    // Thêm 2 filter tags mặc định: "No accidents" và "Great Price"
    if(show != false) {
        addFilter('no-accidents', 'No accidents', 'no-accidents', false);
        addFilter('great-price', 'Great Price', 'great-price', true);
    }
    
    // Initial filter application on page load
    // Ensure all items are visible by default, then apply filters if needed
    $(document).ready(function() {
        // First, ensure all items are visible (all card-box variants)
        var $allCards = $('.card-box');
        $allCards.show().css('display', '');
        
        // Update match count
        var $matchCount = $('#filterMatchesCount');
        if ($matchCount.length) {
            $matchCount.text($allCards.length + ' ');
        }
        
        // Show pagination
        var $pagination = $('.pagination');
        if ($pagination.length && $allCards.length > 0) {
            $pagination.show();
        }
        
        // Then check if there are any filters selected and apply them
        setTimeout(function() {
            var hasRealFilters = false;
            // Find filter container - check both #filterSidebar and .filter-sidebar-desktop
            var $filterContainer = $('#filterSidebar, .filter-sidebar-desktop').first();
            
            if ($filterContainer.length) {
                var hasBrandFilter = $filterContainer.find('input[name="brand"]:checked, input[name="Brand"]:checked').not('[value="all"]').length > 0;
                var hasModelFilter = $filterContainer.find('input[name="model"]:checked').not('[value="all"]').length > 0;
                var hasFuelFilter = $filterContainer.find('input[name="FuelType"]:checked').not('[value="all"]').length > 0;
                var hasTransFilter = $filterContainer.find('input[name="Transmission"]:checked').not('[value="all"]').length > 0;
                
                var $slider = $('#slider-range');
                var priceFiltered = false;
                if ($slider.length) {
                    try {
                        if (typeof $slider.slider === 'function') {
                            var vals = $slider.slider('values');
                            var defaultMin = parseInt($slider.data('min'), 10) || 120;
                            var defaultMax = parseInt($slider.data('max'), 10) || 750;
                            if (vals && vals.length >= 2) {
                                priceFiltered = (vals[0] !== defaultMin || vals[1] !== defaultMax);
                            }
                        }
                    } catch (e) {
                        var $yearMin = $('#yearMin');
                        var $yearMax = $('#yearMax');
                        if ($yearMin.length && $yearMax.length) {
                            var currentMin = parseInt($yearMin.text(), 10);
                            var currentMax = parseInt($yearMax.text(), 10);
                            var defaultMin = parseInt($slider.data('min'), 10) || 120;
                            var defaultMax = parseInt($slider.data('max'), 10) || 750;
                            priceFiltered = (currentMin !== defaultMin || currentMax !== defaultMax);
                        }
                    }
                }
                
                hasRealFilters = hasBrandFilter || hasModelFilter || hasFuelFilter || hasTransFilter || priceFiltered;
            }
            
            // Only apply filters if there are real filter selections
            if (hasRealFilters && typeof applyCarFilters === 'function') {
                applyCarFilters();
            }
        }, 300);
    });
    
    // Thêm hover effect cho filter tags: đổi icon X thành dấu "-" khi hover
    $(document).on('mouseenter', '.select-item:not(.active)', function() {
        var $item = $(this);
        var $icon = $item.find('.filter-icon');
        var hoverIconSrc = $item.data('hover-icon-src');
        if (hoverIconSrc && hoverIconSrc.includes('minus')) {
            $icon.attr('src', hoverIconSrc);
        }
    });
    
    $(document).on('mouseleave', '.select-item:not(.active)', function() {
        var $item = $(this);
        var $icon = $item.find('.filter-icon');
        var iconSrc = $item.data('icon-src');
        if (iconSrc) {
            $icon.attr('src', iconSrc);
        }
    });

// getFilterTypeFromName
function getFilterTypeFromName(name) {
    if (!name) return '';
    
    var nameToTypeMap = {
        'brand': 'brand',
        'model': 'model',
        'bodystyle': 'bodystyle',
        'FuelType': 'FuelType',
        'Transmission': 'Transmission',
        'Doorcount': 'Doorcount',
        'Cylinders': 'Cylinders',
        'body-style': 'body-style',
        'fuel-type': 'fuel-type',
        'transmission': 'transmission',
        'door-count': 'door-count',
        'cylinders': 'cylinders',
        'category': 'category',
        'branding': 'branding'
    };
    
    if (nameToTypeMap[name]) {
        return nameToTypeMap[name];
    }
    
    return name;
}


function formatAllLabel(filterType) {
    if (!filterType) return '';
    
    var typeToLabelMap = {
        'brand': 'All Brand',
        'model': 'All Model',
        'bodystyle': 'All Body Style',
        'FuelType': 'All Fuel Type',
        'Transmission': 'All Transmission',
        'Doorcount': 'All Door Count',
        'Cylinders': 'All Cylinders',
        'body-style': 'all body style',
        'fuel-type': 'all fuel type',
        'transmission': 'all transmission',
        'door-count': 'all door count',
        'cylinders': 'all cylinders',
        'category': 'All Categories',
        'branding': 'All Branding',
        'features': 'All Features'
    };
    
    if (typeToLabelMap[filterType]) {
        return typeToLabelMap[filterType];
    }
    
    // Fallback: capitalize first letter và replace dashes
    var words = filterType.replace(/-/g, ' ').split(' ');
    var formatted = words.map(function(word) {
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    }).join(' ');
    return 'All ' + formatted;
}

// Helper: Extract car data from a .card-box element
function getCarDataFromCard($card) {
    var brand = $card.find('.category a').first().text().trim() || '';
    var model = $card.find('.card-box__title a').first().text().trim() || '';
    
    // Extract price (remove $ and commas, handle format like "$44.900,00" or "$44,900")
    var priceText = $card.find('.card-box__price').first().text().trim() || '';
    var priceMatch = priceText.match(/[\d,]+\.?\d*/);
    var price = 0;
    if (priceMatch) {
        price = parseFloat(priceMatch[0].replace(/[,]/g, '').replace(/\./g, '')) || 0;
        // Handle European format: "44.900,00" -> 44900.00
        if (priceText.indexOf(',') > priceText.indexOf('.')) {
            price = parseFloat(priceMatch[0].replace(/\./g, '').replace(',', '.')) || 0;
        }
    }
    
    // Extract year from tag with calendar icon
    var year = '';
    $card.find('.tag li').each(function() {
        var $li = $(this);
        var $img = $li.find('img[src*="calendar"]');
        if ($img.length) {
            year = $li.find('span').text().trim() || '';
        }
    });
    
    // Extract fuel type from tag with gas pump icon
    var fuelType = '';
    $card.find('.tag li').each(function() {
        var $li = $(this);
        var $img = $li.find('img[src*="gaspump"]');
        if ($img.length) {
            fuelType = $li.find('span').text().trim() || '';
        }
    });
    
    // Extract transmission from tag with manual/auto icon
    var transmission = '';
    $card.find('.tag li').each(function() {
        var $li = $(this);
        var $img = $li.find('img[src*="manual"], img[src*="auto"]');
        if ($img.length) {
            transmission = $li.find('span').text().trim() || '';
        }
    });
    
    // Extract body style from data attribute or other sources (if available)
    var bodyStyle = $card.data('body-style') || $card.data('bodystyle') || '';
    
    // Extract color from data attribute or other sources (if available)
    var color = $card.data('color') || $card.data('exterior-color') || '';
    
    return {
        brand: brand,
        model: model,
        price: price,
        year: year,
        fuelType: fuelType,
        transmission: transmission,
        bodyStyle: bodyStyle,
        color: color
    };
}

// Apply filters to car listings (filter directly on HTML elements)
function applyCarFilters() {
    var $allCards = $('.card-box');
    if (!$allCards.length) {
        return;
    }
    
    // Find filter container - check both #filterSidebar and .filter-sidebar-desktop
    var $filterContainer = $('#filterSidebar, .filter-sidebar-desktop').first();
    if (!$filterContainer.length) {
        $filterContainer = $('body'); // Fallback
    }
    
    // Read filter states from DOM
    var selectedBrands = $filterContainer.find('input[name="brand"]:checked, input[name="Brand"]:checked').not('[value="all"]').map(function() {
        return $(this).val();
    }).get();
    
    var selectedModels = $filterContainer.find('input[name="model"]:checked').not('[value="all"]').map(function() {
        return $(this).val();
    }).get();
    
    var selectedBodyStyles = $filterContainer.find('input[name="bodystyle"]:checked').map(function() {
        return $(this).val();
    }).get();
    
    var selectedFuelTypes = $filterContainer.find('input[name="FuelType"]:checked').not('[value="all"]').map(function() {
        return $(this).val();
    }).get();
    
    var selectedTransmissions = $filterContainer.find('input[name="Transmission"]:checked').not('[value="all"]').map(function() {
        return $(this).val();
    }).get();
    
    // Color filters (exterior and interior)
    var selectedExteriorColor = $filterContainer.find('input[name="exteriorColor"]:checked').not('[value="all"]').map(function() {
        return $(this).val();
    }).get();
    
    var selectedInteriorColor = $filterContainer.find('input[name="interiorColor"]:checked').not('[value="all"]').map(function() {
        return $(this).val();
    }).get();
    
    // Price range - only filter if slider is different from default
    var usePriceFilter = false;
    var minPrice = 0;
    var maxPrice = Infinity;
    var $slider = $('#slider-range');
    if ($slider.length && typeof $slider.slider === 'function') {
        try {
            // Check if slider is initialized by trying to get values
            var vals = $slider.slider('values');
            var defaultMin = parseInt($slider.data('min'), 10) || 120;
            var defaultMax = parseInt($slider.data('max'), 10) || 750;
            
            if (vals && vals.length >= 2) {
                // Only use price filter if different from default
                if (vals[0] !== defaultMin || vals[1] !== defaultMax) {
                    usePriceFilter = true;
                    minPrice = vals[0] * 1000; // Convert from thousands (e.g., 120 -> 120000)
                    maxPrice = vals[1] * 1000;
                }
            }
        } catch (e) {
            // Slider not initialized yet, try to get values from display elements or data attributes
            var $yearMin = $('#yearMin');
            var $yearMax = $('#yearMax');
            if ($yearMin.length && $yearMax.length) {
                var currentMin = parseInt($yearMin.text(), 10);
                var currentMax = parseInt($yearMax.text(), 10);
                var defaultMin = parseInt($slider.data('min'), 10) || 120;
                var defaultMax = parseInt($slider.data('max'), 10) || 750;
                
                // Only use price filter if different from default
                if (currentMin !== defaultMin || currentMax !== defaultMax) {
                    usePriceFilter = true;
                    minPrice = currentMin * 1000;
                    maxPrice = currentMax * 1000;
                }
            }
        }
    }
    
    var visibleCount = 0;
    
    // Filter each card
    $allCards.each(function() {
        var $card = $(this);
        var carData = getCarDataFromCard($card);
        var shouldShow = true;
        
     
        // Brand filter
        if (selectedBrands.length > 0) {
            var brandMatch = selectedBrands.some(function(brand) {
                var brandLower = brand ? brand.toLowerCase() : '';
                var carBrandLower = carData.brand ? carData.brand.toLowerCase() : '';
                var match = carBrandLower.indexOf(brandLower) !== -1 ||
                       brandLower.indexOf(carBrandLower) !== -1 ||
                       carBrandLower === brandLower;
                 
                return match;
            });
            if (!brandMatch) {
                shouldShow = false;
            }
        }
        
        // Model filter
        if (shouldShow && selectedModels.length > 0) {
            var modelMatch = selectedModels.some(function(model) {
                var modelLower = model ? model.toLowerCase() : '';
                var carModelLower = carData.model ? carData.model.toLowerCase() : '';
                return carModelLower.indexOf(modelLower) !== -1 ||
                       modelLower.indexOf(carModelLower) !== -1 ||
                       carModelLower === modelLower;
            });
            if (!modelMatch) {
                shouldShow = false;
            }
        }
        
        // Fuel type filter
        if (shouldShow && selectedFuelTypes.length > 0) {
            var fuelMatch = selectedFuelTypes.some(function(fuel) {
                var fuelLower = fuel ? fuel.toLowerCase() : '';
                var carFuelLower = carData.fuelType ? carData.fuelType.toLowerCase() : '';
                return carFuelLower.indexOf(fuelLower) !== -1 ||
                       fuelLower.indexOf(carFuelLower) !== -1 ||
                       carFuelLower === fuelLower;
            });
            if (!fuelMatch) {
                shouldShow = false;
            }
        }
        
        // Transmission filter
        if (shouldShow && selectedTransmissions.length > 0) {
            var transMatch = selectedTransmissions.some(function(trans) {
                var transLower = trans ? trans.toLowerCase() : '';
                var carTransLower = carData.transmission ? carData.transmission.toLowerCase() : '';
                return carTransLower.indexOf(transLower) !== -1 ||
                       transLower.indexOf(carTransLower) !== -1 ||
                       carTransLower === transLower;
            });
            if (!transMatch) {
                shouldShow = false;
            }
        }
        
        // Body style filter
        // Note: Body style information may not be available in card HTML, so this filter may not work
        // unless cards have data-body-style or data-bodystyle attributes
        if (shouldShow && selectedBodyStyles.length > 0) {
            // If card doesn't have body style data, skip body style filter (show all)
            if (!carData.bodyStyle || carData.bodyStyle === '') {
                // No body style data available, don't filter by body style
            } else {
                var bodyMatch = selectedBodyStyles.some(function(body) {
                    var bodyLower = body ? body.toLowerCase() : '';
                    var carBodyLower = carData.bodyStyle ? carData.bodyStyle.toLowerCase() : '';
                    return carBodyLower.indexOf(bodyLower) !== -1 ||
                           bodyLower.indexOf(carBodyLower) !== -1 ||
                           carBodyLower === bodyLower;
                });
                if (!bodyMatch) {
                    shouldShow = false;
                }
            }
        }
        
        // Exterior color filter
        // Note: Color information may not be available in card HTML, so this filter may not work
        // unless cards have data-color or data-exterior-color attributes
        if (shouldShow && selectedExteriorColor.length > 0) {
            // If card doesn't have color data, skip color filter (show all)
            if (!carData.color || carData.color === '') {
                // No color data available, don't filter by color
            } else {
                var colorMatch = selectedExteriorColor.some(function(color) {
                    var colorLower = color ? color.toLowerCase() : '';
                    var carColorLower = carData.color ? carData.color.toLowerCase() : '';
                    return carColorLower.indexOf(colorLower) !== -1 ||
                           colorLower.indexOf(carColorLower) !== -1 ||
                           carColorLower === colorLower;
                });
                if (!colorMatch) {
                    shouldShow = false;
                }
            }
        }
        
        // Price filter - only apply if price filter is active
        if (shouldShow && usePriceFilter && carData.price > 0) {
            if (carData.price < minPrice || carData.price > maxPrice) {
                shouldShow = false;
            }
        }
        
        // Show/hide card
        if (shouldShow) {
            $card.show().css('display', '');
            visibleCount++;
        } else {
            $card.hide();
        }
    });
    
    // Update match count
    var $matchCount = $('#filterMatchesCount');
    if ($matchCount.length) {
        $matchCount.text(visibleCount + ' ');
    }
    
    // Show/hide pagination based on visible count
    var $pagination = $('.pagination');
    if ($pagination.length) {
        if (visibleCount === 0) {
            $pagination.hide();
        } else {
            $pagination.show();
        }
    }
}