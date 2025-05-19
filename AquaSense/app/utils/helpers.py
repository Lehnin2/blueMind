import re

def is_arabic(text: str) -> bool:
    """
    Check if text contains Arabic characters.
    
    Args:
        text: The text to check
        
    Returns:
        True if text contains Arabic characters, False otherwise
    """
    return bool(re.search(r'[\u0600-\u06FF]', text))