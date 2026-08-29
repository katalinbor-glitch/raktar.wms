import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="WMS Raktárirányító Rendszer", layout="wide")

# 1. INICIALIZÁLÁS (Készlet sarzsokkal/lejárattal/beérkezési árral)
if "cikktorzs" not in st.session_state:
    st.session_state.cikktorzs = pd.DataFrame([
        {"Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Vonalkód": "5901234567891", "Tárhely": "A-01-01", "Biztonsági készlet": 5},
        {"Cikkszám": "ART-002", "Megnevezés": "Egér Logitech MX Master", "Vonalkód": "5901234567892", "Tárhely": "A-01-02", "Biztonsági készlet": 10},
        {"Cikkszám": "ART-003", "Megnevezés": "Monitor HP 27 inch", "Vonalkód": "5901234567893", "Tárhely": "B-02-01", "Biztonsági készlet": 3}
    ])

if "sarzs_keszlet" not in st.session_state:
    st.session_state.sarzs_keszlet = pd.DataFrame([
        {"SarzsID": "S-101", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 10, "Beérkezés": "2026-01-10", "Lejárat": "2028-01-10", "Beszerzési Ár (Ft)": 240000, "Tárhely": "A-01-01"},
        {"SarzsID": "S-102", "Cikkszám": "ART-001", "Megnevezés": "Laptop Dell Latitude", "Mennyiség": 5, "Beérkezés": "2026-02-01", "Lejárat": "2028-02-01", "Beszerzési Ár (Ft)": 260000, "Tárhely": "A-01-01"},
        {"SarzsID": "S-201", "Cikkszám": "ART-002", "Megnevezés": "Egér Logitech MX Master", "Mennyiség": 40, "Beérkezés": "2026-01-15", "Lejárat": "2027-06-30", "Beszerzési Ár (Ft)": 32000, "Tárhely": "A-01-02"},
        {"SarzsID": "S-301", "Cikkszám": "ART-003", "Megnevezés": "Monitor HP 27 inch", "Mennyiség": 8, "Beérkezés": "2026-01-20", "Lejárat": "2029-01-01", "Beszerzési Ár (Ft)": 85000, "Tárhely": "B-02-01"}
    ])

if "naplo" not in st.session_state:
    st.session_state.naplo = pd.DataFrame(columns=["Dátum", "Művelet", "Cikkszám", "Megnevezés", "Mennyiség", "SarzsID", "Stratégia", "Beszerzési Ár (Ft)", "Felhasználó"])

# Cím és Tájékoztató
st.title("📦 WMS Raktárirányítási Rendszer (Összes Raktározási Stratégiával)")
st.info("ℹ️ **Oktatási modul:** Próbáld ki, hogyan választja ki a rendszer a kiadandó sarzsot a kiválasztott raktározási stratégia alapján!")

# Oldalsáv navigáció
menu = st.sidebar.radio("Navigáció / Modulok", [
    "📋 Pillanatnyi Készlet", 
    "📥 Bevételezés", 
    "📤 Kiadás (Készletstratégiák)", 
    "➕ Új Termék Rögzítése",
    "📜 Árumozgás Napló", 
    "⚙️ Adminisztráció / Reset"
])

# 1. PILLANATNYI KÉSZLET
if menu == "📋 Pillanatnyi Készlet":
    st.header("📋 Pillanatnyi Készlet (Sarzsok, Árak & Lejáratok)")
    
    keszlet_összegzo = st.session_state.sarzs_keszlet.groupby("Cikkszám")["Mennyiség"].sum().reset_index()
    df_merged = pd.merge(st.session_state.cikktorzs, keszlet_összegzo, on="Cikkszám", how="left").fillna(0)
    
    st.subheader("Termékek Összesített Készlete")
    st.dataframe(df_merged, use_container_width=True)
    
    st.subheader("Részletes Sarzs Nyilvántartás (Ár, Lejárat, Beérkezés)")
    st.dataframe(st.session_state.sarzs_keszlet, use_container_width=True)

