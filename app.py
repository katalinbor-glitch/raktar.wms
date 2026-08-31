import streamlit as st
import pandas as pd
import datetime

# 1. OLDALBEÁLLÍTÁS
st.set_page_config(page_title="WMS Gyógyszer- & ADR Raktárirányító", layout="wide")

LOGIN_PASSWORD = "wms2026"
ADMIN_PIN = "Coca-cola20"

# 2. AUTHENTIKÁCIÓ
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 WMS Gyógyszer- & Raktárirányító Rendszer - Belépés")
    with st.form("login_form"):
        password_input = st.text_input("Belépési Jelszó", type="password")
        if st.form_submit_button("Belépés"):
            if password_input == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Helytelen jelszó!")
    st.stop()

# 3. INICIALIZÁLÁS (SESSION STATE)
if "tarhely_torzs" not in st.session_state:
    st.session_state.tarhely_torzs = pd.DataFrame([
        {"Tárhely": "A-01-01", "Max Kapacitás": 100, "ADR/Raktár Típus": "Általános"},
        {"Tárhely": "A-01-02", "Max Kapacitás": 50, "ADR/Raktár Típus": "ADR 3 (Gyúlékony)"},
        {"Tárhely": "B-02-01", "Max Kapacitás": 20, "ADR/Raktár Típus": "ADR 8 (Maró)"},
        {"Tárhely": "MED-01", "Max Kapacitás": 500, "ADR/Raktár Típus": "Gyógyszerraktár (Hűtött 2-8°C)"},
        {"Tárhely": "MED-02", "Max Kapacitás": 1000, "ADR/Raktár Típus": "Gyógyszerraktár (Szobahőfok)"}
    ])

if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "MED-001", "Megnevezés": "Algopyrin 500mg", "Típus": "Gyógyszer (Vény nélküli)", "ADR Osztály": "Nem ADR", "Biztonsági készlet": 20, "Rendelésköteles készlet": 50, "Éves Értékforgalom (Ft)": 5000000},
        {"Cikkszám": "MED-002", "Megnevezés": "Xanax 0.5mg", "Típus": "Gyógyszer (Vényköteles / Szigorú)", "ADR Osztály": "Nem ADR", "Biztonsági készlet": 10, "Rendelésköteles készlet": 30, "Éves Értékforgalom (Ft)": 8000000},
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Típus": "Általános Cikk", "ADR Osztály": "Nem ADR", "Biztonsági készlet": 5, "Rendelésköteles készlet": 12, "Éves Értékforgalom (Ft)": 15000000},
        {"Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "Típus": "Veszélyes Áru", "ADR Osztály": "ADR 3", "Biztonsági készlet": 10, "Rendelésköteles készlet": 20, "Éves Értékforgalom (Ft)": 4500000}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-MED-01", "Cikkszám": "MED-001", "Megnevezés": "Algopyrin 500mg", "Mennyiség": 40, "Zárolt_Mennyiség": 0, "Tárhely": "MED-02", "Beérkezés": "2026-01-10", "Lejárat": "2027-12-31", "Beszerzési Ár": 1200},
        {"SarzsID": "S-MED-02", "Cikkszám": "MED-002", "Megnevezés": "Xanax 0.5mg", "Mennyiség": 15, "Zárolt_Mennyiség": 0, "Tárhely": "MED-01", "Beérkezés": "2026-02-01", "Lejárat": "2026-10-15", "Beszerzési Ár": 3500},
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 10, "Zárolt_Mennyiség": 0, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2028-01-10", "Beszerzési Ár": 240000},
        {"SarzsID": "S-201", "Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "Mennyiség": 30, "Zárolt_Mennyiség": 0, "Tárhely": "A-01-02", "Beérkezés": "2026-01-15", "Lejárat": "2027-06-30", "Beszerzési Ár": 12000}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Stratégia/Megjegyzés", "Beszerzési Ár", "Felhasználó"])

