import pandas as pd
import plotly.express as px
import streamlit as st

from utils.loader import filter_events, load_events

st.set_page_config(
    page_title="Force Posture Tracker",
    page_icon="🌐",
    layout="wide",
)

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── coordinate lookup (keyword → approximate lat/lon for to_location) ──────────
_COORDS: dict[str, tuple[float, float]] = {
    "arabian gulf":     (26.0,  54.0),
    "strait of hormuz": (26.5,  56.3),
    "hormuz":           (26.5,  56.3),
    "red sea":          (20.0,  38.5),
    "gulf of aden":     (12.5,  45.0),
    "diego garcia":     (-7.3,  72.4),
    "al udeid":         (25.1,  51.3),
    "qatar":            (25.3,  51.2),
    "al dhafra":        (24.2,  54.5),
    "uae":              (24.5,  54.4),
    "yemen":            (15.5,  48.5),
    "baledogle":        ( 2.2,  44.9),
    "somalia":          ( 2.3,  45.3),
    "lemonnier":        (11.5,  43.1),
    "djibouti":         (11.6,  43.1),
    "south china sea":  (15.0, 114.0),
    "philippine sea":   (17.0, 130.0),
    "luzon":            (16.0, 121.5),
    "palawan":          (10.0, 118.7),
    "philippines":      (14.6, 121.0),
    "darwin":           (-12.5, 130.8),
    "australia":        (-25.3, 133.8),
    "andersen":         (13.6, 144.9),
    "guam":             (13.5, 144.8),
    "kadena":           (26.4, 127.8),
    "okinawa":          (26.4, 127.8),
    "japan":            (35.7, 139.7),
    "thailand":         (15.9, 100.9),
    "western pacific":  (20.0, 140.0),
    "7th fleet":        (20.0, 135.0),
    "orzysz":           (53.8,  21.9),
    "poland":           (52.2,  21.0),
    "kogalniceanu":     (44.4,  28.5),
    "romania":          (44.4,  26.1),
    "mediterranean":    (35.0,  18.0),
    "north atlantic":   (50.0, -30.0),
    "north sea":        (56.0,   3.0),
    "latvia":           (57.0,  24.7),
    "estonia":          (58.6,  25.0),
    "baltics":          (57.5,  24.0),
}

BRANCH_COLORS: dict[str, str] = {
    "Navy":       "#1565C0",
    "Air Force":  "#0288D1",
    "Army":       "#388E3C",
    "Marines":    "#C62828",
    "Joint":      "#7B1FA2",
}

CONFIDENCE_COLORS: dict[str, str] = {
    "High": "#43A047",
    "Med":  "#FB8C00",
    "Low":  "#E53935",
}


def _resolve_coords(location: str) -> tuple[float, float] | None:
    loc = location.lower()
    for key, coords in _COORDS.items():
        if key in loc:
            return coords
    return None


# ── data ───────────────────────────────────────────────────────────────────────
df_all = load_events()

# ── sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Filters")
    st.divider()

    all_regions     = ["All"] + sorted(df_all["region"].dropna().unique().tolist())
    all_branches    = ["All"] + sorted(df_all["branch"].dropna().unique().tolist())
    all_confidences = ["All", "High", "Med", "Low"]

    sel_region     = st.selectbox("Region",     all_regions)
    sel_branch     = st.selectbox("Branch",     all_branches)
    sel_confidence = st.selectbox("Confidence", all_confidences)

    st.divider()
    st.caption(f"{len(df_all)} total events in database")

df = filter_events(
    df_all,
    region     = None if sel_region     == "All" else sel_region,
    branch     = None if sel_branch     == "All" else sel_branch,
    confidence = None if sel_confidence == "All" else sel_confidence,
).reset_index(drop=True)

# ── header ─────────────────────────────────────────────────────────────────────
st.title("Force Posture Tracker")

last_updated = df_all["date_added"].max()
last_updated_str = (
    last_updated.strftime("%B %d, %Y") if pd.notna(last_updated) else "N/A"
)
st.caption(
    f"U.S. military deployment posture as of March 2026  ·  "
    f"Database last updated: **{last_updated_str}**"
)
st.divider()

# ── metric cards ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Events",     len(df))
c2.metric("Active Regions",   df["region"].nunique())
c3.metric("High Confidence",  int((df["confidence"] == "High").sum()))
c4.metric("Asset Types",      df["asset_type"].nunique())

st.divider()

# ── map ────────────────────────────────────────────────────────────────────────
st.subheader("Deployment Map")

