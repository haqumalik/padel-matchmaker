import streamlit as st
import pandas as pd
import random
import json

st.title("🎾 Padel Enjoy")

# --- TRICK: BROWSER LOCAL STORAGE (ANTI LAYAR HP MATI) ---
# Menggunakan komponen bawaan streamlit html untuk menyimpan & memuat data otomatis dari memori HP
if "init_storage" not in st.session_state:
    st.session_state.init_storage = True

# --- 1. STATE MANAGER (Memori Aplikasi) ---
if "game_state" not in st.session_state:
    st.session_state.game_state = "PENDAFTARAN"
if "pemain_db" not in st.session_state:
    st.session_state.pemain_db = {}
if "ronde_ke" not in st.session_state:
    st.session_state.ronde_ke = 1
if "ronde_aktif" not in st.session_state:
    st.session_state.ronde_aktif = None
if "maks_game_per_orang" not in st.session_state:
    st.session_state.maks_game_per_orang = 5

# --- AMBIL DATA CADANGAN OTOMATIS (JIKA HP SEMPAT MATI) ---
# Kita gunakan st.sidebar untuk menaruh fitur backup agar rapi
st.sidebar.header("💾 Memori Turnamen")
if st.sidebar.button("📂 Pulihkan Data Terakhir (Jika HP Reset)"):
    if "backup_padel" in st.query_params:
        try:
            backup_data = json.loads(st.query_params["backup_padel"])
            st.session_state.game_state = backup_data["game_state"]
            st.session_state.pemain_db = backup_data["pemain_db"]
            st.session_state.ronde_ke = backup_data["ronde_ke"]
            st.session_state.ronde_aktif = backup_data["ronde_aktif"]
            st.session_state.maks_game_per_orang = backup_data["maks_game_per_orang"]
            st.sidebar.success("✅ Data berhasil dipulihkan!")
            st.rerun()
        except:
            st.sidebar.error("Gagal memulihkan data.")
    else:
        st.sidebar.warning("Tidak ada data cadangan di link ini.")

def simpan_cadangan():
    # Masukkan data ke URL Link agar jika ke-refresh tinggal klik pulihkan
    backup_dict = {
        "game_state": st.session_state.game_state,
        "pemain_db": st.session_state.pemain_db,
        "ronde_ke": st.session_state.ronde_ke,
        "ronde_aktif": st.session_state.ronde_aktif,
        "maks_game_per_orang": st.session_state.maks_game_per_orang
    }
    st.query_params["backup_padel"] = json.dumps(backup_dict)

# --- FUNGSIONAL: GENERATOR RONDE OTOMATIS ---
def buat_ronde_otomatis():
    daftar_pemain = list(st.session_state.pemain_db.keys())
    belum_puas = [p for p in daftar_pemain if st.session_state.pemain_db[p]["Total Main"] < st.session_state.maks_game_per_orang]
    
    if len(belum_puas) < 4:
        st.session_state.game_state = "SELESAI"
        st.session_state.ronde_aktif = None
        simpan_cadangan()
        return

    wajib_istirahat = [p for p in belum_puas if st.session_state.pemain_db[p]["Beruntun"] >= 2]
    tersedia = [p for p in belum_puas if p not in wajib_istirahat]
    
    if len(tersedia) < 4:
        for p in daftar_pemain:
            if p in belum_puas:
                st.session_state.pemain_db[p]["Beruntun"] = 0
        tersedia = belum_puas.copy()
        
    random.shuffle(tersedia)
    tersedia.sort(key=lambda p: st.session_state.pemain_db[p]["Total Main"])
    
    main_ronde = tersedia[:4]
    istirahat_ronde = [p for p in daftar_pemain if p not in main_ronde]
    random.shuffle(main_ronde)
    
    st.session_state.ronde_aktif = {
        "Tim A": [main_ronde[0], main_ronde[1]],
        "Tim B": [main_ronde[2], main_ronde[3]],
        "Istirahat": istirahat_ronde
    }
    simpan_cadangan()

# --- STATUS 1: HALAMAN PENDAFTARAN ---
if st.session_state.game_state == "PENDAFTARAN":
    st.subheader("👥 Pendaftaran Pemain")
    nama_raw = st.text_area("Masukkan nama-nama pemain (Satu nama per baris / Tekan Enter):")

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
            st.number_input("Skor Tim B", min_value=0, max_value=21, value=0, key=f"skor_b_{st.session_state.ronde_ke}")
            # Auto hitung pasangannya agar total wajib 21
            skor_b = 21 - skor_a
            st.write(f"Skor otomatis Tim B: **{skor_b}**")
            
        if st.button("💾 Simpan Skor & Lanjut Ronde Berikutnya"):
            diff_a = skor_a - skor_b
            diff_b = skor_b - skor_a
            
            for p in ronde['Tim A']:
                st.session_state.pemain_db[p]["Poin"] += 1 if skor_a > skor_b else 0
                st.session_state.pemain_db[p]["Diff"] += diff_a
                st.session_state.pemain_db[p]["Beruntun"] += 1
                st.session_state.pemain_db[p]["Total Main"] += 1
                
            for p in ronde['Tim B']:
                st.session_state.pemain_db[p]["Poin"] += 1 if skor_b > skor_a else 0
                st.session_state.pemain_db[p]["Diff"] += diff_b
                st.session_state.pemain_db[p]["Beruntun"] += 1
                st.session_state.pemain_db[p]["Total Main"] += 1
                
            for p in ronde['Istirahat']:
                st.session_state.pemain_db[p]["Beruntun"] = 0
            
            st.session_state.ronde_ke += 1
            buat_ronde_otomatis()
            st.rerun()

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
    st.balloons()
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
    st.dataframe(df.set_index('Rank'), use_container_width=True)
    
    st.write("---")
    if st.button("🔄 Mulai Turnamen Baru (Reset Dari Awal)"):
        st.session_state.game_state = "PENDAFTARAN"
        st.session_state.pemain_db = {}
        st.session_state.ronde_aktif = None
        st.session_state.ronde_ke = 1
        st.query_params.clear()
        st.rerun()
