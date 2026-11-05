import re
import difflib
from students import MASTER_STUDENTS, KNOWN_ALIASES

SORTED_ALIASES = sorted(KNOWN_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)

def clean_name(raw_text: str) -> str:
    """Removes timestamps, phone status bar noise, MAE tags, emojis, and special chars."""
    t = raw_text.strip().lower()
    
    # Skip obvious system / UI noise
    skip_keywords = [
        "poll details", "yesterday", "today", "device", "volte", "100%", "5g", "going to home", "votes",
        "star", "back"
    ]
    for kw in skip_keywords:
        if kw in t and len(t) < 30 and (":" in t or "yesterday" in t or "today" in t or "poll" in t):
            return ""

    # Remove whole word time indicators like '\bat\b', '\bmae\b', timestamps
    t = re.sub(r"\b(today|yesterday|at|mae|pm|am)\b|\d+[:.]\d+", "", t, flags=re.I)
    # Remove non-alphanumeric chars except space and underscore
    t = re.sub(r"[^\w\s]", "", t)
    return " ".join(t.split())

def match_text_to_student(raw_text: str):
    """
    Returns (roll_no, official_name, match_source) if matched, else None.
    """
    cleaned = clean_name(raw_text)
    if not cleaned or len(cleaned) < 3:
        return None

    # 1. Exact alias check
    if cleaned in KNOWN_ALIASES:
        roll = KNOWN_ALIASES[cleaned]
        return roll, MASTER_STUDENTS[roll], f"Exact Alias ({cleaned})"

    # 2. Longest-match alias substring check (word boundary or whole tokens)
    cleaned_tokens = set(cleaned.split())
    for alias, roll in SORTED_ALIASES:
        alias_tokens = set(alias.split())
        # If all words of alias are in the text
        if alias_tokens.issubset(cleaned_tokens):
            return roll, MASTER_STUDENTS[roll], f"Word Subset Match ({alias})"
        # If alias is exact substring
        if alias in cleaned:
            return roll, MASTER_STUDENTS[roll], f"Alias Substring ({alias})"

    # 3. Direct match against master names
    master_lower = {name.lower(): roll for roll, name in MASTER_STUDENTS.items()}
    if cleaned in master_lower:
        roll = master_lower[cleaned]
        return roll, MASTER_STUDENTS[roll], "Master Exact"

    # 4. Fuzzy match against master names
    close_matches = difflib.get_close_matches(cleaned, master_lower.keys(), n=1, cutoff=0.7)
    if close_matches:
        roll = master_lower[close_matches[0]]
        return roll, MASTER_STUDENTS[roll], f"Fuzzy Match ({close_matches[0]})"

    # 5. Fuzzy match against alias keys
    close_aliases = difflib.get_close_matches(cleaned, list(KNOWN_ALIASES.keys()), n=1, cutoff=0.7)
    if close_aliases:
        roll = KNOWN_ALIASES[close_aliases[0]]
        return roll, MASTER_STUDENTS[roll], f"Fuzzy Alias ({close_aliases[0]})"

    return None

def process_extracted_lines(all_lines: list[str]):
    """
    Processes a list of raw text lines and returns:
    - matched_students: dict of roll_no -> { 'name': ..., 'matched_from': ..., 'source': ... }
    - remaining_students: list of (roll_no, official_name)
    - unmapped_lines: list of lines that had text but didn't match anyone
    """
    matched_students = {}
    unmapped_lines = []

    for line in all_lines:
        line_str = line.strip()
        if not line_str:
            continue
        
        match = match_text_to_student(line_str)
        if match:
            roll, name, src = match
            if roll not in matched_students:
                matched_students[roll] = {
                    "roll": roll,
                    "name": name,
                    "raw_text": line_str,
                    "match_type": src
                }
        else:
            cleaned = clean_name(line_str)
            if cleaned and len(cleaned) >= 4 and not cleaned.isdigit():
                unmapped_lines.append(line_str)

    # Compute set difference (Remaining / Absent)
    all_rolls = set(MASTER_STUDENTS.keys())
    voted_rolls = set(matched_students.keys())
    remaining_rolls = sorted(list(all_rolls - voted_rolls))

    remaining_students = [
        {"roll": r, "name": MASTER_STUDENTS[r]} for r in remaining_rolls
    ]

    return matched_students, remaining_students, unmapped_lines
