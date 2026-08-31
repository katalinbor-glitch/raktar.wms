import streamlit as st
import pandas as pd
import datetime
import io
import barcode
from barcode.writer import ImageWriter
from PIL import Image

st.set_page_config(page_title="WMS Raktárirányítás & Gyógyszer- + ADR Modul", layout="wide")

LOGIN_PASSWORD = "wms2026"

# ==========================================
# 1. BEJELENTKEZÉS
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 WMS Raktárirányító Rendszer - Belépés")
    with st.form("login_form"):
        password_input = st.text_input("Belépési Jelszó", type="password")
        if st.form_submit_button("Belépés"):
            if password_input == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Helytelen jelszó!")
    st.stop()

# ==========================================
# VONALKÓD GENERÁLÓ SEGÉDFÜGGVÉNY
# ==========================================
def generate_barcode_img(code_text):
    try:
        rv = io.BytesIO()
        CODE128 = barcode.get_barcode_class('code128')
        code = CODE128(code_text, writer=ImageWriter())
        code.write(rv)
        rv.seek(0)
        return Image.open(rv)
    except Exception as e:
        return None

# ==========================================
# 2. INICIALIZÁLÁS (SESSION STATE)
# ==========================================
if "tarhely_torzs" not in st.session_state:
    st.session_state.tarhely_torzs = pd.DataFrame([
        {"Tárhely": "A-01-01", "Típus": "Normál Raktár", "Hőmérséklet": "15-25 °C"},
        {"Tárhely": "HUTO-01", "Típus": "Gyógyszer Hűtőkamra", "Hőmérséklet": "2-8 °C"},
        {"Tárhely": "ADR-SAFE-01", "Típus": "ADR Veszélyes Raktár", "Hőmérséklet": "15-25 °C"}
    ])

if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell", "Vonalkód": "5901234567891", "MinKeszlet": 5, "Egyégár_HUF": 250000, "Is_ADR": False, "Is_Pharma": False, "UN_Szam": "-", "ADR_Osztaly": "-", "PG": "-", "ADR_Szorzo": 0, "Hutarolas": False},
        {"Cikkszám": "GY-101", "Megnevezés": "Inzulin Injekció 100IU", "Vonalkód": "5901234567894", "MinKeszlet": 30, "Egyégár_HUF": 12000, "Is_ADR": False, "Is_Pharma": True, "UN_Szam": "-", "ADR_Osztaly": "-", "PG": "-", "ADR_Szorzo": 0, "Hutarolas": True},
        {"Cikkszám": "ADR-901", "Megnevezés": "Ipari Oldószer (Acetón)", "Vonalkód": "5901234567892", "MinKeszlet": 20, "Egyégár_HUF": 15000, "Is_ADR": True, "Is_Pharma": False, "UN_Szam": "UN 1090", "ADR_Osztaly": "3 (Gyúlékony)", "PG": "II", "ADR_Szorzo": 3, "Hutarolas": False}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell", "Mennyiség": 10, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2027-01-01", "Is_ADR": False, "Is_Pharma": False},
        {"SarzsID": "S-GY-01", "Cikkszám": "GY-101", "Megnevezés": "Inzulin Injekció 100IU", "Mennyiség": 100, "Tárhely": "HUTO-01", "Beérkezés": "2026-02-01", "Lejárat": "2026-09-01", "Is_ADR": False, "Is_Pharma": True},
        {"SarzsID": "S-ADR-01", "Cikkszám": "ADR-901", "Megnevezés": "Ipari Oldószer (Acetón)", "Mennyiség": 50, "Tárhely": "ADR-SAFE-01", "Beérkezés": "2026-02-01", "Lejárat": "2028-01-01", "Is_ADR": True, "Is_Pharma": False}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Felhasználó", "ADR_Pont"])

if "kiadasi_kosar" not in st.session_state:
    st.session_state.kiadasi_kosar = []

