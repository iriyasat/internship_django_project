window.console =
  window.console ||
  (function () {
    var e = {};
    e.log =
      e.warn =
      e.debug =
      e.info =
      e.error =
      e.time =
      e.dir =
      e.profile =
      e.clear =
      e.exception =
      e.trace =
      e.assert =
        function () {};
    return e;
  })();

  $(document).ready(function () {
    var e =
      '<div class="switcher-container">' + 
      '<h2>Setting<a href="#" class="sw-click"><img src="assets/icons/icon_setting.svg" class="setting setting_dark"></img><img src="assets/icons/icon_setting_white.svg" class="setting setting_light"></img></a></h2>' +
      '<div class="selector-box">' +
      '<div class="clearfix"></div>' +
      '<div class="sw-odd"><h3>Mode: <span class="light_mode">Light Mode</span><span class="dark_mode">Dark Mode</span></h3>' +
      '<div class="ws-colors">' +
      '<a href="#" class="dark sw-click">Dark Mode</a> '+ 
      '<a href="#" class="light sw-click is_active">Light Mode</a> ' 
      "</div></div>" + 
      '<div class="clearfix"></div>' +
      "</div>" +
      "</div>";
    $("body").append(e);
    switchAnimate.loadEvent();
    switchColor.loadEvent();
    switchThemeMode.loadEvent();
    $( "#cursor_style" ).on( "change", function() {
      if(this.value == 1) {
        $(".cursor1").remove();
        $(".cursor2").remove();
      } else if(this.value == 2){
        var script = document.createElement('script');
        var script2 = document.createElement('script');
        script.src = 'app/js/gsap.min.js';
        script2.src = 'app/js/cursor-mouse.js'; 
        $("body").append('<div class="cursor1"></div>');
        $("body").append('<div class="cursor2"></div>');
        document.body.appendChild(script);
        document.body.appendChild(script2);
      }
  
    });
  });




var switchColor = {
  colorObj: {
    colorCookie: "colorCookie",
    switchClass: ".styleswitch",
    currentClass: "current",
    headLink: "head link[id=colors]",
    colorItem: ".ws-colors a.styleswitch",
    reset: "#reset",
    defaultColor: "color1",
  },
  loadEvent: function () {
    var e = switchColor.colorObj;
    if ($.cookie(e.colorCookie)) {
      switchColor.setColor($.cookie(e.colorCookie));
    } else {
      switchColor.setColor(e.defaultColor);
    }
    $(e.colorItem).on("click", function () {
      var e = $(this).attr("id");
      switchColor.setColor(e);
    });
    $(e.reset).on("click", function () {
      switchColor.setColor(e.defaultColor);
    });
  },
  setColor: function (e) {
    var t = switchColor.colorObj;
    $.cookie(t.colorCookie, e);
    $(t.headLink).attr("href", "stylesheets/colors/" + e + ".css");

    $(t.switchClass).removeClass(t.currentClass);
    $("#" + e).addClass(t.currentClass);

    //set color for text in content
    if ($(".infomation.text-center h3").length === 1) {
      var hiText = $(".infomation.text-center h3")
        .closest(".section")
        .css("background-color")
        .toString();
      if (hiText === "rgb(91, 91, 91)")
        $(".infomation.text-center h3").css("color", "#fff");
    }
  },
};

var switchAnimate = {
  loadEvent: function () {
    $(".switcher-container h2 a.sw-click").on("click", function (e) {
      var t = $(".switcher-container");

      if (t.css("right") === "-290px") {
        $(".switcher-container").animate({ right: "0" }, 300, "easeInOutExpo");
      } else {
        $(".switcher-container").animate(
          { right: "-290px" },
          300,
          "easeInOutExpo"
        );
      }

      e.preventDefault();
    });
  },
};

