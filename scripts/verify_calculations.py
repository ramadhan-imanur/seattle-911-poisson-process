"""
verify_calculations.py
======================
Modul verifikasi analitis rumus matematika proses Poisson homogen:
probabilitas kejadian, waktu tunggu Gamma/Erlang, uji indeks dispersi,
serta verifikasi sifat penipisan (thinning) dan superposisi.

Rujukan Teori:
- Howard M. Taylor & Samuel Karlin (1998), Bab V
- Henk C. Tijms (2003), Bab 1

Fungsi Utama:
1. poisson_probability(lam, t, k) -> Probabilitas P(N(t)=k) dan P(N(t) <= k)
2. waiting_time_gamma(n, lam, t) -> Densitas, CDF, ekspektasi E[W_n], dan variansi Var(W_n)
3. verify_superposition(lambdas) -> Superposisi m proses Poisson independen
4. verify_thinning(lam, p) -> Penipisan/dekomposisi acak proses Poisson
5. dispersion_index_test(data_counts) -> Uji indeks dispersi s^2 / mean (uji kesesuaian Poisson)
6. test_uniform_property(arrival_times, t_end) -> Uji sifat uniform waktu kedatangan bersyarat N(t)=n
"""

import os
import numpy as np
import scipy.stats as stats


def poisson_probability(lam: float, t: float, k: int) -> dict:
    """
    Menghitung probabilitas proses Poisson homogen:
    P(N(t) = k) = ((lambda * t)^k * exp(-lambda * t)) / k!
    """
    if lam <= 0 or t <= 0:
        raise ValueError("Laju intensitas (lambda) dan durasi waktu (t) harus positif.")
    if k < 0:
        raise ValueError("Jumlah kejadian (k) harus non-negatif.")

    param = lam * t
    prob_exact = stats.poisson.pmf(k, param)
    prob_cdf = stats.poisson.cdf(k, param)
    prob_greater = 1.0 - prob_cdf

    return {
        "lambda": lam,
        "t": t,
        "lambda_t": param,
        "k": k,
        "P(N(t) = k)": float(prob_exact),
        "P(N(t) <= k)": float(prob_cdf),
        "P(N(t) > k)": float(prob_greater),
        "E[N(t)]": float(param),
        "Var[N(t)]": float(param),
    }


def waiting_time_gamma(n: int, lam: float, t_eval: float = None) -> dict:
    """
    Menghitung sifat distribusi waktu tunggu kejadian ke-n:
    W_n ~ Gamma(shape=n, scale=1/lambda) alias Erlang(n, lambda).
    E[W_n] = n / lambda
    Var(W_n) = n / (lambda^2)
    """
    if n <= 0 or lam <= 0:
        raise ValueError("Indeks kejadian n dan lambda harus bernilai positif.")

    mean_w = n / lam
    var_w = n / (lam ** 2)
    std_w = np.sqrt(var_w)

    res = {
        "n": n,
        "lambda": lam,
        "E[W_n]": float(mean_w),
        "Var(W_n)": float(var_w),
        "Std(W_n)": float(std_w),
    }

    if t_eval is not None and t_eval > 0:
        pdf_val = stats.gamma.pdf(t_eval, a=n, scale=1.0 / lam)
        cdf_val = stats.gamma.cdf(t_eval, a=n, scale=1.0 / lam)
        res[f"f_W_{n}({t_eval})"] = float(pdf_val)
        res[f"P(W_{n} <= {t_eval})"] = float(cdf_val)

    return res


def verify_superposition(lambdas: list) -> dict:
    """
    Memverifikasi operasi superposisi dari beberapa proses Poisson independen.
    Jika N_1(t), ..., N_m(t) saling bebas dengan laju lambda_1, ..., lambda_m,
    maka N(t) = sum(N_i(t)) adalah proses Poisson dengan laju lambda = sum(lambda_i).
    """
    arr = np.array(lambdas, dtype=float)
    if np.any(arr <= 0):
        raise ValueError("Seluruh laju intensitas individu harus positif.")

    total_lambda = float(np.sum(arr))
    probabilities = arr / total_lambda

    return {
        "input_lambdas": list(arr),
        "total_lambda": total_lambda,
        "proportions_p_i": list(probabilities),
        "keterangan": "Superposisi menghasilkan proses Poisson homogen baru dengan laju total.",
    }


