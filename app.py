import time
import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import streamlit as st
from tvDatafeed import TvDatafeed, Interval

st.set_page_config(page_title="BIST30 SMI-ALMA Tarama", layout="wide")

# ---------------- SABİTLER ----------------
TZ = "Europe/Istanbul"
SEANS_KAPANIS = dt.timedelta(hours=18, minutes=10)   # BIST son 4s mum 17:00-18:10
N_BARS = 1500

A, B, C = 10, 3, 3
VWMA_LEN = 7
ALMA_OFFSET, ALMA_SIGMA = 0.85, 6
ALMA_FLOOR = False
ALMA_FAST, ALMA_SLOW = 3, 7
VOL_LEN = 20

BIST30_DEFAULT = (
    "AKBNK ARCLK ASELS ASTOR BIMAS BRSAN CCOLA CIMSA DOAS EKGYO "
    "ENKAI EREGL FROTO GARAN GUBRF ISCTR KCHOL MGROS OYAKC PETKM "
    "PGSUS SAHOL SASA SISE TCELL THYAO TOASO TTKOM TUPRS YKBNK"
)


# ---------------- GÖSTERGELER ----------------
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def calc_smi(df, a, b):
    ll = df["low"].rolling(a).min()
    hh = df["high"].rolling(a).max()
    diff = hh - ll
    rdiff = df["close"] - (hh + ll) / 2
    avgrel = ema(ema(rdiff, b), b)
    avgdiff = ema(ema(diff, b), b)
    return avgrel / (avgdiff / 2).replace(0, np.nan) * 100


def vwma(x, vol, n):
    return (x * vol).rolling(n).sum() / vol.rolling(n).sum()


def alma(src, length, offset, sigma):
    m = offset * (length - 1)
    if ALMA_FLOOR:
        m = np.floor(m)
    s = length / sigma
    w = np.exp(-((np.arange(length) - m) ** 2) / (2 * s * s))
    w = w / w.sum()
    return src.rolling(length).apply(lambda x: np.dot(x, w), raw=True)


def cross_up(x, y):
    return (x > y) & (x.shift(1) <= y.shift(1))


def cross_dn(x, y):
    return (x < y) & (x.shift(1) >= y.shift(1))


def run_strategy(df, vol_stay_above):
    smi = calc_smi(df, A, B)
    sig = ema(smi, C)
    vw = vwma(smi, df["volume"], VWMA_LEN)
    a3 = alma(df["close"], ALMA_FAST, ALMA_OFFSET, ALMA_SIGMA)
    a7 = alma(df["close"], ALMA_SLOW, ALMA_OFFSET, ALMA_SIGMA)
    vol_ma = df["volume"].rolling(VOL_LEN).mean()

    alma_up = cross_up(a3, a7).values
    alma_dn = cross_dn(a3, a7).values
    sig_up = cross_up(smi, sig).values
    sig_dn = cross_dn(smi, sig).values
    vw_up = cross_up(smi, vw).values
    vw_dn = cross_dn(smi, vw).values
    vol_up = cross_up(df["volume"], vol_ma).values
    vol_dn = cross_dn(df["volume"], vol_ma).values

    smi_v = smi.values
    vol_v = df["volume"].values
    volma_v = vol_ma.values
    green = (df["close"] > df["open"]).values
    red = (df["close"] < df["open"]).values

    in_pos = False
    c1 = c2 = c3 = c4 = False
    s1 = s2 = s3a = s3b = False
    vol_pending = False
    buys, sells = [], []

    for i in range(len(df)):
        if alma_up[i]:
            c1, s2 = True, False
        if alma_dn[i]:
            s2, c1 = True, False
        if sig_dn[i]:
            s3a, c2 = True, False
        if vw_dn[i]:
            s3b, c3 = True, False
        if sig_up[i] and smi_v[i] < -40:
            c2, s3a = True, False
        if vw_up[i] and smi_v[i] < -40:
            c3, s3b = True, False

        if vol_up[i]:
            vol_pending = True
        if vol_dn[i]:
            vol_pending = False
        if vol_pending and green[i] and (not vol_stay_above or vol_v[i] > volma_v[i]):
            c4, s1 = True, False
            vol_pending = False
        if vol_dn[i] and red[i]:
            s1, c4 = True, False

        if (not in_pos) and c1 and c2 and c3 and c4:
            in_pos = True
            buys.append(i)
            s1 = s2 = s3a = s3b = False
        if in_pos and s1 and s2 and s3a and s3b:
            in_pos = False
            sells.append(i)

    return {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "in_pos": in_pos, "buys": buys, "sells": sells}


# ---------------- PİVOT (Traditional) ----------------
def traditional_levels(h, l, c):
    p = (h + l + c) / 3
    return {
        "P": p,
        "R1": 2 * p - l, "S1": 2 * p - h,
        "R2": p + (h - l), "S2": p - (h - l),
        "R3": 2 * p + (h - 2 * l), "S3": 2 * p - (2 * h - l),
        "R4": 3 * p + (h - 3 * l), "S4": 3 * p - (3 * h - l),
        "R5": 4 * p + (h - 4 * l), "S5": 4 * p - (4 * h - l),
    }


def pivots_from_daily(daily, period):
    d = daily.copy()
    d.index = d.index + pd.Timedelta(hours=12)   # saat dilimi kaymasına karşı
    freq = {"D": "D", "W": "W-SUN", "M": "M"}[period]
    g = d.groupby(d.index.to_period(freq)).agg(
        high=("high", "max"), low=("low", "min"), close=("close", "last")
    )
    if len(g) < 2:
        return None
    prev = g.iloc[-2]
    return traditional_levels(prev["high"], prev["low"], prev["close"])