# 4. NAVIGÁCIÓ
st.sidebar.title("📌 Rendszer Menü")
if st.sidebar.button("🚪 Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

menu = st.sidebar.radio("Válassz Modult:", [
    "📋 Pillanatnyi Készlet & Riasztások", 
    "💊 Gyógyszerraktár & FEFO Kiadás",
    "📊 ABC Elemzés (Leírással)",
    "📥 Áru Bevételezés (ADR & Gyógyszer)", 
    "📤 Általános Komissiózás", 
    "🧾 Leltár & Korrekció (Módosítás)",
    "📜 Árumozgás Napló",
    "⚙️ Adminisztráció"
])

st.title("💊📦 WMS Gyógyszer- & Általános Raktárirányító Rendszer")

# MODUL 1: PILLANATNYI KÉSZLET & RIASZTÁSOK
if menu == "📋 Pillanatnyi Készlet & Riasztások":
    st.header("📋 Pillanatnyi Raktárkészlet és Riasztások")
    
    figyelmeztetesek = []
    ma = datetime.date.today()
    
    for _, cikk in st.session_state.cikktorzs.iterrows():
        c_kod = cikk["Cikkszám"]
        fizz = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        zarolt = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Zárolt_Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        szabad = fizz - zarolt
        
        if szabad < cikk["Biztonsági készlet"]:
            figyelmeztetesek.append((f"🚨 **KRITIKUS HIÁNY!** A(z) **{cikk['Megnevezés']} ({c_kod})** szabad készlete ({szabad} db) a Biztonsági Szint ({cikk['Biztonsági készlet']} db) ALÁ CSÖKKENT!", "error"))
        elif szabad <= cikk["Rendelésköteles készlet"]:
            figyelmeztetesek.append((f"⚠️ **UTÁNRENDELÉS SZÜKSÉGES!** A(z) **{cikk['Megnevezés']} ({c_kod})** elérte a rendelési küszöböt ({szabad} / {cikk['Rendelésköteles készlet']} db).", "warning"))

    if not st.session_state.sarzs_keszlet.empty:
        for _, sarzs in st.session_state.sarzs_keszlet.iterrows():
            lejarat_dt = datetime.datetime.strptime(sarzs["Lejárat"], "%Y-%m-%d").date()
            napok_hatra = (lejarat_dt - ma).days
            if napok_hatra <= 90:
                figyelmeztetesek.append((f"⏳ **KÖZELI LEJÁRAT!** Sarzs **{sarzs['SarzsID']}** ({sarzs['Megnevezés']}) lejár **{sarzs['Lejárat']}** napon belül! ({napok_hatra} nap van hátra)", "warning"))

    if figyelmeztetesek:
        st.subheader("🔔 Készlet & Lejárati Riasztások")
        for üzenet, tipus in figyelmeztetesek:
            if tipus == "error": st.error(üzenet)
            else: st.warning(üzenet)
        st.divider()

    st.subheader("📦 Sarzsalapú Részletes Készlet")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)
    
    st.subheader("📊 Cikkszámonkénti Összesítő")
    osszesito = []
    for _, cikk in st.session_state.cikktorzs.iterrows():
        c_kod = cikk["Cikkszám"]
        fizz = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        zarolt = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Zárolt_Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        szabad = fizz - zarolt
        
        allapot = "🟢 Rendben"
        if szabad < cikk["Biztonsági készlet"]: allapot = "🔴 Biztonsági szint alatt!"
        elif szabad <= cikk["Rendelésköteles készlet"]: allapot = "🟡 Utánrendelés szükséges"
            
        osszesito.append({
            "Cikkszám": c_kod, "Megnevezés": cikk["Megnevezés"], "Típus": cikk["Típus"],
            "Fizikai Készlet": fizz, "Zárolt": zarolt, "Szabad Készlet": szabad,
            "Biztonsági Limit": cikk["Biztonsági készlet"], "Utánrendelési Limit": cikk["Rendelésköteles készlet"], "Státusz": allapot
        })
    st.dataframe(pd.DataFrame(osszesito), use_container_width=True)

