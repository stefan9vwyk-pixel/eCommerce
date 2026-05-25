from django.urls import path
from . import views

# This helps Django know these URLs belong to the shopperz app
app_name = 'shopperz'

urlpatterns = [
    # Vendor Dashboard: List all stores owned by the vendor
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),

    # Page to create a new store (for users with permissions)
    path('store/create/', views.create_store, name='create_store'),

    # Page for users to update stores (for users with permissions)
    path(
        'store/<int:store_id>/edit/',
        views.update_store,
        name='update_store'
    ),

    # Page fro user to delete their stores (for users with permissions)
    path(
        'store/<int:store_id>/delete/',
        views.delete_store,
        name='delete_store'
    ),

    # View products within a specific store
    path('store/<int:store_id>/', views.store_detail, name='store_detail'),

    # Add a product
    path('product/<int:store_id>/edit/',
         views.add_or_update_product,
         name='add_product'),

    # Update a product
    path('store/<int:store_id>/product/<int:product_id>/edit/',
         views.add_or_update_product,
         name='update_product'),

    # Delete product
    path('product/<int:product_id>/delete/',
         views.delete_product,
         name='delete_product'),

    # Home page: Shows the list of all products
    path('', views.list_products, name='products_list'),

    # For direct links and redirects (GET requests)
    path(
        'product/<str:product_name>/',
        views.view_product_page,
        name='product_page'
    ),

    # For an empty page with a search bar (POST request)
    path('product/', views.view_product_page, name='product_page'),

    # URL to add an item to the shopping cart (usually called by a form)
    path('add-to-cart/', views.add_item_to_cart, name='add_to_cart'),

    # Page showing all items currently in the user's cart with totals
    path('cart/', views.show_user_cart, name='main_cart_page'),

    # URL to remove single items from cart
    path(
        'cart/remove/<str:item_id>/',
        views.remove_from_cart,
        name='remove_item'
    ),

    # URL to clear all items from the user's cart
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # URL to check out cart
    path('checkout/', views.checkout, name='checkout'),

    # URL to submit a review
    path(
        'submit-review/<str:product_name>/',
        views.submit_review,
        name='submit_review'
    ),

    # API views
    path('get/stores', views.view_stores),

    path('get/products', views.view_products),

    path('add/store', views.add_store),

    path('stores/<str:store_name>/products', views.add_product),
]
