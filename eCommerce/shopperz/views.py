"""
Views for the shopperz e-commerce application.

This module contains view functions for managing vendor stores and products,
handling customer shopping cart operations, checkout, and review submission.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Exists, F
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Order, OrderItem, Store
from .serializers import StoreSerializer, ProductSerializer
from .forms import ReviewForm


# ******** CRUD functions for Stores ********
# Helper function to check if user is a Vendor
def is_vendor(user):
    """
    Check if a user belongs to the Vendors group.

    Args:
        user: The user object to check.

    Returns:
        bool: True if user is in the Vendors group, False otherwise.
    """
    return user.groups.filter(name='Vendors').exists()


@login_required
@user_passes_test(is_vendor)
def vendor_dashboard(request):
    """
    Display the vendor's dashboard showing all their stores and product counts.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered vendor dashboard template with stores data.
    """
    product_count_subquery = Product.objects.filter(
        store=OuterRef('pk')
    ).values('store').annotate(count=Count('id')).values('count')

    # Fetch all stores where the vendor is the current user
    stores = Store.objects.filter(vendor=request.user).annotate(
        products_count=Subquery(product_count_subquery)
    )

    return render(request, 'shopperz/vendor_dashboard.html', {
        'stores': stores
    })


@login_required
@user_passes_test(is_vendor)
def create_store(request):
    """
    Create a new store for the logged-in vendor.

    Handles both GET requests (show form) and POST requests (create store).
    Prevents duplicate store names for the same vendor.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered store form or redirect to vendor dashboard.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        # Check if the store already exists to prevent duplicates
        if not Store.objects.filter(vendor=request.user, name=name).exists():
            Store.objects.create(
                vendor=request.user,
                name=name,
                description=description
            )

        # Redirect to a list of their stores
        return redirect('shopperz:vendor_dashboard')

    return render(request, 'shopperz/store_form.html')


@login_required
@user_passes_test(is_vendor)
def store_detail(request, store_id):
    """
    Display details of a specific store and its products.

    Ensures the vendor can only view their own store details.

    Args:
        request: The HTTP request object.
        store_id: The ID of the store to display.

    Returns:
        HttpResponse: Rendered store detail template with store and products
            data.
    """
    # This ensures the vendor can only see the detail page of their OWN store
    store = get_object_or_404(Store, id=store_id, vendor=request.user)

    # Fetch all products linked to this specific store
    products = store.products.all()

    return render(request, 'shopperz/store_detail.html', {
        'store': store,
        'products': products
    })


@login_required
@user_passes_test(is_vendor)
def update_store(request, store_id):
    """
    Update an existing store's information.

    Handles both GET requests (show form) and POST requests (update store).
    Ensures the vendor can only update their own stores.

    Args:
        request: The HTTP request object.
        store_id: The ID of the store to update.

    Returns:
        HttpResponse: Rendered store form or redirect to vendor dashboard.
    """
    store = get_object_or_404(Store, id=store_id, vendor=request.user)

    if request.method == 'POST':
        store.name = request.POST.get('name')
        store.description = request.POST.get('description')
        store.save()
        return redirect('shopperz:vendor_dashboard')

    return render(request, 'shopperz/store_form.html', {'store': store})


@login_required
@user_passes_test(is_vendor)
def delete_store(request, store_id):
    """
    Delete a store owned by the current vendor.

    Handles both GET requests (show confirmation) and POST requests
    (delete store).
    Ensures the vendor can only delete their own stores.

    Args:
        request: The HTTP request object.
        store_id: The ID of the store to delete.

    Returns:
        HttpResponse: Rendered confirmation template or redirect to vendor
                      dashboard.
    """
    store = get_object_or_404(Store, id=store_id, vendor=request.user)

    if request.method == 'POST':
        store.delete()
        return redirect('shopperz:vendor_dashboard')

    return render(request, 'shopperz/store_confirm_delete.html',
                  {'store': store})


# ******** CRUD functions for products ********
@login_required
def view_product_page(request, product_name=None):
    """
    Display a product page with details and reviews.

    Shows product information and associated reviews with verification status.
    Only users with view_product permissions can access this page.

    Args:
        request: The HTTP request object.
        product_name: Optional product name to display.

    Returns:
        HttpResponse: Rendered product page with product, form, and reviews
                      data.
    """
    user = request.user  # Get current logged in user

    # Check if user has permission to view products
    if (
        user.has_perm('shopperz.view_product')
        or user.has_perm('shopperz.view_products')
    ):
        name = product_name or request.POST.get('product')
        form = ReviewForm()

        if not name:
            return render(request, 'shopperz/product_page.html', {
                    'error': 'No products name was given.'
                })

        try:
            # Try to find the product in the database by its name
            product = Product.objects.get(name=product_name)

            purchased_queryset = OrderItem.objects.filter(
                order__user=OuterRef("user"),
                product=product
            )

            reviews = product.reviews.annotate(
                is_verified=Exists(purchased_queryset)
            ).select_related('user')

            # Show product details on page
            return render(request, 'shopperz/product_page.html', {
                'product': product,
                'form': form,
                'reviews': reviews
            })

        except ObjectDoesNotExist:
            # If product not found, show error on page
            return render(request, 'shopperz/product_page.html', {
                'error': 'Product not found'
            })

    # If user does not have permission to view products, show error
    return render(request, 'shopperz/product_page.html', {
        'error': 'You do not have permission to view this product.'
    })


