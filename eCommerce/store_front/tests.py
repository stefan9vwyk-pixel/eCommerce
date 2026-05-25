from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group


class UserGroupRegistrationTests(TestCase):
    def setUp(self):
        # Create the group that the view expects to add users to
        self.vendor_group = Group.objects.create(name="Vendors")
        self.register_url = reverse('store_front:register')

        # Data for a new user registration
        self.user_data = {
            'username': 'new_vendor',
            'password': 'password123',
            'email': 'new_vendor@email.com',
            'account_type': 'vendor',
        }

    def test_register_user_adds_to_group(self):
        """Test if the user is added to group."""
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(username='new_vendor')

        # Check if the user was added to the group
        self.assertIn(self.vendor_group, user.groups.all())

    def test_registration_succeeds_if_group_missing(self):
        """Test if user is still created even if not group was chosen."""
        Group.objects.all().delete()  # Remove the group created in setUp
        self.client.post(self.register_url, self.user_data)

        # Check that either a user wasn't created or an error was handled
        self.assertTrue(User.objects.filter(username='new_vendor').exists())

    def test_group_assignment_is_idempotent(self):
        """
        Test if user only appears once in the group,
        even if they are added twice.
        """
        user = User.objects.create_user(
            username='idempotent_user',
            password='pwd'
        )
        # Add the same group twice
        user.groups.add(self.vendor_group)
        user.groups.add(self.vendor_group)
        # Verify the user still only has 1 group membership
        self.assertEqual(user.groups.filter(
            id=self.vendor_group.id
        ).count(), 1)

    def test_logged_in_user_has_group(self):
        """Test if user is logged in after registration and if they,
        belong to a group."""
        self.client.post(self.register_url, self.user_data)
        self.client.login(username='new_vendor', password='password123')

        # Verify the logged-in user in the request has the group
        user = User.objects.get(username='new_vendor')
        self.assertTrue(user.groups.filter(name="Vendors").exists())
