import streamlit as st
import pandas as pd
import datetime

# 1. OLDALBEÁLLÍTÁS
st.set_page_config(page_title="WMS Logisztikai & ADR Raktárirányító", layout="wide")

LOGIN_PASSWORD = "wms2026"

# 2. AUTHENTIKÁCIÓ
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 WMS Logisztikai & Raktárirányító Rendszer - Belépés")
    with st.form("login_form"):
        password_input = st.text_input("Belépési Jelszó", type="password")
        if st.form_submit_button("Belépés"):
            if password_input == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Helytelen jelszó!")
    st.stop()

# 3. ADR ÖSSZEFÉRHETŐSÉGI MÁTRIX (SZABÁLYOK)
# Melyik ADR osztály NEM tárolható együtt más ADR osztállyal egy tárhelyen/szektorban
ADR_INCOMPATIBILITY = {
    "ADR 3 (Gyúlékony folyadékok)": ["ADR 5.1 (Oxidáló anyagok)", "ADR 8 (Maró anyagok)"],
    "ADR 5.1 (Oxidáló anyagok)": ["ADR 3 (Gyúlékony folyadékok)", "ADR 4.1 (Gyúlékony szilárd)", "ADR 8 (Maró anyagok)"],
    "ADR 8 (Maró anyagok)": ["ADR 3 (Gyúlékony folyadékok)", "ADR 5.1 (Oxidáló anyagok)"],
    "ADR 6.1 (Mérgező anyagok)": ["ADR 1 (Robbanó)", "ADR 5.1 (Oxidáló anyagok)"]
}

def check_adr_compatibility(uj_adr, tarhely_id):
    """ Ellenőrzi, hogy az adott tárhelyen lévő meglévő sarzsok ADR osztálya kompatibilis-e az új áruval """
    if uj_adr == "Nem ADR":
        return True, ""
    
    meglevo_sarzsok = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Tárhely"] == tarhely_id]
    if meglevo_sarzsok.empty:
        return True, ""
    
    for _, sarzs in meglevo_sarzsok.iterrows():
        cikk_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == sarzs["Cikkszám"]]
        if not cikk_info.empty:
            meglevo_adr = cikk_info.iloc[0]["ADR Osztály"]
            
            # Tiltólista ellenőrzése
            if uj_adr in ADR_INCOMPATIBILITY and meglevo_adr in ADR_INCOMPATIBILITY[uj_adr]:
                return False, f"⚠️ ADR TILTÁS! A tárhelyen már van '{meglevo_adr}' ({sarzs['Megnevezés']}), ami NEM tárolható együtt a(z) '{uj_adr}' osztállyal!"
            if meglevo_adr in ADR_INCOMPATIBILITY and uj_adr in ADR_INCOMPATIBILITY[meglevo_adr]:
                return False, f"⚠️ ADR TILTÁS! A(z) '{meglevo_adr}' nem engedi a(z) '{uj_adr}' együttes tárolását!"
                
    return True, ""

# 4. INICIALIZÁLÁS (SESSION STATE)
if "tarhely_torzs" not in st.session_state:
    st.session_state.tarhely_torzs = pd.DataFrame([
        {"Tárhely": "A-01-01", "Max Kapacitás": 100, "ADR/Raktár Típus": "Általános"},
        {"Tárhely": "A-01-02", "Max Kapacitás": 50, "ADR/Raktár Típus": "ADR 3 (Gyúlékony)"},
        {"Tárhely": "B-02-01", "Max Kapacitás": 20, "ADR/Raktár Típus": "ADR 8 (Maró)"},
        {"Tárhely": "C-01-01", "Max Kapacitás": 200, "ADR/Raktár Típus": "Általános / Vegyes"}
    ])

if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Vonalkód": "5901234567891", "Típus": "Általános Cikk", "ADR Osztály": "Nem ADR", "Biztonsági készlet": 5, "Rendelésköteles készlet": 12, "Éves Értékforgalom (Ft)": 15000000},
        {"Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "Vonalkód": "5909876543210", "Típus": "Veszélyes Áru", "ADR Osztály": "ADR 3 (Gyúlékony folyadékok)", "Biztonsági készlet": 10, "Rendelésköteles készlet": 20, "Éves Értékforgalom (Ft)": 4500000},
        {"Cikkszám": "ART-003", "Megnevezés": "Sósav 33%", "Vonalkód": "5901122334455", "Típus": "Veszélyes Áru", "ADR Osztály": "ADR 8 (Maró anyagok)", "Biztonsági készlet": 8, "Rendelésköteles készlet": 15, "Éves Értékforgalom (Ft)": 2800000}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 10, "Zárolt_Mennyiség": 0, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2028-01-10", "Beszerzési Ár": 240000},
        {"SarzsID": "S-201", "Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "Mennyiség": 30, "Zárolt_Mennyiség": 0, "Tárhely": "A-01-02", "Beérkezés": "2026-01-15", "Lejárat": "2027-06-30", "Beszerzési Ár": 12000}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Stratégia/Megjegyzés", "Beszerzési Ár", "Felhasználó"])

