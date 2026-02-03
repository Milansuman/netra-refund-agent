from typing import TypedDict
from pathlib import Path
import re

POLICY_FILE_PATH = Path(__file__).parent.parent / "policy" / "policy-v1.0.0.md"

class Policy(TypedDict):
    category: str
    title: str
    content: str

# Category identifiers as defined in the policy file
POLICY_CATEGORIES = [
    "DAMAGED_ITEM",
    "MISSING_ITEM",
    "LATE_DELIVERY",
    "DUPLICATE_CHARGE",
    "CANCELLATION",
    "RETURN_PICKUP_FAILED",
    "RETURN_TO_ORIGIN",
    "PAYMENT_DEBITED_BUT_FAILED",
    "SERVICE_NOT_DELIVERED",
    "PRICE_ADJUSTMENT"
]

def _parse_policy_file() -> dict[str, Policy]:
    """Parse the policy markdown file and extract policies by category."""
    policies: dict[str, Policy] = {}
    
    with open(POLICY_FILE_PATH, "r") as f:
        content = f.read()
    
    # Split by section headers (## numbered sections)
    sections = re.split(r'\n---\n\n## \d+\.', content)
    
    # Skip the header section (first split)
    for section in sections[1:]:
        # Extract category identifier from title (e.g., "Damaged or Defective Item (DAMAGED_ITEM)")
        match = re.search(r'\(([A-Z_]+)\)', section)
        if match:
            category = match.group(1)
            
            # Extract title (first line)
            lines = section.strip().split('\n')
            title_match = re.match(r'(.+?)\s*\([A-Z_]+\)', lines[0])
            title = title_match.group(1).strip() if title_match else lines[0].strip()
            
            # Content is everything after the title
            content_lines = lines[1:]
            policy_content = '\n'.join(content_lines).strip()
            
            policies[category] = {
                "category": category,
                "title": title,
                "content": policy_content
            }
    
    return policies

# Cache the parsed policies
_policies_cache: dict[str, Policy] | None = None

def _get_policies_cache() -> dict[str, Policy]:
    """Get or initialize the policies cache."""
    global _policies_cache
    if _policies_cache is None:
        _policies_cache = _parse_policy_file()
    return _policies_cache

def get_policy_by_category(category: str) -> Policy | None:
    """
    Retrieve the policy for a specific category.
    
    Args:
        category: The category identifier (e.g., "DAMAGED_ITEM", "MISSING_ITEM")
    
    Returns:
        Policy object containing category, title, and content, or None if not found.
    """
    policies = _get_policies_cache()
    return policies.get(category)

def get_all_policies() -> list[Policy]:
    """
    Retrieve all policies.
    
    Returns:
        List of all Policy objects.
    """
    policies = _get_policies_cache()
    return list(policies.values())

def get_all_categories() -> list[str]:
    """
    Get all available policy category identifiers.
    
    Returns:
        List of category strings.
    """
    return POLICY_CATEGORIES.copy()
