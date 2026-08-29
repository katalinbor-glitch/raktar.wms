import streamlit as st
import pandas as pd
import sqlite3
import datetime
import io

# Adatbázis kapcsolat
conn = sqlite3.connect('raktar.db', check_same_thread=False)
c = conn.cursor()

# Táblák létrehozása
c.execute('''CREATE TABLE IF NOT EXISTS keszlet 
             (cikkszam TEXT PRIMARY KEY, nev TEXT, tarhely TEXT, mennyiseg INTEGER, egysegar REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS naplo 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, datum TEXT, tipus TEXT, cikkszam TEXT, nev TEXT, mennyiseg INTEGER, tarhely TEXT)''')
conn.commit()

st.set_page_config(page_title="Raktárkezelő Rendszer (WMS)", layout="wide")
st.title("📦 Raktárkezelő Rendszer (WMS)")

tabs = st.tabs(["📥 Bevételezés", "📤 Kiadás", "📋 Pillanatnyi Készlet", "📜 Árumozgás Napló", "⚙️ Adminisztráció"])

# 1. BEVÉTELEZÉS
with tabs[0]:
    st.header("Áru Bevételezése")
    with st.form("bevetel_form"):
        col1, col2 = st.columns(2)
        with col1:
            cikkszam = st.text_input("Cikkszám (pl. CIKK-001)")
            nev = st.text_input("Termék neve")
            egysegar = st.number_input("Egységár (Ft)", min_value=0.0, step=100.0, value=1000.0)
        with col2:
            tarhely = st.text_input("Tárhely (pl. A-01-01)")
            mennyiseg = st.number_input("Mennyiség (db)", min_value=1, step=1)
        
        submit = st.form_submit_button("Bevételezés rögzítése")
        
        if submit:
            if cikkszam and nev and tarhely:
                # Tárhely kapacitás ellenőrzés
                c.execute("SELECT SUM(mennyiseg) FROM keszlet WHERE tarhely = ?", (tarhely,))
                jelenlegi_tarhely_db = c.fetchone()[0] or 0
                if jelenlegi_tarhely_db + mennyiseg > 100:
                    st.warning(f"⚠️ Figyelem! A(z) {tarhely} tárhelyen a bevételezés után {jelenlegi_tarhely_db + mennyiseg} db termék lesz (100 feletti kapacitás!).")

                c.execute("SELECT mennyiseg FROM keszlet WHERE cikkszam = ?", (cikkszam,))
                rekord = c.fetchone()
                if rekord:
                    új_mennyiség = rekord[0] + mennyiseg
                    c.execute("UPDATE keszlet SET mennyiseg = ?, tarhely = ?, egysegar = ? WHERE cikkszam = ?", 
                              (új_mennyiség, tarhely, egysegar, cikkszam))
                else:
                    c.execute("INSERT INTO keszlet VALUES (?, ?, ?, ?, ?)", 
                              (cikkszam, nev, tarhely, mennyiseg, egysegar))
                
                most = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO naplo (datum, tipus, cikkszam, nev, mennyiseg, tarhely) VALUES (?, ?, ?, ?, ?, ?)",
                          (most, "BEVÉTEL", cikkszam, nev, mennyiseg, tarhely))
                conn.commit()
                st.success(f"Sikeres bevételezés: {nev} ({mennyiseg} db)")
            else:
                st.error("Kérjük, töltsön ki minden mezőt!")