# 2. BEVÉTELEZÉS
elif menu == "📥 Bevételezés":
    st.header("📥 Áru Bevételezés (Új Sarzs Rögzítése)")
    
    with st.form("bevételezés_form"):
        cikkszam = st.selectbox("Cikkszám kiválasztása", st.session_state.cikktorzs["Cikkszám"].tolist())
        mennyiseg = st.number_input("Bevételezendő mennyiség", min_value=1, value=5)
        beszerzesi_ar = st.number_input("Beszerzési Egységár (Ft)", min_value=0, value=50000)
        lejarat = st.date_input("Lejárati dátum", value=datetime.date(2027, 12, 31))
        diak_nev = st.text_input("Diák neve / Azonosítója", value="Diák")
        submitted = st.form_submit_button("Bevételezés Rögzítése")
        
        if submitted:
            termek_info = st.session_state.cikktorzs[st.session_state.cikktorzs["Cikkszám"] == cikkszam].iloc[0]
            új_sarzs_id = f"S-{len(st.session_state.sarzs_keszlet) + 101}"
            
            uj_sarzs = {
                "SarzsID": új_sarzs_id,
                "Cikkszám": cikkszam,
                "Megnevezés": termek_info["Megnevezés"],
                "Mennyiség": mennyiseg,
                "Beérkezés": datetime.date.today().strftime("%Y-%m-%d"),
                "Lejárat": lejarat.strftime("%Y-%m-%d"),
                "Beszerzési Ár (Ft)": beszerzesi_ar,
                "Tárhely": termek_info["Tárhely"]
            }
            st.session_state.sarzs_keszlet = pd.concat([st.session_state.sarzs_keszlet, pd.DataFrame([uj_sarzs])], ignore_index=True)
            
            uj_bejegyzes = {
                "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Művelet": "BEVÉTEL",
                "Cikkszám": cikkszam,
                "Megnevezés": termek_info["Megnevezés"],
                "Mennyiség": mennyiseg,
                "SarzsID": új_sarzs_id,
                "Stratégia": "-",
                "Beszerzési Ár (Ft)": beszerzesi_ar,
                "Felhasználó": diak_nev
            }
            st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([uj_bejegyzes])], ignore_index=True)
            st.success(f"Sikeres bevételezés! Sarzs azonosító: {új_sarzs_id}")

