# Empirical Modeling of Seattle 911 Emergency Calls via Homogeneous Poisson Process

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Domain: Stochastic Modeling](https://img.shields.io/badge/Domain-Stochastic%20Modeling-purple.svg)]()
[![Data: Seattle Open Data](https://img.shields.io/badge/Data-Seattle%20Open%20Data-informational.svg)](https://data.seattle.gov/)

Repositori komputasi dan analisis data empiris untuk pemodelan Proses Poisson Homogen $\{N(t), t \ge 0\}$ pada aliran panggilan darurat Seattle Fire Department (SFD), Washington, Amerika Serikat. 

Proyek ini mengimplementasikan pemodelan stokastik empiris dan pipeline pengujian hipotesis untuk menganalisis dinamika antrean layanan darurat perkotaan menggunakan data publik riil.

---

## 1. Ringkasan eksekutif

Analisis ini memodelkan kedatangan panggilan darurat di Seattle selama 24 jam (23 Oktober 2026) menggunakan Proses Poisson Homogen dengan laju konstan $\lambda > 0$. Data bersumber dari City of Seattle Open Data Portal (API Socrata: `kzjm-xkqj`) dengan volume $N(24) = 314$ panggilan riil.

### Parameter dan hasil komputasi

* **Estimasi parameter MLE**:
  $$\hat{\lambda}_{\text{MLE}} = \frac{N(T)}{T} = \frac{314}{24} \approx 13{,}0833 \text{ panggilan/jam} \quad (\hat{\lambda}_{\text{menit}} \approx 0{,}2181 \text{ panggilan/menit})$$
* **Waktu antar-kedatangan empiris vs teoretis**:
  $$\bar{T} = 4{,}5911 \text{ menit} \quad \text{vs} \quad \mathbb{E}[T_n] = \frac{1}{\hat{\lambda}_{\text{menit}}} = 4{,}5860 \text{ menit} \quad (\Delta < 0{,}11\%)$$
* **Uji overdispersi skala 24 jam**:
  $$D = \frac{s^2}{\bar{X}} = 2{,}9438, \quad \chi^2 = 67{,}7070 \quad (\text{df} = 23, \; p = 2{,}73 \times 10^{-6})$$
  Nilai $p < 0{,}05$ menunjukkan data 24 jam tidak homogen secara global akibat fluktuasi siklus diurnal aktivitas warga.
* **Homogenitas lokal (jendela stasioner)**:
  Pada sub-interval dini hari (01.00-06.00), diperoleh $D = 0{,}30$ dengan $p = 0{,}8781 > 0{,}05$. Asumsi Poisson homogen berlaku baik pada jendela waktu ini.
* **Penipisan (thinning) dan superposisi**:
  Pemisahan jenis panggilan menghasilkan dua sub-proses independen:
  - Sub-aliran medis ($p = 66{,}56\%$, $\hat{\lambda}_{\text{medis}} = 8{,}7083$ panggilan/jam)
  - Sub-aliran non-medis ($1-p = 33{,}44\%$, $\hat{\lambda}_{\text{non-medis}} = 4{,}3750$ panggilan/jam)
  - Superposisi: $\hat{\lambda}_{\text{medis}} + \hat{\lambda}_{\text{non-medis}} = 13{,}0833 = \hat{\lambda}_{\text{total}}$.

---

## 2. Struktur repositori

```text
.
├── data/
│   ├── raw/
│   │   ├── seattle_fire_911_calls_20261023.csv   # Data mentah 314 panggilan API Socrata
│   │   └── seattle_fire_911_calls_20261023.json  # Data mentah format JSON
│   └── processed/
│       ├── kedatangan_per_jam.csv                # Agregasi panggilan per jam
│       ├── ringkasan_analisis_poisson.json       # Ringkasan estimasi parameter
│       └── hasil_studi_kasus_lengkap.json        # Hasil olahan data lengkap
├── figures/
│   ├── fluktuasi_laju_per_jam.png                # Pola diurnal laju kedatangan per jam
│   ├── distribusi_waktu_antar_kedatangan.png     # Histogram vs kurva Eksponensial teoretis
│   ├── grafik_lintasan_proses.png                # Realisasi lintasan N(t) vs garis ekspektasi
│   ├── distribusi_waktu_tunggu_gamma.png         # Realisasi waktu tunggu W_n vs kurva Erlang
│   └── simulasi_poisson_homogen.png              # Simulasi lintasan proses dan waktu antar-kedatangan
├── notebooks/
│   └── 01_eksplorasi_dan_simulasi.ipynb          # Notebook eksplorasi dan simulasi
├── scripts/
│   ├── analisis_studi_kasus.py                   # Skrip analisis data empiris
│   └── verify_calculations.py                    # Modul verifikasi rumus Poisson
├── requirements.txt                              # Daftar dependensi Python
├── LICENSE                                       # Lisensi MIT
└── README.md                                     # Dokumentasi repositori
```

---

## 3. Landasan teori matematika

1. **Aksioma kenaikan infinitesimal**:
   $$\mathbb{P}(N(h) = 1) = \lambda h + o(h), \quad \mathbb{P}(N(h) \ge 2) = o(h) \quad \text{saat } h \to 0.$$
2. **Dualitas waktu tunggu dan penghitungan**:
   $$\{W_n \le t\} \iff \{N(t) \ge n\}, \quad W_n \sim \text{Gamma}(n, \lambda) \quad (\text{Erlang-}n).$$
3. **Waktu antar-kedatangan**:
   $$T_n = W_n - W_{n-1} \overset{\text{i.i.d.}}{\sim} \text{Eksp}(\lambda), \quad f_{T_n}(t) = \lambda e^{-\lambda t}.$$
4. **Sifat seragam waktu kedatangan bersyarat**:
   Jika $N(t) = n$, waktu kejadian $\{W_1, W_2, \dots, W_n\}$ memiliki distribusi bersama yang setara dengan statistik tatanan dari $n$ variabel acak independen berdistribusi $\text{Uniform}(0, t)$.

---

## 4. Cara menjalankan

### Prasyarat
Python 3.10 atau versi yang lebih baru.

### 1. Kloning repositori
```bash
git clone https://github.com/ramadhan-imanur/seattle-911-poisson-process.git
cd seattle-911-poisson-process
```

### 2. Pasang dependensi
Gunakan lingkungan virtual:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Jalankan analisis data
Jalankan skrip untuk memproses dataset, menghitung uji statistik, dan menghasilkan grafik:
```bash
python scripts/analisis_studi_kasus.py
```

### 4. Jalankan verifikasi rumus
Jalankan modul verifikasi perhitungan analitis:
```bash
python scripts/verify_calculations.py
```

### 5. Jalankan notebook
```bash
jupyter notebook notebooks/01_eksplorasi_dan_simulasi.ipynb
```

---

## 5. Ringkasan hasil uji statistik

| Parameter / Uji statistik | Nilai teoretis | Nilai empiris | Keterangan |
| :--- | :--- | :--- | :--- |
| **Laju intensitas ($\hat{\lambda}_{\text{jam}}$)** | Parameter MLE | $13{,}0833 \text{ jam}^{-1}$ | Rata-rata 24 jam |
| **Rata-rata IAT ($\bar{T}$)** | $1/\hat{\lambda} = 4{,}5860 \text{ menit}$ | $4{,}5911 \text{ menit}$ | Selisih teoretis $< 0{,}11\%$ |
| **Indeks dispersi global ($D_{24h}$)** | $D = 1$ (Equidispersi) | $D = 2{,}9438$ ($p < 10^{-5}$) | Overdispersi akibat siklus diurnal |
| **Indeks dispersi dini hari** | $D = 1$ (Stasioner) | $D = 0{,}3000$ ($p = 0{,}8781$) | Homogenitas lokal diterima ($p > 0{,}05$) |
| **Proporsi medis ($p$)** | Parameter thinning | $66{,}56\%$ | $\hat{\lambda}_{\text{medis}} = 8{,}7083 \text{ jam}^{-1}$ |
| **Proporsi non-medis ($1-p$)** | Parameter thinning | $33{,}44\%$ | $\hat{\lambda}_{\text{non}} = 4{,}3750 \text{ jam}^{-1}$ |
| **Kejadian simultan ($T_i = 0$)** | $o(h) \implies 0$ kejadian | 38 pasangan ($12{,}14\%$) | Pembulatan data pada satuan menit |

---

## 6. Referensi

1. Taylor, H. M., & Karlin, S. (1998). *An Introduction to Stochastic Modeling* (3rd ed.). Academic Press.
   - Bab V: *The Poisson Process* (§5.1, §5.2, §5.3, §5.5).
2. Tijms, H. C. (2003). *A First Course in Stochastic Models*. John Wiley & Sons.
   - Bab 1: *The Poisson Process and Renewal Theory* (§1.1, §1.2, §1.3).
3. City of Seattle Open Data Portal. *Seattle Real-Time Fire 911 Calls*. Socrata API Resource `kzjm-xkqj`. Tanggal akses: 23 Oktober 2026.

---

## 7. Penulis

* [Ramadhan Imanur Rochim](https://github.com/ramadhan-imanur)
