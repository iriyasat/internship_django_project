var CART_STORAGE_KEY = 'shopping_cart_items';
var FAVORITES_STORAGE_KEY = 'shop_favorites';

// Product data for shop page (loaded from product.json)
var shopAllProducts = [];
var shopProductsMap = {};
var $shopProductList = null;
var $shopProductTemplate = null;
		
// Initialize cart (no default items)
function initializeDefaultItems() {
    // Ensure localStorage is initialized with an empty array
    var items = getCartItems();
    if (!Array.isArray(items)) {
        saveCartItems([]);
    }
}

// Get items from localStorage
function getCartItems() {
    var items = localStorage.getItem(CART_STORAGE_KEY);
    return items ? JSON.parse(items) : [];
}

// Save items to localStorage
function saveCartItems(items) {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
}

// Render cart items into HTML
function renderCartItems() {
    var items = getCartItems();
    var $yourOrder = $('.your-order');
    $yourOrder.empty();
    
    if (items.length === 0) {
        return;
    }
    
    items.forEach(function(item) {
        var itemHtml = 
        '<div class="order-item style-2" data-item-id="' + item.id + '">' +
            '<div class="flex items-center gap-24">' +
                '<img class="order-item-img" src="' + item.image + '" alt="' + item.name + '">' +
                '<div>' +
                    '<a href="shop.html" class="font-weight-600 mb-12 clamp-1 clamp">' + item.name + '</a>' +
                    '<p class="font-weight-600">' + item.quantity + ' X $' + item.price.toFixed(2) + '</p>' +
                '</div>' +
            '</div>' +
            '<a href="#" class="remove-item font-weight-600 text-underline cursor-pointer">Remove</a>' +
        '</div>';
        $yourOrder.append(itemHtml);
    });
    
    updateSubtotal();
}

// Render shopping cart items into #shopCartItems (for shopping-cart.html page)
function renderShoppingCartItems() {
    var $shopCartItems = $('#shopCartItems');
    if (!$shopCartItems.length) {
        return;
    }
    
    var items = getCartItems();
    
    // If no items in localStorage, keep default HTML (do nothing)
    if (items.length === 0) {
        return;
    }
    
    // Clear existing items and render from localStorage
    $shopCartItems.empty();
    
    items.forEach(function(item) {
        var totalPrice = item.price * item.quantity;
        var itemHtml = 
            '<div class="cart-item" data-item-id="' + item.id + '">' +
                '<div class="cart-item__product">' +
                    '<div class="cart-item__image">' +
                        '<img src="' + item.image + '" alt="' + item.name + '">' +
                    '</div>' +
                    '<div class="cart-item__name">' +
                        '<a href="#" class="font-weight-600">' + item.name + '</a>' +
                    '</div>' +
                '</div>' +
                '<div class="cart-item__price">' +
                    '<span class="price">$' + item.price.toFixed(2) + '</span>' +
                '</div>' +
                '<div class="cart-item__quantity">' +
                    '<div class="quantity-selector">' +
                        '<button type="button" class="quantity-selector__btn quantity-selector__btn--minus flex">' +
                            '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                                '<path d="M5 12H19" stroke="#1C1C1C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
                            '</svg>' +
                        '</button>' +
                        '<input class="quantity-selector__value" value="' + item.quantity + '" type="number" min="0" data-item-id="' + item.id + '">' +
                        '<button type="button" class="quantity-selector__btn quantity-selector__btn--plus flex">' +
                            '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                                '<path d="M12 5V19" stroke="#1C1C1C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
                                '<path d="M5 12H19" stroke="#1C1C1C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
                            '</svg>' +
                        '</button>' +
                    '</div>' +
                '</div>' +
                '<div class="cart-item__total">' +
                    '<span class="total-price">' + item.quantity + ' X $' + totalPrice.toFixed(2) + '</span>' +
                '</div>' +
                '<div class="cart-item__action">' +
                    '<button type="button" class="cart-item__remove" aria-label="Remove item" data-item-id="' + item.id + '">' +
                        '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                            '<path d="M9.64052 9.1099C9.67536 9.14474 9.703 9.1861 9.72186 9.23162C9.74071 9.27714 9.75042 9.32594 9.75042 9.37521C9.75042 9.42448 9.74071 9.47327 9.72186 9.5188C9.703 9.56432 9.67536 9.60568 9.64052 9.64052C9.60568 9.67536 9.56432 9.703 9.5188 9.72186C9.47327 9.74071 9.42448 9.75042 9.37521 9.75042C9.32594 9.75042 9.27714 9.74071 9.23162 9.72186C9.1861 9.703 9.14474 9.67536 9.1099 9.64052L6.00021 6.53036L2.89052 9.64052C2.82016 9.71089 2.72472 9.75042 2.62521 9.75042C2.5257 9.75042 2.43026 9.71089 2.3599 9.64052C2.28953 9.57016 2.25 9.47472 2.25 9.37521C2.25 9.2757 2.28953 9.18026 2.3599 9.1099L5.47005 6.00021L2.3599 2.89052C2.28953 2.82016 2.25 2.72472 2.25 2.62521C2.25 2.5257 2.28953 2.43026 2.3599 2.3599C2.43026 2.28953 2.5257 2.25 2.62521 2.25C2.72472 2.25 2.82016 2.28953 2.89052 2.3599L6.00021 5.47005L9.1099 2.3599C9.18026 2.28953 9.2757 2.25 9.37521 2.25C9.47472 2.25 9.57016 2.28953 9.64052 2.3599C9.71089 2.43026 9.75042 2.5257 9.75042 2.62521C9.75042 2.72472 9.71089 2.82016 9.64052 2.89052L6.53036 6.00021L9.64052 9.1099Z" fill="#1C1C1C"/>' +
                        '</svg>' +
                    '</button>' +
                '</div>' +
            '</div>';
        $shopCartItems.append(itemHtml);
    });
    
    updateShoppingCartSubtotal();
}

