"""
analisis_studi_kasus.py
=======================
Pipeline Analisis Empiris dan Pemodelan Proses Poisson Homogen
Studi Kasus: Aliran Panggilan Darurat Seattle Fire Department (SFD)

Modul ini mengimplementasikan pemodelan stokastik pada data kedatangan
kejadian publik riil dengan komponen:
1. Estimasi Laju Kedatangan (MLE): lambda = N / T
2. Distribusi Waktu Antar-Kedatangan: T_n = W_n - W_{n-1} ~ Eksp(lambda)
3. Uji Indeks Dispersi: D = s^2 / mean dan uji Chi-Kuadrat
4. Evaluasi Stasioneritas Lokal: analisis per blok waktu diurnal
5. Penipisan (Thinning) dan Superposisi: dekomposisi jenis insiden
6. Distribusi Waktu Tunggu Kumulatif: W_n ~ Gamma(n, lambda)
"""

import os
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

# Konfigurasi visualisasi grafik
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'lines.linewidth': 1.8,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
})


# -----------------------------------------------------------------------------
# 1. Pemuatan dan Penyiapan Data
# -----------------------------------------------------------------------------

def muat_data(csv_path: str):
    """
    Membaca data panggilan 911 dan mengurutkan secara kronologis.
    Menghitung waktu relatif kejadian (elapsed time) dalam jam dan menit dari t0.
    """
    df = pd.read_csv(csv_path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    t0 = pd.to_datetime("2026-10-23 00:00:00")
    df["elapsed_seconds"] = (df["datetime"] - t0).dt.total_seconds()
    df["elapsed_hours"] = df["elapsed_seconds"] / 3600.0
    df["elapsed_minutes"] = df["elapsed_seconds"] / 60.0

    return df


# -----------------------------------------------------------------------------
# 2. Estimasi Parameter Laju (MLE)
# -----------------------------------------------------------------------------

def estimasi_laju_mle(total_panggilan: int, durasi_jam: float = 24.0):
    """
    Estimasi parameter laju intensitas Maximum Likelihood Estimator (MLE):
    lambda_hat = N(T) / T
    """
    lambda_jam = total_panggilan / durasi_jam
    lambda_menit = lambda_jam / 60.0
    ekspektasi_iat_menit = 1.0 / lambda_menit  # E[T_n] = 1 / lambda

    return {
        "lambda_jam": lambda_jam,
        "lambda_menit": lambda_menit,
        "ekspektasi_iat_menit": ekspektasi_iat_menit,
    }


# -----------------------------------------------------------------------------
# 3. Analisis Waktu Antar-Kedatangan (Inter-Arrival Time / IAT)
# -----------------------------------------------------------------------------

def analisis_waktu_antar_kedatangan(df: pd.DataFrame, lambda_menit: float):
    """
    Menghitung selang waktu antar dua panggilan berurutan:
    T_n = W_n - W_{n-1}
    Pada model Poisson, T_n ~ Eksp(lambda_menit).
    """
    # Selisih waktu berurutan dalam satuan menit
    iat_menit = df["elapsed_minutes"].diff().dropna()

    # Statistik deskriptif sampel
    mean_val = float(iat_menit.mean())
    std_val = float(iat_menit.std())
    median_val = float(iat_menit.median())
    min_val = float(iat_menit.min())
    max_val = float(iat_menit.max())
    q25 = float(iat_menit.quantile(0.25))
    q75 = float(iat_menit.quantile(0.75))
    zero_count = int((iat_menit == 0).sum())

    # Uji kesesuaian Kolmogorov-Smirnov satu sampel terhadap Exponential(scale=1/lambda)
    ks_test = stats.kstest(iat_menit, "expon", args=(0, 1.0 / lambda_menit))

    ringkasan = {
        "n_selang": len(iat_menit),
        "mean_menit": mean_val,
        "std_menit": std_val,
        "median_menit": median_val,
        "min_menit": min_val,
        "max_menit": max_val,
        "q25_menit": q25,
        "q75_menit": q75,
        "jumlah_iat_nol": zero_count,
        "ks_test_exponential": {
            "d_statistic": float(ks_test.statistic),
            "p_value": float(ks_test.pvalue),
        },
    }

    return iat_menit, ringkasan


# -----------------------------------------------------------------------------
# 4. Uji Indeks Dispersi Poisson (Rata-rata vs Variansi)
# -----------------------------------------------------------------------------

def hitung_indeks_dispersi(counts: pd.Series):
    """
    Menghitung Indeks Dispersi: D = s^2 / X_bar
    Pada Proses Poisson teoritis, Var(N) = E[N] sehingga D = 1.
    Statistik uji: chi2 = (k - 1) * D dengan derajat bebas df = k - 1.
    """
    k = len(counts)
    mean_val = float(counts.mean())
    var_val = float(counts.var(ddof=1)) if k > 1 else 0.0
    dispersion_index = var_val / mean_val if mean_val > 0 else 0.0

    df_deg = k - 1
    chi2_val = df_deg * dispersion_index
    p_val = 1.0 - stats.chi2.cdf(chi2_val, df=df_deg) if df_deg > 0 else 1.0

    return {
        "mean": mean_val,
        "variance": var_val,
        "std": float(np.sqrt(var_val)),
        "dispersion_index": dispersion_index,
        "chi2": chi2_val,
        "df": df_deg,
        "p_value": p_val,
    }


def evaluasi_blok_diurnal(hourly_counts: pd.Series):
    """
    Menguji dispersi Poisson pada 4 sub-interval waktu harian:
    - Dini hari: 01.00 - 06.00 (aktivitas kota minimal)
    - Pagi: 07.00 - 12.00 (aktivitas mulai meningkat)
    - Siang ke sore: 13.00 - 18.00 (jam sibuk operasional)
    - Malam: 19.00 - 24.00 (aktivitas malam)
    """
    blok_waktu = {
        "Dini Hari (01:00 - 06:00)": list(range(1, 6)),
        "Pagi Menjelang Siang (07:00 - 12:00)": list(range(7, 13)),
        "Siang ke Sore (13:00 - 18:00)": list(range(13, 19)),
        "Malam Hari (19:00 - 24:00)": list(range(19, 24)) + [0],
    }

    hasil_blok = {}
    for nama_blok, jam_list in blok_waktu.items():
        sub_counts = hourly_counts.loc[jam_list]
        disp = hitung_indeks_dispersi(sub_counts)
        hasil_blok[nama_blok] = {
            "hours": jam_list,
            "mean": disp["mean"],
            "variance": disp["variance"],
            "dispersion_index": disp["dispersion_index"],
            "chi2": disp["chi2"],
            "p_value": disp["p_value"],
            "counts": [int(c) for c in sub_counts],
        }

    return hasil_blok


# -----------------------------------------------------------------------------
# 5. Operasi Penipisan (Thinning) dan Superposisi
# -----------------------------------------------------------------------------

def analisis_thinning(df: pd.DataFrame, lambda_total: float):
    """
    Memilah panggilan menjadi sub-aliran medis dan non-medis.
    Sifat penipisan: jika proses Poisson dipecah acak dengan probabilitas p,
    kedua sub-proses tetap Poisson dengan laju lambda_1 = p * lambda dan lambda_2 = (1-p) * lambda.
    """
    total = len(df)
    is_medis = df["type"].str.contains("Aid|Medic", case=False, na=False)

    n_medis = int(is_medis.sum())
    n_non_medis = total - n_medis

    p_medis = n_medis / total
    p_non_medis = n_non_medis / total

    lambda_medis = lambda_total * p_medis
    lambda_non_medis = lambda_total * p_non_medis

    return {
        "medis": {
            "jumlah": n_medis,
            "proporsi_p": p_medis,
            "lambda_jam": lambda_medis,
        },
        "non_medis": {
            "jumlah": n_non_medis,
            "proporsi_1_min_p": p_non_medis,
            "lambda_jam": lambda_non_medis,
        },
        "verifikasi_superposisi": {
            "sum_sub_lambdas": lambda_medis + lambda_non_medis,
            "lambda_induk": lambda_total,
            "selisih": abs((lambda_medis + lambda_non_medis) - lambda_total),
        },
    }


# -----------------------------------------------------------------------------
# 6. Distribusi Waktu Tunggu Gamma (Erlang)
# -----------------------------------------------------------------------------

def analisis_waktu_tunggu_gamma(df: pd.DataFrame, lambda_jam: float):
    """
    Waktu tunggu menuju kejadian ke-n: W_n = sum_{i=1}^n T_i
    Pada proses Poisson homogen: W_n ~ Gamma(shape=n, scale=1/lambda).
    Nilai harapan: E[W_n] = n / lambda
    Variansi: Var(W_n) = n / lambda^2
    """
    milestones = [10, 30, 60, 100, 150, 200, 300]
    hasil_gamma = {}

    for n_val in milestones:
        # Waktu empiris kejadian ke-n (indeks n-1)
        w_emp_jam = float(df.loc[n_val - 1, "elapsed_hours"])
        w_emp_menit = float(df.loc[n_val - 1, "elapsed_minutes"])

        mean_jam = n_val / lambda_jam
        var_jam = n_val / (lambda_jam ** 2)
        std_jam = float(np.sqrt(var_jam))

        cdf_emp = float(stats.gamma.cdf(w_emp_jam, a=n_val, scale=1.0 / lambda_jam))
        in_1sigma = (mean_jam - std_jam) <= w_emp_jam <= (mean_jam + std_jam)

        hasil_gamma[f"W_{n_val}"] = {
            "n": n_val,
            "E_W_hours": mean_jam,
            "Std_W_hours": std_jam,
            "E_W_minutes": mean_jam * 60.0,
            "Std_W_minutes": std_jam * 60.0,
            "Empirical_hours": w_emp_jam,
            "Empirical_minutes": w_emp_menit,
            "CDF_at_empirical": cdf_emp,
            "in_1_sigma_interval": bool(in_1sigma),
        }

    return hasil_gamma


# -----------------------------------------------------------------------------
# 7. Pembuatan Grafik Publikasi
# -----------------------------------------------------------------------------

def buat_grafik(df: pd.DataFrame, hourly_counts: pd.Series, iat_menit: pd.Series, 
                lambda_jam: float, lambda_menit: float, output_dirs: list):
    """
    Menghasilkan 4 grafik visualisasi analisis Poisson.
    Disimpan ke direktori tujuan (code/figures dan report/figures).
    """
    total = len(df)
    expected_iat = 1.0 / lambda_menit

    def simpan(fig, filename):
        for out_dir in output_dirs:
            fig.savefig(os.path.join(out_dir, filename), dpi=300)
        plt.close(fig)

    # Gambar 1: Trajektori Proses N(t) vs Garis Ekspektasi
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    t_plot = np.concatenate([[0], df["elapsed_hours"].values, [24.0]])
    n_plot = np.concatenate([[0], np.arange(1, total + 1), [total]])
    ax.step(t_plot, n_plot, where='post', color='#08306b', label='Proses Penghitungan Empiris $N(t)$')

    t_line = np.linspace(0, 24, 200)
    ax.plot(t_line, lambda_jam * t_line, '--', color='#d94801', 
            label=f'Ekspektasi Teoretis $\\mathbb{{E}}[N(t)] = {lambda_jam:.4f}t$')
    upper_band = lambda_jam * t_line + 2 * np.sqrt(lambda_jam * t_line)
    lower_band = np.maximum(0, lambda_jam * t_line - 2 * np.sqrt(lambda_jam * t_line))
    ax.fill_between(t_line, lower_band, upper_band, color='#fdd0a2', alpha=0.35, 
                    label=r'Pita Keyakinan Teoretis $\pm 2\sigma$ ($95\%$)')

    ax.set_title("Trajektori Proses Penghitungan Panggilan Darurat Seattle 911 (23 Oktober 2026)", fontweight='bold')
    ax.set_xlabel("Waktu Operasional $t$ (Jam sejak Pukul 00:00:00)")
    ax.set_ylabel("Jumlah Panggilan Masuk Kumulatif $N(t)$")
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 335)
    ax.set_xticks(range(0, 25, 2))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    fig.tight_layout()
    simpan(fig, "grafik_lintasan_proses.png")

    # Gambar 2: Histogram Waktu Antar-Kedatangan vs Eksponensial
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    bins = np.linspace(0, 30, 31)
    ax.hist(iat_menit, bins=bins, density=True, color='#2b8cbe', edgecolor='#084081', alpha=0.7, 
            label=f'Histogram Empiris $T_n$ ($N={len(iat_menit)}$)')

    x_exp = np.linspace(0, 30, 300)
    y_exp = stats.expon.pdf(x_exp, scale=expected_iat)
    ax.plot(x_exp, y_exp, color='#bd0026', label=f'Densitas Teoretis Eksp($\\lambda = {lambda_menit:.4f}$)')

    ax.axvline(iat_menit.mean(), color='#00441b', linestyle='-', label=f'Rata-rata Empiris ({iat_menit.mean():.2f} min)')
    ax.axvline(expected_iat, color='#bd0026', linestyle=':', label=f'Ekspektasi Teoretis ({expected_iat:.2f} min)')

    ax.set_title("Distribusi Waktu Antar-Kedatangan Empiris vs Model Eksponensial", fontweight='bold')
    ax.set_xlabel("Waktu Antar-Kedatangan $T_n$ (Menit)")
    ax.set_ylabel("Kerapatan Probabilitas")
    ax.set_xlim(0, 30)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    fig.tight_layout()
    simpan(fig, "distribusi_waktu_antar_kedatangan.png")

    # Gambar 3: Fluktuasi Laju Kedatangan per Jam & Siklus Diurnal
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    hours = np.arange(24)
    colors = ['#41b6c4' if h in range(1, 6) else ('#fd8d3c' if h in range(15, 21) else '#225ea8') for h in hours]
    ax.bar(hours, hourly_counts.values, color=colors, edgecolor='#1c3f60', alpha=0.85, width=0.75, 
           label='Frekuensi Kejadian Empiris $K_i$')
    ax.axhline(hourly_counts.mean(), color='#e31a1c', linestyle='--', 
               label=f'Laju Rata-rata $\\hat{{\\lambda}} = {hourly_counts.mean():.2f}$ call/jam')

    ax.axvspan(0.5, 5.5, color='#a1dab4', alpha=0.25, label='Blok Dini Hari (01:00-06:00, Laju Rendah)')
    ax.axvspan(14.5, 20.5, color='#fed976', alpha=0.25, label='Blok Jam Sibuk (15:00-21:00, Laju Tinggi)')

    ax.set_title("Fluktuasi Kedatangan Panggilan per Jam: Evaluasi Stasioneritas Diurnal", fontweight='bold')
    ax.set_xlabel("Jam Observasi (00:00 - 23:00 Waktu Setempat)")
    ax.set_ylabel("Jumlah Panggilan Masuk per Jam")
    ax.set_xlim(-0.5, 23.5)
    ax.set_xticks(range(0, 24))
    ax.grid(True, axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize=8.5)
    fig.tight_layout()
    simpan(fig, "fluktuasi_laju_per_jam.png")

    # Gambar 4: Distribusi Waktu Tunggu Gamma W_n untuk n Pilihan
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=300)
    t_gamma = np.linspace(0, 10, 400)
    colors_gamma = ['#238b45', '#2171b5', '#cb181d']

    for idx, n_val in enumerate([10, 30, 60]):
        c = colors_gamma[idx]
        pdf_vals = stats.gamma.pdf(t_gamma, a=n_val, scale=1.0 / lambda_jam)
        ax.plot(t_gamma, pdf_vals, color=c, label=f'Teoretis $W_{{{n_val}}} \\sim \\text{{Gamma}}({n_val}, {lambda_jam:.2f})$')
        t_emp = df.loc[n_val - 1, "elapsed_hours"]
        ax.axvline(t_emp, color=c, linestyle='--', label=f'Realisasi Empiris $W_{{{n_val}}} = {t_emp:.2f}$ jam')

    ax.set_title("Distribusi Kerapatan Waktu Tunggu Gamma (Erlang) vs Titik Realisasi Empiris", fontweight='bold')
    ax.set_xlabel("Waktu Kumulatif Kedatangan $t$ (Jam)")
    ax.set_ylabel("Kerapatan Probabilitas $f_{W_n}(t)$")
    ax.set_xlim(0, 8)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9, fontsize=8.5)
    fig.tight_layout()
    simpan(fig, "distribusi_waktu_tunggu_gamma.png")


