import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="WMS Raktárirányító Rendszer", layout="wide")

# Konfiguráció - Beállított Admin jelszó
ADMIN_PIN = "Coca-cola20"

# 1. INICIALIZÁLÁS (Készlet és Törzsadatok Rendelésköteles Szinttel)
if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Vonalkód": "5901234567891", "Biztonsági készlet": 5, "Rendelésköteles készlet": 12},
        {"Cikkszám": "ART-002", "Megnevezés": "Egér Logitech MX Master", "Vonalkód": "5901234567892", "Biztonsági készlet": 5, "Rendelésköteles készlet": 15},
        {"Cikkszám": "ART-003", "Megnevezés": "Monitor HP 27 inch", "Vonalkód": "5901234567893", "Biztonsági készlet": 2, "Rendelésköteles készlet": 6},
        {"Cikkszám": "ART-004", "Megnevezés": "USB Kábel Type-C", "Vonalkód": "5901234567894", "Biztonsági készlet": 10, "Rendelésköteles készlet": 25}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 10, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2028-01-10", "Beszerzési Ár": 240000},
        {"SarzsID": "S-102", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 5, "Tárhely": "C-03-02", "Beérkezés": "2026-02-01", "Lejárat": "2028-02-01", "Beszerzési Ár": 260000},
        {"SarzsID": "S-201", "Cikkszám": "ART-002", "Megnevezés": "Egér Logitech MX Master", "Mennyiség": 40, "Tárhely": "A-01-02", "Beérkezés": "2026-01-15", "Lejárat": "2027-06-30", "Beszerzési Ár": 32000},
        {"SarzsID": "S-301", "Cikkszám": "ART-003", "Megnevezés": "Monitor HP 27 inch", "Mennyiség": 8, "Tárhely": "B-02-01", "Beérkezés": "2026-01-20", "Lejárat": "2029-01-01", "Beszerzési Ár": 85000},
        {"SarzsID": "S-401", "Cikkszám": "ART-004", "Megnevezés": "USB Kábel Type-C", "Mennyiség": 100, "Tárhely": "D-01-01", "Beérkezés": "2026-01-05", "Lejárat": "2030-01-01", "Beszerzési Ár": 1500}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Stratégia", "Beszerzési Ár", "Felhasználó"])

# Cím
st.title("📦 WMS Raktárirányítási Rendszer")

# Oldalsáv navigáció
menu = st.sidebar.radio("Navigáció / Modulok", [
    "📋 Pillanatnyi Készlet & Rendszint", 
    "📥 Bevételezés", 
    "📤 Kiadás (Stratégia & Tárhely)", 
    "➕ Új Termék Rögzítése",
    "📊 Leltár & Időszaki Export",
    "📈 ABC Elemzés (Készletérték)",
    "📜 Árumozgás Napló", 
    "⚙️ Adminisztráció & Védett Törlés"
])