var switchThemeMode = {
  themeCookie: "themeMode",
  defaultTheme: "light",
  
  loadEvent: function () {
    // Load saved theme or use default
    var savedTheme = $.cookie(switchThemeMode.themeCookie) || switchThemeMode.defaultTheme;
    switchThemeMode.setTheme(savedTheme);
    
    // Bind click events for dark/light buttons
    $(document).on("click", ".ws-colors a.dark.sw-click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      switchThemeMode.setTheme("dark");
    });
    
    $(document).on("click", ".ws-colors a.light.sw-click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      switchThemeMode.setTheme("light");
    });
  },
  
  setTheme: function (theme) {
    var $body = $("body");
    var $html = $("html");
    
    // Remove existing theme classes
    $body.removeClass("is_dark is_light");
    $html.removeClass("is_dark is_light");
    
    // Add new theme class
    if (theme === "dark") {
      $body.addClass("is_dark");
      $html.addClass("is_dark");
    } else {
      $body.addClass("is_light");
      $html.addClass("is_light");
    }
    
    // Save to cookie
    $.cookie(switchThemeMode.themeCookie, theme, { expires: 365 });
    
    // Update button active states
    $(".ws-colors a.dark, .ws-colors a.light").removeClass("is_active");
    $(".ws-colors a." + theme).addClass("is_active");
    
    // Update setting icons visibility
    if (theme === "dark") {
      $(".setting.setting_dark").css("display", "block");
      $(".setting.setting_light").css("display", "none");
    } else {
      $(".setting.setting_dark").css("display", "none");
      $(".setting.setting_light").css("display", "block");
    }
    
    // Update mode text visibility
    if (theme === "dark") {
      $(".sw-odd .light_mode").hide();
      $(".sw-odd .dark_mode").show();
    } else {
      $(".sw-odd .light_mode").show();
      $(".sw-odd .dark_mode").hide();
    }
    
    // Update logo in header (only desktop logo, exclude mobile logo)
    // Target: .logo img but exclude .logo-mobile img
    var $headerLogos = $(".header .logo img, header .logo img").filter(function() {
      // Exclude images inside .logo-mobile
      return !$(this).closest(".logo-mobile").length;
    });
    
    if (theme === "dark") {
      // Change to white logo
      $headerLogos.each(function() {
        var $img = $(this);
        var currentSrc = $img.attr("src");
        // Only change if it's logo.png (not logo-white.png already)
        if (currentSrc && currentSrc.indexOf("logo.png") !== -1 && currentSrc.indexOf("logo-white.png") === -1) {
          var newSrc = currentSrc.replace("logo.png", "logo-white.png");
          $img.attr("src", newSrc);
        }
      });
    } else {
      // Change back to regular logo
      $headerLogos.each(function() {
        var $img = $(this);
        var currentSrc = $img.attr("src");
        // Only change if it's logo-white.png
        if (currentSrc && currentSrc.indexOf("logo-white.png") !== -1) {
          var newSrc = currentSrc.replace("logo-white.png", "logo.png");
          $img.attr("src", newSrc);
        }
      });
    }
    
    // Update icons for dark/light mode
    // Icon mapping: original -> dark version
    var iconMapping = {
      "icon-gauge.svg": "icon-gauge-2.svg",
      "calendar.svg": "calendar-2.svg",
      "gaspump.svg": "gaspump-2.svg",
      "manual.svg": "manual-2.svg",
      "auto.svg": "auto-2.svg",
      "palette.svg": "palette-muted.svg",
      "MapPin.svg": "MapPin-2.svg",
      "Seatbelt.svg": "Seatbelt-2.svg",
      "Frame.svg": "Frame-2.svg",
      "transmission-2.svg": "transmission-3.svg",
      "Barcode.svg": "Barcode-2.svg",
      "QrCode.svg": "QrCode-2.svg",
      "PhoneCall.svg": "PhoneCall-4.svg",
      "line.svg": "line-white.svg",
      "Alarm-white.svg": "Alarm-white-2.svg",
      "star-4.svg": "star-4-white.svg",
      "location.svg": "location-2.svg",
      "ApplePay.svg": "ApplePay-white.svg",
      "clear.svg": "clear-white.svg",
      "input-facebook.svg": "input-facebook-2.svg",
      "input-skype.svg": "input-skype-2.svg",
      "input-x.svg": "input-x-2.svg",
      "input-instagram.svg": "input-instagram-2.svg",
      "input-youtube.svg": "input-youtube-2.svg",
      "input-telegram.svg": "input-telegram-2.svg",
    };
    
    // Reverse mapping for light mode
    var reverseIconMapping = {
      "icon-gauge-2.svg": "icon-gauge.svg",
      "calendar-2.svg": "calendar.svg",
      "gaspump-2.svg": "gaspump.svg",
      "manual-2.svg": "manual.svg",
      "auto-2.svg": "auto.svg",
      "palette-muted.svg": "palette.svg",
      "MapPin-2.svg": "MapPin.svg",
      "Seatbelt-2.svg": "Seatbelt.svg",
      "Frame-2.svg": "Frame.svg",
      "transmission-3.svg": "transmission-2.svg",
      "Barcode-2.svg": "Barcode.svg",
      "QrCode-2.svg": "QrCode.svg",
      "PhoneCall-4.svg": "PhoneCall.svg",
      "line-white.svg": "line.svg",
      "Alarm-white-2.svg": "Alarm-white.svg",
      "star-4-white.svg": "star-4.svg",
      "location-2.svg": "location.svg",
      "ApplePay-white.svg": "ApplePay.svg",
      "clear-white.svg": "clear.svg",
      "input-facebook-2.svg": "input-facebook.svg",
      "input-skype-2.svg": "input-skype.svg",
      "input-x-2.svg": "input-x.svg",
      "input-instagram-2.svg": "input-instagram.svg",
      "input-youtube-2.svg": "input-youtube.svg",
      "input-telegram-2.svg": "input-telegram.svg",
    };
    
    // Find all images with these icons (exclude images inside .core-dropdown)
    var $allImages = $("img").filter(function() {
      // Exclude images inside .core-dropdown
      return !$(this).closest(".core-dropdown").length;
    });
    
    if (theme === "dark") {
      // Change icons to dark version
      $allImages.each(function() {
        var $img = $(this);
        var currentSrc = $img.attr("src");
        if (currentSrc) {
          // Check each icon mapping
          for (var originalIcon in iconMapping) {
            if (currentSrc.indexOf(originalIcon) !== -1 && currentSrc.indexOf(iconMapping[originalIcon]) === -1) {
              var newSrc = currentSrc.replace(originalIcon, iconMapping[originalIcon]);
              $img.attr("src", newSrc);
              break; // Only replace once per image
            }
          }
        }
      });
    } else {
      // Change icons back to light version
      $allImages.each(function() {
        var $img = $(this);
        var currentSrc = $img.attr("src");
        if (currentSrc) {
          // Check each reverse icon mapping
          for (var darkIcon in reverseIconMapping) {
            if (currentSrc.indexOf(darkIcon) !== -1) {
              var newSrc = currentSrc.replace(darkIcon, reverseIconMapping[darkIcon]);
              $img.attr("src", newSrc);
              break; // Only replace once per image
            }
          }
        }
      });
    }
  }
};