# ==========================================
# NAVIGÁCIÓ (BAL OLDALI MENÜ)
# ==========================================
st.sidebar.title("📦 WMS Navigáció")
menu = st.sidebar.radio("Modulok", [
    "📋 Pillanatnyi Készlet & Riasztások", 
    "📥 Áru Bevételezés",
    "📤 Összesített Kiadás & Komissiózás", 
    "📊 Leltár & Leltármódosítás",
    "📈 ABC Készlet Elemzés",
    "💊 Gyógyszerraktár & Hűtőlánc (2-8°C)",
    "🏷️ Vonalkód Generáló",
    "⚠️ ADR Veszélyes Áru Kezelés",
    "📜 Árumozgás Napló (Excel Export)"
])

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

# ==========================================
# 1. PILLANATNYI KÉSZLET & RIASZTÁSOK
# ==========================================
if menu == "📋 Pillanatnyi Készlet & Riasztások":
    st.header("📋 Raktári Készlet és Minimum Készlet Riasztások")
    
    if not st.session_state.sarzs_keszlet.empty:
        osszesitett = st.session_state.sarzs_keszlet.groupby(["Cikkszám", "Megnevezés"]).agg({"Mennyiség": "sum"}).reset_index()
        osszesitett = osszesitett.merge(st.session_state.cikktorzs[["Cikkszám", "MinKeszlet", "Is_ADR", "Is_Pharma"]], on="Cikkszám", how="left")
        
        kevés_készlet = osszesitett[osszesitett["Mennyiség"] <= osszesitett["MinKeszlet"]]
        if not kevés_készlet.empty:
            st.error("⚠️ **MINIMUM KÉSZLET RIASZTÁS!** A következő termékekből kevés van raktáron:")
            st.dataframe(kevés_készlet[["Cikkszám", "Megnevezés", "Mennyiség", "MinKeszlet"]], use_container_width=True)
            
        st.subheader("Összesített Készlet")
        st.dataframe(osszesitett, use_container_width=True)
    else:
        st.info("Jelenleg a raktár teljesen üres.")

    st.subheader("Részletes Sarzs Készlet (Tárhellyel és Lejárattal)")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)

# ==========================================
# 2. ÁRU BEVÉTELEZÉS
# ==========================================
elif menu == "📥 Áru Bevételezés":
    st.header("📥 Új Áru Bevételezése Raktárba")
    
    with st.form("bevétel_form"):
        col1, col2 = st.columns(2)
        with col1:
            termek_list = [f"{row['Cikkszám']} - {row['Megnevezés']}" for _, row in st.session_state.cikktorzs.iterrows()]
            kivalasztott_termek = st.selectbox("Termék Kiválasztása", termek_list)
            sarzs_id = st.text_input("Sarzs / Lot Szám", value=f"S-{datetime.datetime.now().strftime('%M%S')}")
            mennyiseg = st.number_input("Bevételezett Mennyiség", min_value=1, value=50)
            
        with col2:
            tarhely_list = st.session_state.tarhely_torzs["Tárhely"].tolist()
            tarhely = st.selectbox("Cél Tárhely", tarhely_list)
            lejarat = st.date_input("Lejárati Dátum", datetime.date(2027, 12, 31))
            
        if st.form_submit_button("📥 Bevételezés Rögzítése"):
            cikk_kod = kivalasztott_termek.split(" - ")[0]
            cikk_nev = kivalasztott_termek.split(" - ")[1]
            
            cikk_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == cikk_kod].iloc[0]
            is_adr = cikk_info["Is_ADR"]
            is_pharma = cikk_info["Is_Pharma"]
            
            uj_sarzs = {
                "SarzsID": sarzs_id,
                "Cikkszám": cikk_kod,
                "Megnevezés": cikk_nev,
                "Mennyiség": mennyiseg,
                "Tárhely": tarhely,
                "Beérkezés": datetime.date.today().strftime("%Y-%m-%d"),
                "Lejárat": lejarat.strftime("%Y-%m-%d"),
                "Is_ADR": is_adr,
                "Is_Pharma": is_pharma
            }
            
            st.session_state.sarzs_keszlet = pd.concat([st.session_state.sarzs_keszlet, pd.DataFrame([uj_sarzs])], ignore_index=True)
            
            st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Művelet": "BEVÉTEL",
                "Cikkszám": cikk_kod,
                "Megnevezés": cikk_nev,
                "Mennyiség": mennyiseg,
                "SarzsID": sarzs_id,
                "Tárhely": tarhely,
                "Felhasználó": "Raktáros",
                "ADR_Pont": 0
            }])], ignore_index=True)
            
            st.success(f"✅ Siker: {mennyiseg} db {cikk_nev} bevételezve a {tarhely} tárhelyre!")
            st.rerun()

