import json
from pathlib import Path

import pandas as pd

EVENTS_PATH = Path(__file__).parent.parent / "data" / "events.json"


def load_events() -> pd.DataFrame:
    """Read data/events.json and return a pandas DataFrame.

    Returns an empty DataFrame with the expected columns if the file is
    missing or contains no records.
    """
    if not EVENTS_PATH.exists():
        return pd.DataFrame()

    with open(EVENTS_PATH) as f:
        records = json.load(f)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    return df


def filter_events(
    df: pd.DataFrame,
    region: str | None = None,
    branch: str | None = None,
    confidence: str | None = None,
    event_type: str | None = None,
) -> pd.DataFrame:
    """Filter events DataFrame by optional parameters.

    Each parameter is case-insensitive. Unspecified parameters are ignored
    (i.e. no filter applied for that column).

    Args:
        df:          DataFrame returned by load_events().
        region:      Match rows where the 'region' column equals this value.
        branch:      Match rows where the 'branch' column equals this value.
        confidence:  Match rows where the 'confidence' column equals this value
                     (e.g. 'High', 'Med', 'Low').
        event_type:  Match rows where the 'event_type' column equals this value
                     (e.g. 'deployment', 'strike').

    Returns:
        Filtered DataFrame (original index preserved).
    """
    if df.empty:
        return df

    mask = pd.Series(True, index=df.index)

    if region is not None:
        mask &= df["region"].str.lower() == region.lower()

    if branch is not None:
        mask &= df["branch"].str.lower() == branch.lower()

    if confidence is not None:
        mask &= df["confidence"].str.lower() == confidence.lower()

    if event_type is not None:
        mask &= df["event_type"].str.lower() == event_type.lower()

    return df[mask]
