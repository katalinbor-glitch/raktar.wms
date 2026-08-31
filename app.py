import streamlit as st
import pandas as pd
import datetime
import io

# 1. OLDALBEÁLLÍTÁS
st.set_page_config(page_title="WMS Raktárirányító & ADR Rendszer", layout="wide")

LOGIN_PASSWORD = "wms2026"
ADMIN_PIN = "Coca-cola20"

# 2. AUTHENTIKÁCIÓ
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

# 3. INICIALIZÁLÁS (SESSION STATE)
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
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "ADR Osztály": "Nem ADR", "Biztonsági készlet": 5, "Rendelésköteles készlet": 12, "Éves Értékforgalom (Ft)": 15000000},
        {"Cikkszám": "ART-002", "Megnevezés": "Ipari Oldószer (Acetón)", "ADR Osztály": "ADR 3", "Biztonsági készlet": 10, "Rendelésköteles készlet": 20, "Éves Értékforgalom (Ft)": 4500000},
        {"Cikkszám": "ART-003", "Megnevezés": "Sósav Oldat 37%", "ADR Osztály": "ADR 8", "Biztonsági készlet": 3, "Rendelésköteles készlet": 8, "Éves Értékforgalom (Ft)": 800000},
        {"Cikkszám": "ART-004", "Megnevezés": "Hidrogén-peroxid 50%", "ADR Osztály": "ADR 5.1", "Biztonsági készlet": 5, "Rendelésköteles készlet": 15, "Éves Értékforgalom (Ft)": 200000}
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

# 4. NAVIGÁCIÓ
st.sidebar.title("📌 Rendszer Menü")
if st.sidebar.button("🚪 Kijelentkezés"):
    st.session_state.authenticated = False
    st.rerun()

menu = st.sidebar.radio("Válassz Modult:", [
    "📋 Pillanatnyi Készlet & Rendszint", 
    "📊 ABC Elemzés (Leírással)",
    "📥 ADR Bevételezés & Tárhely Ellenőrzés", 
    "📤 Komissiózás & Kiszedési Lista", 
    "🧾 Leltár & Adatexport",
    "📜 Árumozgás Napló",
    "⚙️ Adminisztráció"
])

st.title("📦 WMS Raktárirányító & ADR Veszélyes Áru Rendszer")

# MODUL 1: PILLANATNYI KÉSZLET
if menu == "📋 Pillanatnyi Készlet & Rendszint":
    st.header("📋 Pillanatnyi Raktárkészlet és Zárolások")
    
    # FIGYELMEZTETŐ DOBOZOK GENERÁLÁSA
    figyelmeztetesek = []
    for _, cikk in st.session_state.cikktorzs.iterrows():
        c_kod = cikk["Cikkszám"]
        fizz = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        zarolt = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == c_kod]["Zárolt_Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
        szabad = fizz - zarolt
        
        if szabad < cikk["Biztonsági készlet"]:
            figyelmeztetesek.append((f"🚨 **KRITIKUS HIÁNY!** A(z) **{cikk['Megnevezés']} ({c_kod})** szabad készlete ({szabad} db) a Biztonsági Szint ({cikk['Biztonsági készlet']} db) ALA CSÖKKENT!", "error"))
        elif szabad <= cikk["Rendelésköteles készlet"]:
            figyelmeztetesek.append((f"⚠️ **UTÁNRENDELÉS SZÜKSÉGES!** A(z) **{cikk['Megnevezés']} ({c_kod})** elérte a rendelési küszöböt ({szabad} / {cikk['Rendelésköteles készlet']} db).", "warning"))

    # Figyelmeztető dobozok kirajzolása a felület tetejére
    if figyelmeztetesek:
        st.subheader("🔔 Készlet Riasztások & Teendők")
        for üzenet, tipus in figyelmeztetesek:
            if tipus == "error":
                st.error(üzenet)
            else:
                st.warning(üzenet)
        st.divider()

    st.subheader("📦 Tárhely- és Sarzsalapú Részletes Készlet")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)
    
    st.subheader("📊 Cikkszámonkénti Védelmi Szintek")
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
            "Cikkszám": c_kod, "Megnevezés": cikk["Megnevezés"], "ADR": cikk["ADR Osztály"],
            "Fizikai Készlet": fizz, "Zárolt (Hard Lock)": zarolt, "Szabad Készlet": szabad,
            "Biztonsági Limit": cikk["Biztonsági készlet"], "Utánrendelési Limit": cikk["Rendelésköteles készlet"], "Státusz": allapot
        })
    st.dataframe(pd.DataFrame(osszesito), use_container_width=True)

