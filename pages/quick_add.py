import json
from datetime import date
from pathlib import Path

import anthropic
import streamlit as st

st.set_page_config(
    page_title="Quick Add Event",
    page_icon="⚡",
    layout="wide",
)

with open(Path(__file__).parent.parent / "assets" / "style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

EVENTS_PATH = Path(__file__).parent.parent / "data" / "events.json"
MODEL = "claude-sonnet-4-20250514"

REQUIRED_FIELDS = [
    "asset_name", "asset_type", "branch", "event_type",
    "from_location", "to_location", "region", "date",
    "confidence", "primary_source", "context", "tags",
]

SYSTEM_PROMPT = """You are a military intelligence analyst assistant. Extract a structured event from the provided text and return ONLY a valid JSON object — no markdown, no code fences, no explanation, no commentary before or after.

Return exactly these fields:

{
  "asset_name":      "full name of the unit, vessel, aircraft, or weapon system",
  "asset_type":      "descriptive type, e.g. Carrier Strike Group / Strike Mission / Airborne Brigade",
  "branch":          "exactly one of: Navy | Air Force | Army | Marines | Joint",
  "event_type":      "exactly one of: deployment | strike",
  "from_location":   "origin base, port, or launch location",
  "to_location":     "destination, target, or area of operations",
  "region":          "exactly one of: Middle East | Indo-Pacific | Europe | Africa",
  "date":            "YYYY-MM-DD — best estimate if not stated explicitly",
  "confidence":      "exactly one of: High | Med | Low",
  "primary_source":  "publication or organization name",
  "source_url":      "URL if present in the text, otherwise empty string",
  "context":         "2–3 sentence analyst-style explanation of the event and its significance",
  "tags":            ["array", "of", "lowercase-hyphenated", "keyword", "strings"]
}

Rules:
- Return ONLY the JSON object. Nothing else.
- If a field cannot be determined, use a reasonable default or empty string — never omit a field.
- tags should have 5–10 entries that reflect the event type, assets, location, and operation name if mentioned.
- confidence should reflect how clearly the text supports the extracted details: High = explicitly stated, Med = implied, Low = inferred."""


# ── helpers ────────────────────────────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    """Remove markdown code fences Claude occasionally wraps JSON in."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1  # skip the ```json or ``` line
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()
    return text


def _get_next_event_id() -> str:
    with open(EVENTS_PATH) as f:
        events = json.load(f)
    if not events:
        return "EVT-001"
    nums = [
        int(e["event_id"].split("-")[1])
        for e in events
        if e.get("event_id", "").startswith("EVT-")
    ]
    return f"EVT-{max(nums) + 1:03d}"


def _call_claude(raw_text: str) -> str:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to .streamlit/secrets.toml as:\n  ANTHROPIC_API_KEY = \"sk-ant-...\""
        )
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Extract a structured military event from this text:\n\n{raw_text}",
            }
        ],
    )
    return _strip_fences(message.content[0].text)


def _validate(json_str: str) -> tuple[dict | None, str | None]:
    """Parse and validate the JSON string. Returns (parsed_dict, error_message)."""
    try:
        obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    missing = [f for f in REQUIRED_FIELDS if f not in obj]
    if missing:
        return obj, f"Missing required fields: {', '.join(missing)}"
    valid_branches = {"Navy", "Air Force", "Army", "Marines", "Joint"}
    valid_event_types = {"deployment", "strike"}
    valid_regions = {"Middle East", "Indo-Pacific", "Europe", "Africa"}
    valid_confidences = {"High", "Med", "Low"}
    errors = []
    if obj.get("branch") not in valid_branches:
        errors.append(f"branch must be one of: {', '.join(sorted(valid_branches))}")
    if obj.get("event_type") not in valid_event_types:
        errors.append(f"event_type must be 'deployment' or 'strike'")
    if obj.get("region") not in valid_regions:
        errors.append(f"region must be one of: {', '.join(sorted(valid_regions))}")
    if obj.get("confidence") not in valid_confidences:
        errors.append(f"confidence must be High, Med, or Low")
    return obj, "; ".join(errors) if errors else None