# 1. PILLANATNYI KÉSZLET & JELZŐRENDSZER (RENDELÉSKÖTELES KÉSZLETTEL)
if menu == "📋 Pillanatnyi Készlet & Rendszint":
    st.header("📋 Pillanatnyi Készlet & Újrarendelési Jelzések")
    
    if st.session_state.cikktorzs.empty:
        st.info("ℹ️ A raktári adatbázis jelenleg teljesen üres! Új terméket a '➕ Új Termék Rögzítése' fülön tudsz hozzáadni.")
    else:
        keszlet_összegzo = st.session_state.sarzs_keszlet.groupby("Cikkszám")["Mennyiség"].sum().reset_index()
        df_merged = pd.merge(st.session_state.cikktorzs, keszlet_összegzo, on="Cikkszám", how="left").fillna(0)
        
        # Rendelésköteles készlet vs. Biztonsági készlet ellenőrzése
        def kartya_statusz(row):
            if row["Mennyiség"] <= row["Biztonsági készlet"]:
                return "🚨 KRITIKUS (BIZTONSÁGI KÉSZLET ALATT!)"
            elif row["Mennyiség"] <= row["Rendelésköteles készlet"]:
                return "⚠️ RENDELÉSKÖTELES KÉSZLET ELÉRVE! (RENDELNI KELL!)"
            else:
                return "✅ OPTIMÁLIS KÉSZLET"

        df_merged["Készlet Státusz"] = df_merged.apply(kartya_statusz, axis=1)
        
        rendelendo = df_merged[df_merged["Mennyiség"] <= df_merged["Rendelésköteles készlet"]]
        if not rendelendo.empty:
            st.error(f"🚨 **FIGYELEM! {len(rendelendo)} termék elérte a rendelésköteles készletszintet! Utánrendelés szükséges.**")
            for _, row in rendelendo.iterrows():
                szukseges = (row['Rendelésköteles készlet'] * 2) - row['Mennyiség']
                st.warning(f"👉 **{row['Megnevezés']}** ({row['Cikkszám']}): Jelenleg **{int(row['Mennyiség'])} db** van raktáron (Rendelési limit: **{row['Rendelésköteles készlet']} db** | Biztonsági limit: **{row['Biztonsági készlet']} db**). Javasolt rendelés: **{int(szukseges)} db**")
        else:
            st.success("✅ Minden termékből optimális a készletszint!")

        st.subheader("Összesített Készlet és Rendszint Státusz")
        st.dataframe(df_merged, use_container_width=True)
        
        st.subheader("Részletes Sarzs és Tárhely Nyilvántartás")
        st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)

# 2. BEVÉTELEZÉS
elif menu == "📥 Bevételezés":
    st.header("📥 Áru Bevételezés")
    
    if st.session_state.cikktorzs.empty:
        st.warning("⚠️ Először hozz létre egy terméket az 'Új Termék Rögzítése' menüpontban!")
    else:
        termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
        kivalasztott_termek_label = st.selectbox("Termék kiválasztása", list(termek_opciok.keys()))
        kivalasztott_cikkszam = termek_opciok[kivalasztott_termek_label]
        
        with st.form("bevételezés_form"):
            col1, col2 = st.columns(2)
            with col1:
                mennyiseg = st.number_input("Bevételezendő mennyiség", min_value=1, value=5)
                tarhely = st.text_input("Tárhely (pl. A-01-01, C-03-02)", value="A-01-01")
            with col2:
                beszerzesi_ar = st.number_input("Beszerzési Egységár (Ft)", min_value=0, value=50000)
                lejarat = st.date_input("Lejárati dátum", value=datetime.date(2027, 12, 31))
                
            diak_nev = st.text_input("Kezelő neve", value="Diák")
            submitted = st.form_submit_button("Bevételezés Rögzítése")
            
            if submitted:
                termek_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam].iloc[0]
                új_sarzs_id = f"S-{len(st.session_state.sarzs_keszlet) + 101}"
                
                uj_sarzs = {
                    "SarzsID": új_sarzs_id,
                    "Cikkszám": kivalasztott_cikkszam,
                    "Megnevezés": termek_info["Megnevezés"],
                    "Mennyiség": mennyiseg,
                    "Tárhely": tarhely,
                    "Beérkezés": datetime.date.today().strftime("%Y-%m-%d"),
                    "Lejárat": lejarat.strftime("%Y-%m-%d"),
                    "Beszerzési Ár": beszerzesi_ar
                }
                st.session_state.sarzs_keszlet = pd.concat([st.session_state.sarzs_keszlet, pd.DataFrame([uj_sarzs])], ignore_index=True)
                
                uj_bejegyzes = {
                    "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Művelet": "BEVÉTEL",
                    "Cikkszám": kivalasztott_cikkszam,
                    "Megnevezés": termek_info["Megnevezés"],
                    "Mennyiség": mennyiseg,
                    "SarzsID": új_sarzs_id,
                    "Tárhely": tarhely,
                    "Stratégia": "-",
                    "Beszerzési Ár": beszerzesi_ar,
                    "Felhasználó": diak_nev
                }
                st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([uj_bejegyzes])], ignore_index=True)
                st.success(f"Sikeres bevételezés! Tárhely: {tarhely} | Sarzs: {új_sarzs_id}")