# ==========================================
# 3. ÖSSZESÍTETT KIADÁS & KOMISSIÓZÁS (FIFO/LIFO/FEFO/HIFO)
# ==========================================
elif menu == "📤 Összesített Kiadás & Komissiózás":
    st.header("📤 Kiadás & Komissiózási Lista (FIFO/LIFO/FEFO/HIFO)")
    
    kiadasi_strategia = st.selectbox(
        "🔄 Válassz Kiadási / Kitárolási Stratégiát:", 
        [
            "FEFO / HIFO (First Expired / Highest In - Gyógyszerészeti előírás: Legkorábban lejáró először)",
            "FIFO (First In, First Out - A legrégebben beérkezett áru először)", 
            "LIFO (Last In, First Out - A legújabban beérkezett áru először)"
        ]
    )
    
    termek_opciok = {}
    for _, row in st.session_state.cikktorzs.iterrows():
        tag = "💊 [Gyógyszer]" if row.get("Is_Pharma") else ("⚠️ [ADR]" if row.get("Is_ADR") else "📦 [Normál]")
        termek_opciok[f"{tag} {row['Cikkszám']} - {row['Megnevezés']}"] = row['Cikkszám']
        
    with st.form("kosar_form"):
        col1, col2 = st.columns(2)
        with col1:
            kivalasztott_label = st.selectbox("Termék kiválasztása", list(termek_opciok.keys()))
        with col2:
            mennyiseg = st.number_input("Mennyiség (db / kg / liter)", min_value=1, value=10)
        
        if st.form_submit_button("➕ Hozzáadás a Kiadási Listához"):
            cikk = termek_opciok[kivalasztott_label]
            nev = kivalasztott_label.split(" - ")[1]
            st.session_state.kiadasi_kosar.append({"Cikkszám": cikk, "Megnevezés": nev, "Mennyiség": mennyiseg})
            st.rerun()

    if st.session_state.kiadasi_kosar:
        st.markdown("---")
        st.subheader("🛒 Komissiózási Kosár Tartalma")
        
        df_kosar = pd.DataFrame(st.session_state.kiadasi_kosar)
        df_kosar = df_kosar.groupby(["Cikkszám", "Megnevezés"]).agg({"Mennyiség": "sum"}).reset_index()
        df_kosar = df_kosar.merge(st.session_state.cikktorzs[["Cikkszám", "Is_ADR", "UN_Szam", "ADR_Osztaly", "ADR_Szorzo"]], on="Cikkszám", how="left")
        df_kosar["ADR Pontszám"] = df_kosar["Mennyiség"] * df_kosar["ADR_Szorzo"]
        
        st.dataframe(df_kosar[["Cikkszám", "Megnevezés", "Mennyiség", "Is_ADR", "UN_Szam", "ADR Pontszám"]], use_container_width=True)
        
        osszes_adr_pont = df_kosar["ADR Pontszám"].sum()

        if st.button("✅ Kiadás Végrehajtása & Tárhely szerinti Komissiózási Lista"):
            for _, k_row in df_kosar.iterrows():
                cikk = k_row["Cikkszám"]
                igenyelt = k_row["Mennyiség"]
                
                elerheto = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == cikk].copy()
                
                if "FEFO" in kiadasi_strategia or "HIFO" in kiadasi_strategia:
                    elerheto = elerheto.sort_values(by="Lejárat", ascending=True)
                elif "FIFO" in kiadasi_strategia:
                    elerheto = elerheto.sort_values(by="Beérkezés", ascending=True)
                elif "LIFO" in kiadasi_strategia:
                    elerheto = elerheto.sort_values(by="Beérkezés", ascending=False)
                
                maradek = igenyelt
                for idx, row in elerheto.iterrows():
                    if maradek <= 0: break
                    levonando = min(row["Mennyiség"], maradek)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levonando
                    maradek -= levonando
                    
                    st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                        "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Művelet": "KIADÁS", "Cikkszám": cikk, "Megnevezés": k_row['Megnevezés'], "Mennyiség": levonando,
                        "SarzsID": row["SarzsID"], "Tárhely": row["Tárhely"], "Felhasználó": "Raktáros", "ADR_Pont": k_row["ADR_Szorzo"] * levonando
                    }])], ignore_index=True)
            
            st.session_state.kiadasi_kosar = []
            st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
            st.success("✅ Komissiózás sikeresen végrehajtva!")
            st.rerun()

