from django.db import connection

from .models import Cart, CartItem, Order, TestDriveBooking, Wishlist

WISHLIST_TABLE = Wishlist._meta.db_table
CART_TABLE = Cart._meta.db_table
CART_ITEM_TABLE = CartItem._meta.db_table
ORDER_TABLE = Order._meta.db_table
TEST_DRIVE_TABLE = TestDriveBooking._meta.db_table

CART_PK_COLUMN = Cart._meta.pk.column
CART_ITEM_CART_COLUMN = CartItem._meta.get_field("cart").column


def fetch_customer_nav_counts(customer_id):
    """Return wishlist and cart counts for navbar badges."""
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM {WISHLIST_TABLE} WHERE customer_id = %s",
            [customer_id],
        )
        wishlist_count = cursor.fetchone()[0]

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {CART_ITEM_TABLE} ci
            JOIN {CART_TABLE} c
              ON ci.{CART_ITEM_CART_COLUMN} = c.{CART_PK_COLUMN}
            WHERE c.customer_id = %s
            """,
            [customer_id],
        )
        cart_count = cursor.fetchone()[0]

    return wishlist_count, cart_count
