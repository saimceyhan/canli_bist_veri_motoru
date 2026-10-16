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

    st.sidebar.header("📊 Analiz Kontrol Merkezi")
    st.sidebar.write("---")
    
    # Çoklu Satır Seçimleri
    periyot = st.sidebar.radio("1️⃣ Zaman Dilimi Seçin:", ["Günlük", "4 Saatlik", "2 Saatlik", "Haftalık"])
    ekran_secimi = st.sidebar.selectbox(
        "2️⃣ Gösterilecek Veri Ekranı:",
        ["1. Canlı Tradingview Verileri Tablosu", "2. SMI-ALMA-V11 Strateji Listesi"]
    )
    
    st.sidebar.write("---")
    if st.sidebar.button("🔒 Oturumu Güvenli Kapat"):
        st.session_state["sifreli_giris"] = False
        st.rerun()

    def fmt(v): return f"{v:.2f}" if v is not None else "-"
    def tr_act(s):
        if not s: return "Nötr"
        txt = str(s).upper()
        if "BUY" in txt: return "Al"
        if "SELL" in txt: return "Sat"
        return "Nötr"

    # --- TOPLU VERİ TARAMA VE DEPOLAMA ALANI ---
    toplu_veriler = {}
    tablo_satirlari = []

    # Verileri tek seferde toplu olarak işleme alıyoruz
    with st.spinner("BIST 100 Canlı Veri Piyasası Sorgulanıyor..."):
        for hisse in BIST100:
            res = canli_bist_veri_motoru(hisse, periyot)
            if res:
                toplu_veriler[hisse] = res
                
                # Sinyal kelimeleri ve özet sayı kombinasyonları
                o_rec = tr_act(res["oscillators_summary"].get("RECOMMENDATION"))
                o_counts = f"Al:{res['oscillators_summary'].get('BUY')} Ntr:{res['oscillators_summary'].get('NEUTRAL')} Sat:{res['oscillators_summary'].get('SELL')}"
                
                g_rec = tr_act(res["summary_all"].get("RECOMMENDATION"))
                g_counts = f"Al:{res['summary_all'].get('BUY')} Ntr:{res['summary_all'].get('NEUTRAL')} Sat:{res['summary_all'].get('SELL')}"
                
                m_rec = tr_act(res["moving_averages_summary"].get("RECOMMENDATION"))
                m_counts = f"Al:{res['moving_averages_summary'].get('BUY')} Ntr:{res['moving_averages_summary'].get('NEUTRAL')} Sat:{res['moving_averages_summary'].get('SELL')}"

                strat_status = "AL 🚀" if res["al_sinyali"] else "SAT 🚨" if res["sat_sinyali"] else "BEKLE ◔"

                tablo_satirlari.append({
                    "Hisse": hisse,
                    "Anlık Fiyat": f"{res['canli_fiyat']:.2f} TL",
                    "Osilatör Kararı": o_rec,
                    "Osilatör Detayı": o_counts,
                    "Genel Durum (Özet)": g_rec,
                    "Genel Durum Detayı": g_counts,
                    "MA Ortalamalar Kararı": m_rec,
                    "MA Ortalamalar Detayı": m_counts,
                    "SMI-ALMA Stratejisi": strat_status
                })

    if not tablo_satirlari:
        st.error("Veriler anlık çekilemedi.")
        return

    ana_df = pd.DataFrame(tablo_satirlari)

    # =========================================================================
    # EKRAN 1: ORİJİNAL TRADINGVIEW TOPLU VERİ TABLOSU
    # =========================================================================
    if ekran_secimi == "1. Canlı Tradingview Verileri Tablosu":
        st.header("📊 BIST 100 Canlı Gösterge Çarşaf Listesi")
        st.caption(f"Periyot: {periyot} | Tüm BIST 100 hisseleri anlık TradingView verileriyle listelenmiştir.")
        
        # Dev Üst Tablo
        st.dataframe(ana_df.drop(columns=["SMI-ALMA Stratejisi"]), use_container_width=True, hide_index=True)
        
        # Aşağı Doğru Açılır Detay Pencereleri (Akordeon Yapı)
        st.write("---")
        st.subheader("🔍 Hisse Detay Pencereleri (Aşağı Açılır)")
        
        for hisse in BIST100:
            if hisse in toplu_veriler:
                veri = toplu_veriler[hisse]
                ind = veri["indicators_raw"]
                canli_fiyat = veri["canli_fiyat"]
                
                baslik = f"📂 {hisse} | Fiyat: {canli_fiyat:.2f} TL | Genel: {tr_act(veri['summary_all'].get('RECOMMENDATION'))}"
                
                with st.expander(baslik):
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        st.markdown("🔹 **Osilatör Detayları**")
                        o_names = ["RSI (14)", "Stochastic %K", "CCI (20)", "ADX (14)", "Momentum (10)", "MACD Seviyesi", "Stochastic RSI", "Williams %R", "UO (Nihai)"]
                        o_vals = [fmt(ind.get("RSI")), fmt(ind.get("Stoch.K")), fmt(ind.get("CCI20")), fmt(ind.get("ADX")), fmt(ind.get("Mom")), fmt(ind.get("MACD.macd")), fmt(ind.get("Stoch.RSI.K")), fmt(ind.get("W.R")), fmt(ind.get("UO"))]
                        o_acts = [tr_act(ind.get("Rec.RSI")), tr_act(ind.get("Rec.Stoch.K")), tr_act(ind.get("Rec.CCI20")), "Nötr", tr_act(ind.get("Rec.Mom")), tr_act(ind.get("Rec.MACD")), "Nötr", "Nötr", tr_act(ind.get("Rec.UO"))]
                        st.table(pd.DataFrame({"Osilatör Adı": o_names, "Değer": o_vals, "İşlem detayı": o_acts}))

                    with t_col2:
                        st.markdown("🔹 **Hareketli Ortalamalar Detayları**")
                        ma_names = ["EMA 10", "SMA 10", "EMA 20", "SMA 20", "EMA 50", "SMA 50", "EMA 100", "SMA 100", "EMA 200", "SMA 200", "VWMA (20)"]
                        ma_vals = [fmt(ind.get("EMA10")), fmt(ind.get("SMA10")), fmt(ind.get("EMA20")), fmt(ind.get("SMA20")), fmt(ind.get("EMA50")), fmt(ind.get("SMA50")), fmt(ind.get("EMA100")), fmt(ind.get("SMA100")), fmt(ind.get("EMA200")), fmt(ind.get("SMA200")), fmt(ind.get("VWMA"))]
                        
                        def calc_ma(v): return "Al" if v and canli_fiyat > v else "Sat" if v else "Nötr"
                        ma_acts = [calc_ma(ind.get("EMA10")), calc_ma(ind.get("SMA10")), calc_ma(ind.get("EMA20")), calc_ma(ind.get("SMA20")), calc_ma(ind.get("EMA30")), calc_ma(ind.get("SMA30")), calc_ma(ind.get("EMA50")), calc_ma(ind.get("SMA50")), calc_ma(ind.get("EMA100")), calc_ma(ind.get("SMA100")), calc_ma(ind.get("EMA200")), calc_ma(ind.get("SMA200")), calc_ma(ind.get("VWMA"))]
                        st.table(pd.DataFrame({"Ortalama Tipi": ma_names, "Değer": ma_vals, "İşlem detayı": ma_acts}))

                    st.markdown("📐 **Pivot Seviyeleri Tablosu**")
                    p_rows = ["R3", "R2", "R1", "P", "S1", "S2", "S3"]
                    klasik = [fmt(ind.get("Pivot.M.Classic.R3")), fmt(ind.get("Pivot.M.Classic.R2")), fmt(ind.get("Pivot.M.Classic.R1")), fmt(ind.get("Pivot.M.Classic.Pivot")), fmt(ind.get("Pivot.M.Classic.S1")), fmt(ind.get("Pivot.M.Classic.S2")), fmt(ind.get("Pivot.M.Classic.S3"))]
                    fibo = [fmt(ind.get("Pivot.M.Fibonacci.R3")), fmt(ind.get("Pivot.M.Fibonacci.R2")), fmt(ind.get("Pivot.M.Fibonacci.R1")), fmt(ind.get("Pivot.M.Fibonacci.Pivot")), fmt(ind.get("Pivot.M.Fibonacci.S1")), fmt(ind.get("Pivot.M.Fibonacci.S2")), fmt(ind.get("Pivot.M.Fibonacci.S3"))]
                    cama = [fmt(ind.get("Pivot.M.Camarilla.R3")), fmt(ind.get("Pivot.M.Camarilla.R2")), fmt(ind.get("Pivot.M.Camarilla.R1")), fmt(ind.get("Pivot.M.Camarilla.Pivot")), fmt(ind.get("Pivot.M.Camarilla.S1")), fmt(ind.get("Pivot.M.Camarilla.S2")), fmt(ind.get("Pivot.M.Camarilla.S3"))]
                    st.table(pd.DataFrame({"Pivot": p_rows, "Klasik": klasik, "Fibonacci": fibo, "Camarilla": cama}))

    # =========================================================================
    # EKRAN 2: SMI-ALMA-V11 STRATEJİ LİSTESİ TABLOSU
    # =========================================================================
    elif ekran_secimi == "2. SMI-ALMA-V11 Strateji Listesi":
        st.header("🎯 BIST 100 SMI-ALMA-V11 Strateji Tarama Sonuçları")
        st.caption(f"Periyot: {periyot} | Pine V6 kurallarına göre tüm hisselerin toplu AL-SAT sinyal listesidir.")
        
        # Sadece stratejiyle ilgili kritik sütunları gösteriyoruz
        strat_df = ana_df[["Hisse", "Anlık Fiyat", "Genel Durum (Özet)", "SMI-ALMA Stratejisi"]]
        st.dataframe(strat_df, use_container_width=True, hide_index=True)
