// Page Title Slider 1 - Only initialize if element exists
var swiperMain1, swiperThumb1;
if (document.querySelector(".page-title--slider-1")) {
    var navConfig = {};
    if (document.querySelector(".swiper-btn.navigation-next") && document.querySelector(".swiper-btn.navigation-prev")) {
        navConfig = {
            nextEl: ".swiper-btn.navigation-next",
            prevEl: ".swiper-btn.navigation-prev",
        };
    }
    
    swiperMain1 = new Swiper(".page-title--slider-1", {
        slidesPerView: 1,
        effect: "fade",
        fadeEffect: {
            crossFade: true
        },
        navigation: navConfig,
        autoplay: {
            delay: 3000,
        },
        speed: 100,
        pagination: {
            el: '.pagination-page-title--slider-1',
            clickable: true,
        },
    });

    // Only initialize thumb slider if element exists
    if (document.querySelector(".page-title--slider-1-thumb")) {
        swiperThumb1 = new Swiper(".page-title--slider-1-thumb", {
            effect: "fade",
            fadeEffect: {
                crossFade: true
            },
            slidesPerView: 1,
            allowTouchMove: false,
            speed: 1200,
        });

        // Sync 2 slider 1 - Only if both exist
        if (swiperMain1 && swiperThumb1) {
            swiperMain1.controller.control = swiperThumb1;
            swiperThumb1.controller.control = swiperMain1;
        }
    }
}

var swiper =  new Swiper(".swiper-brand", {
    slidesPerView: 1,
    speed: 800,  
    spaceBetween: 12,
    pagination: {
        el: '.pagination-swiper-brand',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 2,
        },
        600: {
            slidesPerView: 3,
        },
        767: {
            slidesPerView: 4,
        },
        991: {
            slidesPerView: 6,
        },
        1440: {
            slidesPerView: 9.95,
        },
    }
}); 
 
var swiper = new Swiper(".swiper-card", {
    slidesPerView: 1,
    slidesPerGroup: 1,
    speed: 800, 
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        400: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        }, 
        767: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        },
        991: {
            slidesPerView: 3,
            slidesPerGroup: 3,
        },
        1280: {
            slidesPerView: 4,
            slidesPerGroup: 4,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-card');
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-card');
        }
    }
});


var swiper = new Swiper(".swiper-card-style-2", {
    slidesPerView: 1,
    slidesPerGroup: 1,
    speed: 800, 
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card-style-2',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        400: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        }, 
        767: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        },
        991: {
            slidesPerView: 3,
            slidesPerGroup: 3,
        },
        1280: {
            slidesPerView: 4,
            slidesPerGroup: 4,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-card-style-2');
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-card-style-2');
        }
    }
});


var swiper = new Swiper(".swiper-products", {
    slidesPerView: 1,
    slidesPerGroup: 1,
    speed: 800, 
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-products',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        500: {
            slidesPerView: 2,
            slidesPerGroup: 1,
        }, 
        767: {
            slidesPerView: 3,
            slidesPerGroup: 2,
        },
        991: {
            slidesPerView: 3,
            slidesPerGroup: 3,
        },
        1280: {
            slidesPerView: 4,
            slidesPerGroup: 4,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-products');
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-products');
        }
    }
});

var swiperCarBox = new Swiper(".swiper-car-box", {
    slidesPerView: 1,
    speed: 800, 
    spaceBetween: 30,
    pagination: {
        el: '.pagination-car-box',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        }, 
        767: {
            slidesPerView: 2,
        },
        991: {
            slidesPerView: 3,
        },
        1280: {
            slidesPerView: 4,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-car-box');
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-car-box');
        }
    }
});

