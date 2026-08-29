import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="WMS Raktárirányító Rendszer", layout="wide")

# 1. INICIALIZÁLÁS (Készlet és Biztonsági limitszintek)
if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Vonalkód": "5901234567891", "Biztonsági készlet": 12},
        {"Cikkszám": "ART-002", "Megnevezés": "Egér Logitech MX Master", "Vonalkód": "5901234567892", "Biztonsági készlet": 10},
        {"Cikkszám": "ART-003", "Megnevezés": "Monitor HP 27 inch", "Vonalkód": "5901234567893", "Biztonsági készlet": 5}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 10, "Tárhely": "A-01-01", "Beérkezés": "2026-01-10", "Lejárat": "2028-01-10", "Beszerzési Ár": 240000},
        {"SarzsID": "S-102", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 5, "Tárhely": "C-03-02", "Beérkezés": "2026-02-01", "Lejárat": "2028-02-01", "Beszerzési Ár": 260000},
        {"SarzsID": "S-201", "Cikkszám": "ART-002", "Megnevezés": "Egér Logitech MX Master", "Mennyiség": 40, "Tárhely": "A-01-02", "Beérkezés": "2026-01-15", "Lejárat": "2027-06-30", "Beszerzési Ár": 32000},
        {"SarzsID": "S-301", "Cikkszám": "ART-003", "Megnevezés": "Monitor HP 27 inch", "Mennyiség": 8, "Tárhely": "B-02-01", "Beérkezés": "2026-01-20", "Lejárat": "2029-01-01", "Beszerzési Ár": 85000}
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
    "📜 Árumozgás Napló", 
    "⚙️ Adminisztráció / Reset"
])

# 1. PILLANATNYI KÉSZLET & JELZŐRENDSZER
if menu == "📋 Pillanatnyi Készlet & Rendszint":
    st.header("📋 Pillanatnyi Készlet & Újrarendelési Jelzések")
    
    keszlet_összegzo = st.session_state.sarzs_keszlet.groupby("Cikkszám")["Mennyiség"].sum().reset_index()
    df_merged = pd.merge(st.session_state.cikktorzs, keszlet_összegzo, on="Cikkszám", how="left").fillna(0)
    
    # Készlet státusz meghatározása logic
    def kartya_statusz(row):
        if row["Mennyiség"] <= row["Biztonsági készlet"]:
            return "⚠️ UTÁNARENDELÉS SZÜKSÉGES"
        elif row["Mennyiség"] <= row["Biztonsági készlet"] * 1.5:
            return "⚡ OPTIMÁLIS / KÖZELÍT A MINIMUMHOZ"
        else:
            return "✅ OPTIMÁLIS KÉSZLET"

    df_merged["Készlet Státusz"] = df_merged.apply(kartya_statusz, axis=1)
    
    # Figyelmeztető riasztások megjelenítése alacsony készlet esetén
    rendelendo = df_merged[df_merged["Mennyiség"] <= df_merged["Biztonsági készlet"]]
    if not rendelendo.empty:
        st.error(f"🚨 **FIGYELEM! {len(rendelendo)} termék elérte a biztonsági készletszintet! Rendelés szükséges.**")
        for _, row in rendelendo.iterrows():
            szukseges = row['Biztonsági készlet'] * 2 - row['Mennyiség']
            st.warning(f"👉 **{row['Megnevezés']}** ({row['Cikkszám']}): Jelenleg **{int(row['Mennyiség'])} db** van raktáron (Biztonsági limit: **{row['Biztonsági készlet']} db**). Javasolt rendelés: **{int(szukseges)} db**")
    else:
        st.success("✅ Minden termékből optimális a készletszint!")

    st.subheader("Összesített Készlet és Rendszint Státusz")
    st.dataframe(df_merged, use_container_width=True)
    
    st.subheader("Részletes Sarzs és Tárhely Nyilvántartás")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)

# 2. BEVÉTELEZÉS
elif menu == "📥 Bevételezés":
    st.header("📥 Áru Bevételezés")
    
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

# 3. KIADÁS (AZONNALI AUTOMATIKUS RIASZTÁSSAL)
elif menu == "📤 Kiadás (Stratégia & Tárhely)":
    st.header("📤 Áru Kiadás")
    
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
                
                # Kiadás utáni azonnali rendszint ellenőrzés
                friss_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam]["Mennyiség"].sum()
                bizt_keszlet = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == kivalasztott_cikkszam]["Biztonsági készlet"].values[0]
                
                if friss_keszlet <= bizt_keszlet:
                    st.error(f"🚨 **RENDELÉSI RIASZTÁS!** A(z) {kivalasztott_termek_label} készlete kiadás után **{int(friss_keszlet)} db**-ra csökkent, ami eléri a biztonsági szintet ({bizt_keszlet} db)! **Újrarendelés szükséges!**")

# 4. ÚJ TERMÉK RÖGZÍTÉSE
elif menu == "➕ Új Termék Rögzítése":
    st.header("➕ Új Termék Hozzáadása a Törzsbe")
    with st.form("uj_termek_form"):
        col1, col2 = st.columns(2)
        with col1:
            uj_cikkszam = st.text_input("Cikkszám (pl. ART-004)", value="ART-004")
            uj_nev = st.text_input("Megnevezés", value="Billentyűzet")
            uj_vonalkod = st.text_input("Vonalkód (EAN)", value="5901234567894")
        with col2:
            uj_biztonsagi = st.number_input("Biztonsági készlet (db)", min_value=0, value=5)

        submitted_uj = st.form_submit_button("Új Termék Mentése")
        if submitted_uj:
            if uj_cikkszam in st.session_state.cikktorzs["Cikkszám"].values:
                st.error("⚠️ Ez a cikkszám már létezik!")
            else:
                uj_sor = {"Cikkszám": uj_cikkszam, "Megnevezés": uj_nev, "Vonalkód": uj_vonalkod, "Biztonsági készlet": uj_biztonsagi}
                st.session_state.cikktorzs = pd.concat([st.session_state.cikktorzs, pd.DataFrame([uj_sor])], ignore_index=True)
                st.success(f"✅ Termék mentve: {uj_nev}")

# 5. NAPLÓ
elif menu == "📜 Árumozgás Napló":
    st.header("📜 Árumozgási Előzmények")
    st.dataframe(st.session_state.naplo, use_container_width=True)
    csv = st.session_state.naplo.to_csv(index=False).encode('utf-8')
    st.download_button("Napló Letöltése (CSV)", csv, "wms_naplo.csv", "text/csv")

# 6. ADMIN / RESET
elif menu == "⚙️ Adminisztráció / Reset":
    st.header("⚙️ Munkamenet Visszaállítása")
    if st.button("Alaphelyzetbe állítás (Reset)"):
        del st.session_state.cikktorzs
        del st.session_state.sarzs_keszlet
        del st.session_state.naplo
        st.rerun()