# ---------------- VERİ ----------------
def get_tv():
    try:
        user, pwd = st.secrets.get("TV_USER"), st.secrets.get("TV_PASS")
    except Exception:
        user = pwd = None
    return TvDatafeed(user, pwd)


def fetch(tv, sym, interval, n_bars, tries=3):
    for _ in range(tries):
        try:
            df = tv.get_hist(sym, "BIST", interval=interval, n_bars=n_bars)
            if df is not None and len(df) > 50:
                return df
        except Exception:
            pass
        time.sleep(2)
    return None


@st.cache_data(ttl=900, show_spinner=False)
def scan(symbols, pivot_period, drop_forming, vol_stay_above):
    tv = get_tv()
    rows, failed = [], []
    for sym in symbols:
        df = fetch(tv, sym, Interval.in_4_hour, N_BARS)
        daily = fetch(tv, sym, Interval.in_daily, 400)
        if df is None or daily is None:
            failed.append(sym)
            continue

        # tvDatafeed zamanı sunucu saatiyle (UTC) verir, İstanbul'a çevir
        df.index = df.index.tz_localize("UTC").tz_convert(TZ).tz_localize(None)

        if drop_forming:
            now_ist = dt.datetime.now(ZoneInfo(TZ)).replace(tzinfo=None)
            last_open = df.index[-1].to_pydatetime()
            day_start = last_open.replace(hour=0, minute=0, second=0, microsecond=0)
            bar_end = min(last_open + dt.timedelta(hours=4), day_start + SEANS_KAPANIS)
            if now_ist < bar_end:
                df = df.iloc[:-1]

        res = run_strategy(df, vol_stay_above)
        price = float(df["close"].iloc[-1])
        lv = pivots_from_daily(daily, pivot_period)

        row = {
            "Hisse": sym,
            "Son mum": df.index[-1].strftime("%d.%m %H:%M"),
            "Fiyat": round(price, 2),
            "Al Fiyatı": round(float(df["close"].iloc[res["buys"][-1]]), 2)
            if (res["in_pos"] and res["buys"]) else np.nan,
            "1 ALMA": res["c1"], "2 SMI-Sig": res["c2"],
            "3 SMI-VWMA": res["c3"], "4 Hacim": res["c4"],
            "Şart": int(res["c1"]) + int(res["c2"]) + int(res["c3"]) + int(res["c4"]),
            "Pozisyonda": res["in_pos"],
            "Son AL": df.index[res["buys"][-1]].strftime("%d.%m %H:%M") if res["buys"] else "-",
            "En yakın destek": np.nan,
            "En yakın direnç": np.nan,
        }
        if lv:
            above = sorted(v for v in lv.values() if v > price)
            below = sorted((v for v in lv.values() if v < price), reverse=True)
            if below:
                row["En yakın destek"] = round(below[0], 2)
            if above:
                row["En yakın direnç"] = round(above[0], 2)
        rows.append(row)
        time.sleep(0.5)

    return pd.DataFrame(rows), failed, dt.datetime.now(ZoneInfo(TZ)).strftime("%d.%m.%Y %H:%M:%S")


def tick(df):
    out = df.copy()
    for col in ["1 ALMA", "2 SMI-Sig", "3 SMI-VWMA", "4 Hacim", "Pozisyonda"]:
        out[col] = out[col].map(lambda v: "✔" if v else "✘")
    return out


def style_rows(df):
    def f(row):
        color = "background-color: #d4edda" if row["Şart"] == 4 else ""
        return [color] * len(row)
    return df.style.apply(f, axis=1)


# ---------------- ARAYÜZ ----------------
st.title("BIST30 – SMI-ALMA 4 Şart Tarama")

with st.sidebar:
    st.header("Ayarlar")
    sym_text = st.text_area("Hisseler (boşlukla ayır)", BIST30_DEFAULT, height=150)
    pivot_label = st.selectbox("Pivot dönemi", ["Haftalık", "Günlük", "Aylık"])
    drop_forming = st.checkbox("Oluşmakta olan son mumu hariç tut", True)
    vol_stay_above = st.checkbox("Yeşil mumda hacim MA üstünde olsun", True)
    only_full = st.checkbox("Sadece 4 şartı sağlayanları göster", False)
    if st.button("Verileri yenile"):
        st.cache_data.clear()

symbols = tuple(s.strip().upper() for s in sym_text.split() if s.strip())
pivot_period = {"Haftalık": "W", "Günlük": "D", "Aylık": "M"}[pivot_label]

with st.spinner("TradingView'dan veriler çekiliyor, bu birkaç dakika sürebilir..."):
    sonuc, failed, stamp = scan(symbols, pivot_period, drop_forming, vol_stay_above)

st.caption(f"Son güncelleme: {stamp} (İstanbul) · veriler 15 dk önbellekte tutulur")
if failed:
    st.warning("Veri alınamayan hisseler: " + ", ".join(failed))

if sonuc.empty:
    st.error("Hiç veri alınamadı. TradingView istek sınırına takılmış olabilir, biraz bekleyip yenile.")
    st.stop()

sonuc = sonuc.sort_values(["Şart", "Hisse"], ascending=[False, True]).reset_index(drop=True)
tam = sonuc[sonuc["Şart"] == 4]

st.subheader(f"4 şartı sağlayanlar ({len(tam)})")
if len(tam):
    st.dataframe(style_rows(tick(tam)), use_container_width=True, hide_index=True)
else:
    st.info("Şu an 4 şartı birden sağlayan hisse yok.")

if not only_full:
    st.subheader("Tüm hisseler")
    st.dataframe(style_rows(tick(sonuc)), use_container_width=True, hide_index=True)

st.download_button(
    "CSV indir",
    sonuc.to_csv(index=False).encode("utf-8-sig"),
    file_name="bist30_tarama.csv",
    mime="text/csv",
)