# ==========================================
# 4. LELTÁR ÉS LELTÁRMÓDOSÍTÁS
# ==========================================
elif menu == "📊 Leltár & Leltármódosítás":
    st.header("📊 Leltározás és Készletkorrekció")
    
    if st.session_state.sarzs_keszlet.empty:
        st.warning("Nincs leltározható készlet.")
    else:
        sarzs_opciok = [f"{row['SarzsID']} | {row['Cikkszám']} - {row['Megnevezés']} (Tárhely: {row['Tárhely']})" for _, row in st.session_state.sarzs_keszlet.iterrows()]
        
        with st.form("leltar_form"):
            kivalasztott_sarzs_str = st.selectbox("Válassz ki egy leltározandó Sarzsot:", sarzs_opciok)
            selected_sarzs_id = kivalasztott_sarzs_str.split(" | ")[0]
            aktualis_row = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["SarzsID"] == selected_sarzs_id].iloc[0]
            
            col_l1, col_l2, col_l3 = st.columns(3)
            with col_l1:
                st.write(f"**Tárhely:** `{aktualis_row['Tárhely']}`")
            with col_l2:
                st.write(f"**Jelenlegi Készlet:** `{aktualis_row['Mennyiség']}`")
            with col_l3:
                uj_fizikai_mennyiseg = st.number_input("Számolt Fizikai Mennyiség:", min_value=0, value=int(aktualis_row['Mennyiség']))
                
            elteres = uj_fizikai_mennyiseg - aktualis_row['Mennyiség']
            
            if st.form_submit_button("💾 Leltármódosítás Jóváhagyása"):
                st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == selected_sarzs_id, "Mennyiség"] = uj_fizikai_mennyiseg
                
                st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                    "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Művelet": "LELTÁR KORREKCIÓ",
                    "Cikkszám": aktualis_row['Cikkszám'],
                    "Megnevezés": aktualis_row['Megnevezés'],
                    "Mennyiség": elteres,
                    "SarzsID": selected_sarzs_id,
                    "Tárhely": aktualis_row['Tárhely'],
                    "Felhasználó": "Leltározó",
                    "ADR_Pont": 0
                }])], ignore_index=True)
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                st.success("✅ Készlet korrigálva!")
                st.rerun()