# 3. KIADÁS (ÖSSZES STRATÉGIA)
elif menu == "📤 Kiadás (Készletstratégiák)":
    st.header("📤 Áru Kiadás (Választható Stratégiák)")
    
    strategia = st.radio(
        "Kibocsátási Stratégia Kiválasztása:",
        [
            "FIFO (First-In, First-Out) - Legrégebben beérkezett áru kiadása",
            "LIFO (Last-In, First-Out) - Legutoljára beérkezett áru kiadása",
            "FEFO (First-Expired, First-Out) - Legkorábban lejáró áru kiadása",
            "HIFO (Highest-In, First-Out) - Legdrágábban vett áru kiadása",
            "LOFO (Lowest-In, First-Out) - Legolcsóbban vett áru kiadása"
        ]
    )
    
    with st.form("kiadas_form"):
        cikkszam = st.selectbox("Cikkszám kiválasztása", st.session_state.cikktorzs["Cikkszám"].tolist())
        mennyiseg = st.number_input("Kiadandó mennyiség", min_value=1, value=3)
        diak_nev = st.text_input("Diák neve / Azonosítója", value="Diák")
        submitted = st.form_submit_button("Kiadás Végrehajtása")
        
        if submitted:
            elerheto_sarzsok = st.session_state.sarzs_keszlet[
                (st.session_state.sarzs_keszlet["Cikkszám"] == cikkszam) & 
                (st.session_state.sarzs_keszlet["Mennyiség"] > 0)
            ].copy()
            
            osszes_keszlet = elerheto_sarzsok["Mennyiség"].sum()
            
            if mennyiseg > osszes_keszlet:
                st.error(f"Nincs elegendő készlet! Elérhető: {osszes_keszlet} db")
            else:
                # Rendezési logikák
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
                    elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beszerzési Ár (Ft)", ascending=False)
                    strat_nev = "HIFO"
                elif "LOFO" in strategia:
                    elerheto_sarzsok = elerheto_sarzsok.sort_values(by="Beszerzési Ár (Ft)", ascending=True)
                    strat_nev = "LOFO"
                
                maradek_igény = mennyiseg
                kiadott_sarzsok_info = []
                
                for idx, row in elerheto_sarzsok.iterrows():
                    if maradek_igény <= 0:
                        break
                    
                    levonando = min(row["Mennyiség"], maradek_igény)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levonando
                    maradek_igény -= levonando
                    
                    kiadott_sarzsok_info.append(f"{row['SarzsID']} ({levonando} db, {row['Beszerzési Ár (Ft)']} Ft)")
                    
                    uj_bejegyzes = {
                        "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Művelet": "KIADÁS",
                        "Cikkszám": cikkszam,
                        "Megnevezés": row["Megnevezés"],
                        "Mennyiség": levonando,
                        "SarzsID": row["SarzsID"],
                        "Stratégia": strat_nev,
                        "Beszerzési Ár (Ft)": row["Beszerzési Ár (Ft)"],
                        "Felhasználó": diak_nev
                    }
                    st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([uj_bejegyzes])], ignore_index=True)
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                
                st.success(f"✅ Kiadás sikeres ({strat_nev} szerint)! Érintett sarzsok: {', '.join(kiadott_sarzsok_info)}")

# 4. ÚJ TERMÉK RÖGZÍTÉSE
elif menu == "➕ Új Termék Rögzítése":
    st.header("➕ Új Termék Hozzáadása")
    with st.form("uj_termek_form"):
        col1, col2 = st.columns(2)
        with col1:
            uj_cikkszam = st.text_input("Cikkszám (pl. ART-004)", value="ART-004")
            uj_nev = st.text_input("Megnevezés", value="Billentyűzet")
            uj_vonalkod = st.text_input("Vonalkód (EAN)", value="5901234567894")
        with col2:
            uj_tarhely = st.text_input("Tárhely", value="B-01-02")
            uj_biztonsagi = st.number_input("Biztonsági készlet (db)", min_value=0, value=5)

        submitted_uj = st.form_submit_button("Új Termék Mentése")
        if submitted_uj:
            if uj_cikkszam in st.session_state.cikktorzs["Cikkszám"].values:
                st.error("⚠️ Ez a cikkszám már létezik!")
            else:
                uj_sor = {"Cikkszám": uj_cikkszam, "Megnevezés": uj_nev, "Vonalkód": uj_vonalkod, "Tárhely": uj_tarhely, "Biztonsági készlet": uj_biztonsagi}
                st.session_state.cikktorzs = pd.concat([st.session_state.cikktorzs, pd.DataFrame([uj_sor])], ignore_index=True)
                st.success(f"✅ Termék mentve: {uj_nev}")

# 5. NAPLÓ
elif menu == "📜 Árumozgás Napló":
    st.header("📜 Árumozgási Előzmények (Stratégiai Kimutatással)")
    st.dataframe(st.session_state.naplo, use_container_width=True)
    csv = st.session_state.naplo.to_csv(index=False).encode('utf-8')
    st.download_button("Napló Letöltése (CSV)", csv, "wms_naplo_osszes_strategia.csv", "text/csv")

# 6. ADMIN / RESET
elif menu == "⚙️ Adminisztráció / Reset":
    st.header("⚙️ Munkamenet Visszaállítása")
    if st.button("Alaphelyzetbe állítás (Reset)"):
        del st.session_state.cikktorzs
        del st.session_state.sarzs_keszlet
        del st.session_state.naplo
        st.rerun()