function checkAndHidePagination(swiper, paginationSelectorOrElement) {
    // Support both selector string and element
    var paginationEl = typeof paginationSelectorOrElement === 'string' 
        ? document.querySelector(paginationSelectorOrElement) 
        : paginationSelectorOrElement;
    
    if (!paginationEl) return;
    
    var totalSlides = swiper.slides.length;
    if (totalSlides === 0) {
        paginationEl.style.display = 'none';
        return;
    }
    
    // Get current slidesPerView from Swiper instance
    // Use the actual computed value from Swiper
    var currentSlidesPerView = swiper.params.slidesPerView;
    
    // Try to get actual slidesPerView from current breakpoint
    if (swiper.params.breakpoints) {
        var windowWidth = window.innerWidth || document.documentElement.clientWidth;
        var breakpointKeys = Object.keys(swiper.params.breakpoints)
            .map(function(key) { return parseInt(key); })
            .sort(function(a, b) { return b - a; });
        
        // Find the active breakpoint
        for (var i = 0; i < breakpointKeys.length; i++) {
            if (windowWidth >= breakpointKeys[i]) {
                var breakpointKey = breakpointKeys[i].toString();
                var breakpointConfig = swiper.params.breakpoints[breakpointKey];
                if (breakpointConfig && typeof breakpointConfig.slidesPerView !== 'undefined') {
                    currentSlidesPerView = breakpointConfig.slidesPerView;
                }
                break;
            }
        }
    }
    
    // Get current slidesPerColumn (default to 1 if not set)
    var currentSlidesPerColumn = swiper.params.slidesPerColumn || 1;
    
    // Try to get slidesPerColumn from current breakpoint
    if (swiper.params.breakpoints) {
        var windowWidth = window.innerWidth || document.documentElement.clientWidth;
        var breakpointKeys = Object.keys(swiper.params.breakpoints)
            .map(function(key) { return parseInt(key); })
            .sort(function(a, b) { return b - a; });
        
        for (var i = 0; i < breakpointKeys.length; i++) {
            if (windowWidth >= breakpointKeys[i]) {
                var breakpointKey = breakpointKeys[i].toString();
                var breakpointConfig = swiper.params.breakpoints[breakpointKey];
                if (breakpointConfig && typeof breakpointConfig.slidesPerColumn !== 'undefined') {
                    currentSlidesPerColumn = breakpointConfig.slidesPerColumn;
                }
                break;
            }
        }
    }
    
    // Calculate total visible slides (slidesPerView * slidesPerColumn)
    var totalVisibleSlides = currentSlidesPerView * currentSlidesPerColumn;
    
    // Hide pagination if total slides <= total visible slides
    if (totalSlides <= totalVisibleSlides) {
        paginationEl.style.display = 'none';
    } else {
        paginationEl.style.display = '';
    }
}

var swiper = new Swiper(".swiper-card-5", {
    slidesPerView: 1, 
    slidesPerGroup: 1,
    speed: 800, 
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card-5',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        }, 
        767: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        },
        991: {
            slidesPerView: 3,
            slidesPerGroup: 3,
        },
        1440: {
            slidesPerView: 4.63,
            slidesPerGroup: 4,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-card-5');
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-card-5');
        }
    }
});

var swiper = new Swiper(".swiper-card-2", {
    slidesPerView: 1,
    speed: 800,
    spaceBetween: 30,
    slidesPerGroup: 1,
    pagination: {
        el: '.pagination-swiper-card-2',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        }, 
        767: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        991: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        },
    }
});


var swiper = new Swiper(".swiper-card-3", {
    slidesPerView: 1,
    speed: 800,
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card-3',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        }, 
        767: {
            slidesPerView: 2,
        },
        991: {
            slidesPerView: 2,
        },
        1199: {
            slidesPerView: 3,
        },
    },
    on: {
        init: function() {
            checkAllowTouchMove(this);
            checkAndHidePagination(this, '.pagination-swiper-card-3');
        },
        resize: function() {
            checkAllowTouchMove(this);
            checkAndHidePagination(this, '.pagination-swiper-card-3');
        }
    }
});

var swiper = new Swiper(".swiper-card-4", {
    slidesPerView: 1,
    slidesPerColumn: 2,
    slidesPerColumnFill: 'row',
    loop: false,   
    speed: 800,
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card-4',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        }, 
        767: {
            slidesPerView: 1,
        },
        991: {
            slidesPerView: 2,
        },
    }
}); 

