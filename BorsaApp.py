import streamlit as st
import pandas as pd
from bist_analiz import canli_bist_veri_motoru

def borsa_uygulama_paneli():
    # 📋 BIST 100 EKSİKSİZ LİSTESİ
    BIST100 = sorted([
        "AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKSA", "AKSEN", "ALARK", "ALBRK",
        "ALFAS", "ALTNY", "ARCLK", "ASELS", "ASTOR", "BERA", "BIMAS", "BIOEN", "BOBET", "BRSAN",
        "BRYAT", "BUCIM", "CANTE", "CCOLA", "CIMSA", "CWENE", "DOAS", "DOHOL", "ECILC", "ECZYT",
        "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "EUPWR", "EUREN", "FROTO", "GARAN", "GESAN",
        "GUBRF", "GWIND", "HEKTS", "IMASM", "INVES", "ISCTR", "ISDMR", "ISGYO", "ISMEN", "IZENR",
        "KARDMD", "KAYSE", "KCAER", "KCHOL", "KLSER", "KONTR", "KONYA", "KORDS", "KOZAA", "KOZAL",
        "LMKDC", "MAVI", "MGROS", "MIATK", "OBAMS", "ODAS", "OTKAR", "OYAKC", "OZSUB",
        "PAGYO", "PGSUS", "PETKM", "QUAGR", "REEDR", "RYSAS", "SAHOL", "SASA", "SDTTR",
        "SISE", "SKBNK", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO", "TKFEN", "TMSN", "TOASO",
        "TRGYO", "TSKB", "TTKOM", "TTRAK", "TUPRS", "TURSG", "ULKER", "VAKBN", "VESBE", "VESTL",
        "YEOTK", "YKBNK", "YYLGD", "ZRGYO"
    ])

    # 🖥️ SOL MENÜ (SIDEBAR) ÇOKLU SATIR TASARIMI
    st.sidebar.header("📊 Analiz Kontrol Merkezi")
    st.sidebar.write("---")
    
    hisse = st.sidebar.selectbox("1️⃣ Hisse Senedi Seçin (BIST 100):", BIST100, index=BIST100.index("THYAO"))
    periyot = st.sidebar.radio("2️⃣ Zaman Dilimi (Interval):", ["Günlük", "4 Saatlik", "Haftalık"])
    ekran_secimi = st.sidebar.selectbox("3️⃣ Gösterilecek Veri Ekranı:", ["1. SMI-ALMA-V11 Stratejisi (Pine V6)", "2. Canlı Tradingview Verileri"])
    
    st.sidebar.write("---")
    if st.sidebar.button("🔒 Oturumu Güvenli Kapat"):
        st.session_state["sifreli_giris"] = False
        st.rerun()

    veri = canli_bist_veri_motoru(hisse, periyot)
    if not veri:
        st.error("❌ Veriler anlık çekilemedi. Lütfen yenileyin.")
        return

    def fmt(v): return f"{v:.2f}" if v is not None else "-"
    def tr_act(s):
        if not s: return "Nötr"
        txt = str(s).upper()
        if "BUY" in txt: return "Al"
        if "SELL" in txt: return "Sat"
        return "Nötr"

    # =========================================================================
    # 1. EKRAN: PINE SCRIPT SMI-ALMA-V11 STRATEJİSİ
    # =========================================================================
    if ekran_secimi == "1. SMI-ALMA-V11 Stratejisi (Pine V6)":
        st.header("🎯 SMI-ALMA-V11 Strateji Analiz Tablosu")
        st.caption(f"Sembol: {hisse} | Periyot: {periyot} | Pine Script V6 Algoritması")
        
        if veri["al_sinyali"]: st.success("🚀 **STRATEJİ AL SİNYALİ VERDİ (4 ŞART TAMAM)**")
        elif veri["sat_sinyali"]: st.error("🚨 **STRATEJİ SAT SİNYALİ VERDİ (HACİMLİ KIRMIZI + SMI AŞAĞI)**")
        else: st.warning("◔ **STRATEJİ DURUMU: NÖTR / BEKLEMEDE**")

        durum_listesi = [
            {"PINE STRATEJİ MADDESİ": "Mevcut Son Fiyat", "DURUM / SİNYAL": f"{veri['canli_fiyat']:.2f} TL"},
            {"PINE STRATEJİ MADDESİ": "TradingView Özet Kararı", "DURUM / SİNYAL": veri["tv_ozet"]},
            {"PINE STRATEJİ MADDESİ": "Şart 1: SMI > Signal Kesişimi (+40 altı)", "DURUM / SİNYAL": "✔ ŞART TAMAM" if veri["k1"] else "Bekleniyor"},
            {"PINE STRATEJİ MADDESİ": "Şart 2: SMI > VWMA Kesişimi", "DURUM / SİNYAL": "✔ ŞART TAMAM" if veri["k2"] else "Bekleniyor"},
            {"PINE STRATEJİ MADDESİ": "Şart 3: ALMA 3 > ALMA 7 Yön Durumu", "DURUM / SİNYAL": "✔ ŞART TAMAM" if veri["k3"] else "Bekleniyor"},
            {"PINE STRATEJİ MADDESİ": "Şart 4: Hacimli Yeşil Mum", "DURUM / SİNYAL": "✔ ŞART TAMAM" if veri["k4"] else "Hacim Yetersiz"},
            {"PINE STRATEJİ MADDESİ": "SMI Yön Durumu (Signal & VWMA'ya Göre)", "DURUM / SİNYAL": veri["smi_yonu"]}
        ]
        st.table(pd.DataFrame(durum_listesi))

        st.subheader("📐 Anlık Matematiksel Gösterge Seviyeleri")
        col1, col2, col3 = st.columns(3)
        col1.metric("SMI Değeri (%K)", f"{veri['smi']:.2f}")
        col2.metric("Sinyal Çizgisi (%D)", f"{veri['signal']:.2f}")
        col3.metric("VWMA Hattı (SMI Üzerine)", f"{veri['vwma']:.2f}")

    # =========================================================================
    # 2. EKRAN: CANLI TRADINGVIEW VERİLERİ DÜNYASI
    # =========================================================================
    if ekran_secimi == "2. Canlı Tradingview Verileri":
        st.header("📊 Orijinal TradingView Teknik Gösterge Dünyası")
        st.caption(f"Sembol: {hisse} | Periyot: {periyot} | %100 Canlı Sayısal Tablolar")

        o_sum = veri["oscillators_summary"]
        m_sum = veri["moving_averages_summary"]
        a_sum = veri["summary_all"]
        ind = veri["indicators_raw"]
        canli_fiyat = veri["canli_fiyat"]

        c_o, c_a, c_m = st.columns(3)
        with c_o:
            st.info("**Osilatörler**")
            st.metric("Özet Karar", tr_act(o_sum.get("RECOMMENDATION")))
            st.text(f"Al: {o_sum.get('BUY')} | Nötr: {o_sum.get('NEUTRAL')} | Sat: {o_sum.get('SELL')}")
        with c_a:
            st.success("**Özet (Genel Karar)**")
            st.metric("Genel Durum", tr_act(a_sum.get("RECOMMENDATION")))
            st.text(f"Al: {a_sum.get('BUY')} | Nötr: {a_sum.get('NEUTRAL')} | Sat: {a_sum.get('SELL')}")
        with c_m:
            st.warning("**Hareketli Ortalamalar**")
            st.metric("Ortalamalar Kararı", tr_act(m_sum.get("RECOMMENDATION")))
            st.text(f"Al: {m_sum.get('BUY')} | Nötr: {m_sum.get('NEUTRAL')} | Sat: {m_sum.get('SELL')}")

        st.write("---")
        t_col1, t_col2 = st.columns(2)
        
        with t_col1:
            st.subheader("🔍 Osilatör Değerleri")
            osi_names = ["Göreceli Güç Endeksi (RSI) (14)", "Stokastik %K (14, 3, 3)", "Emtia Kanal Endeksi (CCI) (20)", "Ortalama Yönsel Endeks (ADX) (14)", "Müthiş Osilatör", "Momentum (10)", "MACD Seviyesi (12, 26)", "Stokastik RSI Hızlı", "Williams Yüzde Aralığı", "Boğa Ayı Gücü", "Nihai Osilatör (UO)"]
            osi_vals = [fmt(ind.get("RSI")), fmt(ind.get("Stoch.K")), fmt(ind.get("CCI20")), fmt(ind.get("ADX")), fmt(ind.get("AO")), fmt(ind.get("Mom")), fmt(ind.get("MACD.macd")), fmt(ind.get("Stoch.RSI.K")), fmt(ind.get("W.R")), fmt(ind.get("BBPower")), fmt(ind.get("UO"))]
            osi_acts = [tr_act(ind.get("Rec.RSI")), tr_act(ind.get("Rec.Stoch.K")), tr_act(ind.get("Rec.CCI20")), "Nötr", "Nötr", tr_act(ind.get("Rec.Mom")), tr_act(ind.get("Rec.MACD")), "Nötr", "Nötr", "Nötr", tr_act(ind.get("Rec.UO"))]
            st.table(pd.DataFrame({"Adı": osi_names, "Değer": osi_vals, "İşlem detayı": osi_acts}))

        with t_col2:
            st.subheader("⚙️ Hareketli Ortalamalar")
            ma_names = ["Üstel Hareketli Ortalama (10)", "Basit Hareketli Ortalama (10)", "Üstel Hareketli Ortalama (20)", "Basit Hareketli Ortalama (20)", "Üstel Hareketli Ortalama (30)", "Basit Hareketli Ortalama (30)", "Üstel Hareketli Ortalama (50)", "Basit Hareketli Ortalama (50)", "Üstel Hareketli Ortalama (100)", "Basit Hareketli Ortalama (100)", "Üstel Hareketli Ortalama (200)", "Basit Hareketli Ortalama (200)", "Ichimoku Ana Hattı", "Hacim Ağırlıklı Ort. (VWMA)"]
            ma_vals = [fmt(ind.get("EMA10")), fmt(ind.get("SMA10")), fmt(ind.get("EMA20")), fmt(ind.get("SMA20")), fmt(ind.get("EMA30")), fmt(ind.get("SMA30")), fmt(ind.get("EMA50")), fmt(ind.get("SMA50")), fmt(ind.get("EMA100")), fmt(ind.get("SMA100")), fmt(ind.get("EMA200")), fmt(ind.get("SMA200")), fmt(ind.get("Ichimoku.BLine")), fmt(ind.get("VWMA"))]
            
            def calc_ma(v): return "Al" if v and canli_fiyat > v else "Sat" if v else "Nötr"
            ma_acts = [calc_ma(ind.get("EMA10")), calc_ma(ind.get("SMA10")), calc_ma(ind.get("EMA20")), calc_ma(ind.get("SMA20")), calc_ma(ind.get("EMA30")), calc_ma(ind.get("SMA30")), calc_ma(ind.get("EMA50")), calc_ma(ind.get("SMA50")), calc_ma(ind.get("EMA100")), calc_ma(ind.get("SMA100")), calc_ma(ind.get("EMA200")), calc_ma(ind.get("SMA200")), "Nötr", calc_ma(ind.get("VWMA"))]
            st.table(pd.DataFrame({"Adı": ma_names, "Değer": ma_vals, "İşlem detayı": ma_acts}))

        st.write("---")
        st.subheader("📐 Pivotlar")
        p_rows = ["R3", "R2", "R1", "P", "S1", "S2", "S3"]
        klasik = [fmt(ind.get("Pivot.M.Classic.R3")), fmt(ind.get("Pivot.M.Classic.R2")), fmt(ind.get("Pivot.M.Classic.R1")), fmt(ind.get("Pivot.M.Classic.Pivot")), fmt(ind.get("Pivot.M.Classic.S1")), fmt(ind.get("Pivot.M.Classic.S2")), fmt(ind.get("Pivot.M.Classic.S3"))]
        fibo = [fmt(ind.get("Pivot.M.Fibonacci.R3")), fmt(ind.get("Pivot.M.Fibonacci.R2")), fmt(ind.get("Pivot.M.Fibonacci.R1")), fmt(ind.get("Pivot.M.Fibonacci.Pivot")), fmt(ind.get("Pivot.M.Fibonacci.S1")), fmt(ind.get("Pivot.M.Fibonacci.S2")), fmt(ind.get("Pivot.M.Fibonacci.S3"))]
        cama = [fmt(ind.get("Pivot.M.Camarilla.R3")), fmt(ind.get("Pivot.M.Camarilla.R2")), fmt(ind.get("Pivot.M.Camarilla.R1")), fmt(ind.get("Pivot.M.Camarilla.Pivot")), fmt(ind.get("Pivot.M.Camarilla.S1")), fmt(ind.get("Pivot.M.Camarilla.S2")), fmt(ind.get("Pivot.M.Camarilla.S3"))]
        woodie = [fmt(ind.get("Pivot.M.Woodie.R3")), fmt(ind.get("Pivot.M.Woodie.R2")), fmt(ind.get("Pivot.M.Woodie.R1")), fmt(ind.get("Pivot.M.Woodie.Pivot")), fmt(ind.get("Pivot.M.Woodie.S1")), fmt(ind.get("Pivot.M.Woodie.S2")), fmt(ind.get("Pivot.M.Woodie.S3"))]
        dm_list = ["-", "-", fmt(ind.get("Pivot.M.DeMark.R1")), fmt(ind.get("Pivot.M.DeMark.Pivot")), fmt(ind.get("Pivot.M.DeMark.S1")), "-", "-"]
        st.table(pd.DataFrame({"Pivot": p_rows, "Klasik": klasik, "Fibonacci": fibo, "Camarilla": cama, "Woodie": woodie, "DM": dm_list}))
