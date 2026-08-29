import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="WMS Raktárrendszer", page_icon="📦", layout="wide"
)

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] button div {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    h1 { font-size: 36px !important; }
    h2, h3 { font-size: 26px !important; }
    </style>
""",
    unsafe_allow_html=True,
)


def init_db():
    conn = sqlite3.connect("raktar_web.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cikktorzs (
            cikkszam TEXT PRIMARY KEY,
            nev TEXT,
            vonalkod TEXT,
            egyseg TEXT,
            biztonsagi_keszlet INTEGER DEFAULT 0,
            rendelesi_korlat INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keszlet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cikkszam TEXT,
            tarhely TEXT,
            mennyiseg INTEGER
        )
    """)
    # ÚJ TÁBLA AZ ÁRUMOZGÁSOK NAPLÓZÁSÁHOZ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arumozgas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idopont TEXT,
            tipus TEXT,
            cikkszam TEXT,
            mennyiseg INTEGER,
            tarhely TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def get_connection():
    return sqlite3.connect("raktar_web.db")


st.title("📦 Oktatási Raktárirányító Rendszer (WMS)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Cikktörzs",
    "2. Bevételezés",
    "3. Kiadás / Komissió",
    "4. Pillanatnyi Készlet",
    "5. Árumozgás Napló",
])

TARHELYEK = ["A-01-01", "A-01-02", "B-01-01", "B-02-01", "HŰTŐ-01", "RACK-01"]
EGYSEGEK = ["db", "liter (l)", "karton (kt)", "kg", "m"]

# --- 1. CIKKTÖRZS ---
with tab1:
    st.header("Új termék rögzítése")
    with st.form("uj_cikk_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            cikk_szam = st.text_input("Cikkszám")
            cikk_nev = st.text_input("Megnevezés")
        with col2:
            cikk_ean = st.text_input("Vonalkód (EAN)")
            cikk_egyseg = st.selectbox("Mértékegység Törzs", EGYSEGEK)
        with col3:
            bizt_keszlet = st.number_input(
                "Biztonsági készlet (max 100)",
                min_value=0,
                max_value=100,
                value=5,
                step=1,
            )
            rend_korlat = st.number_input(
                "Rendelési küszöb (max 100)",
                min_value=0,
                max_value=100,
                value=10,
                step=1,
            )

        mentes_gomb = st.form_submit_button("Cikk Mentése", type="primary")

    if mentes_gomb:
        if cikk_szam and cikk_nev:
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO cikktorzs VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        cikk_szam,
                        cikk_nev,
                        cikk_ean,
                        cikk_egyseg,
                        int(bizt_keszlet),
                        int(rend_korlat),
                    ),
                )
                conn.commit()
                st.success(f"A(z) {cikk_nev} cikk sikeresen elmentve!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Ez a cikkszám már létezik!")
            finally:
                conn.close()
        else:
            st.warning("Cikkszám és Név megadása kötelező!")

    st.divider()
    st.header("Regisztrált Cikkek és Törlés")
    conn = get_connection()
    df_cikk = pd.read_sql_query("SELECT * FROM cikktorzs", conn)

    if not df_cikk.empty:
        st.dataframe(df_cikk, use_container_width=True)
        st.subheader("🗑️ Cikk Törlése")
        torlendo = st.selectbox(
            "Válassz törlendő cikket:", df_cikk["cikkszam"].tolist()
        )
        if st.button("Kijelölt Cikk Végleges Törlése"):
            conn.execute(
                "DELETE FROM cikktorzs WHERE cikkszam=?", (torlendo,)
            )
            conn.execute("DELETE FROM keszlet WHERE cikkszam=?", (torlendo,))
            conn.commit()
            st.success(f"A(z) {torlendo} cikkszámú termék törölve lett!")
            st.rerun()
    else:
        st.info("Még nincs rögzített cikk.")
    conn.close()

# --- 2. BEVÉTELEZÉS ---
with tab2:
    st.header("Áru Bevételezése Raktárba")
    conn = get_connection()
    cikkek = pd.read_sql_query("SELECT cikkszam, nev FROM cikktorzs", conn)
    conn.close()

    if not cikkek.empty:
        cikk_options = {
            f"{row['cikkszam']} | {row['nev']}": row["cikkszam"]
            for _, row in cikkek.iterrows()
        }
        valasztott_cikk = st.selectbox(
            "Válassz Cikket (Bevétel):", list(cikk_options.keys())
        )
        bev_tarhely = st.selectbox("Tárhely kiválasztása:", TARHELYEK)
        bev_menny = st.number_input(
            "Bevételezendő mennyiség (max 100)",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
        )

        if st.button("Bevételezés Rögzítése", type="primary"):
            cikksz = cikk_options[valasztott_cikk]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_connection()
            cursor = conn.cursor()

            # Készlet frissítése
            cursor.execute(
                "SELECT id, mennyiseg FROM keszlet WHERE cikkszam=? AND"
                " tarhely=?",
                (cikksz, bev_tarhely),
            )
            res = cursor.fetchone()
            if res:
                conn.execute(
                    "UPDATE keszlet SET mennyiseg=? WHERE id=?",
                    (res[1] + int(bev_menny), res[0]),
                )
            else:
                conn.execute(
                    "INSERT INTO keszlet (cikkszam, tarhely, mennyiseg) VALUES"
                    " (?, ?, ?)",
                    (cikksz, bev_tarhely, int(bev_menny)),
                )

            # Mozgás naplózása
            conn.execute(
                "INSERT INTO arumozgas (idopont, tipus, cikkszam, mennyiseg,"
                " tarhely) VALUES (?, ?, ?, ?, ?)",
                (now, "BEVÉTELEZÉS", cikksz, int(bev_menny), bev_tarhely),
            )

            conn.commit()
            conn.close()
            st.success(
                f"Sikeresen bevételezve {int(bev_menny)} egység a(z) {bev_tarhely} tárhelyre!"
            )
    else:
        st.warning(
            "Először rögzíts legalább egy cikket a Cikktörzs fülön!"
        )