// Update subtotal in shopping-cart.html page
function updateShoppingCartSubtotal() {
    var items = getCartItems();
    var total = 0;
    
    items.forEach(function(item) {
        total += item.price * item.quantity;
    });
    
    // Update subtotal in Order Summary section
    $('.send-inquiry p.flex.justify-between').each(function() {
        var $p = $(this);
        var firstSpan = $p.find('span').first().text().trim();
        if (firstSpan === 'Subtotal') {
            $p.find('span').last().text('$' + total.toFixed(2));
        }
    });
}

// Remove item from localStorage and re-render
function removeCartItem(itemId) {
    var items = getCartItems();
    items = items.filter(function(item) {
        return item.id !== itemId;
    });
    saveCartItems(items);
    renderCartItems();
}

// Add item to localStorage and re-render
function addCartItem(itemData) {
    var items = getCartItems();

    // Ensure item has an id
    if (!itemData.id) {
        itemData.id = 'item-' + Date.now();
    }

    // Ensure minimum quantity is 1
    if (!itemData.quantity || itemData.quantity < 1) {
        itemData.quantity = 1;
    }

    // Check if the same product (name + price + image) already exists
    var existingItem = items.find(function(item) {
        return item.name === itemData.name &&
            item.price === itemData.price &&
            item.image === itemData.image;
    });

    if (existingItem) {
        // Increase quantity if it already exists
        existingItem.quantity += itemData.quantity || 1;
    } else {
        // Otherwise push as a new item
        items.push(itemData);
    }

    saveCartItems(items);
    renderCartItems();
}

// Remove item in shopping cart (with animation and close modal when empty)
$(document).on('click', '.your-order .remove-item', function(e) {
    e.preventDefault();
    
    var $removeLink = $(this);
    var $orderItem = $removeLink.closest('.order-item');
    var itemId = $orderItem.data('item-id');
    
    // Fade out item first, then remove from storage
    $orderItem.fadeOut(300, function() {
        // Remove from localStorage
        removeCartItem(itemId);
        
        // Check remaining items
        var remainingItems = getCartItems().length;
        
        // If no items left, close modal
        if (remainingItems === 0) {
            var $modal = $('#ShoppingCartModal');
            if ($modal.length) {
                $modal.find('.close-modal').first().trigger('click');
            }
        }
    });
});

// Remove item from shopping cart page (#shopCartItems)
$(document).on('click', '#shopCartItems .cart-item__remove', function(e) {
    e.preventDefault();
    
    var $removeBtn = $(this);
    var $cartItem = $removeBtn.closest('.cart-item');
    var itemId = $removeBtn.data('item-id') || $cartItem.data('item-id');
    
    if (!itemId) {
        return;
    }
    
    // Fade out item first, then remove from storage
    $cartItem.fadeOut(300, function() {
        removeCartItem(itemId);
        renderShoppingCartItems(); // Re-render shopping cart
    });
});

// Update quantity in shopping cart page
function updateCartItemQuantity(itemId, newQuantity) {
    var items = getCartItems();
    var item = items.find(function(i) {
        return i.id === itemId;
    });
    
    if (!item) {
        return;
    }
    
    if (newQuantity <= 0) {
        // Remove item if quantity is 0 or less
        removeCartItem(itemId);
        renderShoppingCartItems();
        return;
    }
    
    item.quantity = newQuantity;
    saveCartItems(items);
    renderShoppingCartItems();
}

// Handle quantity changes in shopping cart page
$(document).on('click', '#shopCartItems .quantity-selector__btn--plus', function() {
    var $input = $(this).siblings('.quantity-selector__value');
    var itemId = $input.data('item-id');
    var currentValue = parseInt($input.val()) || 0;
    var newValue = currentValue + 1;
    
    $input.val(newValue);
    
    if (itemId) {
        updateCartItemQuantity(itemId, newValue);
    }
});

$(document).on('click', '#shopCartItems .quantity-selector__btn--minus', function() {
    var $input = $(this).siblings('.quantity-selector__value');
    var itemId = $input.data('item-id');
    var currentValue = parseInt($input.val()) || 0;
    
    if (currentValue > 0) {
        var newValue = currentValue - 1;
        $input.val(newValue);
        
        if (itemId) {
            updateCartItemQuantity(itemId, newValue);
        }
    }
});

// Handle manual quantity input change in shopping cart page
$(document).on('change', '#shopCartItems .quantity-selector__value', function() {
    var $input = $(this);
    var itemId = $input.data('item-id');
    var value = parseInt($input.val()) || 0;
    
    if (value < 0) {
        $input.val(0);
        value = 0;
    }
    
    if (itemId) {
        updateCartItemQuantity(itemId, value);
    }
});

