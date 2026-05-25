from django.contrib.auth.models import Group, Permission


def create_groups(sender, **kwargs):

    if sender.name != 'shopperz':
        return

    group_permissions = {
        'Vendors': [
            'add_product',
            'add_products',
            'change_product',
            'change_products',
            'delete_product',
            'delete_products',
            'view_product',
            'view_products',
            'add_store',
            'change_store',
            'delete_store',
            'view_store'
        ],
        'Buyers': [
            'view_product',
            'view_products',
            'add_review',
            'change_review',
            'delete_review',
            'view_review',
            'view_store'
        ]
    }

    for group_name, codenames in group_permissions.items():
        group, created = Group.objects.get_or_create(name=group_name)

        permissions = Permission.objects.filter(codename__in=codenames)

        group.permissions.set(permissions)

    print("Buyers and Vendors groups set up and permissions granted.")