# MODUL 2: GYÓGYSZERRAKTÁR & FEFO
elif menu == "💊 Gyógyszerraktár & FEFO Kiadás":
    st.header("💊 Gyógyszerraktári Modul & FEFO Kiadás")
    st.markdown("> **Gyógyszerészeti Szabályozás:** FEFO (First Expired, First Out) elv kötelező. Vényköteles terméknél az Orvosi Vény azonosító megadása kötelező!")
    st.divider()
    
    gyogyszerek = st.session_state.cikktorzs[st.session_state.cikktorzs["Típus"].str.contains("Gyógyszer")]
    gyogyszer_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']} ({row['Típus']})": row['Cikkszám'] for _, row in gyogyszerek.iterrows()}
    
    if gyogyszer_opciok:
        kivalasztott_label = st.selectbox("Válassz Kiadandó Gyógyszert:", list(gyogyszer_opciok.keys()))
        kivalasztott_cikkszam = gyogyszer_opciok[kivalasztott_label]
        cikk_info = gyogyszerek[gyogyszerek["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
        
        is_venykoteles = "Vényköteles" in cikk_info["Típus"]
        
        with st.form("gyogyszer_kiadas_form"):
            mennyiseg = st.number_input("Kiadandó mennyiség (doboz/db)", min_value=1, value=2)
            veny_szam = st.text_input("Orvosi Vény azonosító / Vény Kód (Vénykötelesnél KÖTELEZŐ)" if is_venykoteles else "Vény azonosító (Opcionális)")
            kiado_szemely = st.text_input("Kiadó Gyógyszerész / Raktáros neve", value="Dr. Gyógyszerész")
            
            submit_gyogyszer = st.form_submit_button("💊 Gyógyszer Kiadása (FEFO elv alapján)")
            
            if submit_gyogyszer:
                if is_venykoteles and not veny_szam.strip():
                    st.error("❌ **HIÁNYZÓ VÉNY!** Vényköteles gyógyszer nem adható ki érvényes Vény Azonosító nélkül!")
                else:
                    elerheto = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam].copy()
                    elerheto["Szabad"] = elerheto["Mennyiség"] - elerheto["Zárolt_Mennyiség"]
                    elerheto = elerheto[elerheto["Szabad"] > 0]
                    
                    össz_szabad = elerheto["Szabad"].sum()
                    
                    if mennyiseg > össz_szabad:
                        st.error(f"🚫 **NINCS ELÉG KÉSZLET!** Szabadon elérhető: {össz_szabad} db | Kért: {mennyiseg} db")
                    else:
                        elerheto = elerheto.sort_values(by="Lejárat", ascending=True)
                        maradek = mennyiseg
                        kiadas_details = []
                        
                        for idx, row in elerheto.iterrows():
                            if maradek <= 0: break
                            levon = min(row["Szabad"], maradek)
                            st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levon
                            maradek -= levon
                            
                            kiadas_details.append({
                                "SarzsID": row["SarzsID"], "Tárhely": row["Tárhely"], "Lejárat": row["Lejárat"], "Mennyiség": levon
                            })
                            
                            st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                                "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Művelet": "GYÓGYSZER KIADÁS (FEFO)", "Cikkszám": kivalasztott_cikkszam,
                                "Megnevezés": row["Megnevezés"], "Mennyiség": levon, "SarzsID": row["SarzsID"],
                                "Tárhely": row["Tárhely"], "Stratégia/Megjegyzés": f"FEFO | Vény: {veny_szam if veny_szam else 'Nincs'}", "Beszerzési Ár": row["Beszerzési Ár"], "Felhasználó": kiado_szemely
                            }])], ignore_index=True)
                        
                        st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                        st.success("✅ **GYÓGYSZER KIADÁS SIKERES!**")
                        st.table(pd.DataFrame(kiadas_details))
    else:
        st.info("Nincs gyógyszer kategóriájú termék a cikktörzsben.")

# MODUL 3: ABC ELEMZÉS
elif menu == "📊 ABC Elemzés (Leírással)":
    st.header("📊 ABC Elemzés (Értékalapú Pareto Raktársorolás)")
    df_abc = st.session_state.cikktorzs.copy().sort_values(by="Éves Értékforgalom (Ft)", ascending=False)
    teljes_forgalom = df_abc["Éves Értékforgalom (Ft)"].sum()
    df_abc["Forgalmi Arány (%)"] = (df_abc["Éves Értékforgalom (Ft)"] / teljes_forgalom) * 100 if teljes_forgalom > 0 else 0
    df_abc["Kumulált (%)"] = df_abc["Forgalmi Arány (%)"].cumsum()
    
    def besorolas(kum_pct):
        if kum_pct <= 80: return "🟢 'A' Osztály (Kiemelt)"
        elif kum_pct <= 95: return "🟡 'B' Osztály (Közepes)"
        else: return "🔴 'C' Osztály (Alacsony)"
        
    df_abc["ABC Osztály"] = df_abc["Kumulált (%)"].apply(besorolas)
    st.dataframe(df_abc[["Cikkszám", "Megnevezés", "Típus", "Éves Értékforgalom (Ft)", "Forgalmi Arány (%)", "Kumulált (%)", "ABC Osztály"]], use_container_width=True)

# MODUL 4: ÁRU BEVÉTELEZÉS (ADR & GYÓGYSZER)
elif menu == "📥 Áru Bevételezés (ADR & Gyógyszer)":
    st.header("📥 Bevételezés Raktártípus & ADR Összeférhetőséggel")
    
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']} ({row['Típus']} / {row['ADR Osztály']})": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_cikkszam = termek_opciok[st.selectbox("Bevételezendő Termék", list(termek_opciok.keys()))]
    termek_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
    
    with st.form("bevételezés_form"):
        col1, col2 = st.columns(2)
        with col1:
            mennyiseg = st.number_input("Bevételezendő mennyiség (db)", min_value=1, value=10)
            tarhely = st.selectbox("Cél Tárhely", st.session_state.tarhely_torzs["Tárhely"].tolist())
        with col2:
            beszerzesi_ar = st.number_input("Beszerzési Egységár (Ft)", min_value=0, value=2500)
            lejarat = st.date_input("Lejárati dátum", value=datetime.date(2027, 12, 31))
            
        diak_nev = st.text_input("Kezelő neve", value="Raktáros")
        submitted = st.form_submit_button("Bevételezés Rögzítése")
        
        if submitted:
            tarhely_info = st.session_state.tarhely_torzs[st.session_state.tarhely_torzs["Tárhely"] == tarhely].iloc[0]
            adr_cikk = termek_info["ADR Osztály"]
            tipus_cikk = termek_info["Típus"]
            tarhely_tipus = tarhely_info["ADR/Raktár Típus"]
            
            if "Gyógyszer" in tipus_cikk and "Gyógyszerraktár" not in tarhely_tipus:
                st.error(f"🚫 **HIBA!** Gyógyszer csak Gyógyszerraktári tárhelyre bevételezhető! ({tarhely} típusa: {tarhely_tipus})")
            elif adr_cikk != "Nem ADR" and adr_cikk not in tarhely_tipus and tarhely_tipus != "Általános":
                st.error(f"🚫 **ADR ÖSSZEFÉRHETETLENSÉG!** {adr_cikk} nem tárolható itt: {tarhely}")
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
                    "Tárhely": tarhely, "Stratégia/Megjegyzés": "-", "Beszerzési Ár": beszerzesi_ar, "Felhasználó": diak_nev
                }])], ignore_index=True)
                st.success(f"✅ Sikeres Bevételezés! SarzsID: {uj_sarzs_id}")

# MODUL 5: ÁLTALÁNOS KOMISSIÓZÁS
elif menu == "📤 Általános Komissiózás":
    st.header("📤 Általános Cikk Komissiózás (FIFO / LIFO / FEFO)")
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_cikkszam = termek_opciok[st.selectbox("Kiadandó Termék", list(termek_opciok.keys()))]
    
    strategia = st.radio("Kibocsátási Stratégia:", ["FIFO", "LIFO", "FEFO", "HIFO", "LOFO"])
    
    with st.form("general_kiadas_form"):
        mennyiseg = st.number_input("Kiadandó mennyiség (db)", min_value=1, value=2)
        submitted = st.form_submit_button("🛒 Kiszedési Lista Generálása")
        if submitted:
            elerheto = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam].copy()
            elerheto["Szabad"] = elerheto["Mennyiség"] - elerheto["Zárolt_Mennyiség"]
            
            if mennyiseg > elerheto["Szabad"].sum():
                st.error("🚫 Nincs elég szabad készlet!")
            else:
                if estrategia == "FIFO": elerheto = elerheto.sort_values(by="Beérkezés", ascending=True)
                elif estrategia == "FEFO": elerheto = elerheto.sort_values(by="Lejárat", ascending=True)
                
                maradek = mennyiseg
                lista = []
                for idx, row in elerheto.iterrows():
                    if maradek <= 0: break
                    levon = min(row["Szabad"], maradek)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levon
                    maradek -= levon
                    lista.append({"Tárhely": row["Tárhely"], "SarzsID": row["SarzsID"], "Kiszedendő": levon})
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                st.success("✅ Kiszedési Utasítás Generálva!")
                st.table(pd.DataFrame(lista))