# MODUL 2: ABC ELEMZÉS LEÍRÁSSAL
elif menu == "📊 ABC Elemzés (Leírással)":
    st.header("📊 ABC Elemzés (Értékalapú Pareto Raktársorolás)")
    
    st.markdown("""
    ### 💡 Mi az az ABC Elemzés a Raktározásban?
    Az ABC elemzés a **Pareto-elv (80/20-as szabály)** alapján kategóriákba sorolja a termékeket az éves értékforgalmuk alapján. 
    Ez határozza meg a termékek **raktári elhelyezését** (közel az expediálási kapuhoz) és a leltározási gyakoriságot:
    
    * **'A' kategória (Kiemelt érték - kb. 80% értékforgalom):** A raktár legkönyebben elérhető tárhelyeire kerülnek. Gyakori, szigorú ellenőrzést igényelnek.
    * **'B' kategória (Közepes érték - kb. 15% értékforgalom):** Átlagos forgási sebességű és elhelyezésű termékek.
    * **'C' kategória (Alacsony érték - kb. 5% értékforgalom):** A raktár távolabbi/felsőbb tárhelyeire kerülnek, ritkább leltározással.
    """)
    st.divider()
    
    df_abc = st.session_state.cikktorzs.copy()
    df_abc = df_abc.sort_values(by="Éves Értékforgalom (Ft)", ascending=False)
    
    teljes_forgalom = df_abc["Éves Értékforgalom (Ft)"].sum()
    df_abc["Forgalmi Arány (%)"] = (df_abc["Éves Értékforgalom (Ft)"] / teljes_forgalom) * 100
    df_abc["Kumulált (%)"] = df_abc["Forgalmi Arány (%)"].cumsum()
    
    def besorolas(kum_pct):
        if kum_pct <= 80: return "🟢 'A' Osztály (Kiemelt)"
        elif kum_pct <= 95: return "🟡 'B' Osztály (Közepes)"
        else: return "🔴 'C' Osztály (Alacsony)"
        
    df_abc["ABC Osztály"] = df_abc["Kumulált (%)"].apply(besorolas)
    st.dataframe(df_abc[["Cikkszám", "Megnevezés", "Éves Értékforgalom (Ft)", "Forgalmi Arány (%)", "Kumulált (%)", "ABC Osztály"]], use_container_width=True)

# MODUL 3: ADR BEVÉTELEZÉS
elif menu == "📥 ADR Bevételezés & Tárhely Ellenőrzés":
    st.header("📥 Áru Bevételezés ADR Összeférhetőségi Vizsgálattal")
    
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']} ({row['ADR Osztály']})": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_termek_label = st.selectbox("Bevételezendő Termék", list(termek_opciok.keys()))
    kivalasztott_cikkszam = termek_opciok[kivalasztott_termek_label]
    termek_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
    
    with st.form("bevételezés_form"):
        col1, col2 = st.columns(2)
        with col1:
            mennyiseg = st.number_input("Bevételezendő mennyiség (db)", min_value=1, value=5)
            tarhely_lista = st.session_state.tarhely_torzs["Tárhely"].tolist()
            tarhely = st.selectbox("Cél Tárhely Kiválasztása", tarhely_lista)
        with col2:
            beszerzesi_ar = st.number_input("Beszerzési Egységár (Ft)", min_value=0, value=15000)
            lejarat = st.date_input("Lejárati dátum", value=datetime.date(2028, 12, 31))
            
        diak_nev = st.text_input("Kezelő neve", value="Raktáros")
        submitted = st.form_submit_button("Bevételezés Rögzítése")
        
        if submitted:
            tarhely_info = st.session_state.tarhely_torzs[st.session_state.tarhely_torzs["Tárhely"] == tarhely].iloc[0]
            adr_cikk = termek_info["ADR Osztály"]
            adr_tarhely = tarhely_info["ADR Engedély"]
            
            if adr_cikk != "Nem ADR" and adr_cikk not in adr_tarhely and adr_tarhely != "Általános":
                st.error(f"🚫 **ADR ÖSSZEFÉRHETETLENSÉG!** A(z) **{adr_cikk}** besorolású termék nem tárolható ezen a tárhelyen: **{tarhely}** ({adr_tarhely})!")
            else:
                max_kapacitas = tarhely_info["Max Kapacitás"]
                j_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Tárhely"] == tarhely]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
                szabad = max_kapacitas - j_keszlet
                
                if mennyiseg > szabad:
                    st.error(f"🚫 **KAPACITÁS HIÁNY!** A(z) {tarhely} tárhelyen csak {szabad} db szabad hely van.")
                else:
                    uj_sarzs_id = f"S-{len(st.session_state.sarzs_keszlet) + 101}"
                    uj_sarzs = {
                        "SarzsID": uj_sarzs_id, "Cikkszám": kivalasztott_cikkszam, "Megnevezés": termek_info["Megnevezés"],
                        "Mennyiség": mennyiseg, "Zárolt_Mennyiség": 0, "Tárhely": tarhely,
                        "Beérkezés": datetime.date.today().strftime("%Y-%m-%d"), "Lejárat": lejarat.strftime("%Y-%m-%d"), "Beszerzési Ár": beszerzesi_ar
                    }
                    st.session_state.sarzs_keszlet = pd.concat([st.session_state.sarzs_keszlet, pd.DataFrame([uj_sarzs])], ignore_index=True)
                    st.success(f"✅ Bevételezés sikeres! Tárhely: {tarhely} | Sarzs: {uj_sarzs_id}")