// Helper: get product data from a `.product` card
function getProductDataFromCard($product) {
    // Prefer JSON data when card has a mapped data-product-id
    var productId = $product.data('product-id') || $product.attr('data-product-id');
    if (productId && shopProductsMap && shopProductsMap[productId]) {
        var p = shopProductsMap[productId];
        return {
            id: productId,
            name: p.name || p.title || 'Product',
            promotion: p.promotion || '',
            image: p.image || '/assets/images/shop/product-1.jpg',
            price: Number(p.price) || 0
        };
    }

    // Prefer common title classes
    var productName = $product.find('.h7, .product-name, .product-title').first().text().trim();

    // Fallback to other typical name locations
    if (!productName) {
        productName = $product.find('.cart-item__name a, a.font-weight-600').first().text().trim();
    }

    // Otherwise, use the first link that is not an action/add-to-cart button
    if (!productName) {
        productName = $product
            .find('a')
            .filter(function () {
                var $el = $(this);
                var text = $el.text().trim().toLowerCase();
                return !$el.hasClass('product-add-to-cart') &&
                    !$el.hasClass('action') &&
                    text !== 'add to cart' &&
                    text !== 'view details';
            })
            .first()
            .text()
            .trim();
    }

    // Last fallback: use h5/h6 if present
    if (!productName) {
        productName = $product.find('h5, h6').first().text().trim();
    }

    if (!productName) {
        productName = 'Product';
    }

    var productImage =
        $product.find('.product-top img, .img img').first().attr('src') ||
        './assets/images/shop/product-1.jpg';

    var productPriceMatch = $product.find('.price').first().text().match(/\$([\d,]+\.?\d*)/);
    var price = productPriceMatch ? parseFloat(productPriceMatch[1].replace(/,/g, '')) : 0;

    // Get productId if not already set
    if (!productId) {
        productId = $product.attr('data-product-id') || $product.data('product-id');
    }

    return {
        id: productId || null,
        name: productName,
        image: productImage,
        price: price,
    };
}

// When opening Quick View, store product data on the modal
$(document).on('click', '.product .action.open-modal[data-modal-id="#QuickViewModal"], .product-add-to-cart.open-modal[data-modal-id="#QuickViewModal"]', function() {
    var $product = $(this).closest('.product');
    var data = getProductDataFromCard($product);

    var $modal = $('#QuickViewModal');
    var productId = data.id || $product.attr('data-product-id') || $product.data('product-id');
    
    // Store product data on modal
    $modal.data('product-id', productId);
    $modal.data('product-name', data.name);
    $modal.data('product-image', data.image);
    $modal.data('product-price', data.price);
    
    // Get position in list
    var $productList = $product.closest('#product-list, .product-list');
    var position = $productList.length ? $productList.find('.product').index($product) : null;
    $modal.data('product-position', position);
    
    // Check and update heart icon in modal
    setTimeout(function() {
        var $modalHeart = $modal.find('.bth-heart');
        if ($modalHeart.length && productId) {
            updateHeartIcon($modalHeart, productId);
        }
        
        // Update total price when modal opens
        updateTotalPriceInModal();
    }, 100);
});

// Handle "Add to cart" clicks and always resolve the correct product
$(document).on('click', '.open-modal[data-modal-id="#ShoppingCartModal"]', function() {
    var $button = $(this);

    var productName = '';
    var productImage = '';
    var price;
    var quantity = 1;

    // 1. Inside Quick View modal
    var $quickViewModal = $button.closest('#QuickViewModal');
    if ($quickViewModal.length) {
        productName =
            $quickViewModal.data('product-name') ||
            $quickViewModal.find('.product-info h3, .modal-inner--title h4').first().text().trim();

        productImage =
            $quickViewModal.data('product-image') ||
            $quickViewModal.find('.product-images img').first().attr('src');

        price = $quickViewModal.data('product-price');
        if (typeof price === 'undefined') {
            var quickPriceText = $quickViewModal.find('.product-info .price, .product-info h3').first().text();
            var quickPriceMatch = quickPriceText && quickPriceText.match(/\$([\d,]+\.?\d*)/);
            price = quickPriceMatch ? parseFloat(quickPriceMatch[1].replace(/,/g, '')) : undefined;
        }

        var $qtyInput = $quickViewModal.find('.quantity-selector__value').first();
        quantity = parseInt($qtyInput.val(), 10);
        if (!quantity || quantity < 1) {
            quantity = 1;
        }
    } else {
        // 2. On main product-details page
        var $details = $button.closest('.product-details-content');
        if ($details.length) {
            productName = $details.find('h3').first().text().trim();

            productImage =
                $('.product-details-slider .listing-details-item img').first().attr('src') ||
                './assets/images/shop/product-1.jpg';

            var detailsPriceText = $details.find('.price').first().text();
            var detailsPriceMatch = detailsPriceText && detailsPriceText.match(/\$([\d,]+\.?\d*)/);
            price = detailsPriceMatch ? parseFloat(detailsPriceMatch[1].replace(/,/g, '')) : undefined;

            var $qty = $details.find('.quantity-selector__value').first();
            quantity = parseInt($qty.val(), 10);
            if (!quantity || quantity < 1) {
                quantity = 1;
            }
        } else {
            // 3. Generic product card (.product), e.g. related products or listing
            var $product = $button.closest('.product');
            if ($product.length) {
                var data = getProductDataFromCard($product);
                productName = data.name;
                productImage = data.image;
                price = data.price;
            }
        }
    }

    // 4. Final fallback: parse price from button text if still missing
    if (typeof price === 'undefined' || isNaN(price)) {
        var btnPriceMatch = $button.text().match(/\$([\d,]+\.?\d*)/);
        price = btnPriceMatch ? parseFloat(btnPriceMatch[1].replace(/,/g, '')) : 0;
    }

    if (!productName) {
        productName = 'Product';
    }

    if (!productImage) {
        productImage = './assets/images/shop/product-1.jpg';
    }

    var itemData = {
        id: 'item-' + Date.now(),
        name: productName,
        image: productImage,
        quantity: quantity,
        price: price,
    };

    addCartItem(itemData);
});

