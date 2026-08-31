import streamlit as st
import pandas as pd
import datetime
import io
import barcode
from barcode.writer import ImageWriter
from PIL import Image

st.set_page_config(page_title="WMS Raktárirányítás & ADR Modul", layout="wide")

LOGIN_PASSWORD = "wms2026"

# 1. BEJELENTKEZÉS
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

# VONALKÓD GENERÁLÓ FÜGGVÉNY (RAM-ban készíti el a képet)
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

# 2. INICIALIZÁLÁS
if "tarhely_torzs" not in st.session_state:
    st.session_state.tarhely_torzs = pd.DataFrame([
        {"Tárhely": "A-01-01", "Típus": "Normál"},
        {"Tárhely": "ADR-SAFE-01", "Típus": "ADR Veszélyes Raktár"},
        {"Tárhely": "ADR-SAFE-02", "Típus": "ADR Veszélyes Raktár"}
    ])

if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell", "Vonalkód": "5901234567891", "Is_ADR": False, "UN_Szam": "-", "ADR_Osztaly": "-", "PG": "-", "ADR_Szorzo": 0},
        {"Cikkszám": "ADR-901", "Megnevezés": "Ipari Oldószer (Acetón)", "Vonalkód": "5901234567892", "Is_ADR": True, "UN_Szam": "UN 1090", "ADR_Osztaly": "3 (Gyúlékony)", "PG": "II", "ADR_Szorzo": 3},
        {"Cikkszám": "ADR-902", "Megnevezés": "Sósav oldat 30%", "Vonalkód": "5901234567893", "Is_ADR": True, "UN_Szam": "UN 1789", "ADR_Osztaly": "8 (Maró)", "PG": "II", "ADR_Szorzo": 3}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell", "Mennyiség": 10, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2027-01-01", "Is_ADR": False},
        {"SarzsID": "S-ADR-01", "Cikkszám": "ADR-901", "Megnevezés": "Ipari Oldószer (Acetón)", "Mennyiség": 50, "Tárhely": "ADR-SAFE-01", "Beérkezés": "2026-02-01", "Lejárat": "2028-01-01", "Is_ADR": True},
        {"SarzsID": "S-ADR-02", "Cikkszám": "ADR-902", "Megnevezés": "Sósav oldat 30%", "Mennyiség": 20, "Tárhely": "ADR-SAFE-02", "Beérkezés": "2026-02-05", "Lejárat": "2027-06-01", "Is_ADR": True}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Felhasználó", "ADR_Pont"])

if "kiadasi_kosar" not in st.session_state:
    st.session_state.kiadasi_kosar = []

# NAVIGÁCIÓ
st.sidebar.title("📦 WMS Navigáció")
menu = st.sidebar.radio("Modulok", [
    "📋 Pillanatnyi Készlet", 
    "🏷️ Vonalkód Generáló",
    "⚠️ ADR Veszélyes Áru Kezelés",
    "📤 Összesített Kiadás & Komissiózás", 
    "📜 Árumozgás Napló (Excel Export)"
])

# --- 1. PILLANATNYI KÉSZLET ---
if menu == "📋 Pillanatnyi Készlet":
    st.header("📋 Raktári Készlet (Normál és ADR)")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)

# --- 2. VONALKÓD GENERÁLÓ MODUL ---
elif menu == "🏷️ Vonalkód Generáló":
    st.header("🏷️ Vonalkód Címke Nyomtatás & Generálás")
    
    termek_lista = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Vonalkód'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott = st.selectbox("Válassz terméket a vonalkód generáláshoz:", list(termek_lista.keys()))
    
    v_kod = termek_lista[kivalasztott]
    st.write(f"**Regisztrált Vonalkód számsor:** `{v_kod}`")
    
    img = generate_barcode_img(v_kod)
    if img:
        st.image(img, caption=f"Generált vonalkód: {v_kod}", width=300)
    else:
        st.error("Nem sikerült a vonalkódot elkészíteni.")

# --- 3. ADR MODUL ---
elif menu == "⚠️ ADR Veszélyes Áru Kezelés":
    st.header("⚠️ ADR Veszélyes Áru Törzsadatok & Összeférhetőség")
    
    tab1, tab2 = st.tabs(["☣️ ADR Cikktörzs Nyilvántartás", "🔒 Tárhely Összeférhetőség"])
    
    with tab1:
        st.subheader("Új ADR-es Termék Regisztrációja")
        with st.form("adr_form"):
            col1, col2 = st.columns(2)
            with col1:
                cikk = st.text_input("Cikkszám", value="ADR-903")
                nev = st.text_input("Megnevezés", value="Akkumulátor Sav")
                vonalkod = st.text_input("Vonalkód", value="5901234567899")
                un_szam = st.text_input("UN-Szám", value="UN 2796")
            with col2:
                osztaly = st.selectbox("ADR Osztály", ["1 (Robbanó)", "2 (Gázok)", "3 (Gyúlékony)", "4.1 (Gyúlékony szilárd)", "5.1 (Oxidáló)", "6.1 (Mérgező)", "8 (Maró)", "9 (Egyéb)"])
                pg = st.selectbox("Csomagolási Csoport (PG)", ["I (Nagyon veszélyes - Szorzó: 50)", "II (Közepesen veszélyes - Szorzó: 3)", "III (Kevésbé veszélyes - Szorzó: 1)"])
                
            if st.form_submit_button("ADR Termék Rögzítése"):
                szorzo = 50 if "I " in pg else (3 if "II " in pg else 1)
                uj_adr = {
                    "Cikkszám": cikk, "Megnevezés": nev, "Vonalkód": vonalkod, "Is_ADR": True, 
                    "UN_Szam": un_szam, "ADR_Osztaly": osztaly, "PG": pg.split(" ")[0], "ADR_Szorzo": szorzo
                }
                st.session_state.cikktorzs = pd.concat([st.session_state.cikktorzs, pd.DataFrame([uj_adr])], ignore_index=True)
                st.success(f"✅ ADR Termék rögzítve: {nev} ({un_szam})")
                st.rerun()

        st.subheader("Jelenlegi ADR Cikktörzs")
        adr_df = st.session_state.cikktorzs[st.session_state.cikktorzs["Is_ADR"] == True]
        st.dataframe(adr_df, use_container_width=True)

    with tab2:
        st.warning("⚠️ **Biztonsági szabály:** Savak (Osztály 8) és Gyúlékony folyadékok (Osztály 3) nem kerülhetnek azonos közvetlen polcra!")

