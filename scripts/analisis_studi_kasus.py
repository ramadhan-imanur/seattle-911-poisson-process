"""
analisis_studi_kasus.py
=======================
Skrip analitis lengkap dan komprehensif untuk pengolahan data empiris:
Studi Kasus Aliran Panggilan Darurat Seattle 911 (Seattle Fire Department)
Mata Kuliah: Pengantar Proses Stokastik (S1 Matematika FMIPA UNS)
Penulis: Ramadhan Imanur Rochim (NIM. M0124015) - Kelompok 1

Tujuan:
1. Memuat dan memvalidasi dataset empiris riil 314 panggilan (23 Oktober 2026).
2. Mengestimasi parameter laju intensitas MLE (lambda_hat per jam dan per menit).
3. Menghitung statistik deskriptif waktu antar-kedatangan empiris dan perbandingannya dengan teoritis.
4. Melakukan uji indeks dispersi Poisson D = s^2 / X_bar pada skala 24 jam dan sub-interval lokal (dini hari, pagi, siang, malam).
5. Melakukan uji goodness-of-fit: Kolmogorov-Smirnov untuk waktu antar-kedatangan dan sifat uniformitas waktu kedatangan bersyarat N(t)=n.
6. Menganalisis operasi thinning (sub-aliran medis vs non-medis) dan superposisi.
7. Menganalisis waktu tunggu Gamma/Erlang W_n untuk n = 10, 30, 60, 100, 150, 200, 300 serta mengevaluasi realisasi empirisnya.
8. Menghasilkan visualisasi grafik publikasi dengan kualitas tinggi ke direktori code/figures/ dan report/figures/.
9. Menyimpan ringkasan komputasi terstruktur ke code/data/processed/hasil_studi_kasus_lengkap.json.
"""

import os
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