// Update subtotal in the cart modal (if element exists)
function updateSubtotal() {
    var total = 0;
    var items = getCartItems();
    
    items.forEach(function(item) {
        total += item.price * item.quantity;
    });
    
    // Update subtotal if we can find the element
    var $subtotal = $('.bottom-modal h4').filter(function() {
        return $(this).text().trim() === 'Subtotal';
    }).next('h4');
    
    if ($subtotal.length) {
        $subtotal.text('$' + total.toFixed(2));
    }
}

// Render product list HTML from template and current product array
function renderProductList(products) {
    if (!$shopProductList || !$shopProductTemplate) {
        return;
    }

    $shopProductList.empty();

    products.forEach(function (product, index) {
        var $card = $shopProductTemplate.clone();

        var title = product.name || product.title || 'Product';
        var image = product.image || '/assets/images/shop/product-1.jpg';
        var rawPrice = Number(product.price) || 0;
        var oldPrice = Number(product.oldPrice) || 0;

        // Format price with locale and 0–2 decimals
        var isInteger = Math.round(rawPrice) === rawPrice;
        var priceFormatted = isInteger
            ? rawPrice.toLocaleString('en-US')
            : rawPrice.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
              });

        // Attach product id
        var productId = product.id || ('product-' + (index + 1));
        $card.attr('data-product-id', productId);

        // Update image
        $card
            .find('.product-top img, .img img')
            .first()
            .attr('src', image)
            .attr('alt', title);

        // Update title
        $card
            .find('a.h7, .h7, .product-name, .product-title')
            .last()
            .text(title);

        // Update price - include old price if available
        var $priceElement = $card.find('.price').first();
        if (oldPrice > 0 && oldPrice > rawPrice) {
            var oldPriceFormatted = isInteger
                ? oldPrice.toLocaleString('en-US')
                : oldPrice.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                  });
            $priceElement.html('$' + priceFormatted + ' <span class="price-old">$' + oldPriceFormatted + '</span>');
        } else {
            $priceElement.html('$' + priceFormatted);
        }

        // Handle promotion: show/hide based on product data
        var $promotion = $card.find('.promotion');
        var promotionText = '';
        var promotionClass = 'bg-primary text-white';
        
        // Check if product has promotion field
        if (product.promotion && product.promotion.trim() !== '') {
            // If promotion is an object with text and class
            if (typeof product.promotion === 'object') {
                promotionText = product.promotion.text || product.promotion.label || '';
                promotionClass = product.promotion.class || 'bg-primary text-white';
            } 
            // If promotion is a string (like "-32%" or "New")
            else if (typeof product.promotion === 'string') {
                promotionText = product.promotion.trim();
                // Determine class based on promotion text
                if (promotionText.toLowerCase() === 'new' || promotionText.toLowerCase().includes('new')) {
                    promotionClass = 'uppercase bg-highlight text-white';
                } else {
                    promotionClass = 'bg-primary text-white';
                }
            }
        }
        // Auto-calculate promotion from oldPrice if available and no explicit promotion
        else if (oldPrice > 0 && oldPrice > rawPrice) {
            var discountPercent = Math.round(((oldPrice - rawPrice) / oldPrice) * 100);
            promotionText = '-' + discountPercent + '%';
            promotionClass = 'bg-primary text-white';
        }
        
        // Show or hide promotion
        if (promotionText && promotionText.trim() !== '') {
            if ($promotion.length) {
                $promotion.text(promotionText);
                $promotion.attr('class', 'promotion ' + promotionClass);
                $promotion.show();
            } else {
                // Create promotion element if it doesn't exist
                $card.find('.product-top').prepend('<div class="promotion ' + promotionClass + '">' + promotionText + '</div>');
            }
        } else {
            // Hide promotion if no promotion data
            if ($promotion.length) {
                $promotion.hide();
            }
        }

        $shopProductList.append($card);
    });

    // Check favorites status after rendering
    checkFavoritesOnRender();

    // Update match count label
    var $matchCount = $('#filterMatchesCount');
    if ($matchCount.length) {
        $matchCount.text(products.length + ' ');
    }

    // Show/hide pagination depending on number of products
    var $pagination = $('.pagination');
    if ($pagination.length) {
        if (products.length === 0) {
            $pagination.hide();
        } else {
            $pagination.show();
        }
    }
}

