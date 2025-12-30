# -*- coding: utf-8 -*-
"""
Modul Handler Google Sheets untuk Input Multi-Divisi
PT. PLN Indonesia Power Suralaya Unit 8

Modul ini menangani semua operasi baca/tulis ke Google Sheets
menggunakan gspread langsung untuk reliability yang lebih baik.
"""

# Mengimpor beberapa library yang diperlukan
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import pytz

# Fungsi untuk mengambil waktu GMT+7
def get_current_timestamp():
    """Mengembalikan timestamp string format YYYY-MM-DD HH:MM:SS (WIB)."""
    # Gunakan zona waktu Jakarta (WIB) secara eksplisit
    jakarta_tz = pytz.timezone("Asia/Jakarta")
    return datetime.now(jakarta_tz).strftime("%Y-%m-%d %H:%M:%S")


# Nama sheet dan kolom yang digunakan
SHEET_NAME = "logs"
COLUMNS = [
    "timestamp",
    # Komponen A
    "komponen_a",
    "price_a",
    "eaf_a",
    # Komponen B
    "komponen_b",
    "price_b",
    "eaf_b",
    # Daya netto dan jumlah hari
    "daya_netto",
    "jum_hari_bln",
    "jum_hari_thn",
    # Komponen C
    "komponen_c_batubara",
    "komponen_c_biomassa",
    "vol_batubara_kg",  # Produksi
    "vol_biomassa_kg",  # Produksi
    "harga_batubara_rp",  # Keuangan
    "harga_biomassa_rp",  # Keuangan
    "hhv_batubara",  # Parameter
    "hhv_biomassa",  # Parameter
    "koef_batubara",  # Parameter
    "koef_biomassa",  # Parameter
    "eio_val",  # Parameter
    # Komponen D
    "komponen_d",
    "price_d",
    "kwh_export"
]

# Scope untuk Google Sheets dan Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============ HELPER PARSING ANGKA ============
def parse_id_numeric(val):
    """
    Parser angka KHUSUS data Google Sheets.
    Aturan final (konsisten & aman finansial):
    - 0.xxx / 0,xxx  -> DESIMAL
    - x.xxx (3 digit) -> RIBUAN
    - multi separator -> RIBUAN
    - locale ID & EN aman
    """
    if val is None:
        return 0.0

    if isinstance(val, (int, float)):
        return float(val)

    s = (
        str(val)
        .strip()
        .replace("Rp", "")
        .replace(" ", "")
    )

    if not s or s.lower() == "nan":
        return 0.0

    import re

    # ===============================
    # 1️⃣ Bersihkan karakter ilegal
    # ===============================
    s = re.sub(r"[^\d.,\-]", "", s)
    if not s:
        return 0.0

    try:
        # ===============================
        # 2️⃣ Normalisasi separator ganda
        # ===============================
        s = re.sub(r"\.+", ".", s)
        s = re.sub(r",+", ",", s)

        has_dot = "." in s
        has_comma = "," in s

        # ===============================
        # KASUS 1: ADA TITIK & KOMA
        # ===============================
        if has_dot and has_comma:
            # Separator terakhir = desimal
            if s.rfind(".") > s.rfind(","):
                # Format EN: 1,234.56
                return float(s.replace(",", ""))
            else:
                # Format ID: 1.234,56
                return float(s.replace(".", "").replace(",", "."))

        # ===============================
        # KASUS 2: HANYA TITIK
        # ===============================
        if has_dot:
            dot_count = s.count(".")
            left, right = s.split(".", 1)

            # 2.1 kiri = 0 / -0 → PASTI DESIMAL
            if left == "0" or left == "-0":
                return float(s)

            # 2.2 lebih dari satu titik → PASTI RIBUAN
            # contoh: 100.000.245
            if dot_count > 1:
                return float(s.replace(".", ""))

            # 2.3 satu titik
            # digit belakang <= 2 → DESIMAL
            if len(right) <= 2:
                return float(s)

            # 2.4 digit belakang >= 3 → RIBUAN
            # contoh: 2.915 → 2915
            return float(s.replace(".", ""))

        # ===============================
        # KASUS 3: HANYA KOMA
        # ===============================
        if has_comma:
            comma_count = s.count(",")
            left, right = s.split(",", 1)

            # 3.1 kiri = 0 / -0 → PASTI DESIMAL
            if left == "0" or left == "-0":
                return float(s.replace(",", "."))

            # 3.2 lebih dari satu koma → RIBUAN
            if comma_count > 1:
                return float(s.replace(",", ""))

            # 3.3 satu koma
            # digit belakang <= 2 → DESIMAL
            if len(right) <= 2:
                return float(s.replace(",", "."))

            # 3.4 digit belakang >= 3 → RIBUAN
            return float(s.replace(",", ""))

        # ===============================
        # KASUS 4: ANGKA MURNI
        # ===============================
        return float(s)

    except Exception:
        return 0.0







@st.cache_resource
def get_gspread_client():
    """
    Mendapatkan client gspread dengan kredensial dari secrets.
    Menggunakan cache untuk efisiensi.
    """
    try:
        # Ambil kredensial dari Streamlit secrets
        creds_dict = {
            "type": st.secrets["connections"]["gsheets"]["type"],
            "project_id": st.secrets["connections"]["gsheets"]["project_id"],
            "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
            "private_key": st.secrets["connections"]["gsheets"]["private_key"],
            "client_email": st.secrets["connections"]["gsheets"]["client_email"],
            "client_id": st.secrets["connections"]["gsheets"]["client_id"],
            "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
            "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"][
                "auth_provider_x509_cert_url"
            ],
            "client_x509_cert_url": st.secrets["connections"]["gsheets"][
                "client_x509_cert_url"
            ],
        }

        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Gagal membuat koneksi: {str(e)}")
        return None


def get_spreadsheet():
    """
    Mendapatkan objek spreadsheet.
    """
    client = get_gspread_client()
    if client is None:
        return None

    try:
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        spreadsheet = client.open_by_url(spreadsheet_url)
        return spreadsheet
    except Exception as e:
        st.error(f"Gagal membuka spreadsheet: {str(e)}")
        return None


def get_worksheet():
    """
    Mendapatkan worksheet 'logs'.
    """
    spreadsheet = get_spreadsheet()
    if spreadsheet is None:
        return None

    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        return worksheet
    except Exception as e:
        st.error(f"Gagal membuka worksheet '{SHEET_NAME}': {str(e)}")
        return None


@st.cache_data(ttl=10, show_spinner=False)
def read_all_data():
    """
    Membaca semua data dari sheet.
    """
    worksheet = get_worksheet()
    if worksheet is None:
        return pd.DataFrame(columns=COLUMNS)

    try:
        data = worksheet.get_all_values()
        if len(data) <= 1:  # Hanya header atau kosong
            return pd.DataFrame(columns=COLUMNS)

        df = pd.DataFrame(data[1:], columns=data[0])  # Skip header row
        return df
    except Exception as e:
        st.error(f"Gagal membaca data: {str(e)}")
        return pd.DataFrame(columns=COLUMNS)


def get_current_period_row():
    """
    Mendapatkan baris periode saat ini (baris terakhir dalam sheet).
    """
    df = read_all_data()

    if df.empty:
        return {
            "timestamp": None,
            "komponen_a":0,
            "price_a":0,
            "eaf_a":0,
            "komponen_b":0,
            "price_b":0,
            "eaf_b":0,
            "daya_netto":0,
            "jum_hari_bln":0,
            "jum_hari_thn":0,
            "komponen_c_batubara":0,
            "komponen_c_biomassa":0,
            "vol_batubara_kg":0,  # Produksi
            "vol_biomassa_kg":0,  # Produksi
            "harga_batubara_rp":0,  # Keuangan
            "harga_biomassa_rp":0,  # Keuangan
            "hhv_batubara":0,  # Parameter
            "hhv_biomassa":0,  # Parameter
            "koef_batubara":0,  # Parameter
            "koef_biomassa":0,  # Parameter
            "eio_val":0,  # Parameter
            "komponen_d":0,
            "price_d":0,
            "kwh_export":0,
            "is_complete": False
        }

    # Ambil baris terakhir
    last_row = df.iloc[-1]

    # Kolom params yang harus diperlakukan sebagai float
    float_cols = [
        "price_a",
        "eaf_a",
        "daya_netto",
        "price_b",
        "eaf_b",
        "price_d",
        "vol_batubara_kg",
        "vol_biomassa_kg",
        "hhv_batubara",
        "hhv_biomassa",
        "koef_batubara",
        "koef_biomassa",
        "eio_val",
        "vol_bb",
        "vol_bio",
        "harga_bb",
        "harga_bio"  # Antisipasi nama pendek if any
    ]

    values = {}
    # Iterate semua kolom di COLUMNS (kecuali timestamp)
    for col in COLUMNS:
        if col == "timestamp":
            continue

        val = last_row.get(col, 0)
        # Use the global parse_id_numeric which is already robust
        parsed_val = parse_id_numeric(val)

        # For integer columns (komponen_a, komponen_b, etc.), convert to int
        if col in float_cols:
            values[col] = parsed_val
        else:
            values[col] = int(parsed_val)

    return {
        "timestamp": last_row.get("timestamp", None),
        **values,
        "is_complete": True,
    }