# 5. NAVIGÁCIÓ
st.sidebar.title("📌 WMS Menü")
if st.sidebar.button("🚪 Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

menu = st.sidebar.radio("Válassz Modult:", [
    "📋 Pillanatnyi Készlet & Riasztások", 
    "➕ ÚJ TERMÉK RÖGZÍTÉSE & VONALKÓD",
    "📥 Áru Bevételezés & ADR Ellenőrzés", 
    "📤 Általános Komissiózás", 
    "📊 ABC Elemzés",
    "🧾 Leltár & Korrekció",
    "📜 Árumozgás Napló"
])

st.title("📦 WMS Általános & ADR Logisztikai Rendszer")

# MODUL 1: PILLANATNYI KÉSZLET
if menu == "📋 Pillanatnyi Készlet & Riasztások":
    st.header("📋 Pillanatnyi Raktárkészlet és Készletszint Riasztások")
    
    figyelmeztetesek = []
    ma = datetime.date.today()
    
    for _, cikk in st.session_state.cikktorzs.iterrows():
        c_kod = cikk["Cikkszám"]
        fizz = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        zarolt = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Zárolt_Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        szabad = fizz - zarolt
        
        if szabad < cikk["Biztonsági készlet"]:
            figyelmeztetesek.append((f"🚨 **KRITIKUS HIÁNY!** A(z) **{cikk['Megnevezés']} ({c_kod})** szabad készlete ({szabad} db) a **Biztonsági készlet** ({cikk['Biztonsági készlet']} db) alá csökkent!", "error"))
        elif szabad <= cikk["Rendelésköteles készlet"]:
            figyelmeztetesek.append((f"⚠️ **UTÁNRENDELÉS SZÜKSÉGES!** A(z) **{cikk['Megnevezés']} ({c_kod})** elérte a **Rendelésköteles készlet** szintjét ({szabad} / {cikk['Rendelésköteles készlet']} db).", "warning"))

    if figyelmeztetesek:
        st.subheader("🔔 Készlet Kockázati Riasztások")
        for üzenet, tipus in figyelmeztetesek:
            if tipus == "error": st.error(üzenet)
            else: st.warning(üzenet)
        st.divider()

    st.subheader("📊 Cikkszámonkénti Összesítő")
    osszesito = []
    for _, cikk in st.session_state.cikktorzs.iterrows():
        c_kod = cikk["Cikkszám"]
        fizz = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        zarolt = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Zárolt_Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        szabad = fizz - zarolt
        
        allapot = "🟢 Rendben"
        if szabad < cikk["Biztonsági készlet"]: allapot = "🔴 Biztonsági készlet alatt!"
        elif szabad <= cikk["Rendelésköteles készlet"]: allapot = "🟡 Rendelésköteles készleten!"
            
        osszesito.append({
            "Cikkszám": c_kod, 
            "Megnevezés": cikk["Megnevezés"], 
            "Vonalkód": cikk["Vonalkód"],
            "ADR Osztály": cikk["ADR Osztály"],
            "Fizikai Készlet": fizz, 
            "Szabad Készlet": szabad,
            "Biztonsági készlet": cikk["Biztonsági készlet"], 
            "Rendelésköteles készlet": cikk["Rendelésköteles készlet"], 
            "Státusz": allapot
        })
    st.dataframe(pd.DataFrame(osszesito), use_container_width=True)

    st.subheader("📦 Sarzsalapú Részletes Készlet")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)

