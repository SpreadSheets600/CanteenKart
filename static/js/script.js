// Enhanced JavaScript for CanteenKart

document.addEventListener('DOMContentLoaded', function() {
    
    // Update cart count on page load
    updateCartCount();

    // Function to update cart item count in header
    async function updateCartCount() {
        try {
            const response = await fetch('/cart-data');
            if (response.ok) {
                const cart = await response.json();
                const itemCount = Object.values(cart).reduce((total, item) => total + item.quantity, 0);
                const cartCountElement = document.getElementById('cart-item-count');
                if (cartCountElement) {
                    cartCountElement.textContent = itemCount;
                    cartCountElement.style.display = itemCount > 0 ? 'flex' : 'none';
                }
            }
        } catch (error) {
            console.error('Error updating cart count:', error);
        }
    }

    // Function to display cart items on the cart page
    async function displayCart() {
        const cartItemsContainer = document.getElementById('cart-items');
        const totalElement = document.getElementById('total-price');

        if (!cartItemsContainer) return;

        try {
            const response = await fetch('/cart-data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const cart = await response.json();

            cartItemsContainer.innerHTML = '';
            let total_price = 0;

            if (Object.keys(cart).length === 0) {
                cartItemsContainer.innerHTML = `
                    <div class="text-center py-12">
                        <i class="fas fa-shopping-cart text-gray-400 text-6xl mb-4"></i>
                        <p class="text-gray-600 text-xl">Your cart is empty</p>
                        <a href="/" class="mt-4 inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors">
                            Start Shopping
                        </a>
                    </div>`;
            } else {
                const itemsContainer = document.createElement('div');
                itemsContainer.className = 'space-y-4';

                for (const itemId in cart) {
                    const item = cart[itemId];
                    const subtotal = item.price * item.quantity;
                    total_price += subtotal;

                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'bg-gray-50 rounded-lg p-4 flex justify-between items-center hover:bg-gray-100 transition-colors';
                    itemDiv.innerHTML = `
                        <div class="flex items-center space-x-4">
                            <div class="bg-blue-500 text-white rounded-full w-12 h-12 flex items-center justify-center">
                                <i class="fas fa-hamburger"></i>
                            </div>
                            <div>
                                <h3 class="font-semibold text-gray-800">${item.name}</h3>
                                <p class="text-gray-600 text-sm">${item.quantity} × $${item.price.toFixed(2)}</p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4">
                            <span class="font-bold text-green-600 text-lg">$${subtotal.toFixed(2)}</span>
                            <a href="/remove_from_cart/${itemId}" 
                               class="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm transition-colors">
                                <i class="fas fa-trash"></i>
                            </a>
                        </div>
                    `;
                    itemsContainer.appendChild(itemDiv);
                }
                cartItemsContainer.appendChild(itemsContainer);
            }

            if (totalElement) {
                totalElement.textContent = `$${total_price.toFixed(2)}`;
            }

        } catch (error) {
            console.error("Error fetching or displaying cart data:", error);
            if (cartItemsContainer) {
                cartItemsContainer.innerHTML = '<p class="text-red-600 text-center py-4">Error loading cart.</p>';
            }
        }
    }

    // Function to handle adding an item to the cart
    function handleAddToCart(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);
        const button = form.querySelector('button');
        const originalText = button.innerHTML;

        button.disabled = true;

        fetch(form.action, {
            method: form.method,
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Show success feedback
            button.innerHTML = '<i class="fas fa-check mr-2"></i>Added!';
            button.className = button.className.replace('from-green-500 to-green-600', 'from-blue-500 to-blue-600');
            
            // Update cart count
            updateCartCount();
            
            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalText;
                button.className = button.className.replace('from-blue-500 to-blue-600', 'from-green-500 to-green-600');
                button.disabled = false;
            }, 2000);
        })
        .catch(error => {
            console.error("Error adding item to cart:", error);
            button.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>Error';
            button.className = button.className.replace('from-green-500 to-green-600', 'from-red-500 to-red-600');
            
            setTimeout(() => {
                button.innerHTML = originalText;
                button.className = button.className.replace('from-red-500 to-red-600', 'from-green-500 to-green-600');
                button.disabled = false;
            }, 2000);
        });
    }

    // Function to validate and handle order placement
    function handlePlaceOrder(event) {
        event.preventDefault();
        
        const form = event.target;
        const timeSlot = document.getElementById('time-slot').value;
        const button = form.querySelector('button[type="submit"]');

        if (!timeSlot) {
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-2';
            errorDiv.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>Please select a pickup time slot.';
            
            const timeSlotContainer = document.getElementById('time-slot').parentElement;
            const existingError = timeSlotContainer.querySelector('.bg-red-100');
            if (existingError) existingError.remove();
            
            timeSlotContainer.appendChild(errorDiv);
            
            setTimeout(() => errorDiv.remove(), 5000);
            return;
        }

        // Show loading state
        const originalButtonText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Placing Order...';
        button.disabled = true;

        // Submit the form
        form.submit();
    }

    // Page-specific initialization
    const currentPath = window.location.pathname;

    if (currentPath === '/') {
        // Index page: Add event listeners to "Add to Cart" forms
        const addToCartForms = document.querySelectorAll('form[action="/add_to_cart"]');
        addToCartForms.forEach(form => {
            form.addEventListener('submit', handleAddToCart);
        });
    } 
    else if (currentPath === '/cart') {
        // Cart page: Display cart and handle order placement
        displayCart();
        
        const orderForm = document.getElementById('order-form');
        if (orderForm) {
            orderForm.addEventListener('submit', handlePlaceOrder);
        }
    }
    else if (currentPath.startsWith('/confirmation/')) {
        // Confirmation page: Handle real-time updates
        console.log("Order confirmation page loaded");
        
        // Check if elements exist before using them
        const statusElement = document.getElementById('status-text');
        const orderStatusDiv = document.getElementById('order-status');
        
        if (statusElement && orderStatusDiv) {
            // Auto-refresh order status
            const tokenMatch = currentPath.match(/\/confirmation\/(\d+)/);
            if (tokenMatch) {
                const token = tokenMatch[1];
                
                function updateOrderStatus() {
                    fetch(`/order_status/${token}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'ready') {
                                statusElement.textContent = 'Ready for Pickup!';
                                statusElement.className = 'font-bold text-green-600';
                                orderStatusDiv.className = 'bg-green-50 rounded-xl p-4 mb-6';
                                
                                const icon = orderStatusDiv.querySelector('i');
                                if (icon) {
                                    icon.className = 'fas fa-check text-green-600';
                                }
                                
                                // Show browser notification
                                if ('Notification' in window && Notification.permission === 'granted') {
                                    new Notification('Order Ready!', {
                                        body: `Your order #${token} is ready for pickup!`,
                                        icon: '/static/favicon.ico'
                                    });
                                }
                            }
                        })
                        .catch(error => console.error('Error checking order status:', error));
                }

                // Request notification permission
                if ('Notification' in window && Notification.permission === 'default') {
                    Notification.requestPermission();
                }

                // Check status every 30 seconds
                setInterval(updateOrderStatus, 30000);
                
                // Check once immediately after 2 seconds
                setTimeout(updateOrderStatus, 2000);
            }
        }
    }
    else if (currentPath === '/admin') {
        // Admin page: Auto-refresh for new orders
        console.log("Admin dashboard loaded");
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            window.location.reload();
        }, 30000);
    }
});

// Utility functions
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg text-white max-w-sm ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    }`;
    toast.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}