# MODUL 4: KOMISSIÓZÁS ÉS KISZEDÉSI LISTA
elif menu == "📤 Komissiózás & Kiszedési Lista":
    st.header("📤 Komissiózás (Picking) & Kiszedési Lista Generálás")
    
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_termek_label = st.selectbox("Kiadandó Termék", list(termek_opciok.keys()))
    kivalasztott_cikkszam = termek_opciok[kivalasztott_termek_label]
    
    # ÉLŐ KÉSZLET ÁLLAPOT KIÍRÁSA A FORM FELETT
    cikk_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
    fizz_aktuális = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam]["Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
    zarolt_aktuális = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam]["Zárolt_Mennyiség"].sum() if not st.session_state.sarzs_keszlet.empty else 0
    szabad_aktuális = fizz_aktuális - zarolt_aktuális
    
    st.info(f"ℹ️ **Aktuális Készlet Állapot:** Szabadon kiadható: **{szabad_aktuális} db** | Biztonsági limit: **{cikk_info['Biztonsági készlet']} db** | Zárolt: {zarolt_aktuális} db")
    
    strategia = st.radio("Kibocsátási Stratégia (Picking Logic):", ["FIFO", "LIFO", "FEFO", "HIFO", "LOFO"])
    
    with st.form("kiadas_form"):
        mennyiseg = st.number_input("Kiadandó mennyiség (db)", min_value=1, value=3)
        admin_override = st.checkbox("🔓 Adminisztrátori felülbírálás (Biztonsági készlet terhére)")
        admin_pin_input = st.text_input("Admin PIN (csak felülbírálás esetén)", type="password")
        diak_nev = st.text_input("Kezelő / Komissiózó neve", value="Raktáros")
        
        submitted = st.form_submit_button("🛒 Komissiózási Lista Generálása")
        
        if submitted:
            biztonsagi_limit = cikk_info["Biztonsági készlet"]
            
            elerheto_sarzsok = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam].copy()
            elerheto_sarzsok["Szabad_Mennyiség"] = elerheto_sarzsok["Mennyiség"] - elerheto_sarzsok["Zárolt_Mennyiség"]
            elerheto_sarzsok = elerheto_sarzsok[elerheto_sarzsok["Szabad_Mennyiség"] > 0]
            
            maradando = fizz_aktuális - mennyiseg
            
            # ELUTASÍTÁSOK / FIGYELMEZTETÉSEK
            if mennyiseg > szabad_aktuális:
                st.error(f"🚫 **NEM TUDJA KIADNI! NINCS ELÉG SZABAD KÉSZLET!**\n\nKért mennyiség: **{mennyiseg} db** | Jelenleg szabadon elérhető: **{szabad_aktuális} db** (Zárolt: {zarolt_aktuális} db).")
            elif maradando < biztonsagi_limit and not admin_override:
                st.error(f"🚫 **KIADÁS BLOKKOLVA! BIROLKI KÉSZLET VÉDELEM!**\n\nA kiadás után a készlet **{maradando} db**-ra csökkenne, ami megsértené a kötelező Biztonsági Készletet (**{biztonsagi_limit} db**)! Rendelés szükséges!")
            elif admin_override and admin_pin_input != ADMIN_PIN:
                st.error("❌ Helytelen Admin PIN kód! A biztonsági készlet terhére nem adható ki áru.")
            else:
                if estrategia == "FIFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beérkezés", ascending=True)
                elif estrategia == "LIFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beérkezés", ascending=False)
                elif estrategia == "FEFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Lejárat", ascending=True)
                elif estrategia == "HIFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beszerzési Ár", ascending=False)
                elif estrategia == "LOFO": elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beszerzési Ár", ascending=True)
                
                maradek_igeny = mennyiseg
                komissio_lista = []
                
                for idx, row in elerheto_sarzsok.iterrows():
                    if maradek_igeny <= 0: break
                    levonando = min(row["Szabad_Mennyiség"], maradek_igeny)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levonando
                    maradek_igeny -= levonando
                    
                    komissio_lista.append({
                        "Kiszedési Útvonal / Tárhely": row["Tárhely"],
                        "Cikkszám": kivalasztott_cikkszam,
                        "Megnevezés": row["Megnevezés"],
                        "SarzsID": row["SarzsID"],
                        "Kiszedendő Mennyiség": f"{levonando} db",
                        "Stratégia": estrategia
                    })
                    
                    # Naplózás
                    st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                        "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Művelet": "KIADÁS (KOMISSIÓ)", "Cikkszám": kivalasztott_cikkszam,
                        "Megnevezés": row["Megnevezés"], "Mennyiség": levonando, "SarzsID": row["SarzsID"],
                        "Tárhely": row["Tárhely"], "Stratégia": estrategia, "Beszerzési Ár": row["Beszerzési Ár"], "Felhasználó": diak_nev
                    }])], ignore_index=True)
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                
                # SIKERES KIADÁS UTÁNI UTÁNRENDELÉSI FIGYELMEZTETÉS
                st.success("✅ **KOMISSIÓZÁSI UTASÍTÁS SIKERESEN GENERÁLVA!**")
                
                uj_maradando = szabad_aktuális - mennyiseg
                if uj_maradando <= cikk_info["Rendelésköteles készlet"]:
                    st.warning(f"⚠️ **FIGYELEM! UTÁNRENDELÉS SZÜKSÉGES!** A kiadás után a megmaradt készlet (**{uj_maradando} db**) elérte vagy megközelítette az Utánrendelési Limit szintjét (**{cikk_info['Rendelésköteles készlet']} db**).")
                
                df_komissio = pd.DataFrame(komissio_lista)
                st.subheader("📝 Hivatalos Kiszedési Lista (Picking Sheet)")
                st.table(df_komissio)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_komissio.to_excel(writer, sheet_name='Kiszedési Lista', index=False)
                
                st.download_button(
                    label="🖨️ Kiszedési Lista Letöltése (Excel/Nyomtatás)",
                    data=buffer.getvalue(),
                    file_name=f"kiszedesi_lista_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# MODUL 5: LELTÁR
elif menu == "🧾 Leltár & Adatexport":
    st.header("🧾 Raktári Leltár és Adatletöltés")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.sarzs_keszlet.to_excel(writer, sheet_name='Készlet', index=False)
        st.session_state.cikktorzs.to_excel(writer, sheet_name='Cikktörzs', index=False)
    
    st.download_button(
        label="📥 Teljes Leltár Letöltése (Excel)",
        data=buffer.getvalue(),
        file_name=f"leltar_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# MODUL 6: NAPLÓ
elif menu == "📜 Árumozgás Napló":
    st.header("📜 Tranzakciós Árumozgás Napló")
    if st.session_state.naplo.empty:
        st.info("Még nem történt árumozgás.")
    else:
        st.dataframe(st.session_state.naplo, use_container_width=True)

# MODUL 7: ADMINISZTRÁCIÓ
elif menu == "⚙️ Adminisztráció":
    st.header("⚙️ Adminisztrációs Beállítások")
    pin = st.text_input("Adminisztrátori PIN kód", type="password")
    if pin == ADMIN_PIN:
        st.success("🔓 Admin hozzáférés engedélyezve.")
        st.subheader("Tárhely Törzs")
        st.dataframe(st.session_state.tarhely_torzs, use_container_width=True)
        st.subheader("Cikktörzs")
        st.dataframe(st.session_state.cikktorzs, use_container_width=True)
    elif pin != "":
        st.error("❌ Helytelen PIN kód!")
