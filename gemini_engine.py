import json
from google import genai
from google.genai import types
from students import MASTER_STUDENTS, KNOWN_ALIASES

PROMPT_TEMPLATE = f"""
You are an intelligent attendance and voter analyst for Mechanical Workshop [ME 104].
Below is the official list of 60 students in the batch and their known WhatsApp aliases/nicknames:

OFFICIAL 60 STUDENTS:
{json.dumps(MASTER_STUDENTS, indent=2)}

SPECIAL KNOWN NICKNAMES / ALIASES:
{json.dumps(KNOWN_ALIASES, indent=2)}

TASK:
1. Examine the provided screenshot(s) of a WhatsApp group poll.
2. Extract EVERY voter shown in the screenshots. Note that "You" is SHOURYA NARAYAN (Roll 260103052).
3. Distinguish carefully:
   - "Satyam Chandel" -> Roll 260103049 (SATYAM RAJ)
   - "Satyam Bablu" -> Roll 260103016 (BURLE PEDDA SATYAM NAIDU)
   - "Shubham Karnataka" / "Shubham Rathod" -> Roll 260103055 (SHUBHAM RATHOD)
   - "Shubham Jhajhria" / "Shubham Jharjaria" / "Shubham" -> Roll 260103054 (SHUBHAM)
   - "Shubh Agrawal" / "Shubh Agarwal" -> Roll 260103053 (SHUBH AGRAWAL)
   - "Ayush Mishra Ciyar Ka bachha" -> Roll 260103012 (AYUSH MISHRA)
   - "Ayush Mishra Mae" -> Roll 260103013 (AYUSH MISHRA)
4. If there are random phone numbers or accounts that do not belong to the 60 students (like "~ Pikachu"), put them in 'unrecognized_entries'.
5. Return ONLY a valid JSON object matching the requested schema.
"""

def analyze_screenshots_with_gemini(image_bytes_list: list[bytes], api_key: str, model_name: str = "gemini-3.8-flash"):
    """
    Analyzes multiple screenshots simultaneously using Gemini Multimodal Vision.
    Returns:
    - matched_students: dict of roll_no -> { 'roll': ..., 'name': ..., 'contact_name': ... }
    - remaining_students: list of { 'roll': ..., 'name': ... }
    - unrecognized: list of strings
    """
    client = genai.Client(api_key=api_key)

    # Convert bytes to genai image parts
    contents = [PROMPT_TEMPLATE]
    for idx, img_bytes in enumerate(image_bytes_list, 1):
        contents.append(f"Screenshot #{idx}:")
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "voted_students": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "roll": {"type": "INTEGER"},
                        "name": {"type": "STRING"},
                        "contact_name": {"type": "STRING"}
                    },
                    "required": ["roll", "name"]
                }
            },
            "unrecognized_entries": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        },
        "required": ["voted_students"]
    }

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.1
    )

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config
    )

    data = json.loads(response.text)
    voted_list = data.get("voted_students", [])
    unrecognized = data.get("unrecognized_entries", [])

    matched = {}
    for item in voted_list:
        roll = item.get("roll")
        if roll and roll in MASTER_STUDENTS:
            matched[roll] = {
                "roll": roll,
                "name": MASTER_STUDENTS[roll],
                "raw_text": item.get("contact_name", MASTER_STUDENTS[roll]),
                "match_type": "Gemini Multimodal Vision AI"
            }

    all_rolls = set(MASTER_STUDENTS.keys())
    voted_rolls = set(matched.keys())
    remaining_rolls = sorted(list(all_rolls - voted_rolls))

    remaining = [
        {"roll": r, "name": MASTER_STUDENTS[r]} for r in remaining_rolls
    ]

    return matched, remaining, unrecognized
