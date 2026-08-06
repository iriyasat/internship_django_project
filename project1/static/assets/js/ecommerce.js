(function () {
    "use strict";
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
    document.addEventListener("DOMContentLoaded", function () {
        const nav = document.getElementById('landing-nav');
        if (nav) {
            const syncNavState = () => nav.classList.toggle('scrolled', window.scrollY > 20);
            syncNavState();
            window.addEventListener('scroll', syncNavState);
        }
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
    document.addEventListener("click", function(e) {
        const link = e.target.closest('a[href*="/compare/"]');
        if (link && !link.search.includes('ids=')) {
            const ids = window.getCompareInventoryIds();
            if (ids && ids.length > 0) {
                e.preventDefault();
                const compareBase = (window.EcommerceConfig && window.EcommerceConfig.compareUrl) || '/compare/';
                window.location.href = `${compareBase}?ids=${ids.join(',')}`;
            }
        }
    });
    window.showEcomToast = function (message, type = 'success') {
        let toastContainer = document.getElementById('ecom-toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'ecom-toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        const bgClass = type === 'danger' ? 'bg-danger' : (type === 'info' ? 'bg-info' : 'bg-dark');
        const iconClass = type === 'danger' ? 'fa-triangle-exclamation' : (type === 'info' ? 'fa-circle-info' : 'fa-circle-check');
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white ${bgClass} border-0 show rounded-3 shadow-lg mb-2`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.innerHTML = `
            <div class="d-flex p-3 align-items-center">
                <i class="fa-solid ${iconClass} me-2 fs-5"></i>
                <div class="toast-body p-0 me-auto fw-semibold fs-6">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white ms-3" onclick="this.closest('.toast').remove()"></button>
            </div>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };

    window.toggleWishlistGlobal = function (vehicleId, btn) {
        if (!vehicleId) {
            console.error("toggleWishlistGlobal called with missing vehicleId");
            return;
        }
        const isWishlistPage = window.location.pathname.includes('/wishlist/');
        const wishlistUrl = (window.EcommerceConfig && window.EcommerceConfig.apiToggleWishlistUrl) || '/api/wishlist/toggle/';
        
        if (btn) btn.disabled = true;

        fetch(wishlistUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                vehicle_id: vehicleId,
                inventory_id: vehicleId,
                action: isWishlistPage ? 'delete' : undefined
            })
        })
        .then(res => res.json())
        .then(data => {
            if (btn) btn.disabled = false;
            if (data.success) {
                const countEl = document.getElementById('nav-wishlist-count');
                const countElMobile = document.getElementById('nav-wishlist-count-mobile');
                if (countEl) countEl.innerText = data.wishlist_count;
                if (countElMobile) countElMobile.innerText = data.wishlist_count;

                if (btn) {
                    const cardCol = btn.closest('.col-lg-3, .col-md-4, .col-sm-6, .vehicle-card-hover, .card');
                    if (cardCol && (!data.added || isWishlistPage)) {
                        cardCol.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                        cardCol.style.opacity = '0';
                        cardCol.style.transform = 'scale(0.85)';

                        setTimeout(() => {
                            cardCol.remove();
                            if (isWishlistPage) {
                                const remainingCards = document.querySelectorAll('.container.mb-5 .col-lg-3, .container.mb-5 .col-md-4, .container.mb-5 .card-img-top');
                                if (remainingCards.length === 0) {
                                    const container = document.querySelector('.container.mb-5');
                                    if (container) {
                                        container.innerHTML = `
                                            <div class="card border-0 shadow-sm rounded-4 p-5 text-center bg-white">
                                                <i class="fa-regular fa-heart display-1 text-muted mb-3"></i>
                                                <h4 class="fw-bold">No Saved Vehicles in Wishlist</h4>
                                                <p class="text-muted">Click the heart icon on any vehicle card in the catalog to save it to your wishlist.</p>
                                                <div>
                                                    <a href="/catalog/" class="btn btn-primary rounded-pill px-4 fw-bold py-2">
                                                        <i class="fa-solid fa-car me-2"></i> Browse Vehicle Catalog
                                                    </a>
                                                </div>
                                            </div>
                                        `;
                                    }
                                }
                            }
                        }, 300);
                    } else {
                        const icon = btn.querySelector('.fa-heart, i');
                        if (icon) {
                            if (data.added) {
                                icon.className = 'fa-solid fa-heart text-danger';
                            } else {
                                icon.className = 'fa-regular fa-heart';
                            }
                        }
                    }
                }
                showEcomToast(data.message, data.added ? 'success' : 'info');
            } else {
                showEcomToast(data.error || "Failed to update wishlist", 'danger');
            }
        })
        .catch(err => {
            if (btn) btn.disabled = false;
            showEcomToast("Network error. Please try again.", 'danger');
        });
    };

    window.addToCartGlobal = function (inventoryId, btn) {
        const cartUrl = (window.EcommerceConfig && window.EcommerceConfig.apiAddToCartUrl) || '/api/cart/add/';
        if (btn) btn.disabled = true;
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
            if (btn) btn.disabled = false;
            if (data.success) {
                const countEl = document.getElementById('nav-cart-count');
                const countElMobile = document.getElementById('nav-cart-count-mobile');
                if (countEl) countEl.innerText = data.cart_count;
                if (countElMobile) countElMobile.innerText = data.cart_count;
                showEcomToast(data.message, 'success');
            } else {
                showEcomToast(data.error || "Failed to add to cart", 'danger');
            }
        })
        .catch(err => {
            if (btn) btn.disabled = false;
            showEcomToast("Network error. Please try again.", 'danger');
        });
    };
})();
