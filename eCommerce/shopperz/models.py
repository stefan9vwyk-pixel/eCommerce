"""
Django models for the shopperz e-commerce application.

This module contains the core data models for managing stores, products,
orders, order items, and reviews in the shopperz e-commerce platform.
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Store(models.Model):
    """
    Model representing a vendor's store in the marketplace.

    Each store belongs to a vendor (user) and contains a collection of
    products.
    Multiple stores can be created by the same vendor.

    Attributes:
        vendor: ForeignKey to User model representing the store owner.
        name: The name of the store (max 255 characters).
        description: A text description of the store.
        created_at: Timestamp of when the store was created.
    """
    vendor = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='stores')
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['vendor', 'name'], name='unique_vendor_store'
                )]


class Product(models.Model):
    """
    Model representing a product offered by a store.

    Each product belongs to a specific store and contains information about
    the product's details, pricing, and inventory.

    Attributes:
        store: ForeignKey to Store model indicating which store offers this
               product.
        name: The product name (max 100 characters).
        description: A detailed description of the product (optional).
        price: The product price with up to 10 digits and 2 decimal places.
        stock: The current quantity of the product in inventory.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE,
                              related_name='products')

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("add_products", "Can add products"),
            ("change_products", "Can change products"),
            ("delete_products", "Can delete products"),
            ("view_products", "Can view products"),
        ]


class Order(models.Model):
    """
    Model representing a customer's order.

    Stores order information to track purchases and enable users to leave
    reviews for products they have bought.

    Attributes:
        user: ForeignKey to User model representing the customer who placed
              the order.
        created_at: Timestamp of when the order was placed.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    """
    Model representing individual items within an order.

    Links products to orders and stores item-specific details such as
    the price and quantity at the time of purchase. Used to verify if a user
    has purchased a product when they attempt to leave a review.

    Attributes:
        order: ForeignKey to Order model indicating which order contains this
               item.
        product: ForeignKey to Product model indicating which product was
                 ordered.
        price: The price of the item at the time of purchase.
        quantity: The quantity of the product ordered.
    """
    order = models.ForeignKey(Order, related_name='items',
                              on_delete=models.CASCADE)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField()


class Review(models.Model):
    """
    Model representing a product review submitted by a customer.

    Stores reviews including ratings and content for products. Only verified
    buyers (users who have purchased the product) should be able to create
    reviews.

    Attributes:
        product: ForeignKey to Product model indicating which product is being
                 reviewed.
        user: ForeignKey to User model indicating who submitted the review.
        content: The review text content (optional).
        rating: Numeric rating out of 5 (default is 5).
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='reviews')

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    content = models.TextField(blank=True)

    rating = models.IntegerField(default=5)

    def is_verified(self):
        """
        Check if the reviewer has actually purchased the product.

        Returns:
            bool: True if the user has a verified purchase of this product,
                  False otherwise.
        """
        return OrderItem.objects.filter(
            order__user=self.user,
            product=self.product
        ).exists()