// Update filter tags displayed in #filterResults (for shop page)
function updateShopFilterTags() {
    var $filterResults = $('#filterResults');
    var $filterTags = $('#filterTags');
    var $filterDivider = $('#filterDivider');
    var $btnClearAll = $('#btnClearAll');

    if (!$filterResults.length || !$filterTags.length) {
        return;
    }

    $filterTags.empty();

    // Category tags
    $('#filterForm .filter-features input[name="category"]:checked').each(function () {
        var $checkbox = $(this);
        var value = $checkbox.val();
        var $span = $checkbox.closest('label').find('span');
        var label = $span.clone().children('em').remove().end().text().trim() || value;

        if (!value) return;

        var tagHtml =
            '<p class="select-item shop-filter-tag" data-filter-type="category" data-filter-value="' +
            value +
            '">' +
            label +
            '<img src="./assets/icons/X.svg" alt="X" class="filter-icon">' +
            '</p>';

        $filterTags.append(tagHtml);
    });

    // Branding tags
    $('#filterForm .filter-features input[name="branding"]:checked').each(function () {
        var $checkbox = $(this);
        var value = $checkbox.val();
        var $span = $checkbox.closest('label').find('span');
        var label = $span.clone().children('em').remove().end().text().trim() || value;

        if (!value) return;

        var tagHtml =
            '<p class="select-item shop-filter-tag" data-filter-type="branding" data-filter-value="' +
            value +
            '">' +
            label +
            '<img src="./assets/icons/X.svg" alt="X" class="filter-icon">' +
            '</p>';

        $filterTags.append(tagHtml);
    });

    // Price range tag (only if different from default)
    var $slider = $('#slider-range');
    if ($slider.length && typeof $slider.slider === 'function') {
        var vals = $slider.slider('values');
        var minPrice = vals[0];
        var maxPrice = vals[1];
        var defaultMin = parseInt($slider.data('min'), 10) || 0;
        var defaultMax = parseInt($slider.data('max'), 10) || 999999;

        if (minPrice !== defaultMin || maxPrice !== defaultMax) {
            var priceLabel = 'Price: $' + minPrice + ' - $' + maxPrice;
            var priceTagHtml =
                '<p class="select-item shop-filter-tag" data-filter-type="price" data-filter-value="price-range">' +
                priceLabel +
                '<img src="./assets/icons/X.svg" alt="X" class="filter-icon">' +
                '</p>';
            $filterTags.append(priceTagHtml);
        }
    }

    var hasTags = $filterTags.children().length > 0;

    if (hasTags) {
        $filterResults.show().removeAttr('style');
        if ($filterDivider.length) $filterDivider.show();
        if ($btnClearAll.length) $btnClearAll.show();
    } else {
        $filterResults.hide();
        if ($filterDivider.length) $filterDivider.hide();
        if ($btnClearAll.length) $btnClearAll.hide();
    }
}

// Apply active filters (category, branding, price) to JSON data and re-render
function applyShopFilters() {
    if (!shopAllProducts.length || !$shopProductList || !$shopProductTemplate) {
        return;
    }

    // Category filters
    var selectedCategories = $('#filterForm .filter-features input[name="category"]:checked').map(function () {
        return $(this).val()
    }).get();

    // Branding filters
    var selectedBrandings = $('#filterForm .filter-features input[name="branding"]:checked').map(function () {
        return $(this).val();
    }).get();

    // Price range slider
    var usePriceFilter = false;
    var minPrice, maxPrice;
    var $slider = $('#slider-range');
    if ($slider.length && typeof $slider.slider === 'function') {
        var vals = $slider.slider('values');
        minPrice = vals[0];
        maxPrice = vals[1];
        var defaultMin = parseInt($slider.data('min'), 10) || 0;
        var defaultMax = parseInt($slider.data('max'), 10) || 999999;
        if (minPrice !== defaultMin || maxPrice !== defaultMax) {
            usePriceFilter = true;
        }
    }

    var filtered = shopAllProducts.filter(function (p) {
        if (selectedCategories.length && $.inArray(p.category, selectedCategories) === -1) {
            return false;
        }
        if (selectedBrandings.length && $.inArray(p.branding, selectedBrandings) === -1) {
            return false;
        }
        if (usePriceFilter) {
            var priceVal = Number(p.price) || 0;
            if (priceVal < minPrice || priceVal > maxPrice) {
                return false;
            }
        }
        return true;
    });

    renderProductList(filtered);
    updateShopFilterTags();
}

// Load product list from fake_data/product.json and render into #product-list
function loadProductsFromJson() {
    $shopProductList = $('#product-list');
    if (!$shopProductList.length) {
        return;
    }

    // Use the first static HTML product as a template
    $shopProductTemplate = $shopProductList.find('.product').first().clone();
    if (!$shopProductTemplate.length) {
        return;
    }

    $.getJSON('./fake_data/product.json').done(function (products) {
        if (!$.isArray(products)) {
            return;
        }

        shopAllProducts = [];
        shopProductsMap = {};

        products.forEach(function (product, index) {
            var normalized = {
                id: product.id || ('product-' + (index + 1)),
                name: product.title || product.name || 'Product',
                promotion: product.promotion || '',
                image: product.image || '/assets/images/shop/product-1.jpg',
                price: Number(product.price) || 0,
                category: product.category || '',
                branding: product.branding || ''
            };

            shopAllProducts.push(normalized);
            shopProductsMap[normalized.id] = normalized;
        });

        // Initial render (all products, filtered by current UI state)
        applyShopFilters();
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
        console.error('Failed to load product data', textStatus || errorThrown);
    });
}