# 3. KIADÁS
elif menu == "📤 Kiadás (Stratégia & Tárhely)":
    st.header("📤 Áru Kiadás")
    
    if st.session_state.cikktorzs.empty:
        st.warning("⚠️ Nincsenek termékek a rendszerben!")
    else:
        termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
        kivalasztott_termek_label = st.selectbox("Kiadandó Termék Kiválasztása", list(termek_opciok.keys()))
        kivalasztott_cikkszam = termek_opciok[kivalasztott_termek_label]
        
        strategia = st.radio(
            "Kibocsátási Stratégia Kiválasztása:",
            [
                "FIFO (First-In, First-Out) - Legrégebben beérkezett áru",
                "LIFO (Last-In, First-Out) - Legutoljára beérkezett áru",
                "FEFO (First-Expired, First-Out) - Legkorábban lejáró áru",
                "HIFO (Highest-In, First-Out) - Legdrágábban vett áru",
                "LOFO (Lowest-In, First-Out) - Legolcsóbban vett áru"
            ]
        )
        
        with st.form("kiadas_form"):
            mennyiseg = st.number_input("Kiadandó mennyiség", min_value=1, value=3)
            diak_nev = st.text_input("Kezelő neve", value="Diák")
            submitted = st.form_submit_button("Kiadás Végrehajtása")
            
            if submitted:
                elerheto_sarzsok = st.session_state.sarzs_keszlet[
                    (st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam) & 
                    (st.session_state.sarzs_keszlet["Mennyiség"] > 0)
                ].copy()
                
                osszes_keszlet = elerheto_sarzsok["Mennyiség"].sum()
                
                if mennyiseg > osszes_keszlet:
                    st.error(f"Nincs elegendő készlet! Elérhető összkészlet: {osszes_keszlet} db")
                else:
                    ar_oszlop = "Beszerzési Ár" if "Beszerzési Ár" in elerheto_sarzsok.columns else "Beszerzési Ár (Ft)"
                    
                    if "FIFO" in strategia:
                        elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beérkezés", ascending=True)
                        strat_nev = "FIFO"
                    elif "LIFO" in strategia:
                        elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beérkezés", ascending=False)
                        strat_nev = "LIFO"
                    elif "FEFO" in strategia:
                        elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Lejárat", ascending=True)
                        strat_nev = "FEFO"
                    elif "HIFO" in strategia:
                        elerheto_sarzsok = elerheto_sarzsok.sort_values(by=ar_oszlop, ascending=False)
                        strat_nev = "HIFO"
                    elif "LOFO" in strategia:
                        elerheto_sarzsok = elerheto_sarzsok.sort_values(by=ar_oszlop, ascending=True)
                        strat_nev = "LOFO"
                    
                    maradek_igény = mennyiseg
                    kiadasi_utasitasok = []
                    
                    for idx, row in elerheto_sarzsok.iterrows():
                        if maradek_igény <= 0:
                            break
                        
                        levonando = min(row["Mennyiség"], maradek_igény)
                        st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levonando
                        maradek_igény -= levonando
                        
                        ar_ertek = row.get("Beszerzési Ár", row.get("Beszerzési Ár (Ft)", 0))
                        kiadasi_utasitasok.append(f"📦 Termék: **{row['Megnevezés']}** | 📍 **Tárhely: {row['Tárhely']}** | Sarzs: {row['SarzsID']} | Mennyiség: **{levonando} db**")
                        
                        uj_bejegyzes = {
                            "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Művelet": "KIADÁS",
                            "Cikkszám": kivalasztott_cikkszam,
                            "Megnevezés": row["Megnevezés"],
                            "Mennyiség": levonando,
                            "SarzsID": row["SarzsID"],
                            "Tárhely": row["Tárhely"],
                            "Stratégia": strat_nev,
                            "Beszerzési Ár": ar_ertek,
                            "Felhasználó": diak_nev
                        }
                        st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([uj_bejegyzes])], ignore_index=True)
                    
                    st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                    
                    st.success(f"✅ Kiadás sikeresen végrehajtva ({strat_nev} alapján)!")
                    st.markdown("### 📋 Kiszedési Utasítás:")
                    for utazas in kiadasi_utasitasok:
                        st.write(f"- {utazas}")
                    
                    friss_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam]["Mennyiség"].sum()
                    rend_keszlet = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam]["Rendelésköteles készlet"].values[0]
                    
                    if friss_keszlet <= rend_keszlet:
                        st.error(f"🚨 **RENDELÉSI RIASZTÁS!** A(z) {kivalasztott_termek_label} készlete kiadás után **{int(friss_keszlet)} db**-ra csökkent, ami eléri a rendelésköteles szintet ({rend_keszlet} db)! **Utánrendelés szükséges!**")

