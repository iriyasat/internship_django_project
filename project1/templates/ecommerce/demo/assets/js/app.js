/**
  * Header Fixed
  * Mobile Navigation
  * Filter Toggle
  * Filter Sidebar Toggle
  * Color Dropdown
  * Select Dropdown
  * Dropdown
  * Parallax
  * Flat Counter
  * Go Top
  * Modal Popup
  * Preloader
  * Rating Input
  * Accordion
  * Get Filter Type From Name
  * Format "All [field name]" Label
  * Password Input 
  * Collapse
  * Car Views Chart
  * Search Modal Toggle
  * Hover Active Gallery
  * Scroll Element
  * Select Options
  * Check Position
  * Scroll Sidebar
  * Newsletter Modal
  * Compare Modal
  * Heart List

*/

(function ($) {
    "use strict";

    var header = document.querySelector('.header');

    /* Header Fixed
    ----------------------------------------------------------------------------*/
    var headerFixed = function () {
        if(!header) return;

        const headerHeight = header.offsetHeight; 

        if (header) {
            var handleScroll = function () {
                var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                
                if (scrollTop > headerHeight + 600) {
                    header.classList.add('is-fixed','is-custom','is-visible');
                } else if (scrollTop > (headerHeight + 300)) {
                    header.classList.add('is-fixed','is-custom');
                    header.classList.remove('is-visible');
                } else if (scrollTop > (headerHeight + 200)) {
                    header.classList.add('is-fixed');
                    header.classList.remove('is-visible');
                } else {
                    header.classList.remove('is-fixed', 'is-visible', 'is-custom');
                } 
            };parallax
            
            // Check ngay khi tải trang
            handleScroll();
            
            // Listener scroll
            window.addEventListener('scroll', handleScroll);
        }
    };

    /* Mobile Navigation
    ----------------------------------------------------------------------------*/
    var mobileNav = function () {
        var mobile = window.matchMedia("(max-width: 1199px)");
        var headerRight = $(".main-nav-wrapper");
        var logo = $(".logo-mobile")
        var headerButton = $(".header-button-mobile");

        // aoverlay background
        var overlay = $('<div class="mobile-menu-overlay"></div>');
        if ($('.mobile-menu-overlay').length === 0) {
           
        } else {
            overlay = $('.mobile-menu-overlay');
        }
        
        responsivemenu(mobile); 
    
        mobile.addListener(responsivemenu);
    
        function responsivemenu(mobile) {
            
          if (mobile.matches) {
            $("#main-nav")
              .append(logo)
              .append(headerButton)
              .attr("id", "main-nav-mobile")
              .appendTo("#header_main")
              .removeClass("active")
              .children(".menu")
              .find("li:has(ul)")
              .children("ul")
              .removeAttr("style")
              .hide();
            
            // Xóa tất cả inline style display:flex từ sub-menu khi chuyển về mobile
            $("#main-nav-mobile .sub-menu").removeAttr("style");

            if ($("#header_main .mobile-menu-overlay").length === 0) {
              $("#header_main").append(overlay);
            }

            $(document).on('click', '.menu-item-inner-title', function(e) {
                // Chỉ xử lý khi không phải mobile menu
                if ($('#main-nav-mobile').length && $('#main-nav-mobile').hasClass('active')) {
                    return; // Để mobileNav xử lý
                }
                
                e.preventDefault();
                e.stopPropagation();
                
                var $title = $(this);
                var $subMenuItemListing = $title.closest('.sub-menu-item-listing');
                var $subMenuItemInner = $subMenuItemListing.find('.sub-menu-item-inner');
                
                // Dừng animation đang chạy để tránh giật
                $subMenuItemInner.stop(true, false);
                
                // Toggle active class - tương tự như mobileNav xử lý menu-item-inner
                $subMenuItemListing.toggleClass('active');
                
                // Sử dụng slideToggle(300) với easing mượt mà hơn
                if ($subMenuItemInner.length) {
                    $subMenuItemInner.slideToggle(300, 'swing');
                }
            });
        } else {
            headerRight.prepend(
              $("#main-nav-mobile").attr("id", "main-nav").removeAttr("style"));
              headerButton.prependTo(".wrapper-header-button");
              $("#main-nav .menu").removeAttr("style");
              $("#main-nav .menu-item").removeClass("active");
              $("#main-nav .sub-menu").removeAttr("style").css("display", "flex");
              $(".mobile-button").removeClass("active");
              $("body").removeClass("main-nav-mobile");
              overlay.hide().css("opacity", "0"); 
          }
        }
        // Hàm đóng menu
        function closeMobileMenu() {
          $(".mobile-button").removeClass("active");
          $("#main-nav-mobile").removeClass("active");
          $('body').removeClass('main-nav-mobile');
          overlay.css('display', 'none');
        }
        
        $(document).on("click", ".mobile-button", function (a) {

          var isActive = $(this).hasClass("active");
          $(this).toggleClass("active");
          $("#main-nav-mobile").toggleClass("active");
          $('body').toggleClass('main-nav-mobile');
          
          if (!isActive) {
            overlay.css('display', 'block');
            setTimeout(function() {
              overlay.css('opacity', '1');
            }, 10);
          } else {
            overlay.css('opacity', '0');
            setTimeout(function() {
              overlay.css('display', 'none');
            }, 300);
          }

        });
        
        // Click overlay close menu
        $(document).on("click", ".mobile-menu-overlay", function () {
          closeMobileMenu();
          overlay.css('opacity', '0');
          setTimeout(function() {
            overlay.css('display', 'none');
          }, 300);
        });
        $(document).on("click", "#main-nav-mobile .menu-item", function (e) {
            $(this).toggleClass("active");
            $(this).find('.sub-menu').first().slideToggle();
        });

        // toggle sub-menu-item-inner
        // Only listen to clicks on menu-item-inner-title, not on the entire menu-item-inner
        // This allows links inside sub-menu-item-inner to work normally
        // $(document).on("click", "#main-nav-mobile .menu-item-inner-title", function (e) {
        //     e.preventDefault();
        //     e.stopPropagation();
        //     var $menuItem = $(this).closest('.menu-item-inner');
        //     var $subMenu = $menuItem.find('.sub-menu-item-inner');
            
        //     if ($subMenu.length) {
        //         $menuItem.toggleClass("active");
        //         $subMenu.slideToggle(300);
        //     }
        // });

        // toggle sub-menu-item-inner trong sub-menu--listing-nav (xử lý tương tự các submenu khác)
        $(document).on("click", "#main-nav-mobile  .menu-item-inner-title", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var $subMenuItemInner = $(this).parent().find('.sub-menu-item-inner');
            
            if ($subMenuItemInner.length) {
                // Dừng animation đang chạy để tránh giật
                $subMenuItemInner.stop(true, false);
                
                $subMenuItemInner.slideToggle(300, 'swing');
            }
        });
    }; 
   

    /* Filter Toggle
    ----------------------------------------------------------------------------*/
    var filterToggle = function () {
        var $filterBtn = $("#filterToggle");
        var $advancedFilters = $("#advancedFilters");
        
        $filterBtn.on("click", function (e) {
            e.stopPropagation();
            $advancedFilters.slideToggle(300);
            $(this).toggleClass("active");
        });
        
        // Click outside to close
        $(document).on("click", function (e) {
            // Check if click is outside both filterBtn and advancedFilters
            if (!$filterBtn.is(e.target) && 
                !$advancedFilters.is(e.target) && 
                $filterBtn.has(e.target).length === 0 && 
                $advancedFilters.has(e.target).length === 0) {
                
                // Only close if it's currently visible
                if ($advancedFilters.is(":visible")) {
                    $advancedFilters.slideUp(300);
                    $filterBtn.removeClass("active");
                }
            }
        });
    };

    /* Filter Sidebar Toggle
    ----------------------------------------------------------------------------*/
    var filterSidebarToggle = function () {
        var $sidebar = $("#filterSidebar");
        var $toggleBtn = $("#filterSidebarToggle");
        var $closeBtn = $("#filterSidebarClose");
        var $overlay = $(".filter-sidebar__overlay");

        // Open sidebar
        $toggleBtn.on("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
                $sidebar.addClass("active");
                $("body").css("overflow", "hidden");
        });

        // Close sidebar
        $closeBtn.on("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            $sidebar.removeClass("active");
            $("body").css("overflow", "");
        });

        // Close sidebar when clicking overlay
        $overlay.on("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            $sidebar.removeClass("active");
            $("body").css("overflow", "");
        });

        // Close sidebar on ESC key
        $(document).on("keydown", function (e) {
            if (e.key === "Escape" && $sidebar.hasClass("active")) {
                $sidebar.removeClass("active");
                $("body").css("overflow", "");
            }
        });

        // Check URL params for filterToggle
        function getUrlParams() {
            var params = {};
            var searchParams = new URLSearchParams(window.location.search);
            for (var pair of searchParams.entries()) {
                params[pair[0]] = pair[1];
            }
            return params;
        }

        // Auto-open sidebar if filterToggle=true in URL
        var urlParams = getUrlParams();
        if (urlParams.filterToggle === "true") {
            $sidebar.addClass("active");
            $("body").css("overflow", "hidden");
        }
    };

    /* Color Dropdown
    ----------------------------------------------------------------------------*/
    var colorDropdown = function () {
        // Initialize each color dropdown
        $('.filter-color-dropdown').each(function() {
            var $dropdown = $(this);
            var colorName = $dropdown.data('name'); // Get name from data-name attribute
            
            if (!colorName) {
                return;
            }
            
            // Set name for all radio buttons in this dropdown
            $dropdown.find('input[type="radio"]').attr('name', colorName);
            
            // Handle color selection
            $dropdown.find('input[type="radio"]').on('change', function() {
                var $radio = $(this);
                var colorValue = $radio.val();
                var $selectedSwatch = $dropdown.find('.filter-color-dropdown__selected .filter-color-dropdown__swatch');
                var $selectedText = $dropdown.find('.filter-color-dropdown__selected .filter-color-dropdown__text');
                var $optionSwatch = $radio.siblings('.filter-color-dropdown__swatch');
                
                // Update swatch color
                var swatchStyle = $optionSwatch.attr('style');
                $selectedSwatch.attr('style', swatchStyle);
                
                // Update text
                $selectedText.text(colorValue);
                
                // Close dropdown
                $dropdown.find('.filter-color-dropdown__toggle').prop('checked', false); 
            });
        });
    };

    /* Select Dropdown
    ----------------------------------------------------------------------------*/
    var selectDropdown = function () {
        $('.filter-select-dropdown').each(function() {
            var $dropdown = $(this);
            var selectName = $dropdown.data('name');
            var $toggle = $dropdown.find('.filter-select-dropdown__toggle');
            var $checkboxes = $dropdown.find('input[type="checkbox"]').not('.filter-select-dropdown__toggle');
            var $text = $dropdown.find('.filter-select-dropdown__text span');
            
            // Set name for all checkboxes
            $checkboxes.attr('name', selectName);
            
            // Update button text based on selected checkboxes
            var updateButtonText = function() {
                var $allCheckbox = $checkboxes.filter('[value="all"]');
                var isAllChecked = $allCheckbox.is(':checked');
                
                // Nếu "all" được checked, hiển thị "ALL [field name]" hoặc "all [field name]"
                if (isAllChecked) {
                    // Lấy name từ checkbox "all" hoặc từ selectName
                    var checkboxName = $allCheckbox.attr('name') || selectName;
                    var filterType = getFilterTypeFromName(checkboxName);
                    if (filterType) {
                        $text.text(formatAllLabel(filterType));
                        return;
                    }
                }
                
                var selected = $checkboxes.filter(':checked').not('[value="all"]').map(function() {
                    return $(this).closest('label').find('span').text();
                }).get();
                
                if (selected.length === 0) {
                    // Nếu không có gì được chọn, giữ nguyên text hiện tại hoặc set về default
                    var defaultText = $dropdown.find('.search-cars__label').text() || 'Select';
                    $text.text(defaultText);
                } else if (selected.length === 1) {
                    $text.text(selected[0]);
                } else {
                    $text.text(selected.length + ' selected');
                }
            };
            
            // Handle toggle change - close other dropdowns when opening this one
            $toggle.on('change', function() {
                if ($(this).is(':checked')) {
                    // Close all other dropdowns
                    $('.filter-select-dropdown__toggle').not(this).prop('checked', false);
                    $('.filter-select-dropdown').not($dropdown).removeClass('active');
                    // Open this dropdown
                    $dropdown.addClass('active');
                } else {
                    $dropdown.removeClass('active');
                }
            });
            
            // Handle checkbox change
            $checkboxes.on('change', function() {
                var $checkbox = $(this);
                var value = $checkbox.val();
                
                if (value === 'all' && $checkbox.is(':checked')) {
                    $checkboxes.not($checkbox).prop('checked', false);
                } else if ($checkbox.is(':checked')) {
                    $checkboxes.filter('[value="all"]').prop('checked', false);
                }
                
                updateButtonText();
            });
            
            // Prevent dropdown from closing when clicking inside menu
            $dropdown.find('.filter-select-dropdown__menu').on('click', function(e) {
                e.stopPropagation();
            });
            
            updateButtonText();
        });
        
        // Close dropdown when clicking outside (single handler for all dropdowns)
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.filter-select-dropdown').length) {
                $('.filter-select-dropdown__toggle').prop('checked', false);
                $('.filter-select-dropdown').removeClass('active');
            }
        });
    };

    /* Dropdown
    ----------------------------------------------------------------------------*/
    var coreDropdown = function () {
        var $dropdown = $(".core-dropdown");
        var $dropdownOptions = $(".core-dropdown__option");

        $(document).on("click", ".core-dropdown__button", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var $currentDropdown = $(this).closest(".core-dropdown");
            $currentDropdown.toggleClass("active");
        });

        // Handle click on <li> in menu with id "coreDropdownMenu"
        $(document).on("click", "#coreDropdownMenu .core-dropdown__list li", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var $li = $(this);
            var text = $li.text().trim();
            var $currentDropdown = $li.closest(".core-dropdown");
            var $menu = $li.closest("#coreDropdownMenu");

            // If menu has id "coreDropdownMenu", update .core-dropdown__label
            if ($menu.length > 0 && $menu.attr("id") === "coreDropdownMenu") {
                var $label = $currentDropdown.find(".core-dropdown__label");
                if ($label.length > 0) {
                    $label.text(text);
                }
            }

            // Update active state for li
            $menu.find("li").removeClass("active");
            $li.addClass("active");

            // Close dropdown
            $currentDropdown.removeClass("active");
        });

        // Handle option selection
        $dropdownOptions.on("click", function (e) {
            e.preventDefault();
            var $option = $(this);
            var value = $option.data("value");
            var id = $option.data("id");
            var text = $option.text();
            var $currentDropdown = $option.closest(".core-dropdown");
            var $currentButton = $currentDropdown.find(".core-dropdown__button");

            // Update selected text (.core-dropdown__selected)
            var $selected = $currentDropdown.find(".core-dropdown__selected");
            if ($selected.length > 0) {
                $selected.text(text);
            }

            // Update active state
            $currentDropdown.find(".core-dropdown__option").removeClass("active");
            $option.addClass("active");

            // Set data-id core-dropdown
            // if not data-id option, get id button (default coreDropdownBtn)
            if (id !== undefined) {
                $currentDropdown.attr("data-id", id);
            } else {
                var buttonId = $currentButton.attr("id") || "coreDropdownBtn";
                $currentDropdown.attr("data-id", buttonId);
            }

            // Close dropdown
            $currentDropdown.removeClass("active"); 
        });

        // Close dropdown when clicking outside
        $(document).on("click", function (e) {
            if (!$dropdown.is(e.target) && 
                $dropdown.has(e.target).length === 0) {
                $dropdown.removeClass("active");
            }
        });
    };

    /* Tabs
    ----------------------------------------------------------------------------*/
    var tabs = function(){
        $('.flat-tabs').each(function(){
            var $flatTabs = $(this);
            $flatTabs.find('.content-tab').children().first().show();
            
            // default li selector
            // Check if has attribute data-custom="true" then find .item-menu, otherwise find li
            var hasCustom = $flatTabs.data('custom') === true || $flatTabs.attr('data-custom') === 'true';
            var selector = hasCustom ? '.item-menu' : 'li';
            
            $flatTabs.find('.menu-tab').children(selector).on('click', function(){
                var liActive = $(this).index();
                var contentActive = $(this).siblings().removeClass('active').parents('.flat-tabs').find('.content-tab').children().eq(liActive);
                contentActive.addClass('active').fadeIn("slow");
                contentActive.siblings().removeClass('active');
                $(this).addClass('active');
            });
        });
    };

    /* Mobile
    ----------------------------------------------------------------------------*/
    var isMobile = {
        Android: function () {
          return navigator.userAgent.match(/Android/i);
        },
        BlackBerry: function () {
          return navigator.userAgent.match(/BlackBerry/i);
        },
        iOS: function () {
          return navigator.userAgent.match(/iPhone|iPad|iPod/i);
        },
        Opera: function () {
          return navigator.userAgent.match(/Opera Mini/i);
        },
        Windows: function () {
          return navigator.userAgent.match(/IEMobile/i);
        },
        any: function () {
          return (
            isMobile.Android() ||
            isMobile.BlackBerry() ||
            isMobile.iOS() ||
            isMobile.Opera() ||
            isMobile.Windows()
          );
        },
    };

    /* Parallax
    ----------------------------------------------------------------------------*/
    var parallax = function () {
        $(".parallax").each(function () {
        new SimpleParallax(this, {
            delay: 0.5,
            orientation: "up",
            scale: 1.3,
            transition: "cubic-bezier(0.2, 0.8, 1, 1)",
            customContainer: "",
            customWrapper: "",
        });
        });
    };

    /* Flat Counter
    ----------------------------------------------------------------------------*/
    var flatCounter = function () {
      if ($(document.body).hasClass("counter-scroll")) {
        var a = 0;
        $(window).scroll(function () {
          var oTop = $(".counter").offset().top - window.innerHeight;
          if (a == 0 && $(window).scrollTop() > oTop) {
            if ($().countTo) {
              $(".counter")
                .find(".count-number")
                .each(function () {
                  var to = $(this).data("to"),
                    speed = $(this).data("speed"),
                    decimals = $(this).data("decimals") || 0,
                    formatter = $(this).data('formatter');
                  
                  if (!formatter) {
                    formatter = function(value, settings) {
                      return value.toFixed(settings.decimals).replace('.', ',');
                    };
                  }
                  
                  $(this).countTo({
                    to: to,
                    speed: speed,
                    decimals: decimals,
                    formatter: formatter,
                  });
                });
            }
            a = 1;
          }
        });
      }
    }; 

    /* Go Top
    ----------------------------------------------------------------------------*/
    var gotop = function () {
      if ($('div').hasClass('progress-wrap')) {
          var progressPath = document.querySelector('.progress-wrap path');
          var pathLength = progressPath.getTotalLength();
          progressPath.style.transition = progressPath.style.WebkitTransition = 'none';
          progressPath.style.strokeDasharray = pathLength + ' ' + pathLength;
          progressPath.style.strokeDashoffset = pathLength;
          progressPath.getBoundingClientRect();
          progressPath.style.transition = progressPath.style.WebkitTransition = 'stroke-dashoffset 10ms linear';
          var updateprogress = function () {
              var scroll = $(window).scrollTop();
              var height = $(document).height() - $(window).height();
              var progress = pathLength - (scroll * pathLength / height);
              progressPath.style.strokeDashoffset = progress;
          }
          updateprogress();
          $(window).scroll(updateprogress);
          var offset = 150;
          var duration = 300;
          jQuery(window).on('scroll', function () {
              if (jQuery(this).scrollTop() > offset) {
                  jQuery('.progress-wrap').addClass('active-progress');
              } else {
                  jQuery('.progress-wrap').removeClass('active-progress');
              }
          });
          jQuery('.progress-wrap').on('click', function (event) {
              event.preventDefault();
              jQuery('html, body').animate({ scrollTop: 0 }, duration);
              return false;
          })
      }
    }

    /* Modal Popup
    ----------------------------------------------------------------------------*/
    var modalPopup = function(openModalClass, bgModalClass, closeBtnClass, closeModalClass) {
        openModalClass = openModalClass || '.open-modal';
        bgModalClass = bgModalClass || '.bg-modal';
        closeBtnClass = closeBtnClass || '.close-modal';
        closeModalClass = closeModalClass || '.close-modal-any';

        $(document).on('click', openModalClass, function(e) {
            e.preventDefault();
            var modalId = $(this).data('modal-id');
            if (modalId) {
                $('.modal.active').removeClass('active');
                $(modalId).addClass('active');
            }
        });

        // Click background close modal
        $(document).on('click', bgModalClass, function(e) {
            e.preventDefault();
            e.stopPropagation();
            var $modal = $(this).closest('.modal');
            if ($modal.length) {
                $modal.removeClass('active');
            }
        });

        // Click bg-modal close modal
        $(document).on('click', '.modal', function(e) {
            var $target = $(e.target);
            if ($target.hasClass('bg-modal') || $target.closest('.bg-modal').length) {
                $(this).removeClass('active');
            }
        });

        // Click close button -> đóng modal
        $(document).on('click', closeBtnClass, function(e) {
            e.preventDefault();
            var $modal = $(this).closest('.modal');
            if ($modal.length) {
                $modal.removeClass('active');
            }
        });

        // Click closeModalClass close current modal
        $(document).on('click', closeModalClass, function(e) {
            e.preventDefault();
            // find and close modal active
            var $activeModal = $('.modal.active');
            if ($activeModal.length) {
                $activeModal.removeClass('active');
            }
        });

        // Click modal-content not close modal
        $(document).on('click', '.modal-content', function(e) {
            e.stopPropagation();
        });
    };

    /* Preloader
    ----------------------------------------------------------------------------*/
    var Preloader = function () {
      setTimeout(function () {
      $(".preload").fadeOut("slow", function () {
          $(this).remove();
      });
      }, 0);
    };

    /* Rating Input
    ----------------------------------------------------------------------------*/
    var ratingInput = function () {
        // Helper function to convert icon paths based on dark mode
        function convertIconForDarkMode(iconPath) {
            if (!iconPath) return iconPath;
            
            // Check if dark mode is active - check both class and cookie
            var isDark = false;
            
            // First check if class is already set
            if ($('body').hasClass('is_dark') || $('html').hasClass('is_dark')) {
                isDark = true;
            } 
            // If class not set yet, check cookie (for initial page load)
            else if (typeof $.cookie !== 'undefined') {
                var savedTheme = $.cookie('themeMode');
                if (savedTheme === 'dark') {
                    isDark = true;
                }
            }
            
            if (isDark) {
                // Replace star-3.svg with star-3-white.svg
                iconPath = iconPath.replace('star-3.svg', 'star-3-white.svg');
                // Replace star-4.svg with star-4-white.svg
                iconPath = iconPath.replace('star-4.svg', 'star-4-white.svg');
            } else {
                // Replace star-3-white.svg back to star-3.svg
                iconPath = iconPath.replace('star-3-white.svg', 'star-3.svg');
                // Replace star-4-white.svg back to star-4.svg
                iconPath = iconPath.replace('star-4-white.svg', 'star-4.svg');
            }
            
            return iconPath;
        }
        
        // Lấy icon từ data attributes hoặc từ HTML
        function getIcons($ratingInput) {
            // Ưu tiên lấy từ data attributes
            var activeIcon = $ratingInput.data('active-icon');
            var inactiveIcon = $ratingInput.data('inactive-icon');
            
            // Nếu không có data attributes, lấy từ icon đầu tiên trong HTML
            if (!activeIcon || !inactiveIcon) {
                var $firstStar = $ratingInput.find('.rating-input__star').first();
                var $firstIcon = $firstStar.find('.star-icon');
                var defaultIconSrc = $firstIcon.attr('src') || './assets/icons/star-3.svg';
                
                // Convert icon path for dark mode
                defaultIconSrc = convertIconForDarkMode(defaultIconSrc);
                
                // Nếu không có inactive icon, dùng icon mặc định từ HTML
                if (!inactiveIcon) {
                    inactiveIcon = defaultIconSrc;
                }
                
                // Nếu không có active icon, suy ra từ inactive icon
                if (!activeIcon) {
                    // Pattern: star-3.svg -> star-4.svg, star-7.svg -> star-6.svg, etc.
                    activeIcon = defaultIconSrc.replace(/star-(\d+)(-white)?\.svg/, function(match, num, white) {
                        var numInt = parseInt(num);
                        // Nếu số >= 4, giảm 1; nếu < 4, tăng 1
                        var newNum = numInt >= 4 ? numInt - 1 : numInt + 1;
                        var whiteSuffix = white ? '-white' : '';
                        return 'star-' + newNum + whiteSuffix + '.svg';
                    });
                }
            }
            
            // Convert icons for dark mode
            activeIcon = convertIconForDarkMode(activeIcon);
            inactiveIcon = convertIconForDarkMode(inactiveIcon);
            
            return {
                active: activeIcon,
                inactive: inactiveIcon
            };
        }

        function updateStarIcon($star, isActive, icons) {
            var $icon = $star.find('.star-icon');
            if (isActive) {
                $icon.attr('src', icons.active);
            } else {
                $icon.attr('src', icons.inactive);
            }
        }

        function updateStarsByRating($ratingInput, rating) {
            var icons = getIcons($ratingInput);
            
            $ratingInput.find('.rating-input__star').each(function() {
                var starRating = parseInt($(this).data('rating'));
                var isActive = starRating <= rating;
                
                if (isActive) {
                    $(this).addClass('active');
                } else {
                    $(this).removeClass('active');
                }
                
                // Update icon based on active state
                updateStarIcon($(this), isActive, icons);
            });
        }

        // Initialize rating based on input value
        function initializeRatingInputs() {
            $('.rating-input').each(function() {
                var $ratingInput = $(this);
                
                // Lưu icon ban đầu của mỗi star
                $ratingInput.find('.rating-input__star .star-icon').each(function() {
                    var $icon = $(this);
                    if (!$icon.data('original-icon')) {
                        $icon.data('original-icon', $icon.attr('src'));
                    }
                });
                
                // Lấy icons và cache lại (sẽ tự động convert cho dark mode)
                getIcons($ratingInput);
                
                // Initialize rating based on input value
                var $hiddenInput = $ratingInput.find('#rating-value');
                var initialRating = parseInt($hiddenInput.val()) || 0;
                
                if (initialRating > 0) {
                    updateStarsByRating($ratingInput, initialRating);
                } else {
                    // Even if no rating, update icons to ensure correct dark mode icons
                    var icons = getIcons($ratingInput);
                    $ratingInput.find('.rating-input__star').each(function() {
                        updateStarIcon($(this), false, icons);
                    });
                }
            });
        }
        
        // Initialize immediately
        initializeRatingInputs();
        
        // Also re-initialize after a short delay to ensure theme is set
        setTimeout(function() {
            initializeRatingInputs();
        }, 100);

        $('.rating-input__star').on('click', function() {
            var rating = parseInt($(this).data('rating'));
            var $ratingInput = $(this).closest('.rating-input');
            var $hiddenInput = $ratingInput.find('#rating-value');
            
            // Update hidden input value
            $hiddenInput.val(rating);
            
            // Update all stars
            updateStarsByRating($ratingInput, rating);
        });
    };

    /* Accordion
    ----------------------------------------------------------------------------*/
    var flatAccordion = function() {
        var args = {duration: 300};
        $('.flat-toggle .toggle-title.active').siblings('.toggle-content').show();
      
        $('.flat-toggle.enable .toggle-title').on('click', function() {
            $(this).closest('.flat-toggle').find('.toggle-content').slideToggle(args);
            $(this).toggleClass('active');
        }); // toggle 
      
        // Ngăn event propagation từ checkbox và label của checkbox trong toggle-content
        $('.flat-accordion .toggle-content input[type="checkbox"], .flat-accordion .toggle-content label').on('click', function(e) {
            e.stopPropagation();
        });
        
        // Ngăn event propagation từ radio button (nhưng không phải label vì label cần xử lý riêng)
        $('.flat-accordion input[type="radio"]').on('click', function(e) {
            e.stopPropagation();
        });

        $('.flat-accordion .toggle-title').on('click', function (e) {
            // Bỏ qua nếu click vào label hoặc radio button
            if ($(e.target).is('label') || $(e.target).is('input[type="radio"]') || $(e.target).closest('label').length > 0) {
                return;
            }
            
            // Bỏ qua nếu click vào checkbox hoặc label của checkbox trong toggle-content
            if ($(e.target).is('input[type="checkbox"]') || $(e.target).closest('.toggle-content').length > 0) {
                return;
            }

            var $clickedTitle = $(this);
            var $clickedToggle = $clickedTitle.closest('.flat-toggle');
            var isCurrentlyActive = $clickedToggle.hasClass('active');

            // Bỏ checked tất cả radio buttons trong flat-accordion
            $('.flat-accordion .flat-toggle').find('input[type="radio"]').prop('checked', false);
            
            // Bỏ active tất cả flat-toggle
            $('.flat-accordion .flat-toggle').removeClass('active');
            $('.flat-accordion .toggle-title').removeClass('active');
            $('.flat-accordion .toggle-content').slideUp(args);

            if (!isCurrentlyActive) {
                // Set active cho toggle được click
                $clickedToggle.addClass('active');
                $clickedTitle.addClass('active');
                $clickedTitle.next('.toggle-content').slideDown(args);
                
                // Tìm và check radio button trong toggle-title
                var $radio = $clickedTitle.find('input[type="radio"]');
                if ($radio.length > 0) {
                    $radio.prop('checked', true);
                }
            }     
        }); // accordion

        // Xử lý click vào label để toggle accordion (chỉ label trong toggle-title, không phải toggle-content)
        $('.flat-accordion .toggle-title label').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            var $label = $(this);
            var $toggleTitle = $label.closest('.toggle-title');
            var $clickedToggle = $toggleTitle.closest('.flat-toggle');
            var isCurrentlyActive = $clickedToggle.hasClass('active');

            // Bỏ checked tất cả radio buttons trong flat-accordion
            $('.flat-accordion .flat-toggle').find('input[type="radio"]').prop('checked', false);
            
            // Bỏ active tất cả flat-toggle
            $('.flat-accordion .flat-toggle').removeClass('active');
            $('.flat-accordion .toggle-title').removeClass('active');
            $('.flat-accordion .toggle-content').slideUp(args);

            if (!isCurrentlyActive) {
                // Set active cho toggle được click
                $clickedToggle.addClass('active');
                $toggleTitle.addClass('active');
                $toggleTitle.next('.toggle-content').slideDown(args);
                
                // Check radio button trong label
                var $radio = $label.find('input[type="radio"]');
                if ($radio.length > 0) {
                    $radio.prop('checked', true);
                }
            }
        });
    }; 

    /* Get Filter Type From Name
    ----------------------------------------------------------------------------*/
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

    /* Format "All [field name]" Label
    ----------------------------------------------------------------------------*/
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

    /* Password Input 
    ----------------------------------------------------------------------------*/
    var passwordInput = function() {
        $('.password-input').each(function () {
            var $input = $(this);
    
            // trạng thái ban đầu
            $input
                .addClass('is-hidden')
                .attr('type', 'password');
    
            $input.on('click', function (e) {
                var iconAreaWidth = 44;
                var inputWidth = $input.outerWidth();
                var clickX = e.offsetX || (e.pageX - $input.offset().left);
    
                // chỉ toggle khi click vùng icon bên phải
                if (clickX < inputWidth - iconAreaWidth) {
                    return;
                }
    
                e.preventDefault();
                e.stopPropagation();
    
                if ($input.attr('type') === 'password') {
                    $input
                        .attr('type', 'text')
                        .removeClass('is-hidden')
                        .addClass('is-visible');
                } else {
                    $input
                        .attr('type', 'password')
                        .removeClass('is-visible')
                        .addClass('is-hidden');
                }
            });
        });
    }
    
    /* Collapse
    ----------------------------------------------------------------------------*/
    var collapse = function () {
        var isMobile = window.matchMedia("(max-width: 767px)");
        
        $(document).on("click", ".collapse-title", function (e) {
            if($(this).data('breakpoint') === 'mobile' && !isMobile.matches) {
                return;
            }
            e.preventDefault(); 
            
            var $collapse = $(this).closest(".collapse");
            var $content = $collapse.find(".collapse-content");
            var $title = $(this);
            var $icon = $title.find(".icon");
            
            // Toggle active class
            $collapse.toggleClass("active");
            $title.toggleClass("active");
            
            // Toggle icon: active = "-", else = "+"
            if ($collapse.hasClass("active")) {
                $icon.text("-");
                $content.slideDown(300);
            } else {
                $icon.text("+");
                $content.slideUp(300);
            }
        });
    };
    
    /* Car Views Chart
    ----------------------------------------------------------------------------*/
    var carViewsChart = function () {
        var canvas = document.getElementById('carViewsChart');
        if (!canvas) return;
        
        var ctx = canvas.getContext('2d');
        var tooltip = document.getElementById('carViewsTooltip');
        var isHovering = false;
        var hoveredIndex = -1;
        var hoverAnimationProgress = 0; // 0 to 1 for smooth animation
        var animationFrameId = null;
        
        // Chart data
        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        var data = [250, 220, 200, 180, 170, 175, 160, 140, 130, 120, 115, 175];
        var maxValue = 300;
        
        var paddingLeft = maxValue.toString().length * 2 + 40;
        // Chart dimensions
        var padding = { top: 40, right: 40, bottom: 40, left: paddingLeft };
        var chartWidth, chartHeight, chartX, chartY;
        
        // Custom font sizes for labels
        var labelFontSize = {
            y: 18, // Y-axis labels font size
            x: 18  // X-axis labels font size
        };
        
        // Custom font family
        var fontFamily = {
            labels: '"Manrope", sans-serif',      // Font cho Y và X axis labels
            tooltip: '"Manrope", sans-serif'      // Font cho tooltip
        };
        
        // Check if dark mode is active
        function isDarkMode() {
            // Check if class is already set
            if ($('body').hasClass('is_dark') || $('html').hasClass('is_dark')) {
                return true;
            }
            // If class not set yet, check cookie (for initial page load)
            if (typeof $.cookie !== 'undefined') {
                var savedTheme = $.cookie('themeMode');
                if (savedTheme === 'dark') {
                    return true;
                }
            }
            return false;
        }
        
        var isDark = isDarkMode();
        
        // Custom colors
        var colors = {
            labelY: isDark ? '#FFFFFF' : '#1C1C1C',         // Color cho Y-axis labels (white in dark mode)
            labelX: isDark ? '#FFFFFF' : '#1C1C1C',         // Color cho X-axis labels (white in dark mode)
            gridLine: '#E7E7E7',       // Color cho grid lines
            verticalLine: '#E7E7E7',   // Color cho vertical line bên phải Y-axis
            dataLine: '#f5a81c',        // Color cho data line
            dataPoint: '#f5a81c',      // Color cho data points
            hoverPoint: '#f5a81c', // Color cho hover point highlight
            tooltipBg: isDark ? '#1C1C1C' : 'white',        // Color cho tooltip background (dark in dark mode)
            tooltipTitle: isDark ? '#FFFFFF' : '#111827',    // Color cho tooltip title text (white in dark mode)
            tooltipValue: isDark ? '#E7E7E7' : '#4B4B4B'     // Color cho tooltip value text (lighter in dark mode)
        };
        
        // Helper function để convert hex to rgba
        function hexToRgba(hex, alpha) {
            var r = parseInt(hex.slice(1, 3), 16);
            var g = parseInt(hex.slice(3, 5), 16);
            var b = parseInt(hex.slice(5, 7), 16);
            return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + alpha + ')';
        }
        
        function resizeCanvas() {
            var container = canvas.parentElement;
            var containerWidth = container.clientWidth;
            var containerHeight = 473;
            
            // Lấy device pixel ratio để tránh hình tròn bị méo
            var dpr = window.devicePixelRatio || 1;
            
            // Set CSS size
            canvas.style.width = containerWidth + 'px';
            canvas.style.height = containerHeight + 'px';
            
            // Set actual size in memory (scaled for device pixel ratio)
            canvas.width = containerWidth * dpr;
            canvas.height = containerHeight * dpr;
            
            // Scale context để đảm bảo vẽ đúng tỷ lệ
            ctx.scale(dpr, dpr);
            
            // Tính toán lại với kích thước CSS (không phải kích thước thực tế)
            chartWidth = containerWidth - padding.left - padding.right;
            chartHeight = containerHeight - padding.top - padding.bottom;
            chartX = padding.left;
            chartY = padding.top;
            
            drawChart();
        }
        
        function drawChart() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw grid lines
            ctx.strokeStyle = colors.gridLine;
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            
            var gridSteps = 6;
            for (var i = 0; i <= gridSteps; i++) {
                var y = chartY + (chartHeight / gridSteps) * i;
                ctx.beginPath();
                ctx.moveTo(chartX, y);
                ctx.lineTo(chartX + chartWidth, y);
                ctx.stroke();
            }
            
            ctx.setLineDash([]);
            
            // Draw Y-axis labels
            ctx.fillStyle = colors.labelY;
            ctx.font = labelFontSize.y + 'px ' + fontFamily.labels;
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            
            // Function làm tròn số cho Y-axis labels
            function formatYAxisValue(value) {
                // Làm tròn thành số nguyên
                return Math.round(value).toString();
            }
            
            for (var i = 0; i <= gridSteps; i++) {
                var value = maxValue - (maxValue / gridSteps) * i;
                var y = chartY + (chartHeight / gridSteps) * i;
                var formattedValue = formatYAxisValue(value);
                ctx.fillText(formattedValue, chartX - 10, y);
            }
            
            // Draw vertical line bên phải Y-axis labels
            ctx.strokeStyle = colors.verticalLine;
            ctx.lineWidth = 1;
            ctx.setLineDash([]);
            ctx.beginPath();
            ctx.moveTo(chartX, chartY);
            ctx.lineTo(chartX, chartY + chartHeight);
            ctx.stroke();
            
            // Draw X-axis labels
            ctx.fillStyle = colors.labelX;
            ctx.font = labelFontSize.x + 'px ' + fontFamily.labels;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            var monthWidth = chartWidth / months.length;
            
            // Kiểm tra nếu là mobile để xử lý labels
            var isMobile = window.matchMedia("(max-width: 767px)").matches;
            var labelStep = 1; // Mặc định hiển thị tất cả labels
            
            if (isMobile) {
                // Trên mobile, chỉ hiển thị mỗi 2 tháng một lần để tránh overlap
                // Hoặc tính toán dựa trên width để đảm bảo không overlap
                var minLabelSpacing = 40; // Khoảng cách tối thiểu giữa các labels (px)
                var availableWidth = chartWidth;
                var maxLabels = Math.floor(availableWidth / minLabelSpacing);
                
                if (maxLabels < months.length) {
                    labelStep = Math.ceil(months.length / maxLabels);
                }
            }
            
            for (var i = 0; i < months.length; i++) {
                // Chỉ hiển thị labels theo step trên mobile
                if (isMobile && i % labelStep !== 0 && i !== 0 && i !== months.length - 1) {
                    continue; // Bỏ qua labels không cần thiết
                }
                
                var x = chartX + monthWidth * i + monthWidth / 2;
                var y = chartY + chartHeight + 15;
                
                // Trên mobile, hiển thị số tháng (1, 2, 3...) thay vì tên tháng
                var labelText = isMobile ? (i + 1).toString() : months[i];
                ctx.fillText(labelText, x, y);
            }
            
            // Draw line and points
            ctx.strokeStyle = colors.dataLine;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            var pointRadius = 6; // 12px width và height (radius * 2)
            var points = [];
            
            for (var i = 0; i < data.length; i++) {
                var x = chartX + monthWidth * i + monthWidth / 2;
                var y = chartY + chartHeight - (data[i] / maxValue) * chartHeight;
                points.push({ x: x, y: y, value: data[i], month: months[i] });
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            
            ctx.stroke();
            
            // Draw points
            for (var i = 0; i < points.length; i++) {
                var point = points[i];
                
                // Highlight hovered point với hiệu ứng glow mượt mà
                if (hoveredIndex === i && hoverAnimationProgress > 0) {
                    // Tạo radial gradient cho hiệu ứng glow
                    var glowRadius = pointRadius + 8 + (hoverAnimationProgress * 4);
                    var gradient = ctx.createRadialGradient(
                        point.x, point.y, pointRadius,
                        point.x, point.y, glowRadius
                    );
                    
                    // Gradient từ màu hover với opacity giảm dần
                    var hoverColor = colors.hoverPoint;
                    var rgbaColor = hexToRgba(hoverColor, 0.3 * hoverAnimationProgress);
                    gradient.addColorStop(0, rgbaColor);
                    gradient.addColorStop(0.5, hexToRgba(hoverColor, 0.15 * hoverAnimationProgress));
                    gradient.addColorStop(1, hexToRgba(hoverColor, 0));
                    
                    // Vẽ glow effect
                    ctx.fillStyle = gradient;
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, glowRadius, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // Vẽ shadow cho data point
                    ctx.shadowColor = hexToRgba(hoverColor, 0.5 * hoverAnimationProgress);
                    ctx.shadowBlur = 8 * hoverAnimationProgress;
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                } else {
                    ctx.shadowColor = 'transparent';
                    ctx.shadowBlur = 0;
                }
                
                // Vẽ fill (bên trong) - đảm bảo fill đầy đủ
                ctx.fillStyle = colors.dataPoint;
                ctx.beginPath();
                ctx.arc(point.x, point.y, pointRadius, 0, Math.PI * 2);
                ctx.fill();
                
                // Vẽ border chỉ khi focus/hover vào data point
                if (hoveredIndex === i && hoverAnimationProgress > 0) { 
                    var borderAlpha = 0.102 * hoverAnimationProgress; // Animate border opacity
                    ctx.strokeStyle = 'rgba(241, 91, 40, ' + borderAlpha + ')';
                    ctx.lineWidth = 8;
                    ctx.lineCap = 'round';
                    ctx.lineJoin = 'round';
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, pointRadius, 0, Math.PI * 2);
                    ctx.stroke();
                }
                
                // Reset shadow
                ctx.shadowColor = 'transparent';
                ctx.shadowBlur = 0;
            }
            
            // Draw tooltip
            if (isHovering && hoveredIndex >= 0) {
                var point = points[hoveredIndex];
                var tooltipX = point.x;
                var tooltipY = point.y - 50; // Điều chỉnh để có chỗ cho icon phía dưới
                var tooltipPadding = { top: 12, right: 12, bottom: 12, left: 12 }; // Tăng padding top và bottom để không sát lề
                var tooltipBorderRadius = 8;
                
                // Tính toán kích thước tooltip dựa trên text
                ctx.font = 'bold 16px ' + fontFamily.tooltip;
                var titleText = point.month + ', 2025';
                var titleWidth = ctx.measureText(titleText).width;
                
                ctx.font = '12px ' + fontFamily.tooltip;
                var valueText = 'Views: ' + point.value;
                var valueWidth = ctx.measureText(valueText).width;
                
                var tooltipWidth = Math.max(titleWidth, valueWidth) + tooltipPadding.left + tooltipPadding.right;
                // Tính toán height: title (16px) + gap (4px) + value (12px) + padding top (12px) + padding bottom (12px)
                var tooltipHeight = 16 + 4 + 12 + tooltipPadding.top + tooltipPadding.bottom;
                
                // Adjust tooltip position if too close to edges
                if (tooltipX + tooltipWidth / 2 > canvas.width - padding.right) {
                    tooltipX = canvas.width - padding.right - tooltipWidth / 2;
                }
                if (tooltipX - tooltipWidth / 2 < padding.left) {
                    tooltipX = padding.left + tooltipWidth / 2;
                }
                
                var tooltipLeft = tooltipX - tooltipWidth / 2;
                var tooltipTop = tooltipY - tooltipHeight / 2;
                
                // Function để vẽ rounded rectangle với icon tam giác tích hợp
                function drawTooltipWithArrow(x, y, width, height, radius, arrowX, arrowSize) {
                    ctx.beginPath();
                    // Top-left corner
                    ctx.moveTo(x + radius, y);
                    // Top edge
                    ctx.lineTo(x + width - radius, y);
                    // Top-right corner
                    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
                    // Right edge
                    ctx.lineTo(x + width, y + height - radius);
                    // Bottom-right corner
                    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
                    // Bottom edge đến vị trí icon tam giác (trái)
                    ctx.lineTo(arrowX + arrowSize / 2, y + height);
                    // Icon tam giác - đỉnh ở bottom của tooltip
                    ctx.lineTo(arrowX, y + height + arrowSize);
                    ctx.lineTo(arrowX - arrowSize / 2, y + height);
                    // Bottom edge tiếp tục
                    ctx.lineTo(x + radius, y + height);
                    // Bottom-left corner
                    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
                    // Left edge
                    ctx.lineTo(x, y + radius);
                    // Top-left corner
                    ctx.quadraticCurveTo(x, y, x + radius, y);
                    ctx.closePath();
                }
                
                // Draw tooltip background với border radius, box-shadow và icon tam giác tích hợp
                // Box-shadow: 0px 5px 18px 5px #40485726
                // Convert #40485726: #404857 = rgb(64, 72, 87), 26 = 38/255 ≈ 0.149
                var arrowSize = 6;
                var arrowX = tooltipX;
                
                ctx.shadowColor = 'rgba(64, 72, 87, 0.149)';
                ctx.shadowBlur = 18;
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 5;
                
                ctx.fillStyle = colors.tooltipBg;
                drawTooltipWithArrow(tooltipLeft, tooltipTop, tooltipWidth, tooltipHeight, tooltipBorderRadius, arrowX, arrowSize);
                ctx.fill();
                
                ctx.shadowColor = 'transparent';
                
                // Draw tooltip text với padding
                var titleY = tooltipTop + tooltipPadding.top + 8; // Top padding (12px) + half of title font size (16/2 = 8)
                var valueY = titleY + 16 + 4; // Title Y + title height (16px) + gap (4px)
                
                ctx.fillStyle = colors.tooltipTitle;
                ctx.font = 'bold 16px ' + fontFamily.tooltip;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(titleText, tooltipX, titleY);
                
                ctx.fillStyle = colors.tooltipValue;
                ctx.font = '12px ' + fontFamily.tooltip;
                ctx.textBaseline = 'middle';
                ctx.fillText(valueText, tooltipX, valueY);
                
            }
        }
        
        // Animation function để làm mượt hiệu ứng hover
        function animateHover() {
            var targetProgress = isHovering ? 1 : 0;
            var speed = 0.15; // Tốc độ animation (0.1 = chậm, 0.3 = nhanh)
            
            if (Math.abs(hoverAnimationProgress - targetProgress) > 0.01) {
                hoverAnimationProgress += (targetProgress - hoverAnimationProgress) * speed;
                drawChart();
                animationFrameId = requestAnimationFrame(animateHover);
            } else {
                hoverAnimationProgress = targetProgress;
                drawChart();
            }
        }
        
        // Mouse move handler
        canvas.addEventListener('mousemove', function(e) {
            var rect = canvas.getBoundingClientRect();
            var mouseX = e.clientX - rect.left;
            var mouseY = e.clientY - rect.top;
            
            var monthWidth = chartWidth / months.length;
            var closestIndex = -1;
            var minDistance = Infinity;
            
            for (var i = 0; i < months.length; i++) {
                var pointX = chartX + monthWidth * i + monthWidth / 2;
                var pointY = chartY + chartHeight - (data[i] / maxValue) * chartHeight;
                var distance = Math.sqrt(Math.pow(mouseX - pointX, 2) + Math.pow(mouseY - pointY, 2));
                
                if (distance < 30 && distance < minDistance) {
                    minDistance = distance;
                    closestIndex = i;
                }
            }
            
            var wasHovering = isHovering;
            var previousHoveredIndex = hoveredIndex;
            
            if (closestIndex >= 0) {
                isHovering = true;
                hoveredIndex = closestIndex;
                canvas.style.cursor = 'pointer';
            } else {
                isHovering = false;
                hoveredIndex = -1;
                canvas.style.cursor = 'default';
            }
            
            // Bắt đầu animation nếu trạng thái hover thay đổi
            if (wasHovering !== isHovering || previousHoveredIndex !== hoveredIndex) {
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                }
                animateHover();
            }
        });
        
        canvas.addEventListener('mouseleave', function() {
            isHovering = false;
            hoveredIndex = -1;
            canvas.style.cursor = 'default';
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            animateHover();
        });
        
        // Initial resize and draw
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
    }; 

    /* Search Modal Toggle
    ----------------------------------------------------------------------------*/
    var searchModalToggle = function () {
        var $searchToggle = $("#searchToggle");
        var $searchModal = $("#SearchModal");
        var $searchModalClose = $("#searchModalClose");
        var $searchModalInput = $("#searchModalInput");
        var $body = $("body");

        // Open modal
        $searchToggle.on("click", function (e) {
            e.preventDefault();
            $searchModal.addClass("active");
            $body.css("overflow", "hidden");
            
            // Focus input after animation
            setTimeout(function() {
                $searchModalInput.focus();
            }, 400);
        });

        // Close modal
        function closeSearchModal() {
            $searchModal.removeClass("active");
            $body.css("overflow", "");
            $searchModalInput.val("");
        }

        $searchModalClose.on("click", function (e) {
            e.preventDefault();
            closeSearchModal();
        });

        // Close on ESC key
        $(document).on("keydown", function (e) {
            if (e.key === "Escape" && $searchModal.hasClass("active")) {
                closeSearchModal();
            }
        });

        // Close on overlay click
        $searchModal.on("click", function (e) {
            if ($(e.target).hasClass("search-modal__overlay")) {
                closeSearchModal();
            }
        });
    };

    /* Hover Active Gallery
    ----------------------------------------------------------------------------*/
    var hoverActiveGallery = function () {
        if ($('.container-grid-gallery').length) {
            $(document).ready(function () {
                $('.slide-gallery-list .slide-gallery').click(
                    function () {
                        $(this).closest('.slide-gallery-list').find('.slide-gallery').removeClass('active');
                        $(this).addClass('active');
                    }
                );
            });
        }
    }

    /* Scroll Element
    ----------------------------------------------------------------------------*/
    var scrollElement = function() {
        var elements = document.querySelectorAll('.scroll-element .element');
        
        elements.forEach(function(element) {
            element.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get attribute href from element
                var href = this.getAttribute('href');
                if (!href || !href.startsWith('#')) {
                    return;
                }
                
                var targetId = href.substring(1); // Remove # from href
                var targetElement = document.getElementById(targetId);
                
                if (!targetElement) {
                    targetElement = document.querySelector('[id="' + targetId + '"]');
                }
                
                if (targetElement) {
                    var header = document.querySelector('.header');
                    var headerHeight = header ? header.offsetHeight : 0;
                    var offset = 20; 
                    
                    var targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight - offset;
                    
                    window.scrollTo({
                        top: Math.max(0, targetPosition),
                        behavior: 'smooth'
                    });
                }
            });
        });
    };

    /* Select Options
    ----------------------------------------------------------------------------*/
    var selectOptions = function () {
        $(".custom-select").each(function () {
            const $select = $(this);
            const $selected = $select.find(".select-selected");
            const $items = $select.find(".select-items");
        
            const targetSelector = $select.data("target");
            const $hiddenInput = $(targetSelector);
        
            $selected.on("click", function (e) {
                e.stopPropagation();
                $(".select-items").not($items).hide();
                $items.toggle();
            });
        
            $items.find("div").on("click", function () {
                const value = $(this).data("value");
                const text = $(this).text();
        
                $selected.text(text);
                $hiddenInput.val(value);
                $items.hide();
            });
        });
      
        $(document).on("click", function () {
          $(".select-items").hide();
        });
    };

    /* Check Position
    ----------------------------------------------------------------------------*/
    const checkPosition = (elemnt, menuSticky, headerHeight) => {

        const totalHeight = elemnt.offsetTop + elemnt.clientHeight - menuSticky.clientHeight - 100;
    
        const rectScroll = elemnt.getBoundingClientRect()
        
        if(window.scrollY > totalHeight) {
            menuSticky.classList.remove('menuFixed')
            menuSticky.classList.add('menuSticky')
            return;
        }
        
        if(rectScroll.top <= headerHeight) {
            menuSticky.classList.add('menuFixed')
            menuSticky.classList.remove('menuSticky')
        } else {
            menuSticky.classList.remove('menuFixed')
            menuSticky.classList.remove('menuSticky')
        }
    }

    /* Scroll Sidebar
    ----------------------------------------------------------------------------*/
    var scrollSidebar = function () {
        var desktop = window.matchMedia("(min-width: 767px)");
        var onScrollHandler = null;
        var referenceElement = null;
        var menuSticky = null;
        
        function initScrollSidebar() {
            // Only run on desktop
            if (!desktop.matches) {
                // Cleanup if switching to mobile
                if (onScrollHandler) {
                    window.removeEventListener('scroll', onScrollHandler);
                    onScrollHandler = null;
                }
                return;
            }
            
            // Cleanup existing handler if re-initializing
            if (onScrollHandler) {
                window.removeEventListener('scroll', onScrollHandler);
                onScrollHandler = null;
            }
            
            if(!header) return;
            const headerHeight = header.offsetHeight;
            menuSticky = document.querySelector('#sidebarSticky')
            const sidebarContainer = document.querySelector('#scrollContainer')

            if(!menuSticky) return;

            // Use sidebarContainer as reference element, or fallback to menuSticky's parent
            referenceElement = sidebarContainer || menuSticky.parentElement;
            if(!referenceElement) return;
            
            if(sidebarContainer) {
                sidebarContainer.style.minHeight = menuSticky.clientHeight + "px";
            }
            
            // Initial check
            checkPosition(referenceElement, menuSticky, headerHeight)
            
            // Scroll handler
            onScrollHandler = () => {
                // Re-check if still desktop on scroll
                if (!desktop.matches) {
                    window.removeEventListener('scroll', onScrollHandler);
                    onScrollHandler = null;
                    return;
                }
                if(!header || !menuSticky || !referenceElement) return;
                const currentHeaderHeight = header.offsetHeight;
                checkPosition(referenceElement, menuSticky, currentHeaderHeight)
            }

            window.addEventListener('scroll', onScrollHandler);
        }
        
        // Initial call
        initScrollSidebar();
        
        // Re-initialize on resize
        window.addEventListener('resize', function() {
            initScrollSidebar();
        });
        
        // Also listen to media query changes
        desktop.addListener(function(mq) {
            initScrollSidebar();
        });
    }

    /* Newsletter Modal
    ----------------------------------------------------------------------------*/
    var newsletterModal = function() {
        var hasSeenNewsletter = localStorage.getItem('suggest_subscribe');
        
        if (!hasSeenNewsletter) {
            var checkPreloadInterval = setInterval(function() {
                if ($(".preload").length === 0) {
                    clearInterval(checkPreloadInterval);
                    setTimeout(function() {
                        $("#NewsletterModal").addClass("active");
                        localStorage.setItem('suggest_subscribe', 'false');
                    }, 100);
                }
            }, 3000);
        }
    };

    /* Compare Modal
    ----------------------------------------------------------------------------*/
    var compareModal = function() {
        // Function to update compare modal UI
        function updateCompareModalUI() {
            var $compareItems = $('#compareItems');
            var $emptyState = $('#compareEmptyState');
            var $compareAction = $('.compare-action');
            var itemCount = $compareItems.find('.compare-item').length;
            
            if (itemCount === 0) {
                // Show empty state, hide items and action button
                $emptyState.show();
                $compareItems.hide();
                $compareAction.hide();
            } else {
                // Hide empty state, show items and action button
                $emptyState.hide();
                $compareItems.show();
                $compareAction.show();
            }
        }
        
        // Handle click on compare-item-remove
        $(document).on('click', '.compare-item-remove', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            var $removeBtn = $(this);
            var $compareItem = $removeBtn.closest('.compare-item');
            
            if ($compareItem.length) {
                // Fade out animation
                $compareItem.fadeOut(300, function() {
                    $(this).remove();
                    // Update UI after removal
                    updateCompareModalUI();
                });
            }
        });
        
        // Initialize UI state on page load
        $(document).ready(function() {
            updateCompareModalUI();
        });
    };

    /* Heart List
    ----------------------------------------------------------------------------*/
    var heartList = function() {
        $(document).ready(function() {
            $(document).on('click', '.heart', function() {
                $(this).toggleClass('active');
            });
        });
    };

  

    $(function () {
        headerFixed();
        mobileNav();
        filterToggle();
        filterSidebarToggle();
        colorDropdown();
        selectDropdown();
        coreDropdown();
        tabs();
        parallax();
        flatCounter();
        gotop();
        modalPopup();
        Preloader();
        ratingInput();
        flatAccordion();
        passwordInput();
        collapse();
        carViewsChart();
        searchModalToggle();
        hoverActiveGallery();
        scrollElement();
        scrollSidebar();
        selectOptions();
        newsletterModal();
        heartList();
        compareModal(); 
    });

    

})(jQuery);
 

wow = new WOW({
  animateClass: 'animated',
  offset: 100
});
wow.init();