// Initialize when page is ready
$(document).ready(function() {
    initializeDefaultItems();
    renderCartItems();
    renderShoppingCartItems(); // Render shopping cart items if on shopping-cart.html
    loadProductsFromJson();
    updateShopFilterTags();
    
    // Check favorites for static products (not loaded from JSON)
    setTimeout(function() {
        checkFavoritesOnRender();
    }, 100);
});

// Listen for category, branding, and price slider changes
$(document).on('change', '#filterForm .filter-features input[type="checkbox"]', function () {
    applyShopFilters();
});

$(document).on('slidechange', '#slider-range', function () {
    applyShopFilters();
});

$(document).on('slide', '#slider-range', function () {
    applyShopFilters();
});

// Clicking on a tag removes the corresponding filter
$(document).on('click', '#filterResults .shop-filter-tag', function (e) {
    e.preventDefault();
    var $tag = $(this);
    var type = $tag.data('filterType');
    var value = $tag.data('filterValue');

    if (type === 'category' || type === 'branding') {
        $('#filterForm .filter-features input[name="' + type + '"][value="' + value + '"]')
            .prop('checked', false)
            .trigger('change');
    } else if (type === 'price') {
        var $slider = $('#slider-range');
        if ($slider.length && typeof $slider.slider === 'function') {
            var defaultMin = parseInt($slider.data('min'), 10) || 0;
            var defaultMax = parseInt($slider.data('max'), 10) || 999999;
            $slider.slider('values', [defaultMin, defaultMax]);
            $('#yearMin').text(defaultMin);
            $('#yearMax').text(defaultMax);
        }
        applyShopFilters();
    }
});

// Remove all tags & reset filters
$(document).on('click', '#btnClearAll', function (e) {
    e.preventDefault();

    // Clear category & branding checkboxes
    $('#filterForm .filter-features input[type="checkbox"]').prop('checked', false);

    // Reset price slider to default values
    var $slider = $('#slider-range');
    if ($slider.length && typeof $slider.slider === 'function') {
        var defaultMin = parseInt($slider.data('min'), 10) || 0;
        var defaultMax = parseInt($slider.data('max'), 10) || 999999;
        $slider.slider('values', [defaultMin, defaultMax]);
        $('#yearMin').text(defaultMin);
        $('#yearMax').text(defaultMax);
    }

    applyShopFilters();
});

// Calculate and update total price in QuickViewModal
function updateTotalPriceInModal() {
    var $modal = $('#QuickViewModal');
    if (!$modal.length) {
        return;
    }
    
    var $quantityInput = $modal.find('#quantity-selector-value, .quantity-selector__value');
    var $totalPriceBtn = $modal.find('#total-price');
    
    if (!$quantityInput.length || !$totalPriceBtn.length) {
        return;
    }
    
    var quantity = parseInt($quantityInput.val()) || 1;
    if (quantity < 1) {
        quantity = 1;
        $quantityInput.val(1);
    }
    
    // Get price from modal data or from price element
    var price = $modal.data('product-price');
    
    // If price not in modal data, try to get from price element in modal
    if (!price || price === 0) {
        // Try to get from price element (look for .h3 that contains price, ignore price-old)
        var $priceElement = $modal.find('.product-info .h3').first();
        if ($priceElement.length) {
            var priceText = $priceElement.text().trim();
            // Extract first price (before price-old if exists)
            var priceMatch = priceText.match(/\$?([\d,]+\.?\d*)/);
            if (priceMatch) {
                price = parseFloat(priceMatch[1].replace(/,/g, ''));
            }
        }
        
        // If still not found, try other price selectors
        if (!price || price === 0) {
            var $altPriceElement = $modal.find('.product-info .price, .product-info p.h3').first();
            if ($altPriceElement.length) {
                var altPriceText = $altPriceElement.text().trim();
                var altPriceMatch = altPriceText.match(/\$?([\d,]+\.?\d*)/);
                if (altPriceMatch) {
                    price = parseFloat(altPriceMatch[1].replace(/,/g, ''));
                }
            }
        }
    }
    
    // Default price if still not found
    if (!price || price === 0) {
        price = 79.99; // Default fallback
    }
    
    // Calculate total
    var total = price * quantity;
    
    // Format total with 2 decimals
    var totalFormatted = total.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    // Update button text
    $totalPriceBtn.text('Add to cart - $' + totalFormatted);
}

// Quantity selector plus button
$(document).on('click', '.quantity-selector__btn--plus', function() {
    var $input = $(this).siblings('.quantity-selector__value');
    var currentValue = parseInt($input.val()) || 0;
    $input.val(currentValue + 1);
    
    // Update total price if in QuickViewModal
    updateTotalPriceInModal();
});