# 4. ÚJ TERMÉK RÖGZÍTÉSE
elif menu == "➕ Új Termék Rögzítése":
    st.header("➕ Új Termék Hozzáadása a Törzsbe")
    with st.form("uj_termek_form"):
        col1, col2 = st.columns(2)
        with col1:
            uj_cikkszam = st.text_input("Cikkszám (pl. ART-005)", value="ART-005")
            uj_nev = st.text_input("Megnevezés", value="Billentyűzet")
            uj_vonalkod = st.text_input("Vonalkód (EAN)", value="5901234567895")
        with col2:
            uj_biztonsagi = st.number_input("Biztonsági készlet (db)", min_value=0, value=5)
            uj_rendeleskoteles = st.number_input("Rendelésköteles készlet (db)", min_value=0, value=12)

        submitted_uj = st.form_submit_button("Új Termék Mentése")
        if submitted_uj:
            if uj_cikkszam in st.session_state.cikktorzs["Cikkszám"].values:
                st.error("⚠️ Ez a cikkszám már létezik!")
            else:
                uj_sor = {
                    "Cikkszám": uj_cikkszam, 
                    "Megnevezés": uj_nev, 
                    "Vonalkód": uj_vonalkod, 
                    "Biztonsági készlet": uj_biztonsagi,
                    "Rendelésköteles készlet": uj_rendeleskoteles
                }
                st.session_state.cikktorzs = pd.concat([st.session_state.cikktorzs, pd.DataFrame([uj_sor])], ignore_index=True)
                st.success(f"✅ Termék mentve: {uj_nev}")