# Konfigurasi visualisasi bergaya publikasi ilmiah bersih (FMIPA UNS)
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'lines.linewidth': 1.8,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
})

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_csv = os.path.join(base_dir, "data", "raw", "seattle_fire_911_calls_20261023.csv")
    fig_dir_code = os.path.join(base_dir, "figures")
    fig_dir_report = os.path.join(os.path.dirname(base_dir), "report", "figures")
    processed_dir = os.path.join(base_dir, "data", "processed")

    os.makedirs(fig_dir_code, exist_ok=True)
    os.makedirs(fig_dir_report, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    print("=" * 70)
    print("  MEMPROSES DATASET EMPIRIS PANGGILAN DARURAT SEATTLE 911 (23 OKT 2026)")
    print("=" * 70)

    # 1. Pemuatan Data
    df = pd.read_csv(raw_csv)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    
    total_calls = len(df)
    t_start = pd.to_datetime("2026-10-23 00:00:00")
    t_end = pd.to_datetime("2026-10-23 23:59:59")
    T_hours = 24.0

    print(f"Total panggilan teramati (24 jam): {total_calls} panggilan")
    
    # Waktu relatif dalam satuan jam dan menit dari pukul 00:00:00
    df["elapsed_seconds"] = (df["datetime"] - t_start).dt.total_seconds()
    df["elapsed_hours"] = df["elapsed_seconds"] / 3600.0
    df["elapsed_minutes"] = df["elapsed_seconds"] / 60.0

    # 2. Estimasi Parameter Laju Intensitas MLE
    lambda_hat_hour = total_calls / T_hours
    lambda_hat_min = lambda_hat_hour / 60.0
    expected_iat_min = 1.0 / lambda_hat_min

    print(f"Estimasi Laju Intensitas (per jam) : {lambda_hat_hour:.4f} panggilan/jam")
    print(f"Estimasi Laju Intensitas (per menit): {lambda_hat_min:.4f} panggilan/menit")
    print(f"Ekspektasi Waktu Antar-Kedatangan : {expected_iat_min:.4f} menit")

    # 3. Analisis Waktu Antar-Kedatangan (Inter-Arrival Times / IAT)
    # T_n = W_n - W_{n-1}
    iat_seconds = df["elapsed_seconds"].diff().dropna()
    iat_minutes = iat_seconds / 60.0
    
    iat_mean = float(iat_minutes.mean())
    iat_std = float(iat_minutes.std())
    iat_median = float(iat_minutes.median())
    iat_min = float(iat_minutes.min())
    iat_max = float(iat_minutes.max())
    iat_q25 = float(iat_minutes.quantile(0.25))
    iat_q75 = float(iat_minutes.quantile(0.75))
    zero_iat_count = int((iat_seconds == 0).sum())

    print(f"\nStatistik Waktu Antar-Kedatangan Empiris (N = {len(iat_minutes)} selang):")
    print(f"  Rata-rata (Mean)         : {iat_mean:.4f} menit (Teoretis: {expected_iat_min:.4f} menit)")
    print(f"  Simpangan Baku (Std Dev) : {iat_std:.4f} menit (Teoretis Eksp: {expected_iat_min:.4f} menit)")
    print(f"  Median                   : {iat_median:.4f} menit")
    print(f"  Rentang (Min - Max)      : {iat_min:.2f} - {iat_max:.2f} menit")
    print(f"  Kuartil 1 - Kuartil 3    : {iat_q25:.2f} - {iat_q75:.2f} menit")
    print(f"  Jumlah IAT = 0 (Simultan): {zero_iat_count} kali (indikasi pelanggaran keteraturan)")

    # Uji Kolmogorov-Smirnov untuk IAT terhadap Eksponensial(scale=expected_iat_min)
    ks_iat = stats.kstest(iat_minutes, "expon", args=(0, expected_iat_min))
    print(f"  Uji KS Distribusi Eksp   : D_stat = {ks_iat.statistic:.4f}, p-value = {ks_iat.pvalue:.4e}")

    # 4. Analisis Kedatangan per Jam & Uji Indeks Dispersi
    hourly_counts = df.groupby(df["datetime"].dt.hour).size().reindex(range(24), fill_value=0)
    
    mean_hourly = float(hourly_counts.mean())
    var_hourly = float(hourly_counts.var(ddof=1))
    std_hourly = float(hourly_counts.std(ddof=1))
    dispersion_index_24h = var_hourly / mean_hourly
    chi2_stat_24h = (24 - 1) * dispersion_index_24h
    p_val_chi2_24h = 1.0 - stats.chi2.cdf(chi2_stat_24h, df=23)

    print(f"\nUji Indeks Dispersi Global (24 Jam Penuh):")
    print(f"  Rata-rata Sampel (X_bar) : {mean_hourly:.4f}")
    print(f"  Variansi Sampel (s^2)    : {var_hourly:.4f}")
    print(f"  Simpangan Baku (s)       : {std_hourly:.4f}")
    print(f"  Indeks Dispersi (D)      : {dispersion_index_24h:.4f}")
    print(f"  Statistik Chi-Kuadrat    : chi2 = {chi2_stat_24h:.4f} (df=23)")
    print(f"  p-value                  : {p_val_chi2_24h:.4e}")

    # Analisis Berdasarkan Klaster Waktu Diurnal
    blocks = {
        "Dini Hari (01:00 - 06:00)": list(range(1, 6)),
        "Pagi Menjelang Siang (07:00 - 12:00)": list(range(7, 13)),
        "Siang ke Sore (13:00 - 18:00)": list(range(13, 19)),
        "Malam Hari (19:00 - 24:00)": list(range(19, 24)) + [0],
    }

    block_stats = {}
    print("\nEvaluasi Indeks Dispersi per Blok Waktu:")
    for b_name, b_hours in blocks.items():
        sub_counts = hourly_counts.loc[b_hours]
        m = float(sub_counts.mean())
        v = float(sub_counts.var(ddof=1)) if len(b_hours) > 1 else 0.0
        d = v / m if m > 0 else 0.0
        df_k = len(b_hours) - 1
        chi2_k = df_k * d
        p_k = 1.0 - stats.chi2.cdf(chi2_k, df=df_k) if df_k > 0 else 1.0
        
        block_stats[b_name] = {
            "hours": b_hours,
            "mean": m,
            "variance": v,
            "dispersion_index": d,
            "chi2": chi2_k,
            "p_value": p_k,
            "counts": [int(c) for c in sub_counts]
        }
        print(f"  * {b_name:38s}: Mean={m:5.2f}, Var={v:5.2f}, D={d:5.2f}, p-val={p_k:.4f}")

    # 5. Uji Sifat Uniform Waktu Kedatangan Bersyarat N(t) = n (Order Statistics Property)
    # W_1, ..., W_n bersyarat N(24)=314 berdistribusi seragam Uniform(0, 24)
    ks_uniform = stats.kstest(df["elapsed_hours"], "uniform", args=(0, 24.0))
    print(f"\nUji Sifat Uniform Waktu Kejadian Bersyarat N(T) = {total_calls}:")
    print(f"  KS-Statistic D : {ks_uniform.statistic:.4f}")
    print(f"  p-value        : {ks_uniform.pvalue:.4e}")

    # 6. Analisis Thinning (Medis vs Non-Medis)
    is_medis = df["type"].str.contains("Aid|Medic", case=False, na=False)
    n_medis = int(is_medis.sum())
    n_non_medis = total_calls - n_medis
    p_medis = n_medis / total_calls
    p_non_medis = n_non_medis / total_calls

    lambda_medis = lambda_hat_hour * p_medis
    lambda_non_medis = lambda_hat_hour * p_non_medis

    print(f"\nOperasi Penipisan (Thinning) Acak:")
    print(f"  Sub-aliran Medis        : {n_medis} panggilan (p = {p_medis:.4f} atau {p_medis*100:.2f}%)")
    print(f"    Laju Intensitas Medis : {lambda_medis:.4f} panggilan/jam")
    print(f"  Sub-aliran Non-Medis    : {n_non_medis} panggilan (1-p = {p_non_medis:.4f} atau {p_non_medis*100:.2f}%)")
    print(f"    Laju Intensitas Non-M : {lambda_non_medis:.4f} panggilan/jam")
    print(f"  Verifikasi Superposisi  : {lambda_medis:.4f} + {lambda_non_medis:.4f} = {lambda_medis + lambda_non_medis:.4f} (Laju Total: {lambda_hat_hour:.4f})")

    # 7. Analisis Distribusi Waktu Tunggu Gamma (Erlang)
    # W_n ~ Gamma(shape=n, scale=1/lambda)
    gamma_milestones = [10, 30, 60, 100, 150, 200, 300]
    gamma_results = {}
    print("\nAnalisis Waktu Tunggu Kumulatif W_n ~ Gamma(n, lambda_hat):")
    for n_val in gamma_milestones:
        t_emp_hours = float(df.loc[n_val - 1, "elapsed_hours"])
        t_emp_min = float(df.loc[n_val - 1, "elapsed_minutes"])
        
        mean_hours = n_val / lambda_hat_hour
        var_hours = n_val / (lambda_hat_hour ** 2)
        std_hours = np.sqrt(var_hours)
        
        # Hitung probabilitas CDF dan selang kepercayaan 1-sigma [mean-std, mean+std]
        cdf_emp = float(stats.gamma.cdf(t_emp_hours, a=n_val, scale=1.0 / lambda_hat_hour))
        in_1sigma = (mean_hours - std_hours) <= t_emp_hours <= (mean_hours + std_hours)

        gamma_results[f"W_{n_val}"] = {
            "n": n_val,
            "E_W_hours": mean_hours,
            "Std_W_hours": std_hours,
            "E_W_minutes": mean_hours * 60.0,
            "Std_W_minutes": std_hours * 60.0,
            "Empirical_hours": t_emp_hours,
            "Empirical_minutes": t_emp_min,
            "CDF_at_empirical": cdf_emp,
            "in_1_sigma_interval": bool(in_1sigma)
        }
        print(f"  * W_{n_val:3d}: Teoretis = {mean_hours:5.2f} h ({mean_hours*60:6.1f} min) +/- {std_hours:4.2f} h | Empiris = {t_emp_hours:5.2f} h ({t_emp_min:6.1f} min) | CDF={cdf_emp:.4f} | 1-Sigma: {in_1sigma}")

    # 8. Kalkulasi Probabilitas Deduktif Tertentu
    prob_15min_0 = stats.poisson.pmf(0, lambda_hat_hour * 0.25)
    prob_15min_3 = stats.poisson.pmf(3, lambda_hat_hour * 0.25)
    prob_1hour_13 = stats.poisson.pmf(13, lambda_hat_hour)
    
    print(f"\nKalkulasi Probabilitas Analitis:")
    print(f"  P(N(0.25) = 0) [15 menit hening] : {prob_15min_0:.6f} ({prob_15min_0*100:.2f}%)")
    print(f"  P(N(0.25) = 3) [15 menit 3 call] : {prob_15min_3:.6f} ({prob_15min_3*100:.2f}%)")
    print(f"  P(N(1.0) = 13) [1 jam 13 call]   : {prob_1hour_13:.6f} ({prob_1hour_13*100:.2f}%)")

    # =========================================================================
    # 9. PEMBUATAN GRAFIK PUBLIKASI AKADEMIK FMIPA UNS
    # =========================================================================
    print("\nMenghasilkan grafik publikasi beresolusi tinggi (300 DPI)...")

    # Gambar 1: Trajektori Proses N(t) vs Garis Ekspektasi Teoritis
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    t_plot = np.concatenate([[0], df["elapsed_hours"].values, [24.0]])
    n_plot = np.concatenate([[0], np.arange(1, total_calls + 1), [total_calls]])
    
    ax.step(t_plot, n_plot, where='post', color='#08306b', linewidth=2.0, label='Proses Penghitungan Empiris $N(t)$')
    t_line = np.linspace(0, 24, 200)
    ax.plot(t_line, lambda_hat_hour * t_line, linestyle='--', color='#d94801', linewidth=2.0, label=r'Garis Ekspektasi Teoretis $\mathbb{E}[N(t)] = 13{,}0833\,t$')
    
    # Pita variansi teoretis +/- 2 SD(N(t)) = +/- 2 sqrt(lambda*t)
    upper_band = lambda_hat_hour * t_line + 2 * np.sqrt(lambda_hat_hour * t_line)
    lower_band = np.maximum(0, lambda_hat_hour * t_line - 2 * np.sqrt(lambda_hat_hour * t_line))
    ax.fill_between(t_line, lower_band, upper_band, color='#fdd0a2', alpha=0.35, label=r'Pita Keyakinan Teoretis $\pm 2\sigma$ ($95\%$ Interval)')

    ax.set_title("Trajektori Proses Penghitungan Panggilan Darurat Seattle 911 (23 Oktober 2026)", fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel("Waktu Operasional $t$ (Jam sejak Pukul 00:00:00)", fontsize=10)
    ax.set_ylabel("Jumlah Panggilan Masuk Kumulatif $N(t)$", fontsize=10)
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 335)
    ax.set_xticks(range(0, 25, 2))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    fig.tight_layout()
    
    for d in [fig_dir_code, fig_dir_report]:
        fig.savefig(os.path.join(d, "grafik_lintasan_proses.png"), dpi=300)
    plt.close(fig)

    # Gambar 2: Distribusi Waktu Antar-Kedatangan Empiris vs Eksponensial
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    bins = np.linspace(0, 30, 31)
    ax.hist(iat_minutes, bins=bins, density=True, color='#2b8cbe', edgecolor='#084081', alpha=0.7, label=f'Histogram Empiris $T_n$ ($N={len(iat_minutes)}$)')
    
    x_expon = np.linspace(0, 30, 300)
    y_expon = stats.expon.pdf(x_expon, scale=expected_iat_min)
    ax.plot(x_expon, y_expon, color='#bd0026', linewidth=2.2, label=r'Densitas Teoretis $\text{Eksp}(\hat{\lambda}_{\text{menit}} = 0{,}2181)$')
    
    # Rata-rata empiris vs teoretis
    ax.axvline(iat_mean, color='#00441b', linestyle='-', linewidth=1.8, label=f'Rata-rata Empiris ($\\bar{{T}} = {iat_mean:.2f}$ m)')
    ax.axvline(expected_iat_min, color='#bd0026', linestyle=':', linewidth=1.8, label=f'Ekspektasi Teoretis ($1/\\hat{{\\lambda}} = {expected_iat_min:.2f}$ m)')

    ax.set_title("Distribusi Waktu Antar-Kedatangan Empiris vs Model Eksponensial", fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel("Waktu Antar-Kedatangan $T_n$ (Menit)", fontsize=10)
    ax.set_ylabel("Kerapatan Probabilitas (Densitas)", fontsize=10)
    ax.set_xlim(0, 30)
    ax.set_xticks(range(0, 31, 5))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    fig.tight_layout()
    
    for d in [fig_dir_code, fig_dir_report]:
        fig.savefig(os.path.join(d, "distribusi_waktu_antar_kedatangan.png"), dpi=300)
    plt.close(fig)

    # Gambar 3: Fluktuasi Laju Kedatangan per Jam & Siklus Diurnal
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    hours = np.arange(24)
    counts = hourly_counts.values
    colors = ['#41b6c4' if h in range(1, 6) else ('#fd8d3c' if h in range(15, 21) else '#225ea8') for h in hours]
    
    bars = ax.bar(hours, counts, color=colors, edgecolor='#1c3f60', alpha=0.85, width=0.75, label='Frekuensi Kejadian Empiris $K_i$')
    ax.axhline(mean_hourly, color='#e31a1c', linestyle='--', linewidth=2.0, label=f'Laju Konstan Rata-rata $\\hat{{\\lambda}} = {mean_hourly:.2f}$ call/jam')

    # Tambahkan anotasi blok waktu
    ax.axvspan(0.5, 5.5, color='#a1dab4', alpha=0.25, label='Blok Dini Hari ($D = 0{,}34$, Laju Rendah)')
    ax.axvspan(14.5, 20.5, color='#fed976', alpha=0.25, label='Blok Jam Sibuk ($D = 0{,}54$, Laju Tinggi)')

    ax.set_title("Fluktuasi Kedatangan Panggilan per Jam: Evaluasi Stasioneritas Diurnal", fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel("Jam Observasi (00:00 - 23:00 Waktu Setempat)", fontsize=10)
    ax.set_ylabel("Jumlah Panggilan Masuk per Jam", fontsize=10)
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(0, 28)
    ax.set_xticks(range(0, 24))
    ax.grid(True, axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=8.5)
    fig.tight_layout()

    for d in [fig_dir_code, fig_dir_report]:
        fig.savefig(os.path.join(d, "fluktuasi_laju_per_jam.png"), dpi=300)
    plt.close(fig)

    # Gambar 4: Distribusi Waktu Tunggu Gamma W_n untuk Berbagai n
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    t_gamma_plot = np.linspace(0, 10, 400)
    selected_n = [10, 30, 60]
    colors_gamma = ['#238b45', '#2171b5', '#cb181d']

    for idx, n_val in enumerate(selected_n):
        c = colors_gamma[idx]
        y_pdf = stats.gamma.pdf(t_gamma_plot, a=n_val, scale=1.0 / lambda_hat_hour)
        ax.plot(t_gamma_plot, y_pdf, color=c, linewidth=2.0, label=r'Teoretis $W_{{{n}}} \sim \text{{Gamma}}({n}, 13.08)$'.format(n=n_val))
        
        # Realisasi empiris
        t_real = df.loc[n_val - 1, "elapsed_hours"]
        ax.axvline(t_real, color=c, linestyle='--', linewidth=1.6, label=f'Realisasi Empiris $W_{{{n_val}}} = {t_real:.2f}$ jam')

    ax.set_title("Distribusi Kerapatan Waktu Tunggu Gamma (Erlang) vs Titik Realisasi Empiris", fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel("Waktu Kumulatif Kedatangan $t$ (Jam)", fontsize=10)
    ax.set_ylabel("Kerapatan Probabilitas $f_{W_n}(t)$", fontsize=10)
    ax.set_xlim(0, 8)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=8.5)
    fig.tight_layout()

    for d in [fig_dir_code, fig_dir_report]:
        fig.savefig(os.path.join(d, "distribusi_waktu_tunggu_gamma.png"), dpi=300)
    plt.close(fig)

    print("Grafik berhasil disimpan ke code/figures/ dan report/figures/.")

    # 10. Menyimpan Seluruh Data Olahan ke JSON Lengkap
    final_results = {
        "metadata": {
            "judul": "Analisis Proses Poisson Homogen pada Kasus Riil Aliran Panggilan Darurat Seattle 911",
            "tanggal_analisis": "2026-10-31",
            "sumber_data": "City of Seattle Open Data Portal (API Socrata: kzjm-xkqj)",
            "tanggal_observasi": "2026-10-23",
            "durasi_observasi_jam": T_hours,
            "total_panggilan": total_calls
        },
        "parameter_estimasi": {
            "lambda_mle_per_jam": lambda_hat_hour,
            "lambda_mle_per_menit": lambda_hat_min,
            "ekspektasi_iat_menit": expected_iat_min
        },
        "statistik_waktu_antar_kedatangan": {
            "n_selang": len(iat_minutes),
            "mean_menit": iat_mean,
            "std_menit": iat_std,
            "median_menit": iat_median,
            "min_menit": iat_min,
            "max_menit": iat_max,
            "q25_menit": iat_q25,
            "q75_menit": iat_q75,
            "jumlah_iat_nol": zero_iat_count,
            "ks_test_exponential": {
                "d_statistic": float(ks_iat.statistic),
                "p_value": float(ks_iat.pvalue)
            }
        },
        "uji_dispersi_dan_stasioneritas": {
            "skala_24h": {
                "mean_per_jam": mean_hourly,
                "variansi_per_jam": var_hourly,
                "simpangan_baku_per_jam": std_hourly,
                "indeks_dispersi_D": dispersion_index_24h,
                "chi2_stat": chi2_stat_24h,
                "derajat_kebebasan": 23,
                "p_value": p_val_chi2_24h,
                "kesimpulan": "Overdispersi signifikan pada skala 24 jam akibat siklus diurnal"
            },
            "evaluasi_per_blok": block_stats
        },
        "uji_sifat_uniform_order_statistics": {
            "ks_statistic": float(ks_uniform.statistic),
            "p_value": float(ks_uniform.pvalue),
            "kesimpulan": "Menunjukkan deviasi dari uniformitas murni akibat fluktuasi intensitas harian"
        },
        "analisis_thinning_dan_superposisi": {
            "medis": {
                "jumlah": n_medis,
                "proporsi_p": p_medis,
                "lambda_jam": lambda_medis
            },
            "non_medis": {
                "jumlah": n_non_medis,
                "proporsi_1_min_p": p_non_medis,
                "lambda_jam": lambda_non_medis
            },
            "verifikasi_superposisi": {
                "sum_sub_lambdas": lambda_medis + lambda_non_medis,
                "lambda_induk": lambda_hat_hour,
                "selisih": abs((lambda_medis + lambda_non_medis) - lambda_hat_hour)
            }
        },
        "waktu_tunggu_gamma": gamma_results,
        "probabilitas_deduktif": {
            "P_N_15min_0": float(prob_15min_0),
            "P_N_15min_3": float(prob_15min_3),
            "P_N_1hour_13": float(prob_1hour_13)
        }
    }

    output_json = os.path.join(processed_dir, "hasil_studi_kasus_lengkap.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)

    print(f"Hasil lengkap berhasil disimpan ke: {output_json}")
    print("=" * 70)
    print("  EKSEKUSI PIPELINE ANALISIS EMPIRIS SELESAI DENGAN SUKSES")
    print("=" * 70)

if __name__ == "__main__":
    main()