$(document).on('click', '.quantity-selector__btn--minus', function() {
    var $input = $(this).siblings('.quantity-selector__value');
    var currentValue = parseInt($input.val()) || 0;
    if (currentValue > 0) {
        $input.val(currentValue - 1);
        
        // Update total price if in QuickViewModal
        updateTotalPriceInModal();
    }
});

// Prevent negative quantities when typing manually
$(document).on('change', '.quantity-selector__value', function() {
    var value = parseInt($(this).val()) || 0;
    if (value < 0) {
        $(this).val(0);
    }
    
    // Update total price if in QuickViewModal
    updateTotalPriceInModal();
});

// ========== FAVORITES MANAGEMENT ==========

// Get favorites from localStorage
function getFavorites() {
    var favorites = localStorage.getItem(FAVORITES_STORAGE_KEY);
    return favorites ? JSON.parse(favorites) : [];
}

// Save favorites to localStorage
function saveFavorites(favorites) {
    localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(favorites));
}

// Add product to favorites
function addToFavorites(productId, productData, position) {
    var favorites = getFavorites();
    
    // Check if already exists
    var existingIndex = favorites.findIndex(function(fav) {
        return fav.productId === productId;
    });
    
    if (existingIndex === -1) {
        // Add new favorite
        favorites.push({
            productId: productId,
            productData: productData,
            position: position,
            addedAt: new Date().toISOString()
        });
        saveFavorites(favorites);
        return true;
    }
    return false;
}

// Remove product from favorites
function removeFromFavorites(productId) {
    var favorites = getFavorites();
    favorites = favorites.filter(function(fav) {
        return fav.productId !== productId;
    });
    saveFavorites(favorites);
}

// Check if product is in favorites
function isFavorite(productId) {
    var favorites = getFavorites();
    return favorites.some(function(fav) {
        return fav.productId === productId;
    });
}

// Get favorite position
function getFavoritePosition(productId) {
    var favorites = getFavorites();
    var favorite = favorites.find(function(fav) {
        return fav.productId === productId;
    });
    return favorite ? favorite.position : null;
}

// Update favorite position
function updateFavoritePosition(productId, newPosition) {
    var favorites = getFavorites();
    var favorite = favorites.find(function(fav) {
        return fav.productId === productId;
    });
    if (favorite) {
        favorite.position = newPosition;
        saveFavorites(favorites);
    }
}

// Heart icon SVG (empty)
var heartIconEmpty = '<sv class="svg-themes" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.6875 3C14.7516 3 13.0566 3.8325 12 5.23969C10.9434 3.8325 9.24844 3 7.3125 3C5.77146 3.00174 4.29404 3.61468 3.20436 4.70436C2.11468 5.79404 1.50174 7.27146 1.5 8.8125C1.5 15.375 11.2303 20.6869 11.6447 20.9062C11.7539 20.965 11.876 20.9958 12 20.9958C12.124 20.9958 12.2461 20.965 12.3553 20.9062C12.7697 20.6869 22.5 15.375 22.5 8.8125C22.4983 7.27146 21.8853 5.79404 20.7956 4.70436C19.706 3.61468 18.2285 3.00174 16.6875 3ZM12 19.3875C10.2881 18.39 3 13.8459 3 8.8125C3.00149 7.66921 3.45632 6.57317 4.26475 5.76475C5.07317 4.95632 6.16921 4.50149 7.3125 4.5C9.13594 4.5 10.6669 5.47125 11.3062 7.03125C11.3628 7.16881 11.4589 7.28646 11.5824 7.36926C11.7059 7.45207 11.8513 7.49627 12 7.49627C12.1487 7.49627 12.2941 7.45207 12.4176 7.36926C12.5411 7.28646 12.6372 7.16881 12.6937 7.03125C13.3331 5.46844 14.8641 4.5 16.6875 4.5C17.8308 4.50149 18.9268 4.95632 19.7353 5.76475C20.5437 6.57317 20.9985 7.66921 21 8.8125C21 13.8384 13.71 18.3891 12 19.3875Z" fill="#1C1C1C"/></sv>';

// Heart icon SVG (empty) - for modal (different format)
var heartIconEmptyModal = '<svg class="svg-themes" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g clip-path="url(#clip0_13399_20463)"><path d="M12 21C12 21 2.25 15.75 2.25 9.5625C2.25 8.21984 2.78337 6.93217 3.73277 5.98277C4.68217 5.03337 5.96984 4.5 7.3125 4.5C9.43031 4.5 11.2444 5.65406 12 7.5C12.7556 5.65406 14.5697 4.5 16.6875 4.5C18.0302 4.5 19.3178 5.03337 20.2672 5.98277C21.2166 6.93217 21.75 8.21984 21.75 9.5625C21.75 15.75 12 21 12 21Z" stroke="#1C1C1C" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></g></svg>';

