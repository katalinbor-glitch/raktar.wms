if st.form_submit_button("Leltárkorrekció Mentése"):
    if korrekcio_pin == ADMIN_PIN:
        s_id = kivalasztott_sarzs_str.split(" - ")[0]
        
        # Régi mennyiség lekéréselected
        regi_db = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Mennyiség"].values[0]
        cikk = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Cikkszám"].values[0]
        nev = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Megnevezés"].values[0]
        tarhely = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Tárhely"].values[0]
        ar = st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Beszerzési Ár"].values[0]
        
        # Készlet frissítése
        st.session_state.sarzs_keszlet.loc[st.session_state.sarzs_keszlet["SarzsID"] == s_id, "Mennyiség"] = uj_tény_mennyiseg
        
        # Naplóbejegyzés a korrekcióról
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