var swiper = new Swiper(".swiper-card-6", {
    slidesPerView: 1,
    slidesPerColumn: 2,
    slidesPerColumnFill: 'row',
    allowTouchMove: true,
    loop: false,   
    speed: 800,
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card-6',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
            allowTouchMove: true,
            slidesPerColumn: 2,
        }, 
        550: {
            slidesPerView: 2,
            allowTouchMove: true,
            slidesPerColumn: 2,
        },
        767: {
            slidesPerView: 3,
            allowTouchMove: true,
            slidesPerColumn: 2,
        },
        991: {
            slidesPerView: 4,
            allowTouchMove: true,
            slidesPerColumn: 2,
        },
        1440: {
            slidesPerView: 5,
            allowTouchMove: false,
            slidesPerColumn: 2,
        },
    },
    on: {
        init: function() {
            // Find pagination in the same container as this swiper
            var swiperEl = this.el;
            var paginationEl = swiperEl.parentElement ? swiperEl.parentElement.querySelector('.pagination-swiper-card-6') : null;
            if (paginationEl) {
                checkAndHidePagination(this, paginationEl);
            }
        },
        resize: function() {
            // Find pagination in the same container as this swiper
            var swiperEl = this.el;
            var paginationEl = swiperEl.parentElement ? swiperEl.parentElement.querySelector('.pagination-swiper-card-6') : null;
            if (paginationEl) {
                checkAndHidePagination(this, paginationEl);
            }
        }
    },
}); 

// Initialize swiper-card-7 with dynamic pagination from data attribute
var swiperCard7Elements = document.querySelectorAll(".swiper-card-7");
swiperCard7Elements.forEach(function(swiperEl) {
    var paginationSelector = swiperEl.getAttribute('data-pagination') || '.pagination-swiper-card-7';
    
    var swiperCard7Config = {
        slidesPerView: 1,
        slidesPerColumn: 2,
        slidesPerColumnFill: 'row',
        allowTouchMove: true,
        loop: false,   
        speed: 800,
        spaceBetween: 30,
        pagination: {
            el: paginationSelector,
            clickable: true,
        },
        breakpoints: {
            0: {
                slidesPerView: 1,
                allowTouchMove: true,
                slidesPerColumn: 2,
            }, 
            550: {
                slidesPerView: 1,
                allowTouchMove: true,
                slidesPerColumn: 2,
            },
            767: {
                slidesPerView: 2,
                allowTouchMove: true,
                slidesPerColumn: 2,
            },
            991: {
                slidesPerView: 3,
                allowTouchMove: true,
                slidesPerColumn: 2,
            },
            1440: {
                slidesPerView: 4,
                allowTouchMove: false,
                slidesPerColumn: 2,
            },
        },
        on: {
            init: function() {
                // Find pagination in the same container as this swiper
                var swiperEl = this.el;
                var paginationSelector = swiperEl.getAttribute('data-pagination');
                if (paginationSelector) {
                    var paginationEl = swiperEl.parentElement ? swiperEl.parentElement.querySelector(paginationSelector) : null;
                    if (paginationEl) {
                        checkAndHidePagination(this, paginationEl);
                    }
                }
            },
            resize: function() {
                // Find pagination in the same container as this swiper
                var swiperEl = this.el;
                var paginationSelector = swiperEl.getAttribute('data-pagination');
                if (paginationSelector) {
                    var paginationEl = swiperEl.parentElement ? swiperEl.parentElement.querySelector(paginationSelector) : null;
                    if (paginationEl) {
                        checkAndHidePagination(this, paginationEl);
                    }
                }
            }
        },
    };
    
    new Swiper(swiperEl, swiperCard7Config);
}); 

var swiper = new Swiper(".swiper-card-8", {
    slidesPerView: 1,
    slidesPerColumn: 2,
    slidesPerColumnFill: 'row',
    allowTouchMove: true,
    loop: false,   
    speed: 800,
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-card-8',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
            allowTouchMove: true,
            slidesPerColumn: 2,
        },  
        400: {
            slidesPerView: 2,
            allowTouchMove: true,
            slidesPerColumn: 2,
        },
        767: {
            slidesPerView: 3,
            allowTouchMove: true,
            slidesPerColumn: 2,
        },
        991: {
            slidesPerView: 4,
            allowTouchMove: true,
            slidesPerColumn: 2,
        }, 
    },
    on: {
        init: function() {
            // Find pagination in the same container as this swiper
            var swiperEl = this.el;
            var paginationEl = swiperEl.parentElement ? swiperEl.parentElement.querySelector('.pagination-swiper-card-8') : null;
            if (paginationEl) {
                checkAndHidePagination(this, paginationEl);
            }
        },
        resize: function() {
            // Find pagination in the same container as this swiper
            var swiperEl = this.el;
            var paginationEl = swiperEl.parentElement ? swiperEl.parentElement.querySelector('.pagination-swiper-card-8') : null;
            if (paginationEl) {
                checkAndHidePagination(this, paginationEl);
            }
        }
    },
}); 