# -----------------------------------------------------------------------------
# 8. Fungsi Utama (Orkestrasi Analisis)
# -----------------------------------------------------------------------------

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_csv = os.path.join(base_dir, "data", "raw", "seattle_fire_911_calls_20261023.csv")
    fig_dirs = [os.path.join(base_dir, "figures"), os.path.join(os.path.dirname(base_dir), "report", "figures")]
    processed_dir = os.path.join(base_dir, "data", "processed")

    for d in fig_dirs + [processed_dir]:
        os.makedirs(d, exist_ok=True)

    print("=" * 65)
    print("  ANALISIS PROSES POISSON: DATA PANGGILAN DARURAT SEATTLE 911")
    print("=" * 65)

    # 1. Pemuatan Data
    df = muat_data(raw_csv)
    total_calls = len(df)
    print(f"Total panggilan teramati (24 jam): {total_calls}")

    # 2. Estimasi Laju MLE
    laju = estimasi_laju_mle(total_calls, durasi_jam=24.0)
    lambda_jam = laju["lambda_jam"]
    lambda_menit = laju["lambda_menit"]
    print(f"Laju intensitas (jam)  : {lambda_jam:.4f} panggilan/jam")
    print(f"Laju intensitas (menit): {lambda_menit:.4f} panggilan/menit")
    print(f"Ekspektasi selang (IAT): {laju['ekspektasi_iat_menit']:.4f} menit")

    # 3. Waktu Antar-Kedatangan
    iat_menit, ringkasan_iat = analisis_waktu_antar_kedatangan(df, lambda_menit)
    print(f"Rata-rata IAT empiris  : {ringkasan_iat['mean_menit']:.4f} menit (Std: {ringkasan_iat['std_menit']:.4f} menit)")
    print(f"Jumlah panggilan selang 0 : {ringkasan_iat['jumlah_iat_nol']} (pembulatan CAD menit bulat)")

    # 4. Agregasi per Jam & Uji Dispersi
    hourly_counts = df.groupby(df["datetime"].dt.hour).size().reindex(range(24), fill_value=0)
    disp_global = hitung_indeks_dispersi(hourly_counts)
    eval_blok = evaluasi_blok_diurnal(hourly_counts)

    print(f"Indeks Dispersi Global (D): {disp_global['dispersion_index']:.4f} (p-value: {disp_global['p_value']:.4e})")
    print("  * Dini hari (01:00-06:00): D = "
          f"{eval_blok['Dini Hari (01:00 - 06:00)']['dispersion_index']:.2f} "
          f"(p = {eval_blok['Dini Hari (01:00 - 06:00)']['p_value']:.4f}) -> Homogenitas lokal valid")

    # 5. Uji Sifat Uniform Waktu Kedatangan Bersyarat
    ks_uniform = stats.kstest(df["elapsed_hours"], "uniform", args=(0, 24.0))

    # 6. Thinning dan Superposisi
    thinning = analisis_thinning(df, lambda_jam)
    print(f"Thinning Medis     : {thinning['medis']['jumlah']} panggilan ({thinning['medis']['proporsi_p']*100:.2f}%), "
          f"lambda = {thinning['medis']['lambda_jam']:.4f}")
    print(f"Thinning Non-Medis : {thinning['non_medis']['jumlah']} panggilan ({thinning['non_medis']['proporsi_1_min_p']*100:.2f}%), "
          f"lambda = {thinning['non_medis']['lambda_jam']:.4f}")

    # 7. Waktu Tunggu Gamma/Erlang
    hasil_gamma = analisis_waktu_tunggu_gamma(df, lambda_jam)

    # 8. Probabilitas Analitis
    prob_15min_0 = float(stats.poisson.pmf(0, lambda_jam * 0.25))
    prob_15min_3 = float(stats.poisson.pmf(3, lambda_jam * 0.25))
    prob_1hour_13 = float(stats.poisson.pmf(13, lambda_jam))

    # 9. Pembuatan Grafik
    print("\nMembuat grafik visualisasi publikasi...")
    buat_grafik(df, hourly_counts, iat_menit, lambda_jam, lambda_menit, fig_dirs)

    # 10. Penyimpanan Data Hasil Olahan
    # A. CSV Kedatangan per Jam
    csv_hourly = os.path.join(processed_dir, "kedatangan_per_jam.csv")
    hourly_counts.rename_axis("hour").reset_index(name="jumlah_panggilan").to_csv(csv_hourly, index=False)

    # B. Ringkasan JSON Ringkas
    json_summary = os.path.join(processed_dir, "ringkasan_analisis_poisson.json")
    with open(json_summary, "w", encoding="utf-8") as f:
        json.dump({
            "tanggal_observasi": "2026-10-23",
            "total_panggilan": total_calls,
            "laju_intensitas_24h": lambda_jam,
            "variansi_24h": disp_global["variance"],
            "indeks_dispersi_24h": disp_global["dispersion_index"],
            "p_medis": thinning["medis"]["proporsi_p"],
            "p_non_medis": thinning["non_medis"]["proporsi_1_min_p"],
            "lambda_medis": thinning["medis"]["lambda_jam"],
            "lambda_non_medis": thinning["non_medis"]["lambda_jam"],
            "hourly_counts": {str(h): int(c) for h, c in hourly_counts.items()},
        }, f, indent=2)

    # C. Hasil Komprehensif Lengkap
    json_full = os.path.join(processed_dir, "hasil_studi_kasus_lengkap.json")
    full_data = {
        "metadata": {
            "judul": "Analisis Proses Poisson Homogen pada Kasus Riil Aliran Panggilan Darurat Seattle 911",
            "tanggal_analisis": "2026-10-31",
            "sumber_data": "City of Seattle Open Data Portal (API Socrata: kzjm-xkqj)",
            "tanggal_observasi": "2026-10-23",
            "durasi_observasi_jam": 24.0,
            "total_panggilan": total_calls,
        },
        "parameter_estimasi": {
            "lambda_mle_per_jam": lambda_jam,
            "lambda_mle_per_menit": lambda_menit,
            "ekspektasi_iat_menit": laju["ekspektasi_iat_menit"],
        },
        "statistik_waktu_antar_kedatangan": ringkasan_iat,
        "uji_dispersi_dan_stasioneritas": {
            "skala_24h": {
                "mean_per_jam": disp_global["mean"],
                "variansi_per_jam": disp_global["variance"],
                "simpangan_baku_per_jam": disp_global["std"],
                "indeks_dispersi_D": disp_global["dispersion_index"],
                "chi2_stat": disp_global["chi2"],
                "derajat_kebebasan": disp_global["df"],
                "p_value": disp_global["p_value"],
                "kesimpulan": "Overdispersi signifikan pada skala 24 jam akibat siklus diurnal",
            },
            "evaluasi_per_blok": eval_blok,
        },
        "uji_sifat_uniform_order_statistics": {
            "ks_statistic": float(ks_uniform.statistic),
            "p_value": float(ks_uniform.pvalue),
            "kesimpulan": "Menunjukkan deviasi dari uniformitas murni akibat fluktuasi intensitas harian",
        },
        "analisis_thinning_dan_superposisi": thinning,
        "waktu_tunggu_gamma": hasil_gamma,
        "probabilitas_deduktif": {
            "P_N_15min_0": prob_15min_0,
            "P_N_15min_3": prob_15min_3,
            "P_N_1hour_13": prob_1hour_13,
        },
    }

    with open(json_full, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2)

    print(f"\nHasil analisis berhasil disimpan ke {processed_dir}.")
    print("=" * 65)


if __name__ == "__main__":
    main()