# 5. LELTÁR ÉS IDŐSZAKI EXPORT
elif menu == "📊 Leltár & Időszaki Export":
    st.header("📊 Leltár és Időszaki Készletkimutatás")
    
    col1, col2 = st.columns(2)
    with col1:
        kezdo_datum = st.date_input("Időszak Kezdete", value=datetime.date(2026, 1, 1))
    with col2:
        zaro_datum = st.date_input("Időszak Vége", value=datetime.date.today())
        
    st.subheader("📋 Szűrt Leltárív (A megadott időszak beérkezései alapján)")
    
    if not st.session_state.sarzs_keszlet.empty:
        df_leltar = st.session_state.sarzs_keszlet.copy()
        df_leltar["Beérkezés_Dátum"] = pd.to_datetime(df_leltar["Beérkezés"]).dt.date
        
        szurt_leltar = df_leltar[
            (df_leltar["Beérkezés_Dátum"] >= kezdo_datum) & 
            (df_leltar["Beérkezés_Dátum"] <= zaro_datum)
        ].drop(columns=["Beérkezés_Dátum"])
        
        szurt_leltar["Készletérték (Ft)"] = szurt_leltar["Mennyiség"] * szurt_leltar["Beszerzési Ár"]
        
        st.dataframe(szurt_leltar, use_container_width=True)
        
        osszes_ertek = szurt_leltar["Készletérték (Ft)"].sum()
        osszes_db = szurt_leltar["Mennyiség"].sum()
        
        st.info(f"💰 **A szűrt időszak összesített záró készletértéke:** {osszes_ertek:,.0f} Ft | **Összes mennyiség:** {osszes_db} db")
        
        csv_data = szurt_leltar.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Leltárív Letöltése (Excel/CSV)",
            data=csv_data,
            file_name=f"leltar_{kezdo_datum}_to_{zaro_datum}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Nincs készleten lévő áru a leltározáshoz!")

    st.markdown("---")
    st.subheader("📝 Leltárkorrekció (Hiány / Többlet Rögzítése)")
    st.info("🔒 A leltárkorrekcióhoz adminisztrátori jelszó szükséges!")
    
    if not st.session_state.sarzs_keszlet.empty:
        with st.form("leltar_korrekcio_form"):
            sarzs_list = st.session_state.sarzs_keszlet["SarzsID"] + " - " + st.session_state.sarzs_keszlet["Megnevezés"] + " (" + st.session_state.sarzs_keszlet["Tárhely"] + ")"
            kivalasztott_sarzs_str = st.selectbox("Módosítandó Tárhely / Sarzs Kiválasztása", sarzs_list)
            uj_tény_mennyiseg = st.number_input("Ténylegesen számolt mennyiség (db)", min_value=0, value=10)
            korrekcio_pin = st.text_input("Admin jelszó", type="password")
            
            submitted_korrekcio = st.form_submit_button("Leltárkorrekció Mentése")
            
            if submitted_korrekcio:
                if korrekcio_pin == ADMIN_PIN:
                    s_id = kivalasztott_sarzs_str.split(" - ")[0]
                    
                    regi_db = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Mennyiség"].values[0]
                    cikk = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Cikkszám"].values[0]
                    nev = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Megnevezés"].values[0]
                    tarhely = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Tárhely"].values[0]
                    ar = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Beszerzési Ár"].values[0]
                    
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Mennyiség"] = uj_tény_mennyiseg
                    
                    eltérés = uj_tény_mennyiseg - regi_db
                    uj_bejegyzes = {
                        "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Művelet": f"LELTÁRKORREKCIÓ ({'+' if eltérés > 0 else ''}{eltérés} db)",
                        "Cikkszám": cikk,
                        "Megnevezés": nev,
                        "Mennyiség": uj_tény_mennyiseg,
                        "SarzsID": s_id,
                        "Tárhely": tarhely,
                        "Stratégia": "LELTÁR",
                        "Beszerzési Ár": ar,
                        "Felhasználó": "ADMIN"
                    }
                    st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([uj_bejegyzes])], ignore_index=True)
                    
                    st.success(f"✅ A(z) {s_id} sarzs készlete módosítva: {regi_db} db ➔ {uj_tény_mennyiseg} db!")
                    st.rerun()
                else:
                    st.error("❌ Helytelen Admin jelszó!")

