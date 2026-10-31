# Empirical Modeling of Seattle 911 Emergency Calls via Homogeneous Poisson Process

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Mathematics: FMIPA UNS](https://img.shields.io/badge/Mathematics-FMIPA%20UNS-informational.svg)](https://mipa.uns.ac.id/)
[![Course: Stochastic Processes](https://img.shields.io/badge/Course-Stochastic%20Processes-purple.svg)](https://uns.ac.id/)

Repositori komputasi dan analisis data empiris untuk pemodelan **Proses Poisson Homogen** $\{N(t), t \ge 0\}$ pada aliran panggilan kegawatdaruratan publik riil yang diterima oleh *Seattle Fire Department* (SFD), Washington, Amerika Serikat. 

Proyek ini dikembangkan sebagai luaran komputasi dan studi kasus terapan pada mata kuliah **Pengantar Proses Stokastik**, Program Studi S1 Matematika, Fakultas Matematika dan Ilmu Pengetahuan Alam (FMIPA), Universitas Sebelas Maret (UNS).

---

## 1. Ringkasan Eksekutif (*Executive Summary*)

Model Proses Poisson Homogen dengan intensitas laju konstan $\lambda > 0$ diterapkan untuk menganalisis dinamika kedatangan panggilan darurat warga Seattle selama 24 jam penuh pada tanggal 23 Oktober 2026. Data sekunder diakses secara terverifikasi dari *City of Seattle Open Data Portal* melalui API Socrata (Dataset ID: `kzjm-xkqj`) dengan volume total $N(24) = 314$ panggilan riil.

### Parameter Kunci & Hasil Komputasi:
* **Estimasi Parameter MLE**:
  $$\hat{\lambda}_{\text{MLE}} = \frac{N(T)}{T} = \frac{314}{24} \approx 13{,}0833 \text{ panggilan/jam} \quad (\hat{\lambda}_{\text{menit}} \approx 0{,}2181 \text{ panggilan/menit})$$
* **Waktu Antar-Kedatangan Empiris vs Teoretis**:
  $$\bar{T} = 4{,}5911 \text{ menit} \quad \text{vs} \quad \mathbb{E}[T_n] = \frac{1}{\hat{\lambda}_{\text{menit}}} = 4{,}5860 \text{ menit} \quad (\Delta < 0{,}11\%)$$
* **Pengujian Overdispersi Skala Global 24 Jam**:
  $$D = \frac{s^2}{\bar{X}} = 2{,}9438, \quad \chi^2 = 67{,}7070 \quad (\text{df} = 23, \; p = 2{,}73 \times 10^{-6} < 0{,}05)$$
  *Menunjukkan penolakan homogenitas global 24 jam akibat osilasi siklus diurnal aktivitas manusia.*
* **Validitas Homogenitas Lokal (Jendela Stasioner)**:
  Pada sub-interval dini hari (01:00–06:00), diperoleh $D = 0{,}30$ dengan $p\text{-value} = 0{,}8781 > 0{,}05$, membuktikan bahwa asumsi Poisson homogen **dapat dipertahankan secara sangat baik** pada jendela operasional tertentu.
* **Operasi Penipisan (*Thinning*) & Superposisi**:
  Dekomposisi acak menghasilkan dua sub-proses Poisson independen:
  - Sub-aliran medis ($p = 66{,}56\%$, $\hat{\lambda}_{\text{medis}} = 8{,}7083$ panggilan/jam)
  - Sub-aliran non-medis ($1-p = 33{,}44\%$, $\hat{\lambda}_{\text{non-medis}} = 4{,}3750$ panggilan/jam)
  - Superposisi: $\hat{\lambda}_{\text{medis}} + \hat{\lambda}_{\text{non-medis}} = 13{,}0833 = \hat{\lambda}_{\text{total}}$ (terbukti aditif eksak).

---

## 2. Struktur Repositori

```text
.
├── data/
│   ├── raw/
│   │   ├── seattle_fire_911_calls_20261023.csv   # Data mentah 314 panggilan API Socrata
│   │   └── seattle_fire_911_calls_20261023.json  # Data mentah format JSON
│   └── processed/
│       ├── kedatangan_per_jam.csv                # Rekap agregasi panggilan per jam
│       ├── ringkasan_analisis_poisson.json       # Ringkasan ringkas parameter estimasi
│       └── hasil_studi_kasus_lengkap.json        # Basis data inferensi lengkap
├── figures/
│   ├── fluktuasi_laju_per_jam.png                # Pola diurnal laju kedatangan per jam
│   ├── distribusi_waktu_antar_kedatangan.png     # Histogram vs kurva Eksponensial teoretis
│   ├── grafik_lintasan_proses.png                # Realisasi lintasan tangga N(t) vs garis ekspektasi
│   └── distribusi_waktu_tunggu_gamma.png         # Realisasi waktu tunggu W_n vs kurva Erlang
├── notebooks/
│   └── 01_eksplorasi_dan_simulasi.ipynb          # Notebook eksplorasi interaktif & simulasi
├── scripts/
│   ├── analisis_studi_kasus.py                   # Modul komprehensif pengolahan data riil
│   └── verify_calculations.py                    # Modul verifikasi analitis rumus matematika
├── requirements.txt                              # Dependensi pustaka Python
├── LICENSE                                       # Lisensi MIT
└── README.md                                     # Dokumentasi repositori
```

---

## 3. Landasan Teori Matematika

1. **Aksioma Kenaikan Infinitesimal**:
   $$\mathbb{P}(N(h) = 1) = \lambda h + o(h), \quad \mathbb{P}(N(h) \ge 2) = o(h) \quad \text{saat } h \to 0.$$
2. **Dualitas Waktu Tunggu & Penghitungan**:
   $$\{W_n \le t\} \iff \{N(t) \ge n\}, \quad W_n \sim \text{Gamma}(n, \lambda) \quad (\text{Erlang-}n).$$
3. **Waktu Antar-Kedatangan Bebas Identik**:
   $$T_n = W_n - W_{n-1} \overset{\text{i.i.d.}}{\sim} \text{Eksp}(\lambda), \quad f_{T_n}(t) = \lambda e^{-\lambda t}.$$
4. **Sifat Uniform Waktu Kedatangan Bersyarat**:
   Diberikan $N(t) = n$, waktu kejadian $\{W_1, W_2, \dots, W_n\}$ memiliki distribusi gabungan yang setara dengan statistik tatanan dari $n$ variabel acak independen berdistribusi $\text{Uniform}(0, t)$.

---

## 4. Cara Menjalankan (*Installation & Usage*)

### Prasyarat
Pastikan sistem Anda telah terpasang **Python 3.10+**.

### 1. Kloning Repositori
```bash
git clone https://github.com/ramadhan-imanur/seattle-911-poisson-process.git
cd seattle-911-poisson-process
```

### 2. Pasang Dependensi
Disarankan menggunakan lingkungan virtual (*virtual environment*):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Eksekusi Analisis Studi Kasus
Jalankan skrip analitis utama untuk memproses dataset, menghitung seluruh uji statistik, dan membuat figur publikasi:
```bash
python scripts/analisis_studi_kasus.py
```

### 4. Eksekusi Verifikasi Rumus Analitis
Jalankan modul verifikasi simbolik dan komparasi numerik:
```bash
python scripts/verify_calculations.py
```

### 5. Eksplorasi Interaktif Jupyter Notebook
```bash
jupyter notebook notebooks/01_eksplorasi_dan_simulasi.ipynb
```

---

## 5. Ringkasan Hasil Uji Statistik

| Parameter / Uji Statistik | Nilai Teoretis / Hipotesis | Nilai Empiris Riil | Evaluasi / Kesimpulan |
| :--- | :--- | :--- | :--- |
| **Laju Intensitas ($\hat{\lambda}_{\text{jam}}$)** | Parameter MLE | $13{,}0833 \text{ jam}^{-1}$ | Laju rata-rata 24 jam |
| **Rata-rata IAT ($\bar{T}$)** | $1/\hat{\lambda} = 4{,}5860 \text{ mnt}$ | $4{,}5911 \text{ mnt}$ | Berimpit kuat ($\Delta < 0{,}11\%$) |
| **Indeks Dispersi Global ($D_{24h}$)** | $D = 1$ (Equidispersi) | $D = 2{,}9438$ ($p < 10^{-5}$) | Overdispersi akibat siklus diurnal |
| **Indeks Dispersi Dini Hari** | $D = 1$ (Stasioner) | $D = 0{,}3000$ ($p = 0{,}8781$) | Asumsi homogenitas terkonfirmasi |
| **Proporsi Medis ($p$)** | Thinning Parameter | $66{,}56\%$ | $\hat{\lambda}_{\text{medis}} = 8{,}7083 \text{ jam}^{-1}$ |
| **Proporsi Non-Medis ($1-p$)** | Thinning Parameter | $33{,}44\%$ | $\hat{\lambda}_{\text{non}} = 4{,}3750 \text{ jam}^{-1}$ |
| **Kejadian Simultan ($T_i = 0$)** | $o(h) \implies 0$ kejadian | 38 pasangan ($12{,}14\%$) | Pelanggaran keteraturan skala menit |

---

## 6. Referensi Buku Teks Wajib

1. **Taylor, H. M., & Karlin, S. (1998).** *An Introduction to Stochastic Modeling* (3rd ed.). Academic Press.
   - Bab V: *The Poisson Process* (§5.1, §5.2, §5.3, §5.5).
2. **Tijms, H. C. (2003).** *A First Course in Stochastic Models*. John Wiley & Sons.
   - Bab 1: *The Poisson Process and Renewal Theory* (§1.1, §1.2, §1.3).
3. **City of Seattle Open Data Portal.** *Seattle Real-Time Fire 911 Calls*. Socrata API Resource `kzjm-xkqj`. Tanggal Akses: 23 Oktober 2026.

---

## 7. Penulis & Informasi Akademik

* **Penulis / Analis Data**: [Ramadhan Imanur Rochim](https://github.com/ramadhan-imanur) (NIM. M0124015)
* **Program Studi**: S1 Matematika, Fakultas Matematika dan Ilmu Pengetahuan Alam (FMIPA)
* **Institusi**: Universitas Sebelas Maret (UNS), Surakarta, Indonesia
* **Mata Kuliah**: Pengantar Proses Stokastik
* **Dosen Pengampu**: Ade Susanti, S.Si., M.Si.