# --- 3. KIADÁS ---
with tab3:
    st.header("Áru Kiadása / Komissiózás")
    conn = get_connection()
    cikkek = pd.read_sql_query("SELECT cikkszam, nev FROM cikktorzs", conn)
    conn.close()

    if not cikkek.empty:
        cikk_options = {
            f"{row['cikkszam']} | {row['nev']}": row["cikkszam"]
            for _, row in cikkek.iterrows()
        }
        valasztott_cikk_kia = st.selectbox(
            "Válassz Cikket (Kiadás):", list(cikk_options.keys())
        )
        kia_tarhely = st.selectbox("Tárhely (honnan?):", TARHELYEK)
        kia_menny = st.number_input(
            "Kiadandó mennyiség (max 100)",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
        )

        if st.button("Kiadás Rögzítése", type="primary"):
            cikksz = cikk_options[valasztott_cikk_kia]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, mennyiseg FROM keszlet WHERE cikkszam=? AND"
                " tarhely=?",
                (cikksz, kia_tarhely),
            )
            res = cursor.fetchone()

            if not res or res[1] < kia_menny:
                st.error("Nincs elegendő készlet ezen a tárhelyen!")
            else:
                new_qty = res[1] - int(kia_menny)
                if new_qty == 0:
                    conn.execute("DELETE FROM keszlet WHERE id=?", (res[0],))
                else:
                    conn.execute(
                        "UPDATE keszlet SET mennyiseg=? WHERE id=?",
                        (new_qty, res[0]),
                    )

                # Mozgás naplózása
                conn.execute(
                    "INSERT INTO arumozgas (idopont, tipus, cikkszam, mennyiseg,"
                    " tarhely) VALUES (?, ?, ?, ?, ?)",
                    (now, "KIADÁS", cikksz, int(kia_menny), kia_tarhely),
                )

                conn.commit()
                st.success(f"Sikeres kiadás: {int(kia_menny)} egység!")
            conn.close()

# --- 4. PILLANATNYI KÉSZLET ---
with tab4:
    st.header("Raktárkészlet és Szintjelzések")
    conn = get_connection()
    query = """
        SELECT k.cikkszam AS Cikkszám, c.nev AS Név, k.tarhely AS Tárhely, 
               CAST(k.mennyiseg AS INTEGER) AS Készlet, c.egyseg AS Egység, 
               CAST(c.biztonsagi_keszlet AS INTEGER) AS bizt_keszlet, 
               CAST(c.rendelesi_korlat AS INTEGER) AS rend_korlat
        FROM keszlet k
        JOIN cikktorzs c ON k.cikkszam = c.cikkszam
    """
    df_keszlet = pd.read_sql_query(query, conn)
    conn.close()

    if not df_keszlet.empty:

        def highlight_stock(row):
            if row["Készlet"] <= row["bizt_keszlet"]:
                return ["background-color: #ff9999; color: black;"] * len(row)
            elif row["Készlet"] <= row["rend_korlat"]:
                return ["background-color: #ffeb99; color: black;"] * len(row)
            return [""] * len(row)

        df_display = df_keszlet.drop(columns=["bizt_keszlet", "rend_korlat"])
        st.dataframe(
            df_keszlet.style.apply(highlight_stock, axis=1),
            use_container_width=True,
        )
        st.caption(
            "🔴 Piros: Biztonsági készlet alatt (Kritikus) | 🟡 Sárga: Újrarendelendő"
        )
    else:
        st.info("A raktár jelenleg üres.")

# --- 5. ÁRUMOZGÁS NAPLÓ ---
with tab5:
    st.header("📋 Árumozgások Előzményei (Napló)")
    conn = get_connection()
    query = """
        SELECT a.idopont AS 'Időpont', 
               a.tipus AS 'Művelet', 
               a.cikkszam AS 'Cikkszám', 
               c.nev AS 'Termék Neve', 
               a.mennyiseg AS 'Mennyiség', 
               c.egyseg AS 'Egység',
               a.tarhely AS 'Tárhely'
        FROM arumozgas a
        LEFT JOIN cikktorzs c ON a.cikkszam = c.cikkszam
        ORDER BY a.id DESC
    """
    df_naplo = pd.read_sql_query(query, conn)
    conn.close()

    if not df_naplo.empty:
        st.dataframe(df_naplo, use_container_width=True)
    else:
        st.info("Még nem történt árumozgás a rendszerben.")