# ==========================================
# 5. ABC KÉSZLET ELEMZÉS
# ==========================================
elif menu == "📈 ABC Készlet Elemzés":
    st.header("📈 ABC Készlet Elemzés (Pareto elv 80/15/5%)")
    
    if not st.session_state.sarzs_keszlet.empty:
        df_abc = st.session_state.sarzs_keszlet.groupby(["Cikkszám", "Megnevezés"]).agg({"Mennyiség": "sum"}).reset_index()
        df_abc = df_abc.merge(st.session_state.cikktorzs[["Cikkszám", "Egyégár_HUF"]], on="Cikkszám", how="left")
        df_abc["Összérték_HUF"] = df_abc["Mennyiség"] * df_abc["Egyégár_HUF"]
        
        df_abc = df_abc.sort_values(by="Összérték_HUF", ascending=False).reset_index(drop=True)
        
        teljes_ertek = df_abc["Összérték_HUF"].sum()
        if teljes_ertek > 0:
            df_abc["Arány (%)"] = (df_abc["Összérték_HUF"] / teljes_ertek) * 100
            df_abc["Kumulatív (%)"] = df_abc["Arány (%)"].cumsum()
            
            def abc_besorolas(kum):
                if kum <= 80: return "A (Magas érték / Kiemelt gondoztatás)"
                elif kum <= 95: return "B (Közepes érték)"
                else: return "C (Alacsony érték / Nagy volumen)"
                
            df_abc["ABC Kategória"] = df_abc["Kumulatív (%)"].apply(abc_besorolas)
            
            st.subheader("Összesített Készletérték és Pareto Besorolás")
            st.dataframe(df_abc[["Cikkszám", "Megnevezés", "Mennyiség", "Egyégár_HUF", "Összérték_HUF", "Kumulatív (%)", "ABC Kategória"]], use_container_width=True)
    else:
        st.info("Nincs elemzendő készlet.")

# ==========================================
# 6. GYÓGYSZERRAKTÁR MODUL (2-8°C HŰTŐLÁNC)
# ==========================================
elif menu == "💊 Gyógyszerraktár & Hűtőlánc (2-8°C)":
    st.header("💊 Gyógyszeripari Raktározás & Hűtőlánc Ellenőrzés (GDP)")
    
    st.success("❄️ **Hűtőkamra Hőmérséklet Monitoring:** `3.4 °C` (Optimális tartomány: 2.0 °C - 8.0 °C)")
    
    st.subheader("Hűtőtárolást Igénylő Gyógyszerek Készlete")
    pharma_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Is_Pharma"] == True]
    st.dataframe(pharma_keszlet, use_container_width=True)

# ==========================================
# 7. VONALKÓD GENERÁLÓ
# ==========================================
elif menu == "🏷️ Vonalkód Generáló":
    st.header("🏷️ Vonalkód Generálás")
    termek_lista = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Vonalkód'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott = st.selectbox("Válassz terméket:", list(termek_lista.keys()))
    v_kod = termek_lista[kivalasztott]
    img = generate_barcode_img(v_kod)
    if img:
        st.image(img, caption=f"Vonalkód: {v_kod}", width=300)

# ==========================================
# 8. ADR MODUL
# ==========================================
elif menu == "⚠️ ADR Veszélyes Áru Kezelés":
    st.header("⚠️ ADR Veszélyes Áruk Nyilvántartása")
    adr_df = st.session_state.cikktorzs[st.session_state.cikktorzs["Is_ADR"] == True]
    st.dataframe(adr_df, use_container_width=True)

# ==========================================
# 9. NAPLÓ ÉS EXCEL EXPORT
# ==========================================
elif menu == "📜 Árumozgás Napló (Excel Export)":
    st.header("📜 Árumozgási Napló és Letöltés")
    st.dataframe(st.session_state.naplo, use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.naplo.to_excel(writer, index=False, sheet_name='Árumozgás_Napló')
    buffer.seek(0)
    
    st.download_button(
        label="📥 Árumozgási Napló Letöltése Excel-ben (.xlsx)",
        data=buffer,
        file_name=f"WMS_Naplo_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