// Helper function to get initialSlide from data attribute
function getInitialSlide(selector) {
    var element = document.querySelector(selector);
    if (element) {
        var initialSlide = element.getAttribute('data-initial-slide') || element.getAttribute('data-set-initialSlide');
        if (initialSlide !== null) {
            return parseInt(initialSlide, 10) || 0;
        }
    }
    return 0;
}

var swiperTestimoniorConfig = {
    slidesPerGroup: 1,
    freemode: true,
    slidesPerView: 1,
    speed: 800,  
    pagination: {
        el: '.pagination-swiper-testimonior',
        clickable: true,
    },
    spaceBetween: 30,
    breakpoints: {
        0: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        400: {
            slidesPerGroup: 1,
            slidesPerView: 1,
        },
        767: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        }, 
        991: {
            slidesPerView: 3,
            slidesPerGroup: 3,
        }, 
    }
};

// Get initialSlide from data attribute, default to 0
swiperTestimoniorConfig.initialSlide = getInitialSlide(".swiper-testimonior");

var swiper =  new Swiper(".swiper-testimonior", swiperTestimoniorConfig);
 

var swiper =  new Swiper(".swiper-testimonior-2", {
    loop: true,
    freemode: true,
    slidesPerView: 1, 
    slidesPerGroup: 1,
    speed: 800,  
    pagination: {
        el: '.pagination-swiper-testimonior-2',
        clickable: true,
    }, 
    spaceBetween: 30,
    breakpoints: {
        0: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        400: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        767: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        }, 
    }
});  

var swiper =  new Swiper(".swiper-outbrand", {
    slidesPerView: 1, 
    speed: 800, 
    pagination: {
        el: '.pagination-swiper-outbrand',
        clickable: true,
    },
    spaceBetween: 30,
    breakpoints: { 
        375: {
            slidesPerView: 2,
        },
        575: {
            slidesPerView: 2,
        },
        767: {
            slidesPerView: 4,
        }, 
        991: {
            slidesPerView: 5,
        },
        1280: {
            slidesPerView: 6,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-outbrand');
            checkAllowTouchMove(this);
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-outbrand');
            checkAllowTouchMove(this);
        }
    }
});  
 

var swiper =  new Swiper(".swiper-outbrand-3", {
    slidesPerView: 1,
    slidesPerColumn: 2,
    slidesPerColumnFill: 'row',
    loop: false,   
    speed: 800,
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-outbrand-3',
        clickable: true,
    },
    breakpoints: {
        375: {
            slidesPerView: 2,
            slidesPerColumn: 2,
        },
        575: {
            slidesPerView: 2,
            slidesPerColumn: 2,
        },
        767: {
            slidesPerView: 4,
            slidesPerColumn: 2,
        }, 
        991: {
            slidesPerView: 5,
            slidesPerColumn: 2,
        },
        1280: {
            slidesPerView: 6,
            slidesPerColumn: 2,
        },
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-outbrand-3');
            checkAllowTouchMove(this);
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-outbrand-3');
            checkAllowTouchMove(this);
        }
    }
});   

var swiper =  new Swiper(".swiper-outbrand-4", {
    slidesPerView: 1, 
    speed: 800, 
    pagination: {
        el: '.pagination-swiper-outbrand-4',
        clickable: true,
    },
    spaceBetween: 20,
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
            slidesPerGroup: 1,
        },
        600: {
            slidesPerView: 2,
            slidesPerGroup: 2,
        }, 
        991: {
            slidesPerView: 3,
            slidesPerGroup: 3,
        },
        1280: {
            slidesPerView: 5,
            slidesPerGroup: 5,
        },
        on: {
            init: function() {
                checkAndHidePagination(this, '.pagination-swiper-outbrand-4');
                checkAllowTouchMove(this);
            },
            resize: function() {
                checkAndHidePagination(this, '.pagination-swiper-outbrand-4');
                checkAllowTouchMove(this);
            }
        }
    }
});  

var swiper =  new Swiper(".swiper-news", {
    slidesPerView: 1, 
    speed: 800,  
    spaceBetween: 30,
    pagination: {
        el: '.pagination-swiper-news',
        clickable: true,
    },
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        },
        767: {
            slidesPerView: 2,
        }, 
        991: {
            slidesPerView: 3,
        }
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.pagination-swiper-news');
        },
        resize: function() {
            checkAndHidePagination(this, '.pagination-swiper-news');
        }
    }
});  

