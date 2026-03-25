import anthropic

client = anthropic.Anthropic()


def extract_events(raw_text: str) -> list[dict]:
    """
    Use Claude to extract structured posture events from raw text.

    Returns a list of event dicts, e.g.:
    [{"timestamp": "...", "type": "posture", "description": "..."}]
    """
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract posture-related events from the following text. "
                    "Return a JSON array of objects with keys: timestamp, type, description.\n\n"
                    f"{raw_text}"
                ),
            }
        ],
    )

    import json
    import re

    content = message.content[0].text
    # Extract JSON array from response
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []
