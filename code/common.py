"""Shared paths, constants and plotting style for the APMCM 2026 Problem C pipeline."""
import os
import numpy as np

BASE = r"D:\Grade 2\数学建模\APMCM2026_C"
DATA = (r"D:\Grade 2\数学建模\2026 APMCM Problems\2026 APMCM Problems"
        r"\2026 APMCM Problem C\date")
FIG = os.path.join(BASE, "figures")
RES = os.path.join(BASE, "results")
EDA = os.path.join(BASE, "eda")

SEED = 42
CALL_TYPES = ["flat", "mod", "tv"]
COLORS = {"flat": "#4C72B0", "mod": "#DD8452", "tv": "#55A868", "control": "#8C8C8C"}
DIST_COLS = ["4m", "8m", "16m", "32m", "64m", "128m", "256m"]
DIST_M = np.array([4, 8, 16, 32, 64, 128, 256], dtype=float)

CORR_FILES = {
    ("flat", "spectrogram"): "Data03_correlation1m_flat_call_spectrogram.csv",
    ("mod", "spectrogram"): "Data04_correlation1m_modulated_call_spectrogram.csv",
    ("tv", "spectrogram"): "Data05_correlation1m_twovoice_call_spectrogram.csv",
    ("flat", "amplitude_spectrum"): "Data06_correlation1m_flat_call_amplitude_spectrum.csv",
    ("mod", "amplitude_spectrum"): "Data07_correlation1m_modulated_call_amplitude_spectrum.csv",
    ("tv", "amplitude_spectrum"): "Data08_correlation1m_twovoice_call_amplitude_spectrum.csv",
    ("flat", "envelope"): "Data09_correlation1m_flat_call_envelope.csv",
    ("mod", "envelope"): "Data10_correlation1m_modulated_call_envelope.csv",
    ("tv", "envelope"): "Data11_correlation1m_twovoice_call_envelope.csv",
}

FEATS = ["Duration", "F01", "Fpeak", "Q25", "Q50", "Q75"]
LABELS = {
    "Duration": "Duration (s)",
    "F01": "F01 (Hz)",
    "F02": "F02 (Hz)",
    "Fpeak": "Peak frequency (Hz)",
    "Q25": "Q25 (Hz)",
    "Q50": "Q50 (Hz)",
    "Q75": "Q75 (Hz)",
    "PulseRate": "Pulse rate (Hz)",
}


def data_path(name):
    return os.path.join(DATA, name)


def apply_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 320,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "figure.autolayout": False,
    })
    return plt