var swiper =  new Swiper(".swiper-news-2", {
    slidesPerView: 1, 
    speed: 3000,  
    spaceBetween: 30,
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        },
        767: {
            slidesPerView: 2,
        },
    },
    pagination: {
        el: ".swiper-news-2-pagination",
        clickable: true,
    },
    on: {
        init: function() {
            checkAndHidePagination(this, '.swiper-news-2-pagination');
        },
        resize: function() {
            checkAndHidePagination(this, '.swiper-news-2-pagination');
        }
    }
});  

var swiper =  new Swiper(".swiper-listing-details", {
    slidesPerView: 1,
    spaceBetween: 20, 
    loop: true,
    navigation: {
        nextEl: ".swiper-listing-details-next",
        prevEl: ".swiper-listing-details-prev",
    }, 
    speed: 2000,
    breakpoints: {
        0: {
            slidesPerView: 1,
        },
        400: {
            slidesPerView: 1,
        },
        767: {
            slidesPerView: 2,
        },
    }
}); 

var swiper =  new Swiper(".swiper-listing-details-4", {
    slidesPerView: 1,
    spaceBetween: 20, 
    loop: true,
    navigation: {
        nextEl: ".swiper-listing-details-4-next",
        prevEl: ".swiper-listing-details-4-prev",
    }, 
    pagination: {
        el: ".swiper-listing-details-4-pagination",
        clickable: true,
    },
    speed: 1000,
}); 

// Listing Details Main Slider with Thumbnails
var swiperThumbs = new Swiper(".swiper-listing-details-thumbs", {
    spaceBetween: 12,
    slidesPerView: 'auto',
    freeMode: false,
    watchSlidesProgress: true,
}); 

var pagithumbs2 = new Swiper(".swiper-listing-details-thumbs-style-2", {
    allowTouchMove: false,
    spaceBetween: 16,
    slidesPerView: 5,
    freeMode: true,
    watchSlidesProgress: true,
    direction: "vertical",
    navigation: {
        nextEl: ".swiper-listing-details-main-prev",
        prevEl: ".swiper-listing-details-main-next",
    },
    pagination: {
        el: ".pagination-swiper-listing-details-main-style-2",
        clickable: true,
    },
});

var swiperMain = new Swiper(".swiper-listing-details-main", {
    spaceBetween: 16,
    slidesPerView: 1,
    loop: false,
    initialSlide: 1,
    speed: 500,
    navigation: {
        nextEl: ".navigation-prev",
        prevEl: ".navigation-next",
    },
    thumbs: {
        swiper: swiperThumbs,
    },
});

var swiperMain2 = new Swiper(".swiper-listing-details-main-style-2", {
    spaceBetween: 16,
    slidesPerView: 1,
    loop: true,
    effect: "fade",
    fadeEffect: {
        crossFade: true,
    },
    initialSlide: 1,
    autoplay: {
        delay: 3000,
        disableOnInteraction: false,
    },
    pagination: {
        el: ".pagination-swiper-listing-details-main-style-2",
        clickable: true,
    },
    navigation: {
        nextEl: ".swiper-listing-details-main-next",
        prevEl: ".swiper-listing-details-main-prev",
    },
    speed: 1000, 
    thumbs: {
        swiper: pagithumbs2,
    },
});
 
// Listing Details Main Slider with Vertical Thumbnails (style-2)
var swiperThumbsVertical = new Swiper(".swiper-listing-details-main.style-2 .swiper-listing-details-thumbs", {
    spaceBetween: 12,
    slidesPerView: 4,
    direction: 'vertical',
    freeMode: false,
    watchSlidesProgress: true,
    breakpoints: {
        0: {
            direction: 'horizontal',
            slidesPerView: 4,
            spaceBetween: 8,
        },
        768: {
            direction: 'vertical',
            slidesPerView: 4,
            spaceBetween: 12,
        },
    }
});

var swiperThumbsVertical = new Swiper(".product-details-page .swiper-listing-details-thumbs", {
    spaceBetween: 20,
    slidesPerView: 'auto',
    freeMode: false,
    watchSlidesProgress: true,
});

