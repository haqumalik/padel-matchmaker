import streamlit as st
import pandas as pd
import random

st.title("🎾 Padel Enjoy")

# --- 1. STATE MANAGER (Memori Aplikasi) ---
if "game_state" not in st.session_state:
    st.session_state.game_state = "PENDAFTARAN"  # Status: PENDAFTARAN, BERJALAN, SELESAI
if "pemain_db" not in st.session_state:
    st.session_state.pemain_db = {}
if "ronde_ke" not in st.session_state:
    st.session_state.ronde_ke = 1
if "ronde_aktif" not in st.session_state:
    st.session_state.ronde_aktif = None
if "maks_game_per_orang" not in st.session_state:
    st.session_state.maks_game_per_orang = 5  # Default jika ber-6, tiap orang main 5 kali

# --- FUNGSIONAL: GENERATOR RONDE OTOMATIS ---
def buat_ronde_otomatis():
    daftar_pemain = list(st.session_state.pemain_db.keys())
    
    # 1. Filter siapa yang belum mencapai batas maksimal bermain
    belum_puas = [p for p in daftar_pemain if st.session_state.pemain_db[p]["Total Main"] < st.session_state.maks_game_per_orang]
    
    # Jika kurang dari 4 orang yang tersisa, turnamen selesai
    if len(belum_puas) < 4:
        st.session_state.game_state = "SELESAI"
        st.session_state.ronde_aktif = None
        return

    # 2. Cek aturan main maksimal 2x beruntun
    wajib_istirahat = [p for p in belum_puas if st.session_state.pemain_db[p]["Beruntun"] >= 2]
    tersedia = [p for p in belum_puas if p not in wajib_istirahat]
    
    # Jika gara-gara aturan beruntun sisa pemain kurang dari 4, reset paksa counter beruntunnya
    if len(tersedia) < 4:
        for p in daftar_pemain:
            if p in belum_puas:
                st.session_state.pemain_db[p]["Beruntun"] = 0
        tersedia = belum_puas.copy()
        
    # 3. KUNCI KEADILAN: Kelompokkan berdasarkan jumlah main
    # Kita acak dulu daftarnya agar pemain dengan jumlah main yang sama posisinya teracak
    random.shuffle(tersedia)
    # Baru kita urutkan stabil berdasarkan 'Total Main' terkecil
    # Python akan mempertahankan keacakan tadi, tapi menjamin yang jarang main berada di PALING DEPAN
    tersedia.sort(key=lambda p: st.session_state.pemain_db[p]["Total Main"])
    
    # 4. Ambil FIX 4 orang terdepan (yang paling berhak main)
    main_ronde = tersedia[:4]
    
    # Sisanya otomatis istirahat
    istirahat_ronde = [p for p in daftar_pemain if p not in main_ronde]
    
    # Acak posisi timnya agar pasangannya bervariasi
    random.shuffle(main_ronde)
    
    st.session_state.ronde_aktif = {
        "Tim A": [main_ronde[0], main_ronde[1]],
        "Tim B": [main_ronde[2], main_ronde[3]],
        "Istirahat": istirahat_ronde
    }