def verify_thinning(lam: float, probabilities: list) -> dict:
    """
    Memverifikasi operasi penipisan (thinning / dekomposisi acak).
    Kejadian diklasifikasikan ke dalam kategori j dengan peluang p_j.
    Sub-proses N_j(t) saling bebas dan berdistribusi Poisson dengan laju lambda_j = p_j * lambda.
    """
    probs = np.array(probabilities, dtype=float)
    if not np.isclose(np.sum(probs), 1.0):
        raise ValueError(f"Total probabilitas klasifikasi harus tepat bernilai 1.0 (ditemukan: {np.sum(probs)}).")
    if lam <= 0 or np.any(probs < 0):
        raise ValueError("Lambda dan probabilitas harus non-negatif.")

    sub_lambdas = lam * probs

    return {
        "lambda_induk": lam,
        "probabilities": list(probs),
        "sub_lambdas": list(sub_lambdas),
        "total_sub_lambdas": float(np.sum(sub_lambdas)),
        "keterangan": "Sub-proses hasil penipisan saling bebas dan berdistribusi Poisson.",
    }


def dispersion_index_test(data_counts: list) -> dict:
    """
    Uji Indeks Dispersi Poisson (Poissonness Test):
    D = s^2 / mean
    Pada distribusi Poisson teoritis: E[X] = Var(X) sehingga D = 1.
    Statistik Uji: (N - 1) * D ~ ChiSquare(df = N - 1).
    """
    arr = np.array(data_counts, dtype=float)
    n_sample = len(arr)
    if n_sample < 2:
        raise ValueError("Data sampel minimal memuat 2 pengamatan.")

    mean_val = float(np.mean(arr))
    var_val = float(np.var(arr, ddof=1))

    if mean_val == 0:
        dispersion_index = 0.0
        p_val = 1.0
    else:
        dispersion_index = var_val / mean_val
        chi2_stat = (n_sample - 1) * dispersion_index
        p_val = 1.0 - stats.chi2.cdf(chi2_stat, df=n_sample - 1)

    kesimpulan = "Sesuai Proses Poisson Homogen"
    if dispersion_index > 1.2 and p_val < 0.05:
        kesimpulan = "Overdispersi (indikasi laju non-homogen atau batch arrivals)"
    elif dispersion_index < 0.8 and p_val > 0.95:
        kesimpulan = "Underdispersi (indikasi kedatangan yang terlalu teratur/deterministik)"

    return {
        "jumlah_sampel": n_sample,
        "mean_sampel (X_bar)": mean_val,
        "variansi_sampel (s^2)": var_val,
        "indeks_dispersi (D = s^2 / X_bar)": float(dispersion_index),
        "chi2_stat": float(chi2_stat) if mean_val > 0 else 0.0,
        "p_value": float(p_val),
        "kesimpulan_evaluasi": kesimpulan,
    }


def test_uniform_property(arrival_times: list, t_end: float) -> dict:
    """
    Uji Sifat Uniform Waktu Kedatangan Bersyarat:
    Diberikan N(t) = n, waktu kedatangan W_1, ..., W_n berdistribusi sama
    dengan statistik tatanan dari n variabel acak Uniform(0, t_end).
    Uji Kolmogorov-Smirnov satu sampel terhadap Uniform(0, t_end).
    """
    times = np.array(arrival_times, dtype=float)
    n = len(times)
    if n == 0 or t_end <= 0:
        raise ValueError("Waktu kedatangan dan durasi harus valid.")

    # Uji KS terhadap Uniform(0, t_end)
    ks_res = stats.kstest(times, "uniform", args=(0, t_end))

    return {
        "n_kedatangan": n,
        "durasi_observasi (t)": t_end,
        "ks_statistic": float(ks_res.statistic),
        "p_value": float(ks_res.pvalue),
        "kesimpulan": (
            "Memenuhi sifat uniformitas waktu kedatangan (asumsi Poisson terdukung)"
            if ks_res.pvalue >= 0.05
            else "Tidak memenuhi sifat uniformitas (indikasi laju intensitas berubah sepanjang waktu)"
        ),
    }