var swiperListingDetails5Element = document.querySelector(".swiper-listing-details-5");
if (swiperListingDetails5Element) {
    // Find breadcrumb navigation buttons (specific to listing-details-5)
    var navNextBreadcrumb = document.querySelector(".swiper-listing-details-navigation .navigation-next");
    var navPrevBreadcrumb = document.querySelector(".swiper-listing-details-navigation .navigation-prev");
    
    // Find navigation buttons inside swiper container
    var navNextInside = swiperListingDetails5Element.querySelector(".navigation-next");
    var navPrevInside = swiperListingDetails5Element.querySelector(".navigation-prev");
    
    var swiperListingDetails5Config = {
        slidesPerView: 1,
        loop: false,
        speed: 800,  
        initialSlide: 1,
        spaceBetween: 20
    };
    
    // Use breadcrumb navigation buttons if available, otherwise use buttons inside swiper
    var navNext = navNextBreadcrumb || navNextInside;
    var navPrev = navPrevBreadcrumb || navPrevInside;
    
    if (navNext && navPrev) {
        swiperListingDetails5Config.navigation = {
            nextEl: navNext,
            prevEl: navPrev,
        };
    }
    
    var swiperListingDetails5 = new Swiper(".swiper-listing-details-5", swiperListingDetails5Config);
    
    // Bind both sets of navigation buttons to the same swiper (if both exist and are different)
    if (navNextBreadcrumb && navNextInside && navNextBreadcrumb !== navNextInside) {
        navNextInside.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            swiperListingDetails5.slideNext();
        });
    }
    if (navPrevBreadcrumb && navPrevInside && navPrevBreadcrumb !== navPrevInside) {
        navPrevInside.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            swiperListingDetails5.slidePrev();
        });
    }
    
    // If breadcrumb buttons exist but weren't used as primary, bind them manually too
    if (navNextBreadcrumb && navNextBreadcrumb !== navNext) {
        navNextBreadcrumb.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            swiperListingDetails5.slideNext();
        });
    }
    if (navPrevBreadcrumb && navPrevBreadcrumb !== navPrev) {
        navPrevBreadcrumb.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            swiperListingDetails5.slidePrev();
        });
    }
}

var navConfig = {};
if (document.querySelector(".swiper-btn.navigation-next") && document.querySelector(".swiper-btn.navigation-prev")) {
    navConfig = {
        nextEl: ".swiper-btn.navigation-next",
        prevEl: ".swiper-btn.navigation-prev",
    };
}

var swiperSingle = new Swiper(".sw-single", {
    loop: true,
    speed: 1000,
    fadeEffect: {
        crossFade: true,
    },
    pagination: {
        el: '.pagination-page-title--slider-1',
        clickable: true,
    },
    autoplay: {
        delay: 3000,
        disableOnInteraction: false,
    },
    parallax: true, 
    navigation: navConfig,
    on: {
        init: function () {
            var swiper = this; 

            if (true) {
                for (var i = 0; i < swiper.slides.length; i++) {
                    var $slide = $(swiper.slides[i]);
                    var $bg = $slide.find(".tp-showcase-slider-bg");
                    
                    // Set parallax
                    $bg.attr({
                        "data-swiper-parallax": 0.75 * swiper.width,
                    });
                    
                    // Set background-image from data-background
                    var bgImage = $bg.attr("data-background");
                    if (bgImage) {
                        $bg.css("background-image", "url(" + bgImage + ")");
                    }
                } 
            }
        }, 
        resize: function () {
            this.update();
        },
    },
}); 
 
  // Only initialize thumb slider if element exists
if (document.querySelector(".sw-single-thumb")) {
    swiperThumb = new Swiper(".sw-single-thumb", {
        effect: "fade",
        fadeEffect: {
            crossFade: true
        },
        slidesPerView: 1,
        allowTouchMove: false,
        speed: 2000,
    });

    // Sync 2 slider 2 - Only if both exist
    if (swiperSingle && swiperThumb) {
        swiperSingle.controller.control = swiperThumb;
        swiperThumb.controller.control = swiperSingle;
    }
}

function getTotalSlides(swiper) {
    if (!swiper || !swiper.slides) {
        return 0;
    }
    return swiper.slides.length;
}

function checkAllowTouchMove(swiper) {
    if (!swiper) return;
    
    var totalSlides = getTotalSlides(swiper);
    // Get current slidesPerView from Swiper instance
    var currentSlidesPerView = swiper.params.slidesPerView;
    
    // If total slides == slidesPerView, disable touch move
    if (totalSlides <= currentSlidesPerView) {
        swiper.allowTouchMove = false;
    } else {
        swiper.allowTouchMove = true;
    }
}