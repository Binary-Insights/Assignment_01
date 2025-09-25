def normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching."""
    import re
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace common abbreviations
    replacements = {
        'amt': 'amount',
        'acct': 'account',
        'accum': 'accumulated',
        'amt.': 'amount',
        'bal.': 'balance',
        'corp.': 'corporation',
        'inc.': 'incorporated',
        'intl.': 'international',
        'pct': 'percent',
        'w/': 'with',
        'w/o': 'without',
        'yr': 'year'
    }
    
    for abbrev, full in replacements.items():
        text = text.replace(abbrev, full)
    
    # Remove parentheses and their contents
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    
    return text

def get_similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity score between two texts."""
    from difflib import SequenceMatcher
    
    # Normalize both texts
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)
    
    # Get word sets
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Calculate Jaccard similarity for word sets
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    jaccard = intersection / union if union > 0 else 0
    
    # Calculate sequence similarity
    sequence_ratio = SequenceMatcher(None, text1, text2).ratio()
    
    # Combine both scores with weights
    return 0.4 * jaccard + 0.6 * sequence_ratio

def find_best_match(target: str, candidates: list[str], threshold: float = 0.7) -> tuple[str, float]:
    """Find the best matching text from a list of candidates."""
    best_score = 0
    best_match = None
    
    for candidate in candidates:
        score = get_similarity_score(target, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_score >= threshold:
        return best_match, best_score
    return None, 0.0