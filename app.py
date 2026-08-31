# MODUL 4: KOMISSIÓZÁS (ÁLLANDÓ KISZEDÉSI UTASÍTÁSSAL & NYOMTATÁSSAL)
elif menu == "📤 Áru Kiadás (FIFO, LIFO, FEFO, HIFO, LOFO)":
    st.header("📤 Áru Kiadás & Kiszedési Utasítás Generálás")
    termek_opciok = {f"{row['Cikkszám']} - {row['Megnevezés']}": row['Cikkszám'] for _, row in st.session_state.cikktorzs.iterrows()}
    kivalasztott_cikkszam = termek_opciok[st.selectbox("Kiadandó Termék Kiválasztása", list(termek_opciok.keys()))]
    
    strategia = st.radio("Alkalmazandó Stratégia:", [
        "FIFO (First In, First Out)", 
        "LIFO (Last In, First Out)", 
        "FEFO (First Expired, First Out)", 
        "HIFO (Highest In, First Out)", 
        "LOFO (Lowest In, First Out)"
    ])
    
    with st.form("general_kiadas_form"):
        mennyiseg = st.number_input("Kiadandó mennyiség (db)", min_value=1, value=2)
        kezelo = st.text_input("Komissiózó neve", value="Komissiózó 01")
        submitted = st.form_submit_button("🛒 Kiszedési Utasítás Generálása")
        
        if submitted:
            elerheto = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Cikkszám"] == kivalasztott_cikkszam].copy()
            elerheto["Szabad"] = elerheto["Mennyiség"] - elerheto["Zárolt_Mennyiség"]
            
            if mennyiseg > elerheto["Szabad"].sum():
                st.error(f"🚫 Nincs elég szabad készlet! Elérhető: {elerheto['Szabad'].sum()} db")
            else:
                if "FIFO" in strategia: elerheto = elerheto.sort_values(by="Beérkezés", ascending=True)
                elif "LIFO" in strategia: elerheto = elerheto.sort_values(by="Beérkezés", ascending=False)
                elif "FEFO" in strategia: elerheto = elerheto.sort_values(by="Lejárat", ascending=True)
                elif "HIFO" in strategia: elerheto = elerheto.sort_values(by="Beszerzési Ár", ascending=False)
                elif "LOFO" in strategia: elerheto = elerheto.sort_values(by="Beszerzési Ár", ascending=True)
                
                maradek = mennyiseg
                lista = []
                for idx, row in elerheto.iterrows():
                    if maradek <= 0: break
                    levon = min(row["Szabad"], maradek)
                    st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == row["SarzsID"], "Mennyiség"] -= levon
                    maradek -= levon
                    
                    lista.append({
                        "Tárhely": row["Tárhely"], 
                        "SarzsID": row["SarzsID"], 
                        "Kiszedendő (db)": levon,
                        "Beérkezés": row["Beérkezés"],
                        "Lejárat": row["Lejárat"],
                        "Beszerzési Ár (Ft)": row["Beszerzési Ár"]
                    })
                    
                    st.session_state.naplo = pd.concat([st.session_state.naplo, pd.DataFrame([{
                        "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Művelet": "KIADÁS", "Cikkszám": kivalasztott_cikkszam,
                        "Megnevezés": row["Megnevezés"], "Mennyiség": levon, "SarzsID": row["SarzsID"],
                        "Tárhely": row["Tárhely"], "Stratégia/Megjegyzés": strategia.split(" ")[0], 
                        "Beszerzési Ár": row["Beszerzési Ár"], "Felhasználó": kezelo
                    }])], ignore_index=True)
                
                st.session_state.sarzs_keszlet = st.session_state.sarzs_keszlet[st.session_state.sarzs_keszlet["Mennyiség"] > 0]
                
                # MENTÉS A SESSION STATE-BE
                st.session_state.aktiv_kiszedes = {
                    "Cikkszám": kivalasztott_cikkszam,
                    "Megnevezés": elerheto.iloc[0]["Megnevezés"],
                    "Össz_Kiadott": mennyiseg,
                    "Stratégia": strategia,
                    "Kezelő": kezelo,
                    "Dátum": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tételek": lista
                }
                st.success("✅ Kiszedési Utasítás rögzítve!")
                st.rerun()

    # ÁLLANDÓ KISZEDÉSI UTASÍTÁSSAL & NYOMTATÁSSAL
    if st.session_state.aktiv_kiszedes is not None:
        st.divider()
        st.subheader("📋 AKTÍV KISZEDÉSI UTASÍTÁS (PICK LIST)")
        
        info = st.session_state.aktiv_kiszedes
        df_kiszedes = pd.DataFrame(info["Tételek"])

        # HTML/CSS ALAPÚ NYOMTATHATÓ CÍMKE / JEGYZÉK
        html_tabla = "".join([f"<tr><td style='border:1px solid #000; padding:8px;'><b>{t['Tárhely']}</b></td><td style='border:1px solid #000; padding:8px;'>{t['SarzsID']}</td><td style='border:1px solid #000; padding:8px; font-size:16px;'><b>{t['Kiszedendő (db)']} db</b></td><td style='border:1px solid #000; padding:8px;'>{t['Lejárat']}</td></tr>" for t in info["Tételek"]])
        
        nyomtatasi_html = f"""
        <div id="print-area" style="background:#fff; color:#000; padding:20px; border:2px solid #000; font-family:Arial, sans-serif;">
            <h2 style="margin-top:0;">📦 WMS KISZEDÉSI UTASÍTÁS</h2>
            <hr style="border:1px solid #000;">
            <p><b>Dátum:</b> {info['Dátum']} | <b>Komissiózó:</b> {info['Kezelő']}</p>
            <p><b>Termék:</b> {info['Megnevezés']} (<code>{info['Cikkszám']}</code>)</p>
            <p><b>Kiadandó Mennyiség:</b> <span style="font-size:18px; font-weight:bold;">{info['Össz_Kiadott']} db</span> | <b>Elv:</b> {info['Stratégia']}</p>
            <br>
            <table style="width:100%; border-collapse:collapse; text-align:left;">
                <thead>
                    <tr style="background-color:#eee;">
                        <th style="border:1px solid #000; padding:8px;">Tárhely</th>
                        <th style="border:1px solid #000; padding:8px;">Sarzs ID</th>
                        <th style="border:1px solid #000; padding:8px;">Kiszedendő</th>
                        <th style="border:1px solid #000; padding:8px;">Lejárat</th>
                    </tr>
                </thead>
                <tbody>
                    {html_tabla}
                </tbody>
            </table>
        </div>
        """
        
        st.markdown(nyomtatasi_html, unsafe_allow_html=True)
        st.write("")

        col_print, col_close, _ = st.columns([2, 2, 4])
        
        with col_print:
            # JavaScript alapú közvetlen böngésző nyomtatás
            st.components.v1.html("""
                <button onclick="window.print()" style="background-color:#008CBA; color:white; padding:10px 20px; border:none; border-radius:5px; font-size:16px; cursor:pointer; width:100%;">
                    🖨️ UTASÍTÁS NYOMTATÁSA / PDF
                </button>
            """, height=50)

        with col_close:
            if st.button("✅ Kiszedés Elvégezve (Munkalap Lezárása)", use_container_width=True):
                st.session_state.aktiv_kiszedes = None
                st.success("Kiszedési utasítás lezárva!")
                st.rerun()