@login_required
@user_passes_test(is_vendor)
def add_or_update_product(request, store_id, product_id=None):
    """
    Create a new product or update an existing product for a store.

    Handles both GET requests (show form) and POST requests
    (create/update product).
    Validates price and stock inputs. Ensures vendor owns the store.

    Args:
        request: The HTTP request object.
        store_id: The ID of the store the product belongs to.
        product_id: Optional product ID for updating; if None, creates new
                    product.

    Returns:
        HttpResponse: Rendered product form or redirect to store detail page.
    """
    # Ensure the vendor owns the store
    store = get_object_or_404(Store, id=store_id, vendor=request.user)

    # If product_id exists, we are editing
    # Otherwise, we are creating a new one
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id, store=store)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')

        try:
            price = float(price)
            if price < 0:
                price = 0.00
        except (ValueError, TypeError):
            price = 0.00

        try:
            stock = int(stock)
            if stock < 0:
                stock = 0
        except (ValueError, TypeError):
            stock = 0

        if product:
            # Update existing
            product.name = name
            product.description = description
            product.price = price
            product.stock = stock
            product.save()
        else:
            # Create new
            Product.objects.create(
                store=store,
                name=name,
                description=description,
                price=price,
                stock=stock
            )

        return redirect('shopperz:store_detail', store_id=store.id)

    return render(request, 'shopperz/product_form.html', {
        'product': product,
        'store': store
    })


@login_required
@user_passes_test(is_vendor)
def delete_product(request, product_id):
    """
    Delete a product from a store.

    Handles both GET requests (show confirmation) and POST requests
    (delete product).
    Ensures vendor owns the store the product belongs to.

    Args:
        request: The HTTP request object.
        product_id: The ID of the product to delete.

    Returns:
        HttpResponse: Rendered confirmation template or redirect to store
                      detail page.
    """
    # Ensure the vendor owns the store this product belongs to
    product = get_object_or_404(Product,
                                id=product_id,
                                store__vendor=request.user)
    store_id = product.store.id  # Save ID before deleting for redirect

    if request.method == 'POST':
        product.delete()
        return redirect('shopperz:store_detail', store_id=store_id)

    return render(request, 'shopperz/confirm_delete.html', {
        'product': product
    })


# ******** Functions for buyers' checkout and cart options ********
def add_item_to_cart(request):
    """
    Add a product to the user's shopping cart.

    Stores cart data in the session. If item already exists in cart,
    increases its quantity.

    Args:
        request: The HTTP request object containing 'item' and 'quantity' POST
                 data.

    Returns:
        HttpResponse: Redirect to main cart page.
    """
    # Get item name and quantity from POST form submission
    item_id = request.POST.get('item_id')
    quantity = request.POST.get('quantity')

    # If either is missing, redirect to cart page without changing anything
    if not item_id or not quantity:
        return redirect('shopperz:main_cart_page')

    try:
        # Convert quantity to integer, and set to 1 if invalid or less than 1
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    # Get existing cart from session, or empty dictionary if none
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=item_id)

    # Calculate what the new quantity would be
    current_qty = cart.get(str(item_id), 0)
    new_qty = current_qty + quantity

    if product.stock >= new_qty:
        cart[str(item_id)] = new_qty
        # Save updated cart back into session so it persists
        request.session['cart'] = cart
        request.session.modified = True

        return redirect('shopperz:main_cart_page')
    else:
        # Show error if user tries to add more than available
        return render(request, 'shopperz/product_page.html', {
            'product': product,
            'error': f"Only {product.stock} items left in stock."
        })


def retrieve_products(request):
    """
    Retrieve product objects for items currently in the cart.

    Fetches Product model instances for all items stored in the session cart.
    Skips items that no longer exist in the database.

    Args:
        request: The HTTP request object containing session data.

    Returns:
        list: List of dictionaries containing 'product' and 'quantity' keys.
    """
    products = []
    session = request.session

    # If cart exists in session, load products and their quantities
    if 'cart' in session:
        for item_id, quantity in session['cart'].items():
            try:
                # Get product from database by name
                product = Product.objects.get(id=item_id)
                # Add product and quantity as a dictionary to list
                products.append({'product': product, 'quantity': quantity})
            except Product.DoesNotExist:
                # Skip if product not found (may have been deleted)
                pass

    return products


def show_user_cart(request):
    """
    Display the user's shopping cart with items and total price.

    Calculates subtotals for each item and the cart total.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered cart page with cart items and total price.
    """
    # Get list of products and quantities from the session cart
    cart_items = retrieve_products(request)

    total_price = 0  # Start total price at zero

    # Calculate subtotal for each cart item and total price for whole cart
    for item in cart_items:
        subtotal = item['product'].price * item['quantity']
        item['subtotal'] = subtotal  # Add subtotal to item dictionary
        total_price += subtotal

    # Render cart page, passing in items and total price
    return render(request, 'shopperz/main_cart_page.html', {
        'cart': cart_items,
        'total_price': total_price,
    })