# 6. ABC ELEMZÉS MODUL
elif menu == "📈 ABC Elemzés (Készletérték)":
    st.header("📈 Készletérték Alapú ABC Elemzés")
    st.markdown("""
    Az ABC elemzés a **Pareto-elv (80/20-as szabály)** alapján csoportosítja a raktári termékeket:
    * **'A' kategória:** A teljes készletérték kb. **80%-át** adó legértékesebb termékek (kiemelt figyelmet igényelnek).
    * **'B' kategória:** A következő kb. **15%-ot** adó közepes értékű termékek.
    * **'C' kategória:** A maradék kb. **5%-ot** adó, kis értékű vagy nagy mennyiségű tömegcikkek.
    """)
    
    if st.session_state.sarzs_keszlet.empty:
        st.warning("⚠️ Nincs készleten lévő áru az elemzés elvégzéséhez!")
    else:
        # Készletérték számítása cikkekre lebontva
        df_abc = st.session_state.sarzs_keszlet.copy()
        df_abc["Készletérték"] = df_abc["Mennyiség"] * df_abc["Beszerzési Ár"]
        
        # Összegzés cikkszámonként
        abc_summary = df_abc.groupby(["Cikkszám", "Megnevezés"]).agg(
            Össz_Mennyiség=("Mennyiség", "sum"),
            Össz_Készletérték=("Készletérték", "sum")
        ).reset_index()
        
        # Csökkenő sorrendbe rendezés érték alapján
        abc_summary = abc_summary.sort_values(by="Össz_Készletérték", ascending=False).reset_index(drop=True)
        
        # Kumulált érték és százalék számítás
        teljes_raktar_ertek = abc_summary["Össz_Készletérték"].sum()
        abc_summary["Kumulált_Érték"] = abc_summary["Össz_Készletérték"].cumsum()
        abc_summary["Kumulált_%"] = (abc_summary["Kumulált_Érték"] / teljes_raktar_ertek) * 100
        
        # ABC Besorolási logika
        def besorolas(pct):
            if pct <= 80:
                return "🔴 'A' Osztály (Szigorú kontroll)"
            elif pct <= 95:
                return "🟡 'B' Osztály (Átlagos kontroll)"
            else:
                return "🟢 'C' Osztály (Egyszerűsített)"

        abc_summary["ABC Osztály"] = abc_summary["Kumulált_%"].apply(besorolas)
        
        st.subheader("📊 Elemzési Eredmények:")
        st.dataframe(abc_summary.style.format({
            "Össz_Készletérték": "{:,.0f} Ft",
            "Kumulált_Érték": "{:,.0f} Ft",
            "Kumulált_%": "{:.2f} %"
        }), use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 'A' Cikkek száma", len(abc_summary[abc_summary["ABC Osztály"].str.contains("'A'")]))
        col2.metric("🟡 'B' Cikkek száma", len(abc_summary[abc_summary["ABC Osztály"].str.contains("'B'")]))
        col3.metric("🟢 'C' Cikkek száma", len(abc_summary[abc_summary["ABC Osztály"].str.contains("'C'")]))

# 7. NAPLÓ
elif menu == "📜 Árumozgás Napló":
    st.header("📜 Árumozgási Előzmények")
    st.dataframe(st.session_state.naplo, use_container_width=True)
    csv = st.session_state.naplo.to_csv(index=False).encode('utf-8')
    st.download_button("Napló Letöltése (CSV)", csv, "wms_naplo.csv", "text/csv")

# 8. ADMINISZTRÁCIÓ ÉS JELSZÓVAL VÉDETT TELJES TÖRLÉS
elif menu == "⚙️ Adminisztráció & Védett Törlés":
    st.header("⚙️ Adminisztráció és Védett Műveletek")
    st.info("🔒 A törlési műveletekhez adminisztrátori jelszó szükséges!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗑️ Cikk Törlése a Törzsből")
        if st.session_state.cikktorzs.empty:
            st.write("Nincs törölhető termék.")
        else:
            termek_torlesre = st.selectbox("Válassz törlendő terméket", st.session_state.cikktorzs["Cikkszám"] + " - " + st.session_state.cikktorzs["Megnevezés"])
            pin_torles = st.text_input("Admin jelszó a törléshez", type="password", key="pin_torles")
            
            if st.button("Termék Végleges Törlése"):
                if pin_torles == ADMIN_PIN:
                    kivalasztott_cikk = termek_torlesre.split(" - ")[0]
                    st.session_state.cikktorzs = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] != kivalasztott_cikk]
                    st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] != kivalasztott_cikk]
                    st.success(f"✅ Termék ({kivalasztott_cikk}) sikeresen törölve a törzsből és a raktárból!")
                    st.rerun()
                else:
                    st.error("❌ Helytelen Admin jelszó!")

    with col2:
        st.subheader("🔥 Teljes Rendszer Törlés (Nullázás)")
        st.warning("⚠️ EZ A MŰVELET MINDEN ADATOT VÉGLEG TÖRÖL (0 termék, 0 készlet, 0 napló)!")
        pin_reset = st.text_input("Admin jelszó a nullázáshoz", type="password", key="pin_reset")
        
        if st.button("Minden Adat Végleges Törlése"):
            if pin_reset == ADMIN_PIN:
                st.session_state.cikktorzs = pd.DataFrame(columns=["Cikkszám", "Megnevezés", "Vonalkód", "Biztonsági készlet", "Rendelésköteles készlet"])
                st.session_state.sarzs_keszlet = pd.DataFrame(columns=["SarzsID", "Cikkszám", "Megnevezés", "Mennyiség", "Tárhely", "Beérkezés", "Lejárat", "Beszerzési Ár"])
                st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Tárhely", "Stratégia", "Beszerzési Ár", "Felhasználó"])
                st.success("✅ A raktár adatbázisa teljesen ki lett ürítve!")
                st.rerun()
            else:
                st.error("❌ Helytelen Admin jelszó!")