# --- STATUS 1: HALAMAN PENDAFTARAN ---
if st.session_state.game_state == "PENDAFTARAN":
    st.subheader("👥 Pendaftaran Pemain")
    nama_raw = st.text_area("Masukkan nama-nama pemain (Satu nama per baris / Tekan Enter):", 

    daftar_pemain = [nama.strip() for nama in nama_raw.split("\n") if nama.strip() != ""]
    jumlah_pemain = len(daftar_pemain)
    st.info(f"Jumlah pemain saat ini: {jumlah_pemain} orang (Minimal 5, Maksimal 10)")

    if jumlah_pemain < 5 or jumlah_pemain > 10:
        st.error("⚠️ Jumlah pemain wajib antara 5 sampai 10 orang!")
    else:
        if st.button("🚀 Kunci Pemain & Mulai Pertandingan"):
            st.session_state.pemain_db = {
                nama: {"Poin": 0, "Diff": 0, "Beruntun": 0, "Total Main": 0} for nama in daftar_pemain
            }
            # Set jatah main maksimal individu (Jumlah pemain - 1)
            st.session_state.maks_game_per_orang = jumlah_pemain - 1
            st.session_state.ronde_ke = 1
            st.session_state.game_state = "BERJALAN"
            buat_ronde_otomatis()
            st.rerun()

# --- STATUS 2: HALAMAN PERTANDINGAN BERJALAN ---
elif st.session_state.game_state == "BERJALAN":
    st.header(f"🎮 Pertandingan - Ronde {st.session_state.ronde_ke}")
    
    ronde = st.session_state.ronde_aktif
    if ronde:
        st.warning(f"☕ **Istirahat Ronde Ini:** {', '.join(ronde['Istirahat'])}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🟢 **Tim A:** {ronde['Tim A'][0]} & {ronde['Tim A'][1]}")
            skor_a = st.number_input("Skor Tim A", min_value=0, max_value=21, value=0, key=f"skor_a_{st.session_state.ronde_ke}")
        with col2:
            st.info(f"🔵 **Tim B:** {ronde['Tim B'][0]} & {ronde['Tim B'][1]}")
            skor_b = st.number_input("Skor Tim B", min_value=0, max_value=21, value=0, key=f"skor_b_{st.session_state.ronde_ke}")
            
        if st.button("💾 Simpan Skor & Lanjut Ronde Berikutnya"):
            if skor_a + skor_b != 21:
                st.error("⚠️ Total skor Padel Americano harus berjumlah 21 poin!")
            else:
                diff_a = skor_a - skor_b
                diff_b = skor_b - skor_a
                
                # Update Tim A
                for p in ronde['Tim A']:
                    st.session_state.pemain_db[p]["Poin"] += 1 if skor_a > skor_b else 0
                    st.session_state.pemain_db[p]["Diff"] += diff_a
                    st.session_state.pemain_db[p]["Beruntun"] += 1
                    st.session_state.pemain_db[p]["Total Main"] += 1
                    
                # Update Tim B
                for p in ronde['Tim B']:
                    st.session_state.pemain_db[p]["Poin"] += 1 if skor_b > skor_a else 0
                    st.session_state.pemain_db[p]["Diff"] += diff_b
                    st.session_state.pemain_db[p]["Beruntun"] += 1
                    st.session_state.pemain_db[p]["Total Main"] += 1
                    
                # Reset yang istirahat
                for p in ronde['Istirahat']:
                    st.session_state.pemain_db[p]["Beruntun"] = 0
                
                # Naikkan nomor ronde & buat pertandingan berikutnya otomatis
                st.session_state.ronde_ke += 1
                buat_ronde_otomatis()
                st.rerun()

    # Tampilkan Live Standings di bawahnya selama game berjalan
    st.subheader("📊 Live Standings (Klasemen Sementara)")
    data_tabel = []
    for nama, data in st.session_state.pemain_db.items():
        data_tabel.append({
            "Nama Pemain": nama,
            "Poin Menang": data["Poin"],
            "Point Difference (Diff)": data["Diff"],
            "Played": f"{data['Total Main']}/{st.session_state.maks_game_per_orang}"
        })
    df = pd.DataFrame(data_tabel)
    df = df.sort_values(by=["Poin Menang", "Point Difference (Diff)"], ascending=[False, False])
    df.insert(0, 'Rank', range(1, 1 + len(df)))
    st.dataframe(df.set_index('Rank'), use_container_width=True)

# --- STATUS 3: HALAMAN AKHIR (TURNAMEN SELESAI) ---
elif st.session_state.game_state == "SELESAI":
    st.balloons() # Efek balon perayaan seru!
    st.header("🏆 TURNAMEN SELESAI! 🏆")
    st.subheader("🥇 Hasil Akhir Klasemen (Final Standings)")
    
    data_tabel = []
    for nama, data in st.session_state.pemain_db.items():
        data_tabel.append({
            "Nama Pemain": nama,
            "Poin Menang": data["Poin"],
            "Point Difference (Diff)": data["Diff"],
            "Total Main": data["Total Main"]
        })
    df = pd.DataFrame(data_tabel)
    df = df.sort_values(by=["Poin Menang", "Point Difference (Diff)"], ascending=[False, False])
    df.insert(0, 'Rank', range(1, 1 + len(df)))
    
    # Menampilkan klasemen final dengan gaya yang bersih
    st.dataframe(df.set_index('Rank'), use_container_width=True)
    
    st.write("---")
    if st.button("🔄 Mulai Turnamen Baru (Reset Dari Awal)"):
        st.session_state.game_state = "PENDAFTARAN"
        st.session_state.pemain_db = {}
        st.session_state.ronde_aktif = None
        st.session_state.ronde_ke = 1
        st.rerun()
