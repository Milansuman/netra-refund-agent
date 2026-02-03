from db import db
from typing import TypedDict

class Product(TypedDict):
    id: int
    title: str
    description: str | None
    price: int
    tax_percent: float
    quantity: int

def create_product(title: str, price: int, tax_percent: float, description: str | None = None) -> int:
    """
    Create a new product.
    
    Args:
        title: Product name/title
        price: Price in cents (e.g., 1999 for $19.99)
        tax_percent: Tax percentage (e.g., 10.0 for 10%)
        description: Optional product description
    
    Returns:
        The ID of the created product
    """
    result = db.execute(
        "INSERT INTO products (title, description, price, tax_percent) VALUES (%s, %s, %s, %s) RETURNING id;",
        (title, description, price, tax_percent)
    )
    return result[0][0]

def get_product(product_id: int) -> Product | None:
    """
    Get a single product by ID.
    
    Args:
        product_id: The ID of the product
    
    Returns:
        Product details or None if not found
    """
    result = db.execute(
        "SELECT id, title, description, price, tax_percent, quantity FROM products WHERE id = %s;",
        (product_id,)
    )
    
    if not result:
        return None
    
    return {
        "id": result[0][0],
        "title": result[0][1],
        "description": result[0][2],
        "price": result[0][3],
        "tax_percent": result[0][4],
        "quantity": result[0][5]
    }

def get_all_products() -> list[Product]:
    """
    Get all products.
    
    Returns:
        List of all products
    """
    result = db.execute(
        "SELECT id, title, description, price, tax_percent, quantity FROM products ORDER BY id;"
    )
    
    products: list[Product] = []
    for row in result:
        products.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "price": row[3],
            "tax_percent": row[4],
            "quantity": row[5]
        })
    
    return products

def search_products(query: str) -> list[Product]:
    """
    Search products by title or description.
    
    Args:
        query: Search term to match against title or description
    
    Returns:
        List of matching products
    """
    result = db.execute(
        """SELECT id, title, description, price, tax_percent, quantity 
           FROM products 
           WHERE title ILIKE %s OR description ILIKE %s
           ORDER BY id;""",
        (f"%{query}%", f"%{query}%")
    )
    
    products: list[Product] = []
    for row in result:
        products.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "price": row[3],
            "tax_percent": row[4],
            "quantity": row[5]
        })
    
    return products

def update_product(
    product_id: int,
    title: str | None = None,
    price: int | None = None,
    tax_percent: float | None = None,
    description: str | None = None,
    quantity: int | None = None
) -> bool:
    """
    Update a product's details. Only provided fields will be updated.
    
    Args:
        product_id: The ID of the product to update
        title: New title (optional)
        price: New price in cents (optional)
        tax_percent: New tax percentage (optional)
        description: New description (optional, pass empty string to clear)
        quantity: New stock quantity (optional)
    
    Returns:
        True if update was successful, False if product not found
    """
    # Build dynamic update query
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = %s")
        params.append(title)
    
    if price is not None:
        updates.append("price = %s")
        params.append(price)
    
    if tax_percent is not None:
        updates.append("tax_percent = %s")
        params.append(tax_percent)
    
    if description is not None:
        updates.append("description = %s")
        params.append(description)
    
    if quantity is not None:
        updates.append("quantity = %s")
        params.append(quantity)
    
    if not updates:
        return False
    
    params.append(product_id)
    query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s;"
    
    result = db.execute(query, tuple(params))
    return result is not None

def delete_product(product_id: int) -> bool:
    """
    Delete a product.
    
    Args:
        product_id: The ID of the product to delete
    
    Returns:
        True if deletion was successful, False if product not found
    """
    try:
        result = db.execute(
            "DELETE FROM products WHERE id = %s RETURNING id;",
            (product_id,)
        )
        return result is not None and len(result) > 0
    except Exception:
        # Product might be referenced by order_items (foreign key constraint)
        return False

def get_products_by_price_range(min_price: int, max_price: int) -> list[Product]:
    """
    Get products within a price range.
    
    Args:
        min_price: Minimum price in cents
        max_price: Maximum price in cents
    
    Returns:
        List of products within the price range
    """
    result = db.execute(
        """SELECT id, title, description, price, tax_percent, quantity 
           FROM products 
           WHERE price BETWEEN %s AND %s
           ORDER BY price;""",
        (min_price, max_price)
    )
    
    products: list[Product] = []
    for row in result:
        products.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "price": row[3],
            "tax_percent": row[4],
            "quantity": row[5]
        })
    
    return products


def check_stock_availability(product_id: int, quantity: int = 1) -> dict:
    """
    Check if a product has sufficient stock for the requested quantity.
    
    Args:
        product_id: The ID of the product to check
        quantity: The quantity requested (default: 1)
    
    Returns:
        Dict with 'available' (bool), 'quantity' (int), and 'message' (str)
    """
    product = get_product(product_id)
    
    if not product:
        return {
            "available": False,
            "quantity": 0,
            "message": f"Product #{product_id} not found"
        }
    
    available = product["quantity"] >= quantity
    
    return {
        "available": available,
        "quantity": product["quantity"],
        "product_name": product["title"],
        "message": f"{'✅ In stock' if available else '❌ Out of stock'} - {product['quantity']} available, {quantity} requested"
    }


def reserve_stock(product_id: int, quantity: int) -> bool:
    """
    Reserve/reduce stock for a product (for order placement or replacement).
    
    Args:
        product_id: The ID of the product
        quantity: The quantity to reserve
    
    Returns:
        True if successful, False if insufficient stock
    """
    # Check availability first
    check = check_stock_availability(product_id, quantity)
    if not check["available"]:
        return False
    
    # Reduce stock
    result = db.execute(
        "UPDATE products SET quantity = quantity - %s WHERE id = %s AND quantity >= %s RETURNING id;",
        (quantity, product_id, quantity)
    )
    
    return result is not None and len(result) > 0


def restore_stock(product_id: int, quantity: int) -> bool:
    """
    Restore/increase stock for a product (for cancellations or returns).
    
    Args:
        product_id: The ID of the product
        quantity: The quantity to restore
    
    Returns:
        True if successful
    """
    result = db.execute(
        "UPDATE products SET quantity = quantity + %s WHERE id = %s RETURNING id;",
        (quantity, product_id)
    )
    
    return result is not None and len(result) > 0


def get_low_stock_products(threshold: int = 10) -> list[Product]:
    """
    Get products with stock below a certain threshold.
    
    Args:
        threshold: Stock quantity threshold (default: 10)
    
    Returns:
        List of products with low stock
    """
    result = db.execute(
        """SELECT id, title, description, price, tax_percent, quantity 
           FROM products 
           WHERE quantity < %s
           ORDER BY quantity;""",
        (threshold,)
    )
    
    products: list[Product] = []
    for row in result:
        products.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "price": row[3],
            "tax_percent": row[4],
            "quantity": row[5]
        })
    
    return products
