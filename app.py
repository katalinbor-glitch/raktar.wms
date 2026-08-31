import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="WMS & ADR Raktárirányító Rendszer", layout="wide")

# LOGIN ÉS ADMIN KONFIGURÁCIÓ
LOGIN_PASSWORD = "wms2026"
ADMIN_PIN = "Coca-cola20"

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

if st.sidebar.button("🚪 Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

# 1. INICIALIZÁLÁS (Tárhelyek, ADR Cikkek, Zárolások)
if "tarhely_torzs" not in st.session_state:
    st.session_state.tarhely_torzs = pd.DataFrame([
        {"Tárhely": "A-01-01", "Max Kapacitás": 100, "ADR Engedély": "Általános"},
        {"Tárhely": "A-01-02", "Max Kapacitás": 50, "ADR Engedély": "ADR 3 (Gyúlékony)"},
        {"Tárhely": "B-02-01", "Max Kapacitás": 20, "ADR Engedély": "ADR 8 (Maró)"},
        {"Tárhely": "C-03-02", "Max Kapacitás": 10, "ADR Engedély": "Általános"},
        {"Tárhely": "D-01-01", "Max Kapacitás": 200, "ADR Engedély": "ADR 5.1 (Oxidáló)"}
    ])

if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "ADR Osztály": "Nem ADR", "Biztonsági készlet": 5, "Rendelésköteles készlet": 12},
        {"Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "ADR Osztály": "ADR 3", "Biztonsági készlet": 10, "Rendelésköteles készlet": 20},
        {"Cikkszám": "ART-003", "Megnevezés": "Sósav Oldat 37%", "ADR Osztály": "ADR 8", "Biztonsági készlet": 3, "Rendelésköteles készlet": 8},
        {"Cikkszám": "ART-004", "Megnevezés": "Hidrogén-peroxid 50%", "ADR Osztály": "ADR 5.1", "Biztonsági készlet": 5, "Rendelésköteles készlet": 15}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 10, "Zárolt_Mennyiség": 0, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2028-01-10", "Beszerzési Ár": 240000},
        {"SarzsID": "S-102", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 5, "Zárolt_Mennyiség": 3, "Tárhely": "C-03-02", "Beérkezés": "2026-02-01", "Lejárat": "2028-02-01", "Beszerzési Ár": 260000},
        {"SarzsID": "S-201", "Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "Mennyiség": 30, "Zárolt_Mennyiség": 0, "Tárhely": "A-01-02", "Beérkezés": "2026-01-15", "Lejárat": "2027-06-30", "Beszerzési Ár": 12000},
        {"SarzsID": "S-301", "Cikkszám": "ART-003", "Megnevezés": "Sósav Oldat 37%", "Mennyiség": 8, "Zárolt_Mennyiség": 0, "Tárhely": "B-02-01", "Beérkezés": "2026-01-20", "Lejárat": "2029-01-01", "Beszerzési Ár": 8500},
        {"SarzsID": "S-401", "Cikkszám": "ART-004", "Megnevezés": "Hidrogén-peroxid 50%", "Mennyiség": 25, "Zárolt_Mennyiség": 0, "Tárhely": "D-01-01", "Beérkezés": "2026-01-05", "Lejárat": "2030-01-01", "Beszerzési Ár": 15000}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Stratégia", "Beszerzési Ár", "Felhasználó"])

st.title("📦 WMS Raktárirányítás & ADR Veszélyes Áru Kezelő Rendszer")

menu = st.sidebar.radio("Navigáció / Modulok", [
    "📋 Pillanatnyi Készlet & Jelzőrendszer", 
    "📥 ADR Bevételezés & Tárhely Ellenőrzés", 
    "📤 Kiadás (Stratégia, Zárolás & Safety Stock)", 
    "📊 Leltár & Időszaki Export",
    "📜 Árumozgás Napló",
    "⚙️ Adminisztráció & Tárhelykezelés"
])

# MODUL 1: BEVÉTELEZÉS ADR ELLENŐRZÉSSEL
if menu == "📥 ADR Bevételezés & Tárhely Ellenőrzés":
    st.header("📥 Áru Bevételezés ADR Összeférhetőségi Vizsgálattal")
    
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']} ({row['ADR Osztály']})": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_termek_label = st.selectbox("Bevételezendő Termék", list(termek_opciok.keys()))
    kivalasztott_cikkszam = termek_opciok[kivalasztott_termek_label]
    termek_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
    
    with st.form("bevételezés_form"):
        col1, col2 = st.columns(2)
        with col1:
            mennyiseg = st.number_input("Bevételezendő mennyiség", min_value=1, value=5)
            tarhely_lista = st.session_state.tarhely_torzs["Tárhely"].tolist()
            tarhely = st.selectbox("Cél Tárhely Kiválasztása", tarhely_lista)
        with col2:
            beszerzesi_ar = st.number_input("Beszerzési Egységár (Ft)", min_value=0, value=15000)
            lejarat = st.date_input("Lejárati dátum", value=datetime.date(2028, 12, 31))
            
        diak_nev = st.text_input("Kezelő neve", value="Raktáros")
        submitted = st.form_submit_button("Bevételezés Rögzítése")
        
        if submitted:
            tarhely_info = st.session_state.tarhely_torzs[st.session_state.tarhely_torzs["Tárhely"] == tarhely].iloc[0]
            
            # ADR VIZSGÁLAT
            adr_cikk = termek_info["ADR Osztály"]
            adr_tarhely = tarhely_info["ADR Engedély"]
            
            adr_hiba = False
            if adr_cikk != "Nem ADR" and adr_cikk not in adr_tarhely and adr_tarhely != "Általános":
                adr_hiba = True
                st.error(f"🚫 **ADR ÖSSZEFÉRHETETLENSÉG!** A(z) **{adr_cikk}** besorolású termék nem tárolható ezen a tárhelyen: **{tarhely}** ({adr_tarhely})!")
            
            if not adr_hiba:
                # KAPACITÁS VIZSGÁLAT
                max_kapacitas = tarhely_info["Max Kapacitás"]
                j_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Tárhely"] == tarhely]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
                szabad = max_kapacitas - j_keszlet
                
                if mennyiseg > szabad:
                    st.error(f"🚫 **KAPACITÁS HIÁNY!** A(z) {tarhely} tárhelyen csak {szabad} db szabad hely van.")
                else:
                    uj_sarzs_id = f"S-{len(st.session_state.sarzs_keszlet) + 101}"
                    uj_sarzs = {
                        "SarzsID": uj_sarzs_id,
                        "Cikkszám": kivalasztott_cikkszam,
                        "Megnevezés": termek_info["Megnevezés"],
                        "Mennyiség": mennyiseg,
                        "Zárolt_Mennyiség": 0,
                        "Tárhely": tarhely,
                        "Beérkezés": datetime.date.today().strftime("%Y-%m-%d"),
                        "Lejárat": lejarat.strftime("%Y-%m-%d"),
                        "Beszerzési Ár": beszerzesi_ar
                    }
                    st.session_state.sarzs_keszlet = pd.concat([st.session_state.sarzs_keszlet, pd.DataFrame([uj_sarzs])], ignore_index=True)
                    st.success(f"✅ Bevételezés sikeres! Tárhely: {tarhely} | Sarzs: {uj_sarzs_id}")

# MODUL 2: KIADÁS KÉSZLETVÉDELEMMEL ÉS ZÁROLÁSSAL
elif menu == "📤 Kiadás (Stratégia, Zárolás & Safety Stock)":
    st.header("📤 Áru Kiadás – Tárhelyalapú Szabályzással")
    
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_termek_label = st.selectbox("Kiadandó Termék", list(termek_opciok.keys()))
    kivalasztott_cikkszam = termek_opciok[kivalasztott_termek_label]
    
    strategia = st.radio("Kibocsátási Stratégia (Picking Logic):", ["FIFO", "LIFO", "FEFO", "HIFO", "LOFO"])
    
    with st.form("kiadas_form"):
        mennyiseg = st.number_input("Kiadandó mennyiség (db)", min_value=1, value=3)
        admin_override = st.checkbox("🔓 Adminisztrátori felülbírálás (Biztonsági készlet terhére)")
        admin_pin_input = st.text_input("Admin PIN (csak felülbírálás esetén)", type="password")
        diak_nev = st.text_input("Kezelő neve", value="Raktáros")
        
        submitted = st.form_submit_button("Kiadási Utasítás Generálása")
        
        if submitted:
            cikk_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
            biztonsagi_limit = cikk_info["Biztonsági készlet"]
            
            elerheto_sarzsok = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam].copy()
            elerheto_sarzsok["Szabad_Mennyiség"] = elerheto_sarzsok["Mennyiség"] - elerheto_sarzsok["Zárolt_Mennyiség"]
            elerheto_sarzsok = elerheto_sarzsok[elerheto_sarzsok["Szabad_Mennyiség"] > 0]
            
            osszes_fizikai = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam]["Mennyiség"].sum()
            osszes_szabad = elerheto_sarzsok["Szabad_Mennyiség"].sum()
            maradando = osszes_fizikai - mennyiseg
            
            if maradando < biztonsagi_limit and not admin_override:
                st.error(f"🚫 **KIADÁS BLOKKOLVA!** A kiadás megsértené a Biztonsági Készletet ({biztonsagi_limit} db)! Maradvány lenne: {maradando} db.")
            elif admin_override and admin_pin_input != ADMIN_PIN:
                st.error("❌ Helytelen Admin PIN kód!")
            elif mennyiseg > osszes_szabad:
                st.error(f"🚫 **NINCS ELÉG SZABAD KÉSZLET!** Szabad: {osszes_szabad} db | Zárolt: {osszes_fizikai - osszes_szabad} db.")
            else:
                if estrategia == "FIFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beérkezés", ascending=True)
                elif estrategia == "LIFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beérkezés", ascending=False)
                elif estrategia == "FEFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Lejárat", ascending=True)
                elif estrategia == "HIFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beszerzési Ár", ascending=False)
                elif estrategia == "LOFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beszerzési Ár", ascending=True)
                
                maradek_igeny = mennyiseg
                kiadasi_utasitasok = []
                
                for idx, row in elerheto_sarzsok.iterrows():
                    if maradek_igeny <= 0: break
                    levonando = min(row["Szabad_Mennyiség"], maradek_igeny)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levonando
                    maradek_igeny -= levonando
                    kiadasi_utasitasok.append(f"📍 **TÁRHELY: {row['Tárhely']}** | Sarzs: `{row['SarzsID']}` | Mennyiség: **{levonando} db**")
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                st.success(f"✅ Kiszedési utasítás elkészült ({estrategia} elv alapján)!")
                for ut in kiadasi_utasitasok: st.write(f"- {ut}")