def get_latest_complete_row():
    """
    Mendapatkan baris terakhir yang SEMUA kolomnya terisi.
    """
    df = read_all_data()

    if df.empty:
        return None

    component_cols = [
        "komponen_a",
        "komponen_b",
        "komponen_c_batubara",
        "komponen_c_biomassa",
        "komponen_d",
    ]

    # Konversi ke numeric dengan parser yang robust
    for col in component_cols:
        df[col] = df[col].apply(parse_id_numeric)

    # Cari baris yang semua komponen > 0
    complete_mask = (df[component_cols] > 0).all(axis=1)
    complete_rows = df[complete_mask]

    if complete_rows.empty:
        return None

    last_complete = complete_rows.iloc[-1]

    return {
        "timestamp": last_complete["timestamp"],
        "komponen_a": int(last_complete["komponen_a"]),
        "komponen_b": int(last_complete["komponen_b"]),
        "komponen_c_batubara": int(last_complete["komponen_c_batubara"]),
        "komponen_c_biomassa": int(last_complete["komponen_c_biomassa"]),
        "komponen_d": int(last_complete["komponen_d"]),
    }


def get_last_valid_prices():
    """
    Mendapatkan harga terakhir yang valid (> 0) dari data historis.
    Digunakan untuk Smart Auto-Fill saat user input Volume tanpa Harga.
    Returns dict dengan:
    - harga_batubara_rp: float
    - harga_biomassa_rp: float
    """
    df = read_all_data()

    default_prices = {
        "harga_batubara_rp": 1000.0,  # Default fallback jika tidak ada data
        "harga_biomassa_rp": 615.0,  # Default fallback
    }

    if df.empty:
        return default_prices

    # Cek apakah kolom harga ada
    price_cols = ["harga_batubara_rp", "harga_biomassa_rp"]
    for col in price_cols:
        if col not in df.columns:
            continue

        # Parse kolom ke numeric
        df[col] = df[col].apply(parse_id_numeric)

        # Cari nilai terakhir yang > 0
        valid_mask = df[col] > 0
        valid_rows = df.loc[valid_mask, col]

        if not valid_rows.empty:
            default_prices[col] = float(valid_rows.iloc[-1])

    return default_prices


def get_component_status():
    """
    Mendapatkan status pengisian masing-masing komponen.
    """
    current = get_current_period_row()

    return {
        "komponen_a": current["komponen_a"] > 0,
        "komponen_b": current["komponen_b"] > 0,
        "komponen_c_batubara": current["komponen_c_batubara"] > 0,
        "komponen_c_biomassa": current["komponen_c_biomassa"] > 0,
        "komponen_d": current["komponen_d"] > 0,
    }


def update_component(component_name: str, value: int):
    """
    Update nilai satu komponen di Google Sheet.
    Menggunakan gspread langsung untuk reliability.
    """
    worksheet = get_worksheet()
    if worksheet is None:
        st.error("Tidak dapat terhubung ke Google Sheet")
        return False

    try:
        # Ambil semua data
        all_data = worksheet.get_all_values()

        # 1. CEK HEADER (Schema Check)
        # Jika jumlah kolom di sheet lebih sedikit dari skema kode, update header
        if len(all_data) > 0:
            header_row = all_data[0]
            if len(header_row) < len(COLUMNS):
                # Update Header Row (A1)
                worksheet.update("A1", [COLUMNS])
        elif len(all_data) == 0:
            # Jika kosong sama sekali, tulis header
            worksheet.update("A1", [COLUMNS])
            all_data = [COLUMNS]  # Simulate header for next logic

        # Siapkan container baris (sesuai panjang total kolom)
        # Default 0 atau string osong
        if len(all_data) <= 1:
            # Sheet kosong (hanya header), buat baris baru
            col_index = COLUMNS.index(component_name) + 1  # gspread uses 1-based index
            new_row = [get_current_timestamp(), 0, 0, 0, 0, 0]
            new_row[COLUMNS.index(component_name)] = value
            worksheet.append_row(new_row)
            # st.success removed
        else:
            # Update baris terakhir
            last_row_index = len(all_data)  # 1-based index
            col_index = COLUMNS.index(component_name) + 1  # 1-based index

            # Update nilai komponen
            worksheet.update_cell(last_row_index, col_index, value)

            # Update timestamp
            timestamp_col = COLUMNS.index("timestamp") + 1
            worksheet.update_cell(
                last_row_index,
                timestamp_col,
                get_current_timestamp(),
            )

            # st.success removed to avoid double alert in modal

        # Clear cache data agar UI langsung update
        read_all_data.clear()
        # st.cache_resource.clear() # Jangan clear resource connection

        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data: {str(e)}")
        return False


