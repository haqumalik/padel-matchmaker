# 🎾 Padel Americano Pro Matchmaker & Standings

Halo Kawan! Selamat datang di proyek **Padel Americano Matchmaker**. Aplikasi berbasis web ini dibuat untuk mempermudah pengaturan pertandingan (matchmaking) dan perhitungan poin turnamen sosial Padel dengan format **Americano**. 

Aplikasi ini sudah di-deploy dan bisa diakses langsung via HP kamu!
👉 **[Klik di Sini untuk Membuka Aplikasi](https://padel-enjoy.streamlit.app/)**

---

## ✨ Fitur Utama

* **👥 Input Pemain Simpel:** Tinggal masukkan nama pemain satu per baris (tekan Enter). Mendukung pembatasan kuota 5 hingga 10 pemain.
* **🎲 Otomatis & Adil (Anti-Zonk):** Sistem akan mengacak tim dan lawan secara otomatis berdasarkan total bermain terkecil. Dijamin jatah main semua orang rata dan adil!
* **⚠️ Batasan 2x Beruntun:** Pemain tidak akan dipaksa bermain lebih dari 2 kali berturut-turut demi menjaga stamina tetap aman.
* **📊 Live Standings & Tie-Breaker:** Klasemen dihitung secara real-time berdasarkan poin menang. Jika poin sama (head-to-head), peringkat ditentukan berdasarkan selisih poin (*Point Difference*) dari skor total game 21.
* **🏆 Halaman Juara:** Begitu semua pemain memenuhi kuota bermain, sistem otomatis mengunci layar, menyalakan efek selebrasi, dan menampilkan klasemen akhir.

---

## 💻 Teknologi yang Digunakan

Proyek ini dibangun dengan sangat ringkas menggunakan:
* [Python](https://www.python.org/) - Bahasa pemrograman utama untuk logika algoritma.
* [Streamlit](https://streamlit.io/) - Framework ajaib untuk menyulap skrip Python menjadi aplikasi web estetik.
* [Pandas](https://pandas.pydata.org/) - Digunakan untuk memproses tabel dan pengurutan (*sorting*) klasemen secara akurat.

---

## 🚀 Cara Menjalankan Secara Lokal (Di Laptop)

Jika kamu ingin mencoba atau mengembangkan kode ini di laptop sendiri:

1. Clone repository ini atau download filenya.
2. Buka terminal di folder project, lalu instal Streamlit:
   ```bash
   pip install streamlit pandas
