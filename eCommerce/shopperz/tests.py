from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Store


class StoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a vendor user
        self.vendor = User.objects.create_user(
            username='vendor',
            password='password'
        )
        # Add user to vendor group
        vendor_group, _ = Group.objects.get_or_create(name='Vendors')
        self.vendor.groups.add(vendor_group)

        # Create another user (to test unauthorized access)
        self.other_user = User.objects.create_user(
            username='other',
            password='password'
        )

        # Create a store for testing
        self.store = Store.objects.create(
            vendor=self.vendor,
            name="Test Store",
            description="A test description"
        )

    def test_create_store_post(self):
        self.client.login(username='vendor', password='password')
        response = self.client.post(reverse('shopperz:create_store'), {
            'name': 'New Store',
            'description': 'New Description'
        })
        self.assertRedirects(response, reverse('shopperz:vendor_dashboard'))
        self.assertTrue(Store.objects.filter(name='New Store').exists())

    def test_store_detail_access(self):
        self.client.login(username='vendor', password='password')
        response = self.client.get(reverse(
            'shopperz:store_detail',
            args=[self.store.id]
        ))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shopperz/store_detail.html')
        self.assertEqual(response.context['store'], self.store)

    def test_store_detail_unauthorized_owner(self):
        """Ensure a vendor cannot see another vendor's store."""
        self.client.login(username='other', password='password')
        response = self.client.get(reverse(
            'shopperz:store_detail',
            args=[self.store.id]
        ))
        self.assertEqual(response.status_code, 302)  # Redirect to login/denied

    def test_update_store_post(self):
        self.client.login(username='vendor', password='password')
        response = self.client.post(reverse(
            'shopperz:update_store',
            args=[self.store.id]
        ), {
            'name': 'Updated Name',
            'description': 'Updated Description'
        })
        self.store.refresh_from_db()
        self.assertEqual(self.store.name, 'Updated Name')
        self.assertRedirects(response, reverse('shopperz:vendor_dashboard'))

    def test_delete_store_post(self):
        self.client.login(username='vendor', password='password')
        response = self.client.post(reverse(
            'shopperz:delete_store',
            args=[self.store.id]
        ))
        self.assertRedirects(response, reverse('shopperz:vendor_dashboard'))
        self.assertFalse(Store.objects.filter(id=self.store.id).exists())
