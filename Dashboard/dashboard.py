import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import streamlit as st

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Air Quality Insights Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# Theme
# =========================
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .hero {
            padding: 1.1rem 1.2rem;
            border-radius: 1.2rem;
            background: linear-gradient(135deg, rgba(15,23,42,1) 0%, rgba(30,41,59,1) 55%, rgba(56,189,248,0.24) 100%);
            color: white;
            box-shadow: 0 14px 40px rgba(15, 23, 42, 0.16);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.15;
        }
        .hero p {
            margin: 0.35rem 0 0 0;
            opacity: 0.92;
            font-size: 0.98rem;
        }
        .card {
            padding: 1rem 1rem;
            border-radius: 1rem;
            background: white;
            border: 1px solid rgba(148,163,184,0.22);
            box-shadow: 0 8px 25px rgba(15,23,42,0.06);
        }
        .insight {
            padding: 0.9rem 1rem;
            border-radius: 1rem;
            background: rgba(14,165,233,0.08);
            border: 1px solid rgba(14,165,233,0.20);
        }
        .small-muted {
            color: #64748b;
            font-size: 0.92rem;
        }
        div[data-testid="stMetric"] {
            background: white;
            padding: 0.4rem 0.7rem;
            border-radius: 0.9rem;
            border: 1px solid rgba(148,163,184,0.18);
            box-shadow: 0 6px 18px rgba(15,23,42,0.05);
        }
        div[data-testid="stDataFrame"] {
            border-radius: 1rem;
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Helpers
# =========================
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_NAME_ID = {
    "January": "Januari",
    "February": "Februari",
    "March": "Maret",
    "April": "April",
    "May": "Mei",
    "June": "Juni",
    "July": "Juli",
    "August": "Agustus",
    "September": "September",
    "October": "Oktober",
    "November": "November",
    "December": "Desember",
}


def find_data_file() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "air_quality_cleaned.csv",
        here / "Dashboard" / "air_quality_cleaned.csv",
        here.parent / "Dashboard" / "air_quality_cleaned.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "File air_quality_cleaned.csv tidak ditemukan. Letakkan file tersebut di folder yang sama dengan app.py "
        "atau di folder Dashboard."
    )