# MODUL 2: ÚJ TERMÉK RÖGZÍTÉSE & VONALKÓD GENERÁLÁS
elif menu == "➕ ÚJ TERMÉK RÖGZÍTÉSE & VONALKÓD":
    st.header("➕ Új Cikk Rögzítése a Cikktörzsbe & Vonalkód Generátor")
    
    with st.form("uj_termek_form_direct"):
        col1, col2 = st.columns(2)
        with col1:
            uj_cikkszam = st.text_input("Cikkszám*", value=f"ART-00{len(st.session_state.cikktorzs)+1}")
            uj_megnevezes = st.text_input("Termék Megnevezése*", placeholder="pl. Ipari Ragasztó 5L")
            uj_tipus = st.selectbox("Termék Kategóriája", ["Általános Cikk", "Veszélyes Áru (ADR)", "Csomagolóanyag", "Alkatrész"])
            
            # Vonalkód generálás opció
            alap_vonalkod = f"590{datetime.datetime.now().strftime('%M%S')}{len(st.session_state.cikktorzs):04d}"
            uj_vonalkod = st.text_input("EAN-13 / Code128 Vonalkód", value=alap_vonalkod)

        with col2:
            uj_adr = st.selectbox("ADR Veszélyességi Osztály", [
                "Nem ADR", 
                "ADR 3 (Gyúlékony folyadékok)", 
                "ADR 4.1 (Gyúlékony szilárd)", 
                "ADR 5.1 (Oxidáló anyagok)", 
                "ADR 6.1 (Mérgező anyagok)", 
                "ADR 8 (Maró anyagok)"
            ])
            uj_bizt = st.number_input("Biztonsági készlet (db)", min_value=0, value=10)
            uj_rendel = st.number_input("Rendelésköteles készlet (db)", min_value=0, value=25)
            uj_ertekesites = st.number_input("Becsült Éves Értékforgalom (Ft)", min_value=0, value=1500000)
        
        submit_uj_termek = st.form_submit_button("💾 Új Termék Mentése & Vonalkód Generálása")
        
        if submit_uj_termek:
            if not uj_cikkszam or not uj_megnevezes:
                st.error("❌ A Cikkszám és Megnevezés mezők kitöltése kötelező!")
            elif uj_cikkszam in st.session_state.cikktorzs["Cikkszám"].values:
                st.error(f"❌ A(z) **{uj_cikkszam}** cikkszám már létezik!")
            else:
                uj_elem = {
                    "Cikkszám": uj_cikkszam,
                    "Megnevezés": uj_megnevezes,
                    "Vonalkód": uj_vonalkod,
                    "Típus": uj_tipus,
                    "ADR Osztály": uj_adr,
                    "Biztonsági készlet": uj_bizt,
                    "Rendelésköteles készlet": uj_rendel,
                    "Éves Értékforgalom (Ft)": uj_ertekesites
                }
                st.session_state.cikktorzs = pd.concat([st.session_state.cikktorzs, pd.DataFrame([uj_elem])], ignore_index=True)
                st.success(f"🎉 Termék **{uj_megnevezes} ({uj_cikkszam})** sikeresen rögzítve!")
                st.rerun()

    st.divider()
    st.subheader("🏷️ Cikktörzs & Generált Vonalkódok Vizuális Nyomtatása")
    
    for _, cikk in st.session_state.cikktorzs.iterrows():
        with st.expander(f"📦 {cikk['Cikkszám']} - {cikk['Megnevezés']} (Vonalkód: {cikk['Vonalkód']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"**Cikkszám:** {cikk['Cikkszám']}")
                st.markdown(f"**ADR Osztály:** {cikk['ADR Osztály']}")
                st.markdown(f"**Biztonsági készlet:** {cikk['Biztonsági készlet']} db")
                st.markdown(f"**Rendelésköteles készlet:** {cikk['Rendelésköteles készlet']} db")
            with c2:
                # Vizuális Vonalkód Címke Grafika (CSS/HTML szimuláció)
                st.markdown(f"""
                <div style="border: 2px solid #000; padding: 10px; background-color: #fff; color: #000; width: 260px; text-align: center; font-family: monospace;">
                    <div style="font-size: 12px; font-weight: bold;">{cikk['Megnevezés'][:25]}</div>
                    <div style="letter-spacing: 4px; font-size: 26px; margin: 5px 0;">||| | |||| | ||| |</div>
                    <div style="font-size: 14px; font-weight: bold;">*{cikk['Vonalkód']}*</div>
                    <div style="font-size: 10px;">ADR: {cikk['ADR Osztály']}</div>
                </div>
                """, unsafe_allow_html=True)

# MODUL 3: ÁRU BEVÉTELEZÉS & ADR ÖSSZEFÉRHETŐSÉG
elif menu == "📥 Áru Bevételezés & ADR Ellenőrzés":
    st.header("📥 Áru Bevételezés (ADR Összeférhetőségi Ellenőrzéssel)")
    
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']} [{row['ADR Osztály']}]": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_cikkszam = termek_opciok[st.selectbox("Bevételezendő Termék", list(termek_opciok.keys()))]
    termek_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
    
    with st.form("bevételezés_form"):
        col1, col2 = st.columns(2)
        with col1:
            mennyiseg = st.number_input("Bevételezendő mennyiség (db)", min_value=1, value=10)
            tarhely = st.selectbox("Cél Tárhely Kiválasztása", st.session_state.tarhely_torzs["Tárhely"].tolist())
        with col2:
            beszerzesi_ar = st.number_input("Beszerzési Egységár (Ft)", min_value=0, value=2500)
            lejarat = st.date_input("Lejárati dátum", value=datetime.date(2027, 12, 31))
            
        kezelo_nev = st.text_input("Raktáros Neve", value="Kezelő 01")
        submitted = st.form_submit_button("📥 Bevételezés Rögzítése")
        
        if submitted:
            adr_cikk = termek_info["ADR Osztály"]
            
            # ADR SZIGORÚ ÖSSZEFÉRHETŐSÉGI ELLENŐRZÉS
            kompatibilis, hiba_uzenet = check_adr_compatibility(adr_cikk, tarhely)
            
            if not kompatibilis:
                st.error(hiba_uzenet)
            else:
                uj_sarzs_id = f"S-{len(st.session_state.sarzs_keszlet) + 101}"
                uj_sarzs = {
                    "SarzsID": uj_sarzs_id, "Cikkszám": kivalasztott_cikkszam, "Megnevezés": termek_info["Megnevezés"],
                    "Mennyiség": mennyiseg, "Zárolt_Mennyiség": 0, "Tárhely": tarhely,
                    "Beérkezés": datetime.date.today().strftime("%Y-%m-%d"), "Lejárat": lejarat.strftime("%Y-%m-%d"), "Beszerzési Ár": beszerzesi_ar
                }
                st.session_state.sarzs_keszlet = pd.concat([st.session_state.sarzs_keszlet, pd.DataFrame([uj_sarzs])], ignore_index=True)
                
                st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                    "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Művelet": "BEVÉTELEZÉS", "Cikkszám": kivalasztott_cikkszam,
                    "Megnevezés": termek_info["Megnevezés"], "Mennyiség": mennyiseg, "SarzsID": uj_sarzs_id,
                    "Tárhely": tarhely, "Stratégia/Megjegyzés": f"ADR: {adr_cikk}", "Beszerzési Ár": beszerzesi_ar, "Felhasználó": kezelo_nev
                }])], ignore_index=True)
                st.success(f"✅ Sikeres Bevételezés a(z) **{tarhely}** tárhelyre! SarzsID: {uj_sarzs_id}")