// Drag icon SVG (6 dots in 2 columns)
var dragIcon = '<svg class="svg-themes" xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" width="24" height="24" x="0" y="0" viewBox="0 0 48 48" style="enable-background:new 0 0 24 24" xml:space="preserve" class=""><g><g data-name="Recycle Bin"><path d="M39 6h-9V5a3 3 0 0 0-3-3h-7a3 3 0 0 0-3 3v1H9a3 3 0 0 0-3 3v2a3 3 0 0 0 2.025 2.824l.854 27.332a4.977 4.977 0 0 0 5 4.844h20.244a4.977 4.977 0 0 0 5-4.844l.854-27.332A3 3 0 0 0 42 11V9a3 3 0 0 0-3-3zM19 5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v1h-9zm18.122 36.094a2.987 2.987 0 0 1-3 2.906H13.877a2.987 2.987 0 0 1-3-2.906L10.032 14h27.936zM40 11a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1h30a1 1 0 0 1 1 1z" fill="#000000" opacity="1" data-original="#000000" class=""></path><path d="M24 19a1 1 0 0 0-1 1v18a1 1 0 0 0 2 0V20a1 1 0 0 0-1-1zM31.028 19a.972.972 0 0 0-1.028.972l-.5 18A1 1 0 0 0 30.472 39h.028a1 1 0 0 0 1-.972l.5-18A1 1 0 0 0 31.028 19zM16.972 19A1 1 0 0 0 16 20.028l.5 18a1 1 0 0 0 1 .972h.028a1 1 0 0 0 .972-1.028l-.5-18A1 1 0 0 0 16.972 19z" fill="#000000" opacity="1" data-original="#000000" class=""></path></g></g></svg>';

// Update heart icon based on favorite status
function updateHeartIcon($heartButton, productId) {
    if (!productId) {
        return;
    }
    
    // Check if it's modal heart or product card heart
    var isModalHeart = $heartButton.hasClass('bth-heart') || $heartButton.closest('#QuickViewModal').length > 0;
    var emptyHeartIcon = isModalHeart ? heartIconEmptyModal : heartIconEmpty;
    
    if (isFavorite(productId)) {
        // Change to drag icon
        $heartButton.html(dragIcon);
        $heartButton.addClass('is-favorite');
    } else {
        // Change to heart icon
        $heartButton.html(emptyHeartIcon);
        $heartButton.removeClass('is-favorite');
    }
}

// Handle click on action-heart (in product cards)
$(document).on('click', '.action-heart', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    var $heartButton = $(this);
    var $product = $heartButton.closest('.product');
    var productId = $product.attr('data-product-id');
    
    if (!productId) {
        // Try to get product ID from product data
        var productData = getProductDataFromCard($product);
        productId = productData.id || 'product-' + Date.now();
        $product.attr('data-product-id', productId);
    }
    
    // Get product data
    var productData = getProductDataFromCard($product);
    productData.id = productId;
    
    // Get position in list (index of product in the list)
    var $productList = $product.closest('#product-list, .product-list');
    var position = $productList.length ? $productList.find('.product').index($product) : null;
    
    if (isFavorite(productId)) {
        // Remove from favorites
        removeFromFavorites(productId);
        updateHeartIcon($heartButton, productId);
        
        // Also update modal heart if modal is open
        var $modal = $('#QuickViewModal');
        var modalProductId = $modal.data('product-id');
        if (modalProductId === productId) {
            var $modalHeart = $modal.find('.bth-heart');
            if ($modalHeart.length) {
                updateHeartIcon($modalHeart, productId);
            }
        }
    } else {
        // Add to favorites
        addToFavorites(productId, productData, position);
        updateHeartIcon($heartButton, productId);
        
        // Also update modal heart if modal is open
        var $modal = $('#QuickViewModal');
        var modalProductId = $modal.data('product-id');
        if (modalProductId === productId) {
            var $modalHeart = $modal.find('.bth-heart');
            if ($modalHeart.length) {
                updateHeartIcon($modalHeart, productId);
            }
        }
    }
});

// Handle click on heart in QuickViewModal
$(document).on('click', '#QuickViewModal .bth-heart', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    var $heartButton = $(this);
    var $modal = $('#QuickViewModal');
    var productId = $modal.data('product-id');
    
    if (!productId) {
        return;
    }
    
    // Get product data from modal
    var productData = {
        id: productId,
        name: $modal.data('product-name') || '',
        image: $modal.data('product-image') || '',
        price: $modal.data('product-price') || 0
    };
    
    var position = $modal.data('product-position');
    
    if (isFavorite(productId)) {
        // Remove from favorites
        removeFromFavorites(productId);
        updateHeartIcon($heartButton, productId);
        
        // Also update product card heart if visible
        var $productCard = $('.product[data-product-id="' + productId + '"]');
        if ($productCard.length) {
            var $cardHeart = $productCard.find('.action-heart');
            if ($cardHeart.length) {
                updateHeartIcon($cardHeart, productId);
            }
        }
    } else {
        // Add to favorites
        addToFavorites(productId, productData, position);
        updateHeartIcon($heartButton, productId);
        
        // Also update product card heart if visible
        var $productCard = $('.product[data-product-id="' + productId + '"]');
        if ($productCard.length) {
            var $cardHeart = $productCard.find('.action-heart');
            if ($cardHeart.length) {
                updateHeartIcon($cardHeart, productId);
            }
        }
    }
});

// Check and update heart icons when products are rendered
function checkFavoritesOnRender() {
    $('#product-list .product, .product-list .product').each(function() {
        var $product = $(this);
        var productId = $product.attr('data-product-id');
        
        if (productId) {
            var $heartButton = $product.find('.action-heart');
            if ($heartButton.length) {
                updateHeartIcon($heartButton, productId);
            }
        }
    });
}