def list_products(request):
    """
    Display a list of all available products in the store.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered products list template with all products.
    """
    # Get all products from database
    products = Product.objects.all()
    # Show products list page, passing products to template
    return render(request, 'shopperz/products_list.html',
                  {'products': products})


def remove_from_cart(request, item_id):
    """
    Remove a specific item from the user's shopping cart.

    Args:
        request: The HTTP request object.
        item_name: The name of the item to remove from cart.

    Returns:
        HttpResponse: Redirect to main cart page.
    """
    if request.method == 'POST':
        cart = request.session.get('cart', {})

        if item_id in cart:
            del cart[item_id]
            request.session['cart'] = cart
            request.session.modified = True

        return redirect('shopperz:main_cart_page')


def clear_cart(request):
    """
    Remove all items from the user's shopping cart.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Redirect to main cart page.
    """
    # Empty the cart by setting session cart to empty dictionary
    request.session['cart'] = {}
    request.session.modified = True  # Mark session as changed

    # Redirect to cart page after clearing
    return redirect('shopperz:main_cart_page')


def send_checkout_email(user, order_item, total_price):
    """
    Create and send an invoice email to the customer at checkout.

    Generates a formatted invoice with order items, prices, quantities,
    and total.

    Args:
        user: The User object to send the email to.
        order_item: List of OrderItem objects for the order.
        total_price: The total price of the order.
    """
    subject = "Order Invoice - Shopperz"

    body = f"Hi {user.username},\n\n"
    body += "Here is the invoice of your recent order:\n"
    body += f"{'Product':<20} {'Price':<10} {'Qty':<5} {'Subtotal':<10}\n"
    body += "-" * 50 + "\n"

    # Create each product line using a for loop
    for item in order_item:
        name = item.product.name
        price = item.price
        qty = item.quantity
        subtotal = price * qty
        body += f"{name:<20} R{price:10} {qty:<5} R{subtotal:<10}\n"

    body += "-" * 50 + "\n"
    body += f"TOTAL: R{total_price:.2f}\n\n"
    body += "Thank you for purchase."

    send_mail(
        subject,
        body,
        "admin@shopperz.com",
        [user.email],
        fail_silently=False,
    )


@login_required
def checkout(request):
    """
    Process the checkout and create an order from the shopping cart.

    Creates an Order and associated OrderItems from the current cart session.
    Sends an invoice email to the customer and clears the cart.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered order success page or redirect to cart if empty.
    """
    if request.method == 'POST':
        cart_items = retrieve_products(request)
        if not cart_items:
            return redirect('shopperz:main_cart_page')

        with transaction.atomic():
            order = Order.objects.create(user=request.user)
            total_price = 0
            order_items_list = []

            # Convert session items into OrderItems
            for item in cart_items:
                product = item['product']
                qty = item['quantity']

                oi = OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=qty
                )
                order_items_list.append(oi)
                total_price += (product.price * qty)

                product.stock = F('stock') - qty
                product.save()

        # Send email at checkout
        try:
            send_checkout_email(request.user, order_items_list, total_price)
        except Exception as e:
            print(f"Email failed: {e}")  # Log error but don't stop checkout

        request.session['cart'] = {}
        return render(request, 'shopperz/order_success.html')


@login_required
def submit_review(request, product_name):
    """
    Submit a review for a product.

    Processes review form submission and saves the review with the product
    and current user.

    Args:
        request: The HTTP request object containing review form data.
        product_name: The name of the product being reviewed.

    Returns:
        HttpResponse: Redirect to product page.
    """
    if request.method == 'POST':
        product = get_object_or_404(Product, name=product_name)
        form = ReviewForm(request.POST)

        if form.is_valid():

            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

        return redirect('shopperz:product_page', product_name=product.name)


# ***** API Views section *******************

# View can only be accessed with GET request
@api_view(['GET'])
# Requires a valid username and password
@authentication_classes([BasicAuthentication])
# Check if user is authenticated
@permission_classes([IsAuthenticated])
def view_stores(request):
    # Fetch all stores with the products
    stores = Store.objects.prefetch_related('products').all()

    serializer = StoreSerializer(stores, many=True)  # Serialize the data
    return JsonResponse(data=serializer.data, safe=False)


@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_products(request):
    products = Product.objects.prefetch_related('reviews').all()

    serializer = ProductSerializer(products, many=True)

    return JsonResponse(data=serializer.data, safe=False)


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_store(request):
    # Check if user is a Vendor
    vendor_id = request.data.get('vendor')
    if vendor_id is None:
        return Response({'error': 'Vendor field is required'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Ensure user making request matches vendor profile.
    if int(vendor_id) != request.user.id:
        return Response({'error': 'User ID and vendor ID do not match.'},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = StoreSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_product(request, store_name):
    store = get_object_or_404(Store, name=store_name)

    if store.vendor != request.user:
        return Response({'error': 'User does not match store vendor.'},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(store=store)
        return JsonResponse(serializer.data, status=201)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
