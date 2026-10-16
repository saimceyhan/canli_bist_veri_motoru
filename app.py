import streamlit as st

# 📄 Sayfa Başlık Ayarları
st.set_page_config(page_title="Özel Canlı BIST Strateji Paneli", layout="wide")

def ana_giris_kapisi():
    if "sifreli_giris" not in st.session_state:
        st.session_state["sifreli_giris"] = False

    if not st.session_state["sifreli_giris"]:
        st.title("🔒 SMI-ALMA-V11 Özel Takip Paneli")
        st.write("Bu analiz paneli sadece yetkili kullanıcılara özel şifre korumalıdır.")
        
        girilen_sifre = st.text_input("Giriş Şifresini Yazın:", type="password")
        dogru_sifre = st.secrets.get("GIRIS_SIFRESI", "bist2026*")
        
        if st.button("Sisteme Giriş Yap"):
            if girilen_sifre == dogru_sifre:
                st.session_state["sifreli_giris"] = True
                st.rerun()
            else:
                st.error("❌ Hatalı veya geçersiz şifre girdiniz!")
        return False
    return True

if ana_giris_kapisi():
    from BorsaApp import borsa_uygulama_paneli
    borsa_uygulama_paneli()