def verify_empirical_dataset(csv_path: str) -> dict:
    """
    Memverifikasi dataset empiris riil panggilan darurat 911 (Seattle Open Data).
    Menghitung laju intensitas, indeks dispersi, dan parameter thinning.
    """
    import os
    import pandas as pd
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Berkas empiris tidak ditemukan: {csv_path}")

    df = pd.read_csv(csv_path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    total_n = len(df)
    hourly_counts = df.groupby(df["datetime"].dt.hour).size().reindex(range(24), fill_value=0)
    
    mean_hourly = float(hourly_counts.mean())
    var_hourly = float(hourly_counts.var(ddof=1))
    disp_index = var_hourly / mean_hourly if mean_hourly > 0 else 0.0

    # Thinning: Medis vs Non-Medis
    is_med = df["type"].str.contains("Aid|Medic", case=False, na=False)
    n_med = int(is_med.sum())
    n_non_med = total_n - n_med
    p_med = n_med / total_n
    p_non_med = n_non_med / total_n

    # Waktu antar-kedatangan
    iat = df["datetime"].diff().dt.total_seconds().dropna() / 60.0  # menit

    return {
        "total_kejadian_24h": total_n,
        "laju_intensitas_lambda_hat": mean_hourly,
        "variansi_sampel_s2": var_hourly,
        "indeks_dispersi_D": disp_index,
        "p_medis": p_med,
        "lambda_medis": mean_hourly * p_med,
        "p_non_medis": p_non_med,
        "lambda_non_medis": mean_hourly * p_non_med,
        "iat_mean_menit": float(iat.mean()),
        "iat_std_menit": float(iat.std()),
        "teoritis_1_per_lambda_menit": float(60.0 / mean_hourly),
    }


if __name__ == "__main__":
    print("=" * 65)
    print("  VERIFIKASI RUMUS MATEMATIKA PROSES POISSON HOMOGEN")
    print("=" * 65)

    # 1. Uji Probabilitas Poisson
    p_res = poisson_probability(lam=4.0, t=1.0, k=4)
    print(f"\n[1] Probabilitas Poisson (lambda=4, t=1, k=4):")
    print(f"    P(N(t)=4)  = {p_res['P(N(t) = k)']:.6f}")
    print(f"    E[N(t)]    = {p_res['E[N(t)]']:.2f}")
    print(f"    Var[N(t)]  = {p_res['Var[N(t)]']:.2f}")

    # 2. Uji Waktu Tunggu Gamma
    w_res = waiting_time_gamma(n=3, lam=4.0, t_eval=0.75)
    print(f"\n[2] Waktu Tunggu Gamma (n=3, lambda=4, t=0.75):")
    print(f"    E[W_3]     = {w_res['E[W_n]']:.4f} satuan waktu")
    print(f"    Var(W_3)   = {w_res['Var(W_n)']:.4f}")
    print(f"    P(W_3<=0.75) = {w_res.get('P(W_3 <= 0.75)', 0):.6f}")

    # 3. Uji Superposisi & Thinning
    sup_res = verify_superposition([2.5, 1.5])
    print(f"\n[3] Superposisi (lambda_1=2.5, lambda_2=1.5):")
    print(f"    Laju Total = {sup_res['total_lambda']:.2f}")

    thin_res = verify_thinning(lam=4.0, probabilities=[0.7, 0.3])
    print(f"\n[4] Penipisan (lambda=4.0, p=[0.7, 0.3]):")
    print(f"    Sub-laju   = {thin_res['sub_lambdas']}")

    # 4. Uji Indeks Dispersi Sampel Sintetis
    sample_data = [4, 5, 3, 4, 6, 4, 3, 5, 4, 4, 5, 3]
    disp_res = dispersion_index_test(sample_data)
    print(f"\n[5] Uji Indeks Dispersi Sampel Sintetis:")
    print(f"    Mean   = {disp_res['mean_sampel (X_bar)']:.4f}")
    print(f"    Var    = {disp_res['variansi_sampel (s^2)']:.4f}")
    print(f"    D      = {disp_res['indeks_dispersi (D = s^2 / X_bar)']:.4f}")
    print(f"    Status = {disp_res['kesimpulan_evaluasi']}")

    # 5. Uji Dataset Empiris Riil (Seattle 911 Dispatches)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_csv = os.path.join(base_dir, "data", "raw", "seattle_fire_911_calls_20261023.csv")
    if os.path.exists(data_csv):
        emp_res = verify_empirical_dataset(data_csv)
        print(f"\n[6] Verifikasi Data Empiris Riil (Seattle 911 Calls, 23 Okt 2026):")
        print(f"    Total Panggilan (24 Jam)    = {emp_res['total_kejadian_24h']}")
        print(f"    Laju Intensitas (lambda_hat) = {emp_res['laju_intensitas_lambda_hat']:.4f} panggilan/jam")
        print(f"    Variansi Sampel (s^2)        = {emp_res['variansi_sampel_s2']:.4f}")
        print(f"    Indeks Dispersi D            = {emp_res['indeks_dispersi_D']:.4f}")
        print(f"    Waktu Antar-Kedatangan (IAT) = {emp_res['iat_mean_menit']:.4f} menit (Std: {emp_res['iat_std_menit']:.4f} menit)")
        print(f"    Teoritis 1/lambda            = {emp_res['teoritis_1_per_lambda_menit']:.4f} menit")
        print(f"    Thinning Medis (p={emp_res['p_medis']:.4f})  = {emp_res['lambda_medis']:.4f} panggilan/jam")
        print(f"    Thinning Non-Medis           = {emp_res['lambda_non_medis']:.4f} panggilan/jam")

    print("\n" + "=" * 65)
    print("  VERIFIKASI PERHITUNGAN SELESAI")
    print("=" * 65)

