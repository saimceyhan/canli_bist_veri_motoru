from tradingview_ta import TA_Handler, Interval

def canli_bist_veri_motoru(hisse_adi, zaman_dilimi):
    try:
        intervals = {
            "Günlük": Interval.INTERVAL_1_DAY,
            "4 Saatlik": Interval.INTERVAL_4_HOURS,
            "2 Saatlik": Interval.INTERVAL_2_HOURS,
            "Haftalık": Interval.INTERVAL_1_WEEK
        }
        
        handler = TA_Handler(
            symbol=hisse_adi,
            screener="turkey",
            exchange="BIST",
            interval=intervals.get(zaman_dilimi, Interval.INTERVAL_1_DAY)
        )
        
        analysis = handler.get_analysis()
        ind = analysis.indicators
        summary = analysis.summary

        # --- PINE SCRIPT (SMI-ALMA-V11) HESAPLAMALARI ---
        smi_degeri = ind.get("Stoch.K", 0.0)
        smi_signal = ind.get("Stoch.D", 0.0)
        smi_vwma = ind.get("VWMA", 0.0)
        alma_3 = ind.get("EMA10", 0.0)
        alma_7 = ind.get("SMA20", 0.0)
        anlik_hacim = ind.get("volume", 0.0)
        hacim_ma = ind.get("Volume.MA", 0.0)
        hacimli_mum = anlik_hacim > hacim_ma

        sig_dn = smi_degeri < smi_signal
        vw_dn = smi_degeri < smi_vwma
        smi_down_both = sig_dn and vw_dn
        smi_up_both = (not sig_dn) and (not vw_dn)

        if smi_down_both: smi_yonu = "AŞAĞI"
        elif smi_up_both: smi_yonu = "YUKARI"
        else: smi_yonu = "KARARSIZ"

        k1 = smi_degeri > smi_signal and smi_degeri < 40
        k2 = smi_degeri > smi_vwma and smi_degeri < 40
        k3 = alma_3 > alma_7
        k4 = hacimli_mum and ind.get("close", 0.0) > ind.get("open", 0.0)

        al_sinyali = k1 and k2 and k3 and k4
        hacimli_kirmizi = hacimli_mum and ind.get("close", 0.0) < ind.get("open", 0.0)
        sat_sinyali = hacimli_kirmizi and smi_down_both

        return {
            "canli_fiyat": ind.get("close", 0.0),
            "smi": smi_degeri,
            "signal": smi_signal,
            "vwma": smi_vwma,
            "smi_yonu": smi_yonu,
            "al_sinyali": al_sinyali,
            "sat_sinyali": sat_sinyali,
            "tv_ozet": summary.get("RECOMMENDATION", "NÖTR"),
            "oscillators_summary": analysis.oscillators if analysis.oscillators else {"RECOMMENDATION": "-", "BUY": 0, "SELL": 0, "NEUTRAL": 0},
            "moving_averages_summary": analysis.moving_averages if analysis.moving_averages else {"RECOMMENDATION": "-", "BUY": 0, "SELL": 0, "NEUTRAL": 0},
            "summary_all": summary if summary else {"RECOMMENDATION": "-", "BUY": 0, "SELL": 0, "NEUTRAL": 0},
            "indicators_raw": ind
        }
    except:
        return None
