import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import load_config
from i18n import LANGUAGE_NAMES, t
from storage import latest, recent

cfg = load_config()
db_path = cfg["storage"]["db_path"]
warn = cfg["thresholds"]["warn"]
alert = cfg["thresholds"]["alert"]
refresh = cfg["dashboard"]["refresh_seconds"]
default_window = cfg["dashboard"]["default_window_minutes"]
default_lang = cfg.get("language", "de")

# language must be resolved before set_page_config so the ⋮ menu is localized.
# precedence: ?lang= query param → session_state → config.yaml
_qp_lang = st.query_params.get("lang") if hasattr(st, "query_params") else None
if "lang" not in st.session_state:
    st.session_state.lang = _qp_lang or default_lang
elif _qp_lang and _qp_lang != st.session_state.lang:
    st.session_state.lang = _qp_lang

_page_lang = st.session_state.lang
st.set_page_config(
    page_title=t(_page_lang, "title"),
    layout="wide",
    menu_items={
        "About": t(_page_lang, "menu_about"),
        "Get help": None,
        "Report a bug": None,
    },
)

with st.sidebar:
    codes = list(LANGUAGE_NAMES.keys())
    idx = codes.index(st.session_state.lang) if st.session_state.lang in codes else 0
    chosen = st.selectbox(
        "🌐 " + t(st.session_state.lang, "language"),
        codes, index=idx, format_func=lambda c: LANGUAGE_NAMES[c],
    )
    st.session_state.lang = chosen

lang = st.session_state.lang
st.title(t(lang, "title"))

with st.sidebar:
    st.header(t(lang, "settings"))
    options = [5, 15, 60, 240, 1440]
    win_idx = options.index(default_window) if default_window in options else 1
    window = st.selectbox(t(lang, "window_minutes"), options, index=win_idx)
    st.caption(t(lang, "auto_refresh", s=refresh))

latest_row = latest(db_path)
rows = recent(db_path, window)

col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    current = latest_row["analog"] if latest_row and latest_row["analog"] is not None else 0
    max_val = max(1023, alert * 1.2)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current,
        title={"text": t(lang, "current_analog")},
        gauge={
            "axis": {"range": [0, max_val]},
            "bar": {"color": "black"},
            "steps": [
                {"range": [0, warn], "color": "#b6e3b6"},
                {"range": [warn, alert], "color": "#ffe08a"},
                {"range": [alert, max_val], "color": "#ff7b7b"},
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "value": alert},
        },
    ))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    digital = latest_row["digital"] if latest_row else None
    ts = latest_row["ts"] if latest_row else "—"
    color = "#ff4b4b" if digital == 0 else "#4caf50" if digital == 1 else "#888"
    label = (t(lang, "digital_tripped") if digital == 0
             else t(lang, "digital_ok") if digital == 1
             else t(lang, "digital_nodata"))
    st.markdown(
        f"""
        <div style='text-align:center;padding:20px;border-radius:10px;background:{color};color:white;'>
            <div style='font-size:18px;'>{t(lang, "digital_label")}</div>
            <div style='font-size:42px;font-weight:bold;margin:10px 0;'>{label}</div>
            <div style='font-size:12px;opacity:0.85;'>{t(lang, "last", ts=ts)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    if rows:
        df = pd.DataFrame(rows)
        df["analog"] = pd.to_numeric(df["analog"], errors="coerce")
        st.metric(t(lang, "mean"), f"{df['analog'].mean():.0f}")
        st.metric(t(lang, "min"), f"{df['analog'].min():.0f}")
        st.metric(t(lang, "max"), f"{df['analog'].max():.0f}")
        st.metric(t(lang, "samples"), len(df))
    else:
        st.info(t(lang, "no_data"))

st.subheader(t(lang, "last_window", n=window))
if rows:
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"])
    df["analog"] = pd.to_numeric(df["analog"], errors="coerce")
    line = go.Figure()
    line.add_trace(go.Scatter(x=df["ts"], y=df["analog"], mode="lines",
                              name=t(lang, "analog"), line=dict(color="#1f77b4")))
    line.add_hline(y=warn, line_dash="dash", line_color="orange",
                   annotation_text=t(lang, "warn"))
    line.add_hline(y=alert, line_dash="dash", line_color="red",
                   annotation_text=t(lang, "alert"))
    line.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=10),
                       xaxis_title="", yaxis_title=t(lang, "analog"))
    st.plotly_chart(line, use_container_width=True)

    if "digital" in df:
        dig = go.Figure()
        dig.add_trace(go.Scatter(x=df["ts"], y=pd.to_numeric(df["digital"], errors="coerce"),
                                 mode="lines", line_shape="hv", line=dict(color="#d62728")))
        dig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=10),
                          yaxis=dict(tickvals=[0, 1], range=[-0.1, 1.1]),
                          title=t(lang, "digital_label"))
        st.plotly_chart(dig, use_container_width=True)
else:
    st.info(t(lang, "waiting"))

import time as _t
_t.sleep(refresh)
st.rerun()
