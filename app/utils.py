import re

def slugify(text):
    """
    Generates a slug from the given text.
    Replaces whitespace with dashes and lowercases the text.
    """
    if not text:
        return ""
    return re.sub(r'\s+', '-', text).lower()