def get_penjualan_value():
    """
    Mendapatkan nilai total Penjualan (kWh) yang akan digunakan model.
    """
    current = get_current_period_row()

    if current["is_complete"]:
        total = (
            current["komponen_a"]
            + current["komponen_b"]
            + current["komponen_c_batubara"]
            + current["komponen_c_biomassa"]
            + current["komponen_d"]
        )
        return {
            "total": total,
            "source": "current",
            "components": {
                "A": current["komponen_a"],
                "B": current["komponen_b"],
                "C_BB": current["komponen_c_batubara"],
                "C_Bio": current["komponen_c_biomassa"],
                "D": current["komponen_d"],
            },
            "is_current_complete": True,
            "timestamp": current["timestamp"],
        }
    else:
        # Gunakan data lengkap terakhir
        last_complete = get_latest_complete_row()

        if last_complete is None:
            return {
                "total": 0,
                "source": "none",
                "components": {
                    "A": 0,
                    "B": 0,
                    "C_BB": 0,
                    "C_Bio": 0,
                    "D": 0,
                },
                "is_current_complete": False,
                "timestamp": None,
            }

        total = (
            last_complete["komponen_a"]
            + last_complete["komponen_b"]
            + last_complete["komponen_c_batubara"]
            + last_complete["komponen_c_biomassa"]
            + last_complete["komponen_d"]
        )
        return {
            "total": total,
            "source": "last_complete",
            "components": {
                "A": last_complete["komponen_a"],
                "B": last_complete["komponen_b"],
                "C_BB": last_complete["komponen_c_batubara"],
                "C_Bio": last_complete["komponen_c_biomassa"],
                "D": last_complete["komponen_d"],
            },
            "is_current_complete": False,
            "timestamp": last_complete["timestamp"],
        }


def delete_current_period_row():
    """
    Menghapus baris terakhir (periode saat ini) dari sheet.
    Digunakan untuk fitur Reset Data.
    """
    worksheet = get_worksheet()
    if worksheet is None:
        return False

    try:
        all_data = worksheet.get_all_values()
        if len(all_data) > 1:
            # Delete last row
            worksheet.delete_rows(len(all_data))
            st.cache_resource.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Gagal mereset data: {str(e)}")
        return False


def update_detailed_row(data_dict: dict):
    """
    Update banyak kolom sekaligus dalam satu baris (Batch Update).
    Digunakan untuk input detail Komponen C (Volume, Harga, dll).
    Memastikan Header Row sinkron dengan COLUMNS.
    """
    worksheet = get_worksheet()
    if worksheet is None:
        st.error("Tidak dapat terhubung ke Google Sheet")
        return False

    try:
        # Ambil semua data
        all_data = worksheet.get_all_values()

        # 1. CEK HEADER (Schema Check)
        if len(all_data) > 0:
            header_row = all_data[0]
            # Jika kolom fisik kurang dari definisi kode, update header
            if len(header_row) < len(COLUMNS):
                worksheet.update("A1", [COLUMNS])
        elif len(all_data) == 0:
            # Kosong total, tulis header
            worksheet.update("A1", [COLUMNS])
            all_data = [COLUMNS]

        # Siapkan container baris
        row_values = [0] * len(COLUMNS)

        # Timestamp update
        timestamp_idx = COLUMNS.index("timestamp")
        row_values[timestamp_idx] = get_current_timestamp()

        target_row_idx = 0

        if len(all_data) > 1:
            # U
            target_row_idx = len(all_data)
            current_row = all_data[-1]

            # Map data lama
            for i, val in enumerate(current_row):
                if i < len(row_values):
                    row_values[i] = val
        else:
            # Row 2 (Baris data pertama)
            target_row_idx = 2

        # Apply Updates
        for key, val in data_dict.items():
            if key in COLUMNS:
                idx = COLUMNS.index(key)
                row_values[idx] = val
            # else: pdate baris terakhir ignore key not in columns

        # Write Row
        range_name = f"A{target_row_idx}"
        worksheet.update(range_name, [row_values])

        # Clear cache
        read_all_data.clear()
        return True

    except Exception as e:
        st.error(f"Gagal update detail: {e}")
        return False