# --- 4. ÖSSZESÍTETT KIADÁS ÉS ADR PONTSZÁMÍTÁS ---
elif menu == "📤 Összesített Kiadás & Komissiózás":
    st.header("📤 Kiadás & Komissiózási Lista (ADR Pontszámítással)")
    
    termek_opciok = {}
    for _, row in st.session_state.cikktorzs.iterrows():
        tag = "⚠️ [ADR]" if row.get("Is_ADR") else "📦 [Normál]"
        termek_opciok[f"{tag} {row['Cikkszám']} - {row['Megnevezés']}"] = row['Cikkszám']
        
    with st.form("kosar_form"):
        col1, col2 = st.columns(2)
        with col1:
            kivalasztott_label = st.selectbox("Termék kiválasztása", list(termek_opciok.keys()))
        with col2:
            mennyiseg = st.number_input("Mennyiség (kg / liter / db)", min_value=1, value=10)
        
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
        
        st.markdown("### 🧮 ADR 1000-es Pontszám Ellenőrzés")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric(label="Összesített ADR Pontszám erre a szállítmányra", value=f"{osszes_adr_pont} pont")
        with col_p2:
            if osszes_adr_pont > 1000:
                st.error("🚨 **FIGYELEM: A szállítmány meghaladja az 1000 ADR pontot!**\n\nKizárólag ADR vizsgával rendelkező sofőr és felszerelt (narancssárga táblás) gépjármű viheti el!")
            elif osszes_adr_pont > 0:
                st.success("✅ **ADR 1000 pont alatti mentesített szállítás.** (Nem szükséges narancssárga tábla, de poroltó és ADR okmány kell).")
            else:
                st.info("ℹ️ Ebben a kiadásban nincs ADR-es veszélyes tétel.")

        if st.button("✅ Kiadás Végrehajtása & Tárhely szerinti Komissiózási Lista"):
            komissio_rows = ""
            
            for _, k_row in df_kosar.iterrows():
                cikk = k_row["Cikkszám"]
                igenyelt = k_row["Mennyiség"]
                
                elerheto = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == cikk].copy()
                maradek = igenyelt
                
                for idx, row in elerheto.iterrows():
                    if maradek <= 0: break
                    levonando = min(row["Mennyiség"], maradek)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levonando
                    maradek -= levonando
                    
                    adr_figyelmeztetes = f"<b style='color:red;'>⚠️ ADR: {k_row['UN_Szam']} (Osztály: {k_row['ADR_Osztaly']})</b>" if k_row['Is_ADR'] else "Normál tétel"
                    
                    komissio_rows += f"""
                    <tr>
                        <td style="border:1px solid #ccc; padding:8px;"><b>{row['Tárhely']}</b></td>
                        <td style="border:1px solid #ccc; padding:8px;">{cikk} - {k_row['Megnevezés']}</td>
                        <td style="border:1px solid #ccc; padding:8px;">{adr_figyelmeztetes}</td>
                        <td style="border:1px solid #ccc; padding:8px; font-weight:bold; font-size:16px;">{levonando} db/kg/L</td>
                    </tr>
                    """
                    
                    st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                        "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Művelet": "KIADÁS", "Cikkszám": cikk, "Megnevezés": k_row['Megnevezés'], "Mennyiség": levonando,
                        "SarzsID": row["SarzsID"], "Tárhely": row["Tárhely"], "Felhasználó": "Raktáros", "ADR_Pont": k_row["ADR_Szorzo"] * levonando
                    }])], ignore_index=True)
            
            html_bizonylat = f"""
            <div style="border:3px solid #d32f2f; padding:15px; background-color:#fff8f8; font-family:Arial;">
                <h2 style="color:#d32f2f; margin-top:0;">⚠️ ÖSSZESÍTETT KOMISSIÓZÁSI LISTA + ADR DEKLARÁCIÓ</h2>
                <p><b>Összesített ADR Pontszám:</b> <span style="font-size:18px; font-weight:bold;">{osszes_adr_pont} Pont</span></p>
                <table style="width:100%; border-collapse:collapse; background:white;">
                    <thead>
                        <tr style="background:#d32f2f; color:white;">
                            <th style="padding:8px;">Tárhely</th>
                            <th style="padding:8px;">Termék</th>
                            <th style="padding:8px;">ADR Besorolás / UN Szám</th>
                            <th style="padding:8px;">Mennyiség</th>
                        </tr>
                    </thead>
                    <tbody>
                        {komissio_rows}
                    </tbody>
                </table>
            </div>
            """
            st.session_state.kiadasi_kosar = []
            st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
            st.markdown(html_bizonylat, unsafe_allow_html=True)
            st.success("✅ Komissiózási lista és ADR okmány elkészült!")

# --- 5. NAPLÓ ÉS EXCEL EXPORT ---
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
