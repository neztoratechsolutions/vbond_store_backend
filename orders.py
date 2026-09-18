from sqlalchemy import text
from app.database import engine


def update_orders_table():
    with engine.begin() as connection:

        # Add the new customer_details column
        connection.execute(
            text("""
                ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS customer_details JSON;
            """)
        )

        # Remove the old foreign key constraints
        connection.execute(
            text("""
                ALTER TABLE orders
                DROP CONSTRAINT IF EXISTS orders_customer_id_fkey;
            """)
        )

        connection.execute(
            text("""
                ALTER TABLE orders
                DROP CONSTRAINT IF EXISTS orders_address_id_fkey;
            """)
        )

        # Remove the old columns
        connection.execute(
            text("""
                ALTER TABLE orders
                DROP COLUMN IF EXISTS customer_id;
            """)
        )

        connection.execute(
            text("""
                ALTER TABLE orders
                DROP COLUMN IF EXISTS address_id;
            """)
        )

        # Make customer_details NOT NULL after removing old columns
        connection.execute(
            text("""
                ALTER TABLE orders
                ALTER COLUMN customer_details SET NOT NULL;
            """)
        )

    print("Orders table updated successfully!")


if __name__ == "__main__":
    update_orders_table()