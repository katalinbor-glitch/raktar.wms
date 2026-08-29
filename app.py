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
             (cikkszam TEXT PRIMARY KEY, nev TEXT, tarhely TEXT, mennyiseg INTEGER, egyseg TEXT, egysegar REAL, bizt_keszlet INTEGER, rend_keszlet INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS naplo 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, datum TEXT, tipus TEXT, cikkszam TEXT, nev TEXT, mennyiseg INTEGER, egyseg TEXT, tarhely TEXT)''')
conn.commit()

# Adatbázis sémakorrekciók
try:
    c.execute("ALTER TABLE keszlet ADD COLUMN egyseg TEXT DEFAULT 'db'")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE keszlet ADD COLUMN egysegar REAL DEFAULT 0.0")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE keszlet ADD COLUMN bizt_keszlet INTEGER DEFAULT 20")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE keszlet ADD COLUMN rend_keszlet INTEGER DEFAULT 30")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE naplo ADD COLUMN egyseg TEXT DEFAULT 'db'")
    conn.commit()
except sqlite3.OperationalError:
    pass

# Előre definiált opciók
TARHELYEK = [
    "A-01-01", "A-01-02", "A-01-03",
    "A-02-01", "A-02-02", "A-02-03",
    "B-01-01", "B-01-02", "B-01-03",
    "B-02-01", "B-02-02", "B-02-03"
]

EGYSÉGEK = ["db", "kg", "liter", "karton", "m2", "pár", "csomag"]

st.set_page_config(page_title="Raktárkezelő Rendszer (WMS)", layout="wide")
st.title("🏭 Raktárkezelő Rendszer (WMS)")

tabs = st.tabs(["📥 Bevételezés", "📤 Kiadás", "📋 Pillanatnyi Készlet", "📜 Árumozgás Napló", "⚙️ Adminisztráció"])

# 1. BEVÉTELEZÉS
with tabs[0]:
    st.header("📥 Áru Bevételezése")
    with st.form("bevetel_form"):
        col1, col2 = st.columns(2)
        with col1:
            cikkszam = st.text_input("🏷️ Cikkszám (pl. CIKK-001)")
            nev = st.text_input("📦 Termék neve")
            egysegar = st.number_input("💵 Egységár (Ft)", min_value=0.0, step=100.0, value=1000.0)
            tarhely = st.selectbox("📍 Tárhely kiválasztása", TARHELYEK)
        with col2:
            mennyiseg = st.number_input("🔢 Mennyiség", min_value=1, step=1)
            egyseg = st.selectbox("📏 Mennyiségi egység", EGYSÉGEK)
            bizt_keszlet = st.number_input("🚨 Egyedi Biztonsági Készlet", min_value=0, value=20, step=1)
            rend_keszlet = st.number_input("⚠️ Egyedi Rendelésköteles Készlet", min_value=0, value=30, step=1)
        
        submit = st.form_submit_button("📥 Bevételezés rögzítése")
        
        if submit:
            if cikkszam and nev and tarhely:
                c.execute("SELECT SUM(mennyiseg) FROM keszlet WHERE tarhely = ?", (tarhely,))
                jelenlegi_tarhely_db = c.fetchone()[0] or 0
                if jelenlegi_tarhely_db + mennyiseg > 100:
                    st.warning(f"⚠️ Figyelem! A(z) {tarhely} tárhelyen a bevételezés után {jelenlegi_tarhely_db + mennyiseg} termék lesz (100 feletti kapacitás!).")

                c.execute("SELECT mennyiseg FROM keszlet WHERE cikkszam = ?", (cikkszam,))
                rekord = c.fetchone()
                if rekord:
                    új_mennyiség = rekord[0] + mennyiseg
                    c.execute("UPDATE keszlet SET mennyiseg = ?, egyseg = ?, tarhely = ?, egysegar = ?, bizt_keszlet = ?, rend_keszlet = ? WHERE cikkszam = ?", 
                              (új_mennyiség, egyseg, tarhely, egysegar, bizt_keszlet, rend_keszlet, cikkszam))
                else:
                    c.execute("INSERT INTO keszlet VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                              (cikkszam, nev, tarhely, mennyiseg, egyseg, egysegar, bizt_keszlet, rend_keszlet))
                
                most = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO naplo (datum, tipus, cikkszam, nev, mennyiseg, egyseg, tarhely) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (most, "BEVÉTEL", cikkszam, nev, mennyiseg, egyseg, tarhely))
                conn.commit()
                st.success(f"✅ Sikeres bevételezés: {nev} ({mennyiseg} {egyseg})")
                st.rerun()
            else:
                st.error("❌ Kérjük, töltsön ki minden mezőt!")

# 2. KIADÁS
with tabs[1]:
    st.header("📤 Áru Kiadása")
    c.execute("SELECT cikkszam, nev, mennyiseg, egyseg FROM keszlet WHERE mennyiseg > 0")
    elrheto_cikkek = c.fetchall()
    
    if elrheto_cikkek:
        cikk_opciok = {f"{r[0]} - {r[1]} (Készlet: {r[2]} {r[3]})": r[0] for r in elrheto_cikkek}
        kivalasztott = st.selectbox("📦 Válassz terméket a kiadáshoz:", list(cikk_opciok.keys()))
        kivalasztott_cikkszam = cikk_opciok[kivalasztott]
        
        kiadas_mennyiseg = st.number_input("🔢 Kiadandó mennyiség", min_value=1, step=1)
        
        if st.button("📤 Kiadás rögzítése"):
            c.execute("SELECT mennyiseg, nev, egyseg, tarhely, bizt_keszlet, rend_keszlet FROM keszlet WHERE cikkszam = ?", (kivalasztott_cikkszam,))
            k_rekord = c.fetchone()
            jelnlegi = k_rekord[0]
            nev = k_rekord[1]
            egyseg = k_rekord[2]
            tarhely = k_rekord[3]
            bizt = k_rekord[4] or 20
            rend = k_rekord[5] or 30
            
            if kiadas_mennyiseg > jelnlegi:
                st.error("❌ Nincs elegendő készlet a raktárban!")
            else:
                új_mennyiség = jelnlegi - kiadas_mennyiseg
                c.execute("UPDATE keszlet SET mennyiseg = ? WHERE cikkszam = ?", (új_mennyiség, kivalasztott_cikkszam))
                
                most = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO naplo (datum, tipus, cikkszam, nev, mennyiseg, egyseg, tarhely) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (most, "KIADÁS", kivalasztott_cikkszam, nev, kiadas_mennyiseg, egyseg, tarhely))
                conn.commit()
                
                st.success(f"✅ Sikeres kiadás: {nev} ({kiadas_mennyiseg} {egyseg})")
                
                # Figyelmeztetések az egyedi készletszintekről
                if új_mennyiség <= bizt:
                    st.error(f"🚨 KRITIKUS KÉSZLET: A(z) {nev} elérte vagy átlépte az egyedi biztonsági készlet szintjét ({bizt} {egyseg})! Jelenlegi: {új_mennyiség} {egyseg}.")
                elif új_mennyiség <= rend:
                    st.warning(f"⚠️ RENDELÉS SZÜKSÉGES: A(z) {nev} elérte az egyedi rendelésköteles készlet szintjét ({rend} {egyseg})! Jelenlegi: {új_mennyiség} {egyseg}.")
                
                st.rerun()
    else:
        st.info("ℹ️ Jelenleg nincs kiadható készlet a raktárban.")

# 3. PILLANATNYI KÉSZLET
with tabs[2]:
    st.header("📋 Pillanatnyi Készlet")
    
    kereses = st.text_input("🔍 Keresés (Cikkszám, Név vagy Tárhely alapján):")
    
    query = """
    SELECT 
        cikkszam AS Cikkszám, 
        nev AS Név, 
        tarhely AS Tárhely, 
        mennyiseg AS Mennyiség, 
        egyseg AS Egység, 
        egysegar AS 'Egységár (Ft)',
        bizt_keszlet AS 'Biztonsági Készlet',
        rend_keszlet AS 'Rendelésköteles Készlet'
    FROM keszlet
    """
    df_keszlet = pd.read_sql_query(query, conn)
    
    if not df_keszlet.empty:
        df_keszlet['Egységár (Ft)'] = df_keszlet['Egységár (Ft)'].fillna(0)
        df_keszlet['Mennyiség'] = df_keszlet['Mennyiség'].fillna(0)
        df_keszlet['Összérték (Ft)'] = df_keszlet['Mennyiség'] * df_keszlet['Egységár (Ft)']
        
        # Logisztikai státusz kiszámítása az egyedi értékek alapján
        def keszlet_statusz(sor):
            m = sor['Mennyiség']
            b = sor['Biztonsági Készlet'] if pd.notnull(sor['Biztonsági Készlet']) else 20
            r = sor['Rendelésköteles Készlet'] if pd.notnull(sor['Rendelésköteles Készlet']) else 30
            
            if m <= b:
                return '🚨 Biztonsági szint alatt!'
            elif m <= r:
                return '⚠️ Újrarendelendő!'
            else:
                return '✅ Optimális'
        
        df_keszlet['Készlet Státusz'] = df_keszlet.apply(keszlet_statusz, axis=1)
        
        if kereses:
            df_keszlet = df_keszlet[
                df_keszlet['Cikkszám'].astype(str).str.contains(kereses, case=False, na=False) |
                df_keszlet['Név'].astype(str).str.contains(kereses, case=False, na=False) |
                df_keszlet['Tárhely'].astype(str).str.contains(kereses, case=False, na=False)
            ]
        
        st.dataframe(df_keszlet, use_container_width=True)
        
        teljes_ertek = float(df_keszlet['Összérték (Ft)'].sum())
        ertek_formazott = f"{teljes_ertek:,.0f}".replace(",", " ")
        st.metric(label="💰 Teljes Raktárkészlet Értéke", value=f"{ertek_formazott} Ft")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_keszlet.to_excel(writer, index=False, sheet_name='Keszlet')
        st.download_button(
            label="📊 Készlet letöltése Excel fájlként",
            data=buffer.getvalue(),
            file_name="raktar_keszlet.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.info("ℹ️ A raktár jelenleg üres.")

# 4. ÁRUMOZGÁS NAPLÓ
with tabs[3]:
    st.header("📜 Árumozgás Napló")
    df_naplo = pd.read_sql_query("SELECT datum AS Dátum, tipus AS Típus, cikkszam AS Cikkszám, nev AS Név, mennyiseg AS Mennyiség, egyseg AS Egység, tarhely AS Tárhely FROM naplo ORDER BY id DESC", conn)
    
    if not df_naplo.empty:
        st.dataframe(df_naplo, use_container_width=True)
        
        buffer_naplo = io.BytesIO()
        with pd.ExcelWriter(buffer_naplo, engine='openpyxl') as writer:
            df_naplo.to_excel(writer, index=False, sheet_name='Naplo')
        st.download_button(
            label="📑 Napló letöltése Excel fájlként",
            data=buffer_naplo.getvalue(),
            file_name="raktar_naplo.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.info("ℹ️ Még nem történt árumozgás a rendszerben.")

# 5. ADMINISZTRÁCIÓ
with tabs[4]:
    st.header("⚙️ Adminisztráció & Rendszerkarbantartás")
    
    st.subheader("🗑️ Egyes cikkek törlése a készletből")
    c.execute("SELECT cikkszam, nev FROM keszlet")
    minden_cikk = c.fetchall()
    if minden_cikk:
        torlendo = st.selectbox("Válaszd ki a törlendő cikket:", [f"{r[0]} - {r[1]}" for r in minden_cikk])
        if st.button("❌ Cikk törlése"):
            torlendo_cikkszam = torlendo.split(" - ")[0]
            c.execute("DELETE FROM keszlet WHERE cikkszam = ?", (torlendo_cikkszam,))
            conn.commit()
            st.success(f"✅ A(z) {torlendo_cikkszam} cikkszámú termék törölve lett!")
            st.rerun()
    else:
        st.info("ℹ️ Nincs törölhető cikk a raktárban.")

    st.markdown("---")
    st.subheader("🚨 Teljes adatbázis törlése (Reset)")
    st.warning("⚠️ Figyelem! Az adatbázis törlése nem vonható vissza.")
    jelszo = st.text_input("🔑 Adminisztrátori jelszó a törléshez:", type="password")
    if st.button("🗑️ Adatbázis alaphelyzetbe állítása (Reset)"):
        if jelszo == "tanar123":
            c.execute("DELETE FROM keszlet")
            c.execute("DELETE FROM naplo")
            conn.commit()
            st.success("✅ Az adatbázis sikeresen kiürítve!")
            st.rerun()
        else:
            st.error("❌ Hibás jelszó!")