map_df = df.copy()
map_df["_lat"] = map_df["to_location"].apply(
    lambda x: (_resolve_coords(x) or (None, None))[0]
)
map_df["_lon"] = map_df["to_location"].apply(
    lambda x: (_resolve_coords(x) or (None, None))[1]
)
map_df = map_df.dropna(subset=["_lat", "_lon"])

if map_df.empty:
    st.info("No mappable events match the current filters.")
else:
    fig = px.scatter_geo(
        map_df,
        lat="_lat",
        lon="_lon",
        color="branch",
        color_discrete_map=BRANCH_COLORS,
        hover_name="asset_name",
        hover_data={
            "asset_type":  True,
            "region":      True,
            "confidence":  True,
            "date":        "|%b %d, %Y",
            "_lat":        False,
            "_lon":        False,
        },
        projection="natural earth",
    )
    fig.update_traces(
        marker=dict(size=11, opacity=0.88, line=dict(width=0.6, color="white"))
    )
    fig.update_geos(
        showland=True,       landcolor="#1e2130",
        showocean=True,      oceancolor="#0d1117",
        showlakes=True,      lakecolor="#0d1117",
        showcoastlines=True, coastlinecolor="#3a3f55",
        showcountries=True,  countrycolor="#2a2f45",
        showframe=False,
        bgcolor="#0d1117",
    )
    fig.update_layout(
        paper_bgcolor="#0d1117",
        font_color="#cdd6f4",
        margin=dict(l=0, r=0, t=0, b=0),
        height=460,
        legend=dict(
            title="Branch",
            bgcolor="#1e2130",
            bordercolor="#3a3f55",
            borderwidth=1,
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── event table ────────────────────────────────────────────────────────────────
st.subheader("Events")

TABLE_COLS = [
    "event_id", "date", "asset_name", "asset_type",
    "branch", "region", "confidence",
]
display_df = df[TABLE_COLS].copy()
display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

selection = st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "event_id":   st.column_config.TextColumn("ID",         width="small"),
        "date":       st.column_config.TextColumn("Date",       width="small"),
        "asset_name": st.column_config.TextColumn("Asset",      width="large"),
        "asset_type": st.column_config.TextColumn("Type",       width="medium"),
        "branch":     st.column_config.TextColumn("Branch",     width="small"),
        "region":     st.column_config.TextColumn("Region",     width="medium"),
        "confidence": st.column_config.TextColumn("Confidence", width="small"),
    },
)

# ── detail panel ───────────────────────────────────────────────────────────────
selected_rows = selection.selection.rows if selection.selection else []
if selected_rows:
    event = df.iloc[selected_rows[0]]

    st.divider()

    conf_color = CONFIDENCE_COLORS.get(event["confidence"], "#888")
    branch_color = BRANCH_COLORS.get(event["branch"], "#888")

    st.markdown(
        f"### {event['asset_name']} &nbsp;"
        f"<span style='font-size:0.8rem; background:{branch_color}; "
        f"color:white; padding:2px 8px; border-radius:4px;'>{event['branch']}</span>"
        f" &nbsp;"
        f"<span style='font-size:0.8rem; background:{conf_color}; "
        f"color:white; padding:2px 8px; border-radius:4px;'>{event['confidence']} Confidence</span>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.markdown("**Event Details**")
        st.markdown(f"- **ID:** `{event['event_id']}`")
        date_str = (
            event["date"].strftime("%B %d, %Y")
            if pd.notna(event["date"])
            else "N/A"
        )
        st.markdown(f"- **Date:** {date_str}")
        st.markdown(f"- **Asset Type:** {event['asset_type']}")
        st.markdown(f"- **Branch:** {event['branch']}")
        st.markdown(f"- **Region:** {event['region']}")

    with right:
        st.markdown("**Positioning**")
        st.markdown(f"- **From:** {event['from_location']}")
        st.markdown(f"- **To:** {event['to_location']}")
        st.markdown("**Source**")
        st.markdown(f"- **Publication:** {event['primary_source']}")
        st.markdown(
            f"- **URL:** [{event['source_url']}]({event['source_url']})"
        )

    st.markdown("**Analyst Context**")
    st.info(event["context"])

    tags = event["tags"] if isinstance(event["tags"], list) else []
    if tags:
        st.markdown(
            " ".join(
                f"<code style='background:#1e2130; padding:2px 6px; "
                f"border-radius:3px; font-size:0.78rem;'>{t}</code>"
                for t in tags
            ),
            unsafe_allow_html=True,
        )
else:
    st.caption("Select a row to view full event details.")