# MODUL 6: LELTÁR ÉS MÓDOSÍTÁS / KORREKCIÓ
elif menu == "🧾 Leltár & Korrekció (Módosítás)":
    st.header("🧾 Leltár Ellenőrzés és Készletkorrekció")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)
    st.divider()
    
    st.subheader("🛠️ Leltáreltérés Módosítás")
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

# MODUL 8: ADMINISZTRÁCIÓ (ÚJ TERMÉK RÖGZÍTÉSÉVEL)
elif menu == "⚙️ Adminisztráció":
    st.header("⚙️ Adminisztrációs Beállítások & Cikktörzs Kezelés")
    
    admin_pin_input = st.text_input("Adminisztrátori PIN Kód", type="password")
    
    if admin_pin_input == ADMIN_PIN:
        st.success("🔓 Admin hozzáférés engedélyezve.")
        
        tab1, tab2 = st.tabs(["📋 Jelenlegi Cikktörzs", "➕ Új Termék Rögzítése"])
        
        with tab1:
            st.subheader("Regisztrált Cikkek Listája")
            st.dataframe(st.session_state.cikktorzs, use_container_width=True)
            
        with tab2:
            st.subheader("🆕 Új Cikk / Gyógyszer Hozzáadása a Cikktörzshöz")
            with st.form("uj_termek_form"):
                col1, col2 = st.columns(2)
                with col1:
                    uj_cikkszam = st.text_input("Cikkszám (pl. MED-003 vagy ART-003)", value=f"ART-00{len(st.session_state.cikktorzs)+1}")
                    uj_megnevezes = st.text_input("Termék Megnevezése", placeholder="pl. Paracetamol 500mg")
                    uj_tipus = st.selectbox("Termék Típusa / Kategóriája", [
                        "Gyógyszer (Vényköteles / Szigorú)",
                        "Gyógyszer (Vény nélküli)",
                        "Veszélyes Áru",
                        "Általános Cikk"
                    ])
                with col2:
                    uj_adr = st.selectbox("ADR Veszélyességi Osztály", ["Nem ADR", "ADR 3", "ADR 8", "ADR 6.1"])
                    uj_bizt = st.number_input("Biztonsági Készlet Limit (db)", min_value=0, value=10)
                    uj_rendel = st.number_input("Utánrendelési Küszöb (db)", min_value=0, value=25)
                    uj_ertekesites = st.number_input("Becsült Éves Értékforgalom (Ft)", min_value=0, value=1000000)
                
                submit_uj_termek = st.form_submit_button("➕ Új Termék Elmentése")
                
                if submit_uj_termek:
                    if not uj_cikkszam or not uj_megnevezes:
                        st.error("❌ A Cikkszám és Megnevezés mezők kitöltése kötelező!")
                    elif uj_cikkszam in st.session_state.cikktorzs["Cikkszám"].values:
                        st.error(f"❌ A(z) **{uj_cikkszam}** cikkszám már létezik a rendszerben!")
                    else:
                        uj_elem = {
                            "Cikkszám": uj_cikkszam,
                            "Megnevezés": uj_megnevezes,
                            "Típus": uj_tipus,
                            "ADR Osztály": uj_adr,
                            "Biztonsági készlet": uj_bizt,
                            "Rendelésköteles készlet": uj_rendel,
                            "Éves Értékforgalom (Ft)": uj_ertekesites
                        }
                        st.session_state.cikktorzs = pd.concat([st.session_state.cikktorzs, pd.DataFrame([uj_elem])], ignore_index=True)
                        st.success(f"🎉 **{uj_megnevezes} ({uj_cikkszam})** sikeresen hozzáadva a Cikktörzshöz!")
                        st.rerun()
    elif admin_pin_input != "":
        st.error("❌ Helytelen PIN Kód!")