@st.cache_data(show_spinner=False)
def load_data(path_str: str) -> pd.DataFrame:
    df = pd.read_csv(path_str)

    # Ensure datetime fields are usable
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]], errors="coerce")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        df["date"] = df["datetime"].dt.normalize()

    if "month_name" not in df.columns:
        df["month_name"] = df["datetime"].dt.strftime("%B")
    if "day_name" not in df.columns:
        df["day_name"] = df["datetime"].dt.day_name()
    if "year_month" not in df.columns:
        df["year_month"] = df["datetime"].dt.to_period("M").astype(str)
    if "season" not in df.columns:
        month = df["datetime"].dt.month
        df["season"] = np.select(
            [
                month.isin([12, 1, 2]),
                month.isin([3, 4, 5]),
                month.isin([6, 7, 8]),
                month.isin([9, 10, 11]),
            ],
            ["Winter", "Spring", "Summer", "Autumn"],
            default="Unknown",
        )
    if "time_period" not in df.columns:
        hour = df["datetime"].dt.hour
        df["time_period"] = np.select(
            [
                hour.isin([0, 1, 2, 3, 4, 5]),
                hour.isin([6, 7, 8, 9, 10, 11]),
                hour.isin([12, 13, 14, 15, 16, 17]),
                hour.isin([18, 19, 20, 21, 22, 23]),
            ],
            ["Dini Hari", "Pagi", "Siang", "Malam"],
            default="Unknown",
        )
    if "pm25_category" not in df.columns:
        bins = [-np.inf, 12, 35.4, 55.4, 150.4, np.inf]
        labels = ["Baik", "Sedang", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
        df["pm25_category"] = pd.cut(df["PM2.5"], bins=bins, labels=labels)
    if "is_unhealthy" not in df.columns:
        df["is_unhealthy"] = df["PM2.5"] >= 55

    return df


def fmt(x, digits=2):
    if pd.isna(x):
        return "-"
    return f"{x:,.{digits}f}"


def styled_subheader(title, subtitle=""):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<div class='small-muted'>{subtitle}</div>", unsafe_allow_html=True)


def safe_fig_to_streamlit(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def compute_insights(df: pd.DataFrame) -> dict:
    total_rows = len(df)
    total_station = df["station"].nunique() if "station" in df.columns else 0
    avg_pm25 = df["PM2.5"].mean()
    unhealthy_share = df["is_unhealthy"].mean() * 100 if len(df) else np.nan

    station_means = df.groupby("station")["PM2.5"].mean().sort_values(ascending=False) if len(df) else pd.Series(dtype=float)
    top_station = station_means.index[0] if len(station_means) else "-"
    top_station_val = station_means.iloc[0] if len(station_means) else np.nan
    cleanest_station = station_means.index[-1] if len(station_means) else "-"
    cleanest_station_val = station_means.iloc[-1] if len(station_means) else np.nan

    monthly_means = df.groupby(df["datetime"].dt.month)["PM2.5"].mean().sort_values(ascending=False) if len(df) else pd.Series(dtype=float)
    peak_month_num = int(monthly_means.index[0]) if len(monthly_means) else None
    peak_month_name = MONTH_NAME_ID.get(pd.Timestamp(year=2000, month=peak_month_num, day=1).strftime("%B"), "-") if peak_month_num else "-"

    hourly_unhealthy = df.groupby("hour")["is_unhealthy"].mean().sort_values(ascending=False) if len(df) else pd.Series(dtype=float)
    worst_hour = int(hourly_unhealthy.index[0]) if len(hourly_unhealthy) else None
    worst_hour_val = hourly_unhealthy.iloc[0] * 100 if len(hourly_unhealthy) else np.nan

    seasonal = df[df["datetime"].dt.month.isin([12, 1, 2, 6, 7, 8])].copy()
    if len(seasonal):
        seasonal["season2"] = np.where(seasonal["datetime"].dt.month.isin([12, 1, 2]), "Winter", "Summer")
        ss = seasonal.groupby(["station", "season2"])["PM2.5"].mean().unstack()
        if "Winter" in ss.columns and "Summer" in ss.columns:
            ss["gap"] = ss["Winter"] - ss["Summer"]
            max_gap_station = ss["gap"].idxmax()
            max_gap_val = ss["gap"].max()
        else:
            max_gap_station, max_gap_val = "-", np.nan
    else:
        max_gap_station, max_gap_val = "-", np.nan

    dominant_wd = "-"
    if "wd" in df.columns and df["wd"].notna().any():
        dominant_wd = df["wd"].value_counts().idxmax()

    return {
        "total_rows": total_rows,
        "total_station": total_station,
        "avg_pm25": avg_pm25,
        "unhealthy_share": unhealthy_share,
        "top_station": top_station,
        "top_station_val": top_station_val,
        "cleanest_station": cleanest_station,
        "cleanest_station_val": cleanest_station_val,
        "peak_month_name": peak_month_name,
        "worst_hour": worst_hour,
        "worst_hour_val": worst_hour_val,
        "max_gap_station": max_gap_station,
        "max_gap_val": max_gap_val,
        "dominant_wd": dominant_wd,
        "station_means": station_means,
    }


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filter interaktif")

    stations = sorted(df["station"].dropna().unique().tolist())
    years = sorted(df["year"].dropna().astype(int).unique().tolist())
    seasons = sorted(df["season"].dropna().unique().tolist())
    periods = sorted(df["time_period"].dropna().unique().tolist())
    categories = sorted(df["pm25_category"].dropna().astype(str).unique().tolist())

    selected_station = st.sidebar.multiselect("Station", stations, default=stations)
    selected_year = st.sidebar.slider(
        "Rentang tahun",
        min_value=min(years),
        max_value=max(years),
        value=(min(years), max(years)),
    )
    selected_season = st.sidebar.multiselect("Season", seasons, default=seasons)
    selected_period = st.sidebar.multiselect("Time period", periods, default=periods)
    selected_category = st.sidebar.multiselect("PM2.5 category", categories, default=categories)

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    selected_date = st.sidebar.date_input(
        "Rentang tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    filtered = df.copy()
    filtered = filtered[filtered["station"].isin(selected_station)]
    filtered = filtered[(filtered["year"] >= selected_year[0]) & (filtered["year"] <= selected_year[1])]
    filtered = filtered[filtered["season"].isin(selected_season)]
    filtered = filtered[filtered["time_period"].isin(selected_period)]
    filtered = filtered[filtered["pm25_category"].astype(str).isin(selected_category)]

    if isinstance(selected_date, (tuple, list)) and len(selected_date) == 2:
        start, end = selected_date
        filtered = filtered[(filtered["date"].dt.date >= start) & (filtered["date"].dt.date <= end)]
    elif selected_date:
        filtered = filtered[filtered["date"].dt.date == selected_date]

    return filtered


def add_kpi_row(filtered_df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total data terfilter", f"{len(filtered_df):,}".replace(",", "."))
    with c2:
        st.metric("Rata-rata PM2.5", fmt(filtered_df["PM2.5"].mean()))
    with c3:
        unhealthy_share = filtered_df["is_unhealthy"].mean() * 100 if len(filtered_df) else np.nan
        st.metric("Proporsi tidak sehat", f"{unhealthy_share:.1f}%")
    with c4:
        st.metric("Jumlah station", f"{filtered_df['station'].nunique():,}".replace(",", "."))


# =========================
# Load data
# =========================
data_path = find_data_file()
df = load_data(str(data_path))
filtered_df = filter_data(df)
ins = compute_insights(filtered_df)

# =========================
# Header
# =========================
st.markdown(
    f"""
    <div class="hero">
        <h1>🌫️ Air Quality Insights Dashboard</h1>
        <p>Analisis interaktif kualitas udara berdasarkan PM2.5, tren waktu, station, musim, dan jam rawan dari {ins['total_station']} station.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# Empty state
# =========================
if filtered_df.empty:
    st.warning("Tidak ada data yang cocok dengan filter saat ini. Coba longgarkan filter di sidebar.")
    st.stop()

# =========================
# Insight banner
# =========================
st.markdown(
    f"""
    <div class="insight">
        <strong>Insight cepat:</strong>
        Station dengan rata-rata PM2.5 tertinggi pada data terfilter adalah <b>{ins["top_station"]}</b> ({fmt(ins["top_station_val"])}) ,
        sedangkan yang terendah adalah <b>{ins["cleanest_station"]}</b> ({fmt(ins["cleanest_station_val"])}) .
        Bulan dengan PM2.5 tertinggi adalah <b>{ins["peak_month_name"]}</b>,
        jam paling rawan adalah <b>{ins["worst_hour"]:02d}.00</b>,
        dan arah angin yang paling sering muncul adalah <b>{ins["dominant_wd"]}</b>.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

add_kpi_row(filtered_df)

st.write("")

# =========================
# Tabs
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["Ringkasan", "Pola Waktu", "Perbandingan Station", "Eksplorasi Data"])

with tab1:
    left, right = st.columns([1.15, 0.85])

    with left:
        styled_subheader("Peringkat station berdasarkan PM2.5", "Semakin tinggi bar, semakin buruk kualitas udara rata-rata pada station tersebut.")
        station_rank = (
            filtered_df.groupby("station", as_index=False)["PM2.5"]
            .mean()
            .sort_values("PM2.5", ascending=True)
        )
        fig, ax = plt.subplots(figsize=(10, max(5, 0.34 * len(station_rank) + 1.5)))
        sns.barplot(data=station_rank, x="PM2.5", y="station", ax=ax)
        ax.set_xlabel("Rata-rata PM2.5")
        ax.set_ylabel("")
        ax.set_title("Ranking station berdasarkan rata-rata PM2.5")
        ax.grid(axis="x", alpha=0.25)
        safe_fig_to_streamlit(fig)

    with right:
        styled_subheader("Insight otomatis")
        bullets = f"""
        <div class="card">
            <ul>
                <li><b>{ins["top_station"]}</b> adalah station paling tinggi rata-rata PM2.5 ({fmt(ins["top_station_val"])}).</li>
                <li><b>{ins["cleanest_station"]}</b> adalah station paling rendah rata-rata PM2.5 ({fmt(ins["cleanest_station_val"])}).</li>
                <li>Bulan paling berat polusinya adalah <b>{ins["peak_month_name"]}</b>.</li>
                <li>Jam dengan proporsi kondisi tidak sehat tertinggi adalah <b>{ins["worst_hour"]:02d}.00</b> ({ins["worst_hour_val"]:.1f}%).</li>
                <li>Selisih musim dingin vs musim panas terbesar ada di <b>{ins["max_gap_station"]}</b> ({fmt(ins["max_gap_val"])}).</li>
            </ul>
        </div>
        """
        st.markdown(bullets, unsafe_allow_html=True)

        st.markdown("#### Komposisi kategori PM2.5")
        cat = filtered_df["pm25_category"].astype(str).value_counts().reset_index()
        cat.columns = ["Kategori", "Jumlah"]
        fig, ax = plt.subplots(figsize=(8, 4.8))
        sns.barplot(data=cat, x="Kategori", y="Jumlah", ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("Jumlah")
        ax.set_title("Kategori PM2.5")
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
        safe_fig_to_streamlit(fig)

    styled_subheader("Ringkasan numerik", "Statistik deskriptif membantu melihat skala dan sebaran tiap variabel.")
    num_cols = [c for c in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"] if c in filtered_df.columns]
    metrics = filtered_df[num_cols].describe().T[["mean", "std", "min", "25%", "50%", "75%", "max"]].round(2)
    st.dataframe(metrics, use_container_width=True, height=420)

with tab2:
    c1, c2 = st.columns(2)

    with c1:
        styled_subheader("Tren bulanan PM2.5", "Garis ini membantu melihat kapan lonjakan dan penurunan terjadi.")
        monthly = filtered_df.copy()
        monthly["month_start"] = monthly["datetime"].dt.to_period("M").dt.to_timestamp()
        monthly_trend = monthly.groupby("month_start", as_index=False)["PM2.5"].mean().sort_values("month_start")
        fig, ax = plt.subplots(figsize=(10, 4.8))
        sns.lineplot(data=monthly_trend, x="month_start", y="PM2.5", marker="o", ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("Rata-rata PM2.5")
        ax.set_title("Tren bulanan PM2.5")
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.grid(True, alpha=0.25)
        fig.autofmt_xdate()
        safe_fig_to_streamlit(fig)

    with c2:
        styled_subheader("Jam rawan kondisi tidak sehat", "Menunjukkan proporsi jam saat PM2.5 masuk kategori tidak sehat/berbahaya.")
        hour_unhealthy = filtered_df.groupby("hour", as_index=False)["is_unhealthy"].mean()
        hour_unhealthy["unhealthy_pct"] = hour_unhealthy["is_unhealthy"] * 100
        fig, ax = plt.subplots(figsize=(10, 4.8))
        sns.barplot(data=hour_unhealthy, x="hour", y="unhealthy_pct", ax=ax)
        ax.set_xlabel("Jam")
        ax.set_ylabel("% Tidak sehat")
        ax.set_title("Proporsi kondisi tidak sehat per jam")
        ax.set_ylim(0, max(5, hour_unhealthy["unhealthy_pct"].max() * 1.15))
        ax.grid(axis="y", alpha=0.25)
        safe_fig_to_streamlit(fig)

    c3, c4 = st.columns(2)

    with c3:
        styled_subheader("Heatmap jam x bulan", "Membaca pola konsentrasi rata-rata secara lebih detail.")
        heat = filtered_df.copy()
        heat["month_name_en"] = heat["datetime"].dt.strftime("%B")
        pivot = (
            heat.pivot_table(index="hour", columns="month_name_en", values="PM2.5", aggfunc="mean")
            .reindex(index=range(24))
            .reindex(columns=MONTH_ORDER)
        )
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.heatmap(pivot, cmap="YlOrRd", ax=ax, cbar_kws={"label": "PM2.5"})
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Jam")
        ax.set_title("Heatmap rata-rata PM2.5 per jam dan bulan")
        ax.set_xticklabels([MONTH_NAME_ID.get(m.get_text(), m.get_text()) for m in ax.get_xticklabels()], rotation=45, ha="right")
        safe_fig_to_streamlit(fig)

    with c4:
        styled_subheader("Perbedaan musim dingin vs musim panas", "Salah satu pertanyaan bisnis utama dari analisis ini.")
        seasonal = filtered_df[filtered_df["datetime"].dt.month.isin([12, 1, 2, 6, 7, 8])].copy()
        if len(seasonal):
            seasonal["season2"] = np.where(seasonal["datetime"].dt.month.isin([12, 1, 2]), "Winter", "Summer")
            season_cmp = seasonal.groupby(["station", "season2"], as_index=False)["PM2.5"].mean()
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=season_cmp, x="station", y="PM2.5", hue="season2", ax=ax)
            ax.set_xlabel("")
            ax.set_ylabel("Rata-rata PM2.5")
            ax.set_title("Winter vs Summer per station")
            ax.tick_params(axis="x", rotation=30)
            ax.grid(axis="y", alpha=0.25)
            ax.legend(title="")
            safe_fig_to_streamlit(fig)
        else:
            st.info("Data musim dingin/panas pada filter saat ini tidak cukup.")

with tab3:
    c1, c2 = st.columns(2)

    with c1:
        styled_subheader("Boxplot PM2.5 per station", "Melihat sebaran, median, dan kemungkinan nilai ekstrem pada tiap station.")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.boxplot(data=filtered_df, x="station", y="PM2.5", ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("PM2.5")
        ax.set_title("Sebaran PM2.5 per station")
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.25)
        safe_fig_to_streamlit(fig)

    with c2:
        styled_subheader("Korelasi variabel numerik", "Membantu melihat variabel yang bergerak bersama PM2.5.")
        keep = [c for c in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"] if c in filtered_df.columns]
        corr = filtered_df[keep].corr(numeric_only=True).round(2)
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.heatmap(corr, cmap="RdBu_r", center=0, annot=True, fmt=".2f", ax=ax, cbar_kws={"label": "Corr"})
        ax.set_title("Matriks korelasi")
        safe_fig_to_streamlit(fig)

    styled_subheader("Perbandingan gap musim", "Station dengan selisih Winter - Summer terbesar ada di bagian atas.")
    station_season = filtered_df[filtered_df["datetime"].dt.month.isin([12, 1, 2, 6, 7, 8])].copy()
    if len(station_season):
        station_season["season2"] = np.where(station_season["datetime"].dt.month.isin([12, 1, 2]), "Winter", "Summer")
        gap = station_season.groupby(["station", "season2"])["PM2.5"].mean().unstack()
        if "Winter" in gap.columns and "Summer" in gap.columns:
            gap["Gap (Winter-Summer)"] = gap["Winter"] - gap["Summer"]
            gap = gap.sort_values("Gap (Winter-Summer)", ascending=False).reset_index()
            gap_display = gap[["station", "Winter", "Summer", "Gap (Winter-Summer)"]].copy()
            gap_display.columns = ["Station", "Winter", "Summer", "Gap (Winter-Summer)"]
            st.dataframe(gap_display.round(2), use_container_width=True, height=360)
    else:
        st.info("Data musim dingin/panas tidak cukup untuk dibandingkan.")

with tab4:
    styled_subheader("Dataset terfilter")
    st.write(f"Baris data yang sedang ditampilkan: **{len(filtered_df):,}**".replace(",", "."))
    st.dataframe(filtered_df.head(100), use_container_width=True, height=500)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download data terfilter (CSV)",
        data=csv,
        file_name="air_quality_filtered.csv",
        mime="text/csv",
    )

    st.markdown("#### Statistik per station")
    stat_cols = [c for c in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"] if c in filtered_df.columns]
    stat_station = filtered_df.groupby("station")[stat_cols].mean().round(2).reset_index()
    st.dataframe(stat_station, use_container_width=True, height=320)

st.markdown(
    """
    <div class="small-muted">
        Dibuat untuk eksplorasi kualitas udara dengan fokus pada PM2.5, station, musim, dan jam rawan.
    </div>
    """,
    unsafe_allow_html=True,
)
