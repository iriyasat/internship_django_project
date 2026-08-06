/* ==========================================================================
   Automobile E-Commerce Master JavaScript
   Centralized JS for Navbar, Mobile Drawer, Cart, Wishlist & Compare
   ========================================================================== */

(function () {
    "use strict";

    // ─── API Logger Interceptor for Browser Console ───
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url ? args[0].url : '');
        const response = await originalFetch.apply(this, args);
        if (url && url.includes('/api/')) {
            try {
                const clone = response.clone();
                const data = await clone.json();
                console.log(`🚀 [API Data] ${url}:`, data);
            } catch (e) {
                console.log(`🚀 [API Request] ${url} Status: ${response.status}`);
            }
        }
        return response;
    };

    // ─── Helper: Get CSRF Cookie ───
    window.getCookie = function (name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    // ─── Navigation Scroll State ───
    document.addEventListener("DOMContentLoaded", function () {
        const nav = document.getElementById('landing-nav');
        if (nav) {
            const syncNavState = () => nav.classList.toggle('scrolled', window.scrollY > 20);
            syncNavState();
            window.addEventListener('scroll', syncNavState);
        }

        // ─── Mobile Drawer Navigation ───
        const mobileToggle  = document.getElementById('mobile-menu-toggle');
        const mobileDrawer  = document.getElementById('mobile-nav-drawer');
        const mobileOverlay = document.getElementById('mobile-nav-overlay');
        const mobileClose   = document.getElementById('mobile-drawer-close');

        function openMobileDrawer() {
            if (!mobileDrawer) return;
            mobileDrawer.classList.add('is-open');
            if (mobileOverlay) mobileOverlay.classList.add('is-visible');
            if (mobileToggle) mobileToggle.setAttribute('aria-expanded', 'true');
            mobileDrawer.setAttribute('aria-hidden', 'false');
            if (mobileOverlay) mobileOverlay.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        }

        function closeMobileDrawer() {
            if (!mobileDrawer) return;
            mobileDrawer.classList.remove('is-open');
            if (mobileOverlay) mobileOverlay.classList.remove('is-visible');
            if (mobileToggle) mobileToggle.setAttribute('aria-expanded', 'false');
            mobileDrawer.setAttribute('aria-hidden', 'true');
            if (mobileOverlay) mobileOverlay.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }

        if (mobileToggle) mobileToggle.addEventListener('click', openMobileDrawer);
        if (mobileClose)  mobileClose.addEventListener('click', closeMobileDrawer);
        if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileDrawer);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeMobileDrawer();
        });

        // ─── Mobile Footer Accordion Toggle ───
        document.querySelectorAll('.collapse-title[data-breakpoint="mobile"]').forEach(title => {
            title.addEventListener('click', () => {
                const content = title.nextElementSibling;
                const icon = title.querySelector('.icon');
                if (content && content.classList.contains('collapse-content')) {
                    content.classList.toggle('md-hidden');
                    if (icon) {
                        icon.innerText = content.classList.contains('md-hidden') ? '+' : '−';
                    }
                }
            });
        });

        // ─── Compare Nav Link Click Handler ───
        const compareNavLink = document.getElementById("nav-compare-link");
        if (compareNavLink) {
            compareNavLink.addEventListener("click", function (e) {
                const ids = getCompareInventoryIds();
                if (ids.length === 0) return;
                e.preventDefault();
                const compareBase = (window.EcommerceConfig && window.EcommerceConfig.compareUrl) || '/compare/';
                window.location.href = `${compareBase}?ids=${ids.join(",")}`;
            });
        }

        // ─── Footer Newsletter Subscription Form ───
        const footerForm = document.querySelector('.form-footer');
        if (footerForm) {
            footerForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const emailInput = document.getElementById('footer-email');
                const email = emailInput ? emailInput.value : '';
                const sendUrl = (window.EcommerceConfig && window.EcommerceConfig.apiSendSuperuserMessageUrl) || '/api/superuser-message/';

                fetch(sendUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken")
                    },
                    body: JSON.stringify({ email: email })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        if (emailInput) emailInput.value = '';
                    } else {
                        alert(data.error || "Failed to submit inquiry.");
                    }
                });
            });
        }

        updateCompareBadge();
    });

    // ─── Global Compare Storage & Logic ───
    const COMPARE_STORAGE_KEY = "compare_inventory_ids";
    const MAX_COMPARE_ITEMS = 4;

    window.getCompareInventoryIds = function () {
        try {
            const parsed = JSON.parse(localStorage.getItem(COMPARE_STORAGE_KEY) || "[]");
            if (!Array.isArray(parsed)) return [];
            return parsed
                .map((id) => Number(id))
                .filter((id) => Number.isInteger(id) && id > 0);
        } catch (e) {
            return [];
        }
    };

    window.setCompareInventoryIds = function (ids) {
        localStorage.setItem(COMPARE_STORAGE_KEY, JSON.stringify(ids));
        updateCompareBadge();
    };

    window.updateCompareBadge = function () {
        const countEl = document.getElementById("nav-compare-count");
        const countElMobile = document.getElementById("nav-compare-count-mobile");
        const count = String(window.getCompareInventoryIds().length);
        if (countEl) countEl.innerText = count;
        if (countElMobile) countElMobile.innerText = count;
    };

    window.addToCompareGlobal = function (inventoryId, redirectToCompare = false) {
        const id = Number(inventoryId);
        if (!Number.isInteger(id) || id <= 0) return;

        const ids = window.getCompareInventoryIds();
        const compareBase = (window.EcommerceConfig && window.EcommerceConfig.compareUrl) || '/compare/';

        if (ids.includes(id)) {
            alert("Vehicle is already in compare list.");
            if (redirectToCompare) {
                window.location.href = `${compareBase}?ids=${ids.join(",")}`;
            }
            return;
        }
        if (ids.length >= MAX_COMPARE_ITEMS) {
            alert("You can compare a maximum of 4 vehicles.");
            return;
        }

        ids.push(id);
        window.setCompareInventoryIds(ids);
        alert("Vehicle added to compare list.");
        if (redirectToCompare) {
            window.location.href = `${compareBase}?ids=${ids.join(",")}`;
        }
    };

    window.removeFromCompareGlobal = function (inventoryId, refreshPage = true) {
        const id = Number(inventoryId);
        const ids = window.getCompareInventoryIds().filter((item) => item !== id);
        window.setCompareInventoryIds(ids);
        if (refreshPage) {
            const compareBase = (window.EcommerceConfig && window.EcommerceConfig.compareUrl) || '/compare/';
            const target = ids.length ? `${compareBase}?ids=${ids.join(",")}` : compareBase;
            window.location.href = target;
        }
    };

    // ─── Global Wishlist Toggle Function ───
    window.toggleWishlistGlobal = function (vehicleId, btn) {
        const wishlistUrl = (window.EcommerceConfig && window.EcommerceConfig.apiToggleWishlistUrl) || '/api/wishlist/toggle/';
        fetch(wishlistUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ vehicle_id: vehicleId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const countEl = document.getElementById('nav-wishlist-count');
                const countElMobile = document.getElementById('nav-wishlist-count-mobile');
                if (countEl) countEl.innerText = data.wishlist_count;
                if (countElMobile) countElMobile.innerText = data.wishlist_count;
                alert(data.message);
            } else {
                alert(data.error || "Failed to update wishlist");
            }
        });
    };

    // ─── Global Add to Cart Function ───
    window.addToCartGlobal = function (inventoryId, btn) {
        const cartUrl = (window.EcommerceConfig && window.EcommerceConfig.apiAddToCartUrl) || '/api/cart/add/';
        fetch(cartUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ inventory_id: inventoryId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const countEl = document.getElementById('nav-cart-count');
                const countElMobile = document.getElementById('nav-cart-count-mobile');
                if (countEl) countEl.innerText = data.cart_count;
                if (countElMobile) countElMobile.innerText = data.cart_count;
                alert(data.message);
            } else {
                alert(data.error || "Failed to add to cart");
            }
        });
    };
})();