# 2. KIADÁS
with tabs[1]:
    st.header("Áru Kiadása")
    c.execute("SELECT cikkszam, nev, mennyiseg FROM keszlet WHERE mennyiseg > 0")
    elrheto_cikkek = c.fetchall()
    
    if elrheto_cikkek:
        cikk_opciok = {f"{r[0]} - {r[1]} (Készlet: {r[2]} db)": r[0] for r in elrheto_cikkek}
        kivalasztott = st.selectbox("Válassz terméket", list(cikk_opciok.keys()))
        kivalasztott_cikkszam = cikk_opciok[kivalasztott]
        
        kiadas_mennyiseg = st.number_input("Kiadandó mennyiség (db)", min_value=1, step=1)
        
        if st.button("Kiadás rögzítése"):
            c.execute("SELECT mennyiseg, nev, tarhely FROM keszlet WHERE cikkszam = ?", (kivalasztott_cikkszam,))
            k_rekord = c.fetchone()
            jelnlegi = k_rekord[0]
            nev = k_rekord[1]
            tarhely = k_rekord[2]
            
            if kiadas_mennyiseg > jelnlegi:
                st.error("Nincs elegendő készlet!")
            else:
                új_mennyiség = jelnlegi - kiadas_mennyiseg
                c.execute("UPDATE keszlet SET mennyiseg = ? WHERE cikkszam = ?", (új_mennyiség, kivalasztott_cikkszam))
                
                most = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO naplo (datum, tipus, cikkszam, nev, mennyiseg, tarhely) VALUES (?, ?, ?, ?, ?, ?)",
                          (most, "KIADÁS", kivalasztott_cikkszam, nev, kiadas_mennyiseg, tarhely))
                conn.commit()
                st.success(f"Sikeres kiadás: {nev} ({kiadas_mennyiseg} db)")
                st.rerun()
    else:
        st.info("Jelenleg nincs kiadható készlet a raktárban.")

# 3. PILLANATNYI KÉSZLET
with tabs[2]:
    st.header("Pillanatnyi Készlet")
    
    kereses = st.text_input("🔍 Keresés (Cikkszám, Név vagy Tárhely alapján):")
    
    query = "SELECT cikkszam AS Cikkszám, nev AS Név, tarhely AS Tárhely, mennyiseg AS Mennyiség, egysegar AS 'Egységár (Ft)' FROM keszlet"
    df_keszlet = pd.read_sql_query(query, conn)
    
    if not df_keszlet.empty:
        df_keszlet['Összérték (Ft)'] = df_keszlet['Mennyiség'] * df_keszlet['Egységár (Ft)']
        
        if kereses:
            df_keszlet = df_keszlet[
                df_keszlet['Cikkszám'].str.contains(kereses, case=False, na=False) |
                df_keszlet['Név'].str.contains(kereses, case=False, na=False) |
                df_keszlet['Tárhely'].str.contains(kereses, case=False, na=False)
            ]
        
        st.dataframe(df_keszlet, use_container_width=True)
        
        teljes_ertek = df_keszlet['Összérték (Ft)'].sum()
        st.metric(label="💰 Teljes Raktárkészlet Értéke", value=f"{teljes_ertek:,.0f} Ft".replace(",", " "))
        
        # Excel letöltés
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_keszlet.to_excel(writer, index=False, sheet_name='Keszlet')
        st.download_button(
            label="📊 Készlet letöltése Excelben",
            data=buffer.getvalue(),
            file_name="raktar_keszlet.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.write("A raktár jelenleg üres.")

# 4. ÁRUMOZGÁS NAPLÓ
with tabs[3]:
    st.header("Árumozgás Napló")
    df_naplo = pd.read_sql_query("SELECT datum AS Dátum, tipus AS Típus, cikkszam AS Cikkszám, nev AS Név, mennyiseg AS Mennyiség, tarhely AS Tárhely FROM naplo ORDER BY id DESC", conn)
    
    if not df_naplo.empty:
        st.dataframe(df_naplo, use_container_width=True)
        
        buffer_naplo = io.BytesIO()
        with pd.ExcelWriter(buffer_naplo, engine='openpyxl') as writer:
            df_naplo.to_excel(writer, index=False, sheet_name='Naplo')
        st.download_button(
            label="📜 Napló letöltése Excelben",
            data=buffer_naplo.getvalue(),
            file_name="raktar_naplo.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.write("Még nem történt árumozgás.")

# 5. ADMINISZTRÁCIÓ
with tabs[4]:
    st.header("⚙️ Adminisztráció & Rendszerkarbantartás")
    st.warning("Figyelem! Az adatbázis törlése nem vonható vissza.")
    
    jelszo = st.text_input("Adminisztrátori jelszó a törléshez:", type="password")
    if st.button("🗑️ Adatbázis alaphelyzetbe állítása (Reset)"):
        if jelszo == "tanar123":
            c.execute("DELETE FROM keszlet")
            c.execute("DELETE FROM naplo")
            conn.commit()
            st.success("Az adatbázis sikeresen kiürítve!")
            st.rerun()
        else:
            st.error("Hibás jelszó!")
