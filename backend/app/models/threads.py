from db.connections import db

def clear_thread(thread_id: str) -> bool:
    """
    Clear all state associated with a conversation thread.
    
    Args:
        thread_id: The thread ID to clear
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Delete all checkpoints for this thread
        # Note: PostgresSaver doesn't have a direct delete method,
        # so we'll need to use the underlying connection
        db.execute(
            "DELETE FROM checkpoints WHERE thread_id = %s",
            (thread_id,)
        )
        
        return True
    except Exception as e:
        print(f"Error clearing thread {thread_id}: {e}")
        return False