# ── session state ──────────────────────────────────────────────────────────────
if "qa_json_str" not in st.session_state:
    st.session_state.qa_json_str = None
if "qa_error" not in st.session_state:
    st.session_state.qa_error = None
if "qa_added" not in st.session_state:
    st.session_state.qa_added = None

# ── page ───────────────────────────────────────────────────────────────────────
st.title("⚡ Quick Add Event")
st.caption(
    f"Paste a tweet, headline, or article excerpt — Claude ({MODEL}) "
    "extracts a structured event ready to add to the database."
)
st.divider()

raw_text = st.text_area(
    "Paste raw text",
    height=160,
    placeholder=(
        "e.g. 'BREAKING: USS Abraham Lincoln strike group entered the Persian Gulf "
        "today as U.S.-Iran tensions reach their highest point since 2020. "
        "— Reuters, Jan 23 2026'"
    ),
)

col_btn, col_hint = st.columns([1, 5])
with col_btn:
    extract_clicked = st.button(
        "Extract Event",
        type="primary",
        disabled=not raw_text.strip(),
        use_container_width=True,
    )
with col_hint:
    st.caption("Claude will infer all schema fields from the text above.")

if extract_clicked:
    st.session_state.qa_json_str = None
    st.session_state.qa_error = None
    st.session_state.qa_added = None
    with st.spinner(f"Calling {MODEL}…"):
        try:
            raw_result = _call_claude(raw_text)
            _, err = _validate(raw_result)
            st.session_state.qa_json_str = json.dumps(
                json.loads(raw_result), indent=2
            )
            if err:
                st.session_state.qa_error = err
        except Exception as exc:
            st.session_state.qa_error = str(exc)

# ── error banner ───────────────────────────────────────────────────────────────
if st.session_state.qa_error and not st.session_state.qa_json_str:
    st.error(st.session_state.qa_error)

# ── review + edit ──────────────────────────────────────────────────────────────
if st.session_state.qa_json_str:
    st.divider()
    st.subheader("Extracted Event — Review & Edit")

    if st.session_state.qa_error:
        st.warning(f"Validation warning: {st.session_state.qa_error}")

    edited = st.text_area(
        "JSON (editable — fix any fields before adding)",
        value=st.session_state.qa_json_str,
        height=420,
    )

    parsed, validation_error = _validate(edited)

    # Live validation feedback under the editor
    if validation_error:
        st.error(f"Fix before adding: {validation_error}")
    else:
        # Preview key fields as a quick visual check
        p = parsed
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Asset", p.get("asset_name", "")[:28])
        c2.metric("Branch / Type", f"{p.get('branch','')} · {p.get('event_type','')}")
        c3.metric("Region", p.get("region", ""))
        c4.metric("Confidence", p.get("confidence", ""))

    st.divider()

    add_col, reset_col = st.columns([1, 1])
    with add_col:
        if st.button(
            "Add to Database",
            type="primary",
            disabled=bool(validation_error),
            use_container_width=True,
        ):
            parsed["event_id"] = _get_next_event_id()
            parsed["date_added"] = date.today().isoformat()
            # Ensure tags is a list
            if isinstance(parsed.get("tags"), str):
                parsed["tags"] = [t.strip() for t in parsed["tags"].split(",")]

            with open(EVENTS_PATH) as f:
                events = json.load(f)
            events.append(parsed)
            with open(EVENTS_PATH, "w") as f:
                json.dump(events, f, indent=2)

            st.session_state.qa_added = parsed["event_id"]
            st.session_state.qa_json_str = None
            st.session_state.qa_error = None
            st.rerun()

    with reset_col:
        if st.button("Clear", use_container_width=True):
            st.session_state.qa_json_str = None
            st.session_state.qa_error = None
            st.session_state.qa_added = None
            st.rerun()

# ── success banner ─────────────────────────────────────────────────────────────
if st.session_state.qa_added:
    st.success(
        f"**{st.session_state.qa_added}** added to `data/events.json`. "
        "Return to the main dashboard to see it on the map.",
        icon="✅",
    )
    st.session_state.qa_added = None