# MODUL 4: KOMISSIÓZÁS
elif menu == "📤 Általános Komissiózás":
    st.header("📤 Áru Kiadás & Komissiózás (FIFO / LIFO / FEFO)")
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_cikkszam = termek_opciok[st.selectbox("Kiadandó Termék", list(termek_opciok.keys()))]
    
    strategia = st.radio("Kibocsátási Stratégia:", ["FIFO (Első be, első ki)", "FEFO (Mielőbbi lejárat)", "LIFO (Utolsó be, első ki)"])
    
    with st.form("general_kiadas_form"):
        mennyiseg = st.number_input("Kiadandó mennyiség (db)", min_value=1, value=2)
        submitted = st.form_submit_button("🛒 Kiszedési Utasítás Generálása")
        if submitted:
            elerheto = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam].copy()
            elerheto["Szabad"] = elerheto["Mennyiség"] - elerheto["Zárolt_Mennyiség"]
            
            if mennyiseg > elerheto["Szabad"].sum():
                st.error("🚫 Nincs elég szabad készlet!")
            else:
                if "FIFO" in strategia: elerheto = elerheto.sort_values(by="Beérkezés", ascending=True)
                elif "FEFO" in strategia: elerheto = elerheto.sort_values(by="Lejárat", ascending=True)
                elif "LIFO" in strategia: elerheto = elerheto.sort_values(by="Beérkezés", ascending=False)
                
                maradek = mennyiseg
                lista = []
                for idx, row in elerheto.iterrows():
                    if maradek <= 0: break
                    levon = min(row["Szabad"], maradek)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levon
                    maradek -= levon
                    lista.append({"Tárhely": row["Tárhely"], "SarzsID": row["SarzsID"], "Kiszedendő (db)": levon})
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                st.success("✅ Kiszedési Utasítás Generálva!")
                st.table(pd.DataFrame(lista))

