from db.connections import db
from schemas.tickets import Ticket

def create_ticket(user_id: int, order_id: int, title: str, description: str | None = None) -> int:
    """
    Create a new support ticket for manual review.
    
    Args:
        user_id: The ID of the user raising the ticket
        order_id: The ID of the order this ticket is related to
        title: A brief title describing the issue
        description: Optional detailed description of the issue
    
    Returns:
        The ID of the created ticket
    """
    result = db.execute(
        "INSERT INTO tickets (order_id, user_id, title, description) VALUES (%s, %s, %s, %s) RETURNING id;",
        (order_id, user_id, title, description)
    )
    return result[0][0]

def get_user_tickets(user_id: int) -> list[Ticket]:
    """
    Get all tickets for a specific user.
    
    Args:
        user_id: The ID of the user
    
    Returns:
        List of tickets
    """
    result = db.execute(
        "SELECT id, order_id, user_id, title, description FROM tickets WHERE user_id = %s ORDER BY id DESC;",
        (user_id,)
    )
    
    tickets: list[Ticket] = []
    for row in result:
        tickets.append({
            "id": row[0],
            "order_id": row[1],
            "user_id": row[2],
            "title": row[3],
            "description": row[4]
        })
    
    return tickets