# MODUL 5: ABC ELEMZÉS
elif menu == "📊 ABC Elemzés":
    st.header("📊 ABC Elemzés (Értékalapú Sorolás)")
    df_abc = st.session_state.cikktorzs.copy().sort_values(by="Éves Értékforgalom (Ft)", ascending=False)
    teljes_forgalom = df_abc["Éves Értékforgalom (Ft)"].sum()
    df_abc["Forgalmi Arány (%)"] = (df_abc["Éves Értékforgalom (Ft)"] / teljes_forgalom) * 100 if teljes_forgalom > 0 else 0
    df_abc["Kumulált (%)"] = df_abc["Forgalmi Arány (%)"].cumsum()
    
    def besorolas(kum_pct):
        if kum_pct <= 80: return "🟢 'A' Osztály (Magas értékforgalom)"
        elif kum_pct <= 95: return "🟡 'B' Osztály (Közepes értékforgalom)"
        else: return "🔴 'C' Osztály (Alacsony értékforgalom)"
        
    df_abc["ABC Osztály"] = df_abc["Kumulált (%)"].apply(besorolas)
    st.dataframe(df_abc[["Cikkszám", "Megnevezés", "Típus", "Éves Értékforgalom (Ft)", "Forgalmi Arány (%)", "Kumulált (%)", "ABC Osztály"]], use_container_width=True)

# MODUL 6: LELTÁR ÉS KORREKCIÓ
elif menu == "🧾 Leltár & Korrekció":
    st.header("🧾 Leltári Korrekció")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)
    st.divider()
    
    if not st.session_state.sarzs_keszlet.empty:
        sarzs_opciok = {f"{row['SarzsID']} - {row['Megnevezés']} (Tárhely: {row['Tárhely']} | Könyvelt: {row['Mennyiség']} db)": row['SarzsID'] for _, row in st.session_state.sarzs_keszlet.iterrows()}
        kivalasztott_sarzs_id = sarzs_opciok[st.selectbox("Módosítandó Sarzs Kiválasztása:", list(sarzs_opciok.keys()))]
        sarzs_data = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["SarzsID"] == kivalasztott_sarzs_id].iloc[0]
        
        with st.form("leltar_korrekcio_form"):
            uj_fizikai_mennyiseg = st.number_input("Ténylegesen megszámolt Fizikai Mennyiség (db):", min_value=0, value=int(sarzs_data['Mennyiség']))
            ok_leiras = st.selectbox("Indok:", ["Leltárhiány (Selejt/Kár)", "Leltártöbblet (Talált áru)", "Sérülés / Minőségi Zárolás", "Adminisztrációs Korrekció"])
            leltarozo_nev = st.text_input("Kezelő Neve:", value="Leltárfelelős")
            
            if st.form_submit_button("💾 Leltáreltérés Módosítása"):
                regi = sarzs_data['Mennyiség']
                kulonbseg = uj_fizikai_mennyiseg - regi
                
                if uj_fizikai_mennyiseg == 0:
                    st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["SarzsID"] != kivalasztott_sarzs_id]
                else:
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == kivalasztott_sarzs_id, "Mennyiség"] = uj_fizikai_mennyiseg
                
                st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                    "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Művelet": f"LELTÁR KORREKCIÓ ({kulonbseg:+d} db)", "Cikkszám": sarzs_data["Cikkszám"],
                    "Megnevezés": sarzs_data["Megnevezés"], "Mennyiség": uj_fizikai_mennyiseg, "SarzsID": kivalasztott_sarzs_id,
                    "Tárhely": sarzs_data["Tárhely"], "Stratégia/Megjegyzés": f"Indok: {ok_leiras}", "Beszerzési Ár": sarzs_data["Beszerzési Ár"], "Felhasználó": leltarozo_nev
                }])], ignore_index=True)
                st.success(f"✅ Leltármódosítás elmentve! Új készlet: {uj_fizikai_mennyiseg} db.")
                st.rerun()

# MODUL 7: NAPLÓ
elif menu == "📜 Árumozgás Napló":
    st.header("📜 Tranzakciós Árumozgás Napló")
    st.dataframe(st.session_state.naplo, use_container_width=True)
