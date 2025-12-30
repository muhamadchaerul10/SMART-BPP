# -*- coding: utf-8 -*-
"""
Aplikasi Prediksi BPP (Biaya Pokok Produksi)
PT. PLN Indonesia Power Suralaya Unit 8

@author: Mega Bagus Herlambang
"""

# Menyiapkan library
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import sklearn
from sklearn import set_config
import pickle
import plotly.graph_objects as go
import shap
from scipy.stats import gaussian_kde
import tensorflow as tf
import matplotlib.ticker as mtick
import os
from tensorflow.keras.models import load_model
from streamlit_js_eval import streamlit_js_eval
from style import (
    custom_style,
    nilai_kanan,
    garis_pemisah,
    sidebar_footer,
    custom_caption,
    info_card,
)
from config import apply_app_config

# Import handler untuk koneksi Google Sheets (Multi-Divisi Input)
try:
    from gsheet_handler import (
        get_penjualan_value,
        get_component_status,
        update_component,
        get_current_period_row,
        delete_current_period_row,
        update_detailed_row,
        get_last_valid_prices,
    )

    GSHEET_AVAILABLE = True
except Exception as e:
    GSHEET_AVAILABLE = False
    print(f"Warning: Google Sheets tidak tersedia: {e}")


# Menerapkan fungsi apply_app_config
apply_app_config()


# ============ CUSTOM CSS ============
def local_css():
    st.markdown(
        """
        <style>
        .full-width-alert {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            width: 100% !important;
            display: block;
            box-sizing: border-box;
        }
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-warning {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        /* Fix modal content padding to allow full width */
        div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] {
            gap: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


local_css()

# ============ HELPER FORMAT INDONESIA ============
def format_id(num, decimals=0):
    """
    Format angka ke format Indonesia (titik = ribuan, koma = desimal).
    Contoh: 1234567.89 -> "1.234.567,89"
    """
    if num is None:
        return "0"
    try:
        if decimals > 0:
            formatted = f"{num:,.{decimals}f}"
        else:
            formatted = f"{num:,.0f}"
        # Swap , dan . untuk format Indonesia
        # 1,234,567.89 -> 1.234.567,89
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except:
        return str(num)


# ============ HELPER INPUT & PARSING ============
def parse_numeric(val_str):
    """
    Parser angka stabil untuk Google Sheets & input user.
    Aturan utama:
    - 0.xxx  -> DESIMAL
    - x.xxx  -> RIBUAN (jika digit belakang >= 3)
    - 100.000.245 -> RIBUAN
    - Locale ID & EN aman
    """
    if val_str is None or str(val_str).strip() == "":
        return 0.0, None

    s = (
        str(val_str)
        .strip()
        .replace("Rp", "")
        .replace(" ", "")
    )

    if not s or s.lower() == "nan":
        return 0.0, None

    import re

    # ===============================
    # 1️⃣ Validasi karakter
    # ===============================
    if re.search(r"[^\d.,\-]", s):
        illegal = re.findall(r"[^\d.,\-]", s)
        return 0.0, f"Karakter tidak valid: {' '.join(set(illegal))}"

    # ===============================
    # 2️⃣ Normalisasi separator ganda
    # ===============================
    s = re.sub(r"\.+", ".", s)
    s = re.sub(r",+", ",", s)

    try:
        has_dot = "." in s
        has_comma = "," in s

        # ===============================
        # KASUS 1: ADA TITIK & KOMA
        # ===============================
        if has_dot and has_comma:
            # Separator terakhir = desimal
            if s.rfind(".") > s.rfind(","):
                # Format EN: 1,234.56
                return float(s.replace(",", "")), None
            else:
                # Format ID: 1.234,56
                return float(s.replace(".", "").replace(",", ".")), None

        # ===============================
        # KASUS 2: HANYA TITIK
        # ===============================
        if has_dot:
            dot_count = s.count(".")
            left, right = s.split(".", 1)

            # 2.1 kiri = 0 atau -0 → PASTI DESIMAL
            if left == "0" or left == "-0":
                return float(s), None

            # 2.2 lebih dari satu titik → PASTI RIBUAN
            # contoh: 100.000.245
            if dot_count > 1:
                return float(s.replace(".", "")), None

            # 2.3 satu titik
            # digit belakang <= 2 → DESIMAL
            if len(right) <= 2:
                return float(s), None

            # 2.4 digit belakang >= 3 → RIBUAN
            # contoh: 2.915 -> 2915
            return float(s.replace(".", "")), None

        # ===============================
        # KASUS 3: HANYA KOMA
        # ===============================
        if has_comma:
            comma_count = s.count(",")
            left, right = s.split(",", 1)

            # 3.1 kiri = 0 atau -0 → PASTI DESIMAL
            if left == "0" or left == "-0":
                return float(s.replace(",", ".")), None

            # 3.2 lebih dari satu koma → RIBUAN
            if comma_count > 1:
                return float(s.replace(",", "")), None

            # 3.3 satu koma
            # digit belakang <= 2 → DESIMAL
            if len(right) <= 2:
                return float(s.replace(",", ".")), None

            # 3.4 digit belakang >= 3 → RIBUAN
            return float(s.replace(",", "")), None

        # ===============================
        # KASUS 4: ANGKA MURNI
        # ===============================
        return float(s), None

    except ValueError:
        return 0.0, "Gagal memproses angka. Pastikan format benar."







# ============ MODAL DIALOGS UNTUK INPUT KOMPONEN ============


@st.dialog("Rincian Komponen C (Batubara & Biomassa)", width="large")
def modal_detail_komponen_c():
    st.markdown("### 📊 Kalkulasi Beban Bahan Bakar")
    st.caption(
        "Silakan input data volume pemakaian dan harga satuan untuk melakukan simulasi perhitungan biaya."
    )

    # Ambil data eksisting untuk pre-fill
    # Modal selalu terbuka dalam keadaan KOSONG (0).
    # Tidak mengambil data dari database untuk pre-fill.
    # Ambil data eksisting untuk pre-fill (Khusus Koefisien)
    # Modal Volume & Harga selalu kosongan (0).
    # TAPI Koefisien harus tersinkronisasi dengan database.
    current_data = {}
    if GSHEET_AVAILABLE:
        try:
            row = get_current_period_row()
            if row:
                current_data = row
        except:
            pass

    def get_val(key, default=0.0):
        # KHUSUS KOEFISIEN: Ambil dari database jika ada
        if "koef" in key:
            val = current_data.get(key, 0)
            if val and float(val) > 0:
                return float(val)
            return default

        # Volume & Harga: Selalu return 0 (Reset/Kosong)
        return 0.0

    # Helper untuk parsing angka dari text_input (mendukung ribuan . atau ,)
    def parse_float(val_str):
        if not val_str:
            return 0.0
        # Bersihkan spasi dan simbol Rp
        s = str(val_str).strip().replace("Rp", "").replace("RP", "").replace(" ", "")
        try:
            # Jika ada koma, asumsikan format ID (1.000,50)
            if "," in s:
                return float(s.replace(".", "").replace(",", "."))
            # Jika ada lebih dari satu titik, asumsikan format ID ribuan (1.000.000)
            if s.count(".") > 1:
                return float(s.replace(".", ""))
            # Sisa: 1000.5 atau 1000
            return float(s)
        except:
            return 0.0

    # TABS INPUT
    tab_vol, tab_harga, tab_koef = st.tabs(
        ["📦 Data Volume", "💰 Data Harga", "⚙️ Koefisien"]
    )
    errors = []

    with tab_vol:
        col1, col2 = st.columns(2)
        with col1:
            val_vbb = get_val("vol_batubara_kg")
            # Placeholder Logic: Kosongkan jika nilai 0 atau <= 0
            val_vbb_str = f"{val_vbb:,.0f}".replace(",", ".") if val_vbb > 0 else ""

            vol_bb_str = st.text_input(
                "Volume Batubara (Kg)",
                value=val_vbb_str,
                key="v_bb_text",
                placeholder="Contoh: 214.430.602",
                help="💡 Input bebas: bisa pakai/tanpa pemisah ribuan.\n- Contoh: 33232323 atau 33.232.323 → dibaca sama\n- Untuk desimal pakai titik/koma: 214430602.50 atau 214.430.602,50",
            )
            vol_bb, err_vbb = parse_numeric(vol_bb_str)
            if err_vbb:
                st.error(err_vbb)
                errors.append(err_vbb)
            elif vol_bb > 0:
                st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {vol_bb:,.2f} Kg</div>',
                    unsafe_allow_html=True,
                )

        with col2:
            val_vbio = get_val("vol_biomassa_kg")
            # Placeholder Logic: Kosongkan jika nilai 0 atau <= 0
            val_vbio_str = f"{val_vbio:,.0f}".replace(",", ".") if val_vbio > 0 else ""

            vol_bio_str = st.text_input(
                "Volume Biomassa (Kg)",
                value=val_vbio_str,
                key="v_bio_text",
                placeholder="Contoh: 7.267.520",
                help="💡 Input bebas: bisa pakai/tanpa pemisah ribuan.\n- Contoh: 7267520 atau 7.267.520 → dibaca sama\n- Untuk desimal pakai titik/koma: 7267520.75 atau 7.267.520,75",
            )
            vol_bio, err_vbio = parse_numeric(vol_bio_str)
            if err_vbio:
                st.error(err_vbio)
                errors.append(err_vbio)
            elif vol_bio > 0:
                st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {vol_bio:,.2f} Kg</div>',
                    unsafe_allow_html=True,
                )

    with tab_harga:
        col1, col2 = st.columns(2)
        with col1:
            val_hbb = get_val("harga_batubara_rp")
            # Jika nilainya sangat kecil (< 10), anggap belum diisi -> tampilkan kosong
            val_hbb_fmt = (
                f"{val_hbb:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                if val_hbb >= 10
                else ""
            )
            harga_bb_str = st.text_input(
                "Harga Batubara (Rp/Kg)",
                value=val_hbb_fmt,
                key="h_bb_text",
                placeholder="Contoh: 1.023,82",
                help="💡 Input bebas: bisa pakai/tanpa pemisah ribuan.\n- Untuk desimal pakai titik/koma: 1023.82 atau 1.023,82",
            )
            harga_bb, err_hbb = parse_numeric(harga_bb_str)
            if err_hbb:
                st.error(err_hbb)
                errors.append(err_hbb)
            elif harga_bb > 0:
                st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: Rp {harga_bb:,.2f}</div>',
                    unsafe_allow_html=True,
                )

        with col2:
            val_hbio = get_val("harga_biomassa_rp")
            val_hbio_fmt = (
                f"{val_hbio:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                if val_hbio >= 10
                else ""
            )
            harga_bio_str = st.text_input(
                "Harga Biomassa (Rp/Kg)",
                value=val_hbio_fmt,
                key="h_bio_text",
                placeholder="Contoh: 605,84",
                help="💡 Input bebas: bisa pakai/tanpa pemisah ribuan.\n- Untuk desimal pakai titik/koma: 605.84 atau 605,84",
            )
            harga_bio, err_hbio = parse_numeric(harga_bio_str)
            if err_hbio:
                st.error(err_hbio)
                errors.append(err_hbio)
            elif harga_bio > 0:
                st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: Rp {harga_bio:,.2f}</div>',
                    unsafe_allow_html=True,
                )

    with tab_koef:
        st.caption(
            "Nilai koefisien default disesuaikan dengan data historis. Anda dapat mengubahnya jika diperlukan."
        )
        coef_bb = 0.99558
        coef_bio = 0.00442
        col1, col2 = st.columns(2)
        with col1:
            val_kbb = get_val("koef_batubara", coef_bb)
            # Default fallback jika 0
            if val_kbb <= 0:
                val_kbb = coef_bb

            koef_bb = st.number_input(
                "Koefisien Batubara",
                value=float(val_kbb),
                format="%.5f",
                step=0.00001,
                help=f"Faktor pengali untuk Batubara (Default: {coef_bb})",
            )

        with col2:
            val_kbio = get_val("koef_biomassa", coef_bio)
            # Default fallback jika 0
            if val_kbio <= 0:
                val_kbio = coef_bio

            koef_bio = st.number_input(
                "Koefisien Biomassa",
                value=float(val_kbio),
                format="%.5f",
                step=0.00001,
                help=f"Faktor pengali untuk Biomassa (Default: {coef_bio})",
            )

    # ============ SMART AUTO-FILL LAST PRICE ============
    # Jika Volume > 0 tapi Harga = 0, ambil harga terakhir yang valid dari database
    autofill_alerts = []
    if GSHEET_AVAILABLE:
        last_prices = get_last_valid_prices()

        # Batubara: Cek apakah perlu auto-fill
        if vol_bb > 0 and harga_bb <= 0:
            harga_bb = last_prices.get("harga_batubara_rp", 1000.0)
            autofill_alerts.append(
                f"⚠️ Harga Batubara belum diisi. Menggunakan harga referensi: **Rp {harga_bb:,.2f}/Kg**"
            )

        # Biomassa: Cek apakah perlu auto-fill
        if vol_bio > 0 and harga_bio <= 0:
            harga_bio = last_prices.get("harga_biomassa_rp", 615.0)
            autofill_alerts.append(
                f"⚠️ Harga Biomassa belum diisi. Menggunakan harga referensi: **Rp {harga_bio:,.2f}/Kg**"
            )

    # Tampilkan Alert Auto-Fill jika ada
    if autofill_alerts:
        for alert in autofill_alerts:
            st.warning(alert)

    # LOGIKA PERHITUNGAN
    st.divider()

    # Rumus : Volume x Harga x Koefisien

    comp_c_bb = vol_bb * harga_bb * koef_bb
    comp_c_bio = vol_bio * harga_bio * koef_bio

    total_tagihan = comp_c_bb + comp_c_bio

    # TAMPILKAN HASIL
    st.markdown("#### 📊 Hasil Perhitungan")

    # TAMPILKAN RUMUS UNTUK TRANSPARANSI
    formula_html = f"""
    <div style="background: #fef3c7; padding: 12px 16px; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
        <div style="font-size: 13px; color: #92400e; font-weight: 600; margin-bottom: 8px;">📐 Rumus Perhitungan:</div>
        <div style="font-size: 12px; color: #78350f; font-family: monospace; line-height: 1.6;">
            <b>Batubara:</b> {vol_bb:,.0f} Kg × Rp {harga_bb:,.2f} × {koef_bb:.5f} = <b style="color:#166534">Rp {comp_c_bb:,.0f}</b><br/>
            <b>Biomassa:</b> {vol_bio:,.0f} Kg × Rp {harga_bio:,.2f} × {koef_bio:.5f} = <b style="color:#166534">Rp {comp_c_bio:,.0f}</b>
        </div>
    </div>
    """
    st.markdown(formula_html, unsafe_allow_html=True)

    # TAMPILKAN HASIL DENGAN CUSTOM HTML (Biar tidak terpotong untuk angka besar)
    html_result = f"""
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <div style="flex: 1; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 150px;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Komponen C Batubara</div>
            <div style="font-size: 15px; color: #0f172a; font-weight: 700; word-break: break-all;">Rp {comp_c_bb:,.0f}</div>
        </div>
        <div style="flex: 1; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 150px;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Komponen C Biomassa</div>
            <div style="font-size: 15px; color: #0f172a; font-weight: 700; word-break: break-all;">Rp {comp_c_bio:,.0f}</div>
        </div>
        <div style="flex: 1; background: #ecfeff; padding: 12px; border-radius: 8px; border: 1px solid #a5f3fc; min-width: 150px;">
            <div style="font-size: 11px; color: #0891b2; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Total Tagihan</div>
            <div style="font-size: 15px; color: #0e7490; font-weight: 700; word-break: break-all;">Rp {total_tagihan:,.0f}</div>
        </div>
    </div>
    <div style="margin-bottom: 15px; font-size: 12px; color: #64748b; font-style: italic;">
        ℹ️ <b>Catatan:</b> Menekan tombol <b>Simpan</b> akan memperbarui nilai <b>Beban Batubara</b> & <b>Beban Biomassa</b> pada halaman utama sesuai hasil di atas.
    </div>
    """
    st.markdown(html_result, unsafe_allow_html=True)

    if st.button(
        "💾 Simpan & Update Dashboard",
        type="primary",
        use_container_width=True,
        disabled=len(errors) > 0,
    ):
        if GSHEET_AVAILABLE:
            # Siapkan payload
            payload = {
                # Hasil Hitungan Utama
                "komponen_c_batubara": int(comp_c_bb),
                "komponen_c_biomassa": int(comp_c_bio),
                # Detail Input untuk Audit
                "vol_batubara_kg": vol_bb,
                "vol_biomassa_kg": vol_bio,
                "harga_batubara_rp": harga_bb,
                "harga_biomassa_rp": harga_bio,
                "koef_batubara": koef_bb,
                "koef_biomassa": koef_bio,
                # Legacy params (diset 0 atau default agar tidak error di schema)
                "hhv_batubara": 0,
                "hhv_biomassa": 0,
                "eio_val": 0,
            }

            with st.spinner("Menyimpan data..."):
                if update_detailed_row(payload):
                    # Set session state untuk update sidebar number_input
                    st.session_state["b_batubara"] = int(comp_c_bb)
                    st.session_state["b_biomassa"] = int(comp_c_bio)

                    # Set alert (tanpa emoji karena st.toast sudah ada icon)
                    st.session_state.app_alert = {
                        "type": "success",
                        "msg": "Komponen C (Batubara & Biomassa) berhasil disimpan!",
                    }

                    # Clear SEMUA cache data agar GSheet terbaca ulang
                    st.cache_data.clear()

                    st.rerun()
                else:
                    st.error("Gagal menyimpan ke database.")
        else:
            st.error("Google Sheets tidak terhubung.")


@st.dialog("📊 Input Komponen A", width="large")
def modal_komponen_a():
    """
    Modal dialog untuk input Komponen A (Investasi/Fixed Cost).
    Rumus: Harga Komponen A × Daya Netto × EAF A × (Hari Bulan / Hari Tahun)
    """
    st.write("Masukkan nilai Komponen A untuk periode ini.")

    # Ambil nilai saat ini dari Google Sheets
    try:
        current = get_current_period_row()
        current_value_a = int(current.get("komponen_a", 0))
        current_value_price_a = int(current.get("price_a", 0))
        current_value_eaf_a = float(current.get("eaf_a", 0))
        current_value_daya_netto = int(current.get("daya_netto", 0))
        current_value_jum_hari_bln = int(current.get("jum_hari_bln", 0))
        current_value_jum_hari_thn = int(current.get("jum_hari_thn", 0))
    except:
        current_value_a = 0
        current_value_price_a = 0
        current_value_eaf_a = 0
        current_value_daya_netto = 0
        current_value_jum_hari_bln = 30
        current_value_jum_hari_thn = 365
    
    if current_value_jum_hari_bln==0:
        current_value_jum_hari_bln = 30
    if current_value_jum_hari_thn==0:
        current_value_jum_hari_thn = 365
    
    # Mengisikan nilai harga dan eaf komponen A serta daya netto
    col1, col2 = st.columns(2)
    with col1:
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        val_price_a_fmt = f"{current_value_price_a:,.0f}".replace(",", ".")
        price_a_str = st.text_input(
            "Pricing Komponen A (Rp/kW-Tahun)",
            value = val_price_a_fmt if current_value_price_a > 0 else "",
            placeholder = "Contoh: 1.939.201",
            key = "input_modal_a_1",
            help = "Tips: Anda bisa memasukkan angka dengan titik pemisah ribuan agar lebih mudah terbaca.",
        )

        # Parse nilai menggunakan helper robust
        price_a, error_msg = parse_numeric(price_a_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if price_a >= 0 and not error_msg:
            st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: Rp {format_id(price_a, 0)}</div>',
                unsafe_allow_html=True,
            )
        
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        daya_netto_fmt = f"{current_value_daya_netto:,.0f}".replace(",", ".")
        daya_netto_str = st.text_input(
            "Daya Mampu Netto (kW)",
            value = daya_netto_fmt if current_value_daya_netto > 0 else "",
            placeholder = "Contoh: 540.000",
            key = "input_modal_a_3",
            help = "💡 Kapasitas daya pembangkit dalam kiloWatt.\n- Contoh: 625.000 kW = 625 MW.",
        )

        # Parse nilai menggunakan helper robust
        daya_netto, error_msg = parse_numeric(daya_netto_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if daya_netto >= 0 and not error_msg:
            st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(daya_netto, 0)} kW</div>',
                unsafe_allow_html=True,
                )
        
    
    with col2:
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        eaf_a_fmt = f"{current_value_eaf_a}".replace(",", ".")
        eaf_a_str = st.text_input(
            "EAF Komponen A",
            value = eaf_a_fmt if current_value_eaf_a > 0 else "",
            placeholder = "Contoh: 0.843",
            key = "input_modal_a_2",
            help = "💡 Equivalent Availability Factor (0-1).\n- Nilai EAF menunjukkan ketersediaan unit pembangkit.\n- Contoh: 0,84830 = 84,83% ketersediaan.",
        )

        # Parse nilai menggunakan helper robust
        eaf_a, error_msg = parse_numeric(eaf_a_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if eaf_a >= 0 and not error_msg:
            st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(eaf_a, 3)}</div>',
                unsafe_allow_html=True,
                )
    
        # Mengisikan nilai jumlah hari dalam bulan dan tahun yang dimaksud
        kiri, kanan = st.columns(2)
        with kiri:
            # Gunakan text_input untuk angka besar agar lebih fleksibel
            jum_hari_bln_fmt = f"{current_value_jum_hari_bln:,.0f}".replace(",", ".")
            jum_hari_bln_str = st.text_input(
                "Jumlah hari dalam bulan dimaksud",
                value = jum_hari_bln_fmt if current_value_jum_hari_bln > 0 else "",
                placeholder = "Contoh: 30",
                key = "input_modal_a_4",
                help = "Tips: Masukkan antara 28,29,30 atau 31",
            )

            # Parse nilai menggunakan helper robust
            jum_hari_bln, error_msg = parse_numeric(jum_hari_bln_str)

            if error_msg:
                st.error(error_msg)

            # Tampilkan preview format yang SANGAT JELAS
            if jum_hari_bln >= 0 and not error_msg:
                st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(jum_hari_bln, 0)}</div>',
                unsafe_allow_html=True,
                )
        
        with kanan:
            # Gunakan text_input untuk angka besar agar lebih fleksibel
            jum_hari_thn_fmt = f"{current_value_jum_hari_thn}".replace(",", ".")
            jum_hari_thn_str = st.text_input(
                "Jumlah hari dalam tahun dimaksud",
                value = jum_hari_thn_fmt if current_value_jum_hari_thn > 0 else "",
                placeholder = "Contoh: 365",
                key = "input_modal_a_5",
                help = "Tips: Masukkan jumlah hari dalam 1 tahun (normalnya 365 hari)",
            )

            # Parse nilai menggunakan helper robust
            jum_hari_thn, error_msg = parse_numeric(jum_hari_thn_str)

            if error_msg:
                st.error(error_msg)

            # Tampilkan preview format yang SANGAT JELAS
            if jum_hari_thn >= 0 and not error_msg:
                st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(jum_hari_thn, 0)}</div>',
                unsafe_allow_html=True,
                )
    
    
    
    komponen_a = price_a*eaf_a*daya_netto*(jum_hari_bln/jum_hari_thn)
    
    # TAMPILKAN HASIL
    st.markdown("#### 📊 Hasil Perhitungan")

    # TAMPILKAN RUMUS UNTUK TRANSPARANSI
    formula_html = f"""
    <div style="background: #fef3c7; padding: 12px 16px; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
        <div style="font-size: 13px; color: #92400e; font-weight: 600; margin-bottom: 8px;">📐 Rumus Perhitungan:</div>
        <div style="font-size: 12px; color: #78350f; font-family: monospace; line-height: 1.6;">
            <b>Komponen A:</b> Rp {price_a:,.0f} × {eaf_a:,.2f} × {daya_netto:.0f} kW x ({jum_hari_bln:,.0f}/{jum_hari_thn:,.0f})  = <b style="color:#166534"> {komponen_a:,.0f}</b><br/>
        </div>
    </div>
    """
    st.markdown(formula_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "💾 Simpan",
            use_container_width=True,
            type="primary",
            key="save_a",
            disabled=(error_msg is not None),
        ):
        
            if GSHEET_AVAILABLE:
                # Siapkan payload
                payload = {
                    # Hasil Hitungan Utama
                    "price_a": int(price_a),
                    "eaf_a": eaf_a,
                    "daya_netto": daya_netto,
                    "jum_hari_bln": jum_hari_bln,
                    "jum_hari_thn": jum_hari_thn,
                    "komponen_a": komponen_a
                }

                with st.spinner("Menyimpan data..."):
                    if update_detailed_row(payload):

                        # Set alert (tanpa emoji karena st.toast sudah ada icon)
                        st.session_state.app_alert = {
                            "type": "success",
                            "msg": "Komponen A berhasil disimpan!",
                        }

                        # Clear SEMUA cache data agar GSheet terbaca ulang
                        st.cache_data.clear()

                        st.rerun()
                    else:
                        st.error("Gagal menyimpan ke database.")

    with col2:
        if st.button("❌ Batal", use_container_width=True, key="cancel_a"):
            st.rerun()


@st.dialog("📊 Input Komponen B", width="large")
def modal_komponen_b():
    """
    Modal dialog untuk input Komponen B (Fixed O&M).
    Rumus: Harga Komponen B × Daya Netto × EAF B × (Hari Bulan / Hari Tahun)
    """
    st.write("Masukkan nilai Komponen B untuk periode ini.")
    # Caption removed

    # Ambil nilai saat ini dari Google Sheets
    try:
        current = get_current_period_row()
        current_value_b = int(current.get("komponen_b", 0))
        current_value_price_b = int(current.get("price_b", 0))
        current_value_eaf_b = float(current.get("eaf_b", 0))
        current_value_daya_netto = int(current.get("daya_netto", 0))
        current_value_jum_hari_bln = int(current.get("jum_hari_bln", 0))
        current_value_jum_hari_thn = int(current.get("jum_hari_thn", 0))
    except:
        current_value_b = 0
        current_value_price_b = 0
        current_value_eaf_b = 0
        current_value_daya_netto = 0
        current_value_jum_hari_bln = 30
        current_value_jum_hari_thn = 365
    
    if current_value_jum_hari_bln==0:
        current_value_jum_hari_bln = 30
    if current_value_jum_hari_thn==0:
        current_value_jum_hari_thn = 365
    
    # Mengisikan nilai harga dan eaf komponen A serta daya netto
    col1, col2 = st.columns(2)
    with col1:
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        val_price_b_fmt = f"{current_value_price_b:,.0f}".replace(",", ".")
        price_b_str = st.text_input(
            "Pricing Komponen B (Rp/kW-Tahun)",
            value = val_price_b_fmt if current_value_price_b > 0 else "",
            placeholder = "Contoh: 890.000",
            key = "input_modal_b_1",
            help = "Tips: Anda bisa memasukkan angka dengan titik pemisah ribuan agar lebih mudah terbaca.",
        )

        # Parse nilai menggunakan helper robust
        price_b, error_msg = parse_numeric(price_b_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if price_b >= 0 and not error_msg:
            st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: Rp {format_id(price_b, 0)}</div>',
                unsafe_allow_html=True,
            )

        # Gunakan text_input untuk angka besar agar lebih fleksibel
        daya_netto_fmt = f"{current_value_daya_netto:,.0f}".replace(",", ".")
        daya_netto_str = st.text_input(
            "Daya Mampu Netto (kW)",
            value = daya_netto_fmt if current_value_daya_netto > 0 else "",
            placeholder = "Contoh: 540.000",
            key = "input_modal_b_3",
            help = "💡 Kapasitas daya pembangkit dalam kiloWatt.\n- Contoh: 625.000 kW = 625 MW.",
        )

        # Parse nilai menggunakan helper robust
        daya_netto, error_msg = parse_numeric(daya_netto_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if daya_netto >= 0 and not error_msg:
            st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(daya_netto, 0)}</div>',
                unsafe_allow_html=True,
            )

    
    with col2:
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        eaf_b_fmt = f"{current_value_eaf_b}".replace(",", ".")
        eaf_b_str = st.text_input(
            "EAF Komponen B",
            value = eaf_b_fmt if current_value_eaf_b > 0 else "",
            placeholder = "Contoh: 0.929",
            key = "input_modal_b_2",
            help = "Tips: Anda bisa memasukkan angka dengan titik pemisah ribuan agar lebih mudah terbaca.",
        )

        # Parse nilai menggunakan helper robust
        eaf_b, error_msg = parse_numeric(eaf_b_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if eaf_b >= 0 and not error_msg:
            st.markdown(
                f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(eaf_b, 3)}</div>',
                unsafe_allow_html=True,
            )
    

        # Mengisikan nilai jumlah hari dalam bulan dan tahun yang dimaksud
        kiri, kanan = st.columns(2)
        with kiri:
            # Gunakan text_input untuk angka besar agar lebih fleksibel
            jum_hari_bln_fmt = f"{current_value_jum_hari_bln:,.0f}".replace(",", ".")
            jum_hari_bln_str = st.text_input(
                "Jumlah hari dalam bulan dimaksud",
                value = jum_hari_bln_fmt if current_value_jum_hari_bln > 0 else "",
                placeholder = "Contoh: 30",
                key = "input_modal_b_4",
                help = "Tips: Masukkan antara 28,29,30 atau 31",
            )

            # Parse nilai menggunakan helper robust
            jum_hari_bln, error_msg = parse_numeric(jum_hari_bln_str)

            if error_msg:
                st.error(error_msg)

            # Tampilkan preview format yang SANGAT JELAS
            if jum_hari_bln >= 0 and not error_msg:
                st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(jum_hari_bln, 0)}</div>',
                    unsafe_allow_html=True,
                )
        
        with kanan:
            # Gunakan text_input untuk angka besar agar lebih fleksibel
            jum_hari_thn_fmt = f"{current_value_jum_hari_thn}".replace(",", ".")
            jum_hari_thn_str = st.text_input(
                "Jumlah hari dalam tahun dimaksud",
                value = jum_hari_thn_fmt if current_value_jum_hari_thn > 0 else "",
                placeholder = "Contoh: 365",
                key = "input_modal_b_5",
                help = "Tips: Masukkan jumlah hari dalam 1 tahun (normalnya 365 hari)",
            )

            # Parse nilai menggunakan helper robust
            jum_hari_thn, error_msg = parse_numeric(jum_hari_thn_str)

            if error_msg:
                st.error(error_msg)

            # Tampilkan preview format yang SANGAT JELAS
            if jum_hari_thn >= 0 and not error_msg:
                st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(jum_hari_thn, 0)}</div>',
                    unsafe_allow_html=True,
                )
    
    komponen_b = price_b*eaf_b*daya_netto*(jum_hari_bln/jum_hari_thn)
    
    # TAMPILKAN HASIL
    st.markdown("#### 📊 Hasil Perhitungan")

    # TAMPILKAN RUMUS UNTUK TRANSPARANSI
    formula_html = f"""
    <div style="background: #fef3c7; padding: 12px 16px; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
        <div style="font-size: 13px; color: #92400e; font-weight: 600; margin-bottom: 8px;">📐 Rumus Perhitungan:</div>
        <div style="font-size: 12px; color: #78350f; font-family: monospace; line-height: 1.6;">
            <b>Komponen A:</b> Rp {price_b:,.0f} × {eaf_b:,.2f} × {daya_netto:.0f} kW x ({jum_hari_bln:,.0f}/{jum_hari_thn:,.0f})  = <b style="color:#166534"> {komponen_b:,.0f}</b><br/>
        </div>
    </div>
    """
    st.markdown(formula_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "💾 Simpan",
            use_container_width=True,
            type="primary",
            key="save_b",
            disabled=(error_msg is not None),
        ):
        
            if GSHEET_AVAILABLE:
                # Siapkan payload
                payload = {
                    # Hasil Hitungan Utama
                    "price_b": int(price_b),
                    "eaf_b": eaf_b,
                    "daya_netto": daya_netto,
                    "jum_hari_bln": jum_hari_bln,
                    "jum_hari_thn": jum_hari_thn,
                    "komponen_b": komponen_b
                }

                with st.spinner("Menyimpan data..."):
                    if update_detailed_row(payload):

                        # Set alert (tanpa emoji karena st.toast sudah ada icon)
                        st.session_state.app_alert = {
                            "type": "success",
                            "msg": "Komponen B berhasil disimpan!",
                        }

                        # Clear SEMUA cache data agar GSheet terbaca ulang
                        st.cache_data.clear()

                        st.rerun()
                    else:
                        st.error("Gagal menyimpan ke database.")

    with col2:
        if st.button("❌ Batal", use_container_width=True, key="cancel_b"):
            st.rerun()


@st.dialog("📊 Komponen C - Batubara (Lihat Nilai)", width="large")
def modal_komponen_c_batubara():
    """Modal dialog untuk MELIHAT Komponen C Batubara (Read-Only)."""

    try:
        current = get_current_period_row()
        current_value = int(current.get("komponen_c_batubara", 0))
        # Ambil data detail untuk formula display
        vol_bb = float(current.get("vol_batubara_kg", 0))
        harga_bb = float(current.get("harga_batubara_rp", 0))
        koef_bb = float(current.get("koef_batubara", 0.99558)) or 0.99558
    except:
        current_value = 0
        vol_bb = 0
        harga_bb = 0
        koef_bb = 0.99558

    # INFO ALERT - FORMAL
    st.info(
        "**Nilai Komponen C (Batubara) dihitung otomatis** dari Input Detail Komponen C. "
        "Untuk mengubah nilai ini, silakan gunakan tombol **'🧮 Input Detail Komponen C'** di bagian atas sidebar.",
        icon="ℹ️",
    )

    # TAMPILKAN FORMULA
    st.markdown("#### 📐 Rumus Perhitungan")
    formula_html = f"""
    <div style="background: #fef3c7; padding: 12px 16px; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
        <div style="font-size: 12px; color: #78350f; font-family: monospace; line-height: 1.8;">
            <b>Volume:</b> {vol_bb:,.0f} Kg<br/>
            <b>Harga Satuan:</b> Rp {harga_bb:,.2f} /Kg<br/>
            <b>Koefisien:</b> {koef_bb:.5f}<br/>
            <hr style="border-color: #f59e0b; margin: 8px 0;"/>
            <b>Perhitungan:</b> {vol_bb:,.0f} × {harga_bb:,.2f} × {koef_bb:.5f}<br/>
            <span style="font-size: 14px;"><b>= Rp {vol_bb * harga_bb * koef_bb:,.0f}</b></span>
        </div>
    </div>
    """
    st.markdown(formula_html, unsafe_allow_html=True)

    # TAMPILKAN NILAI TERSIMPAN
    st.markdown("#### 💰 Nilai Tersimpan di Database")
    nilai_html = f"""
    <div style="background: #ecfeff; padding: 15px; border-radius: 8px; border: 2px solid #0891b2; text-align: center;">
        <div style="font-size: 12px; color: #0891b2; font-weight: 600; margin-bottom: 5px;">KOMPONEN C BATUBARA</div>
        <div style="font-size: 22px; color: #0e7490; font-weight: 700;">Rp {current_value:,.0f}</div>
    </div>
    """
    st.markdown(nilai_html, unsafe_allow_html=True)

    st.write("")
    if st.button("✅ Tutup", use_container_width=True, type="primary"):
        st.rerun()


@st.dialog("📊 Komponen C - Biomassa (Lihat Nilai)", width="large")
def modal_komponen_c_biomassa():
    """Modal dialog untuk MELIHAT Komponen C Biomassa (Read-Only)."""

    try:
        current = get_current_period_row()
        current_value = int(current.get("komponen_c_biomassa", 0))
        # Ambil data detail untuk formula display
        vol_bio = float(current.get("vol_biomassa_kg", 0))
        harga_bio = float(current.get("harga_biomassa_rp", 0))
        koef_bio = float(current.get("koef_biomassa", 0.00442)) or 0.00442
    except:
        current_value = 0
        vol_bio = 0
        harga_bio = 0
        koef_bio = 0.00442

    # INFO ALERT - FORMAL
    st.info(
        "**Nilai Komponen C (Biomassa) dihitung otomatis** dari Input Detail Komponen C. "
        "Untuk mengubah nilai ini, silakan gunakan tombol **'🧮 Input Detail Komponen C'** di bagian atas sidebar.",
        icon="ℹ️",
    )

    # TAMPILKAN FORMULA
    st.markdown("#### 📐 Rumus Perhitungan")
    formula_html = f"""
    <div style="background: #fef3c7; padding: 12px 16px; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
        <div style="font-size: 12px; color: #78350f; font-family: monospace; line-height: 1.8;">
            <b>Volume:</b> {vol_bio:,.0f} Kg<br/>
            <b>Harga Satuan:</b> Rp {harga_bio:,.2f} /Kg<br/>
            <b>Koefisien:</b> {koef_bio:.5f}<br/>
            <hr style="border-color: #f59e0b; margin: 8px 0;"/>
            <b>Perhitungan:</b> {vol_bio:,.0f} × {harga_bio:,.2f} × {koef_bio:.5f}<br/>
            <span style="font-size: 14px;"><b>= Rp {vol_bio * harga_bio * koef_bio:,.0f}</b></span>
        </div>
    </div>
    """
    st.markdown(formula_html, unsafe_allow_html=True)

    # TAMPILKAN NILAI TERSIMPAN
    st.markdown("#### 💰 Nilai Tersimpan di Database")
    nilai_html = f"""
    <div style="background: #ecfeff; padding: 15px; border-radius: 8px; border: 2px solid #0891b2; text-align: center;">
        <div style="font-size: 12px; color: #0891b2; font-weight: 600; margin-bottom: 5px;">KOMPONEN C BIOMASSA</div>
        <div style="font-size: 22px; color: #0e7490; font-weight: 700;">Rp {current_value:,.0f}</div>
    </div>
    """
    st.markdown(nilai_html, unsafe_allow_html=True)

    st.write("")
    if st.button("✅ Tutup", use_container_width=True, type="primary"):
        st.rerun()


@st.dialog("📊 Input Komponen D", width="large")
def modal_komponen_d():
    """Modal dialog untuk input Komponen D (Variable O&M)."""
    st.write("Masukkan nilai Komponen D untuk periode ini.")

    # Ambil nilai saat ini dari Google Sheets
    try:
        current = get_current_period_row()
        current_value_d = int(current.get("komponen_d", 0))
        current_value_price_d = float(current.get("price_d", 0))
        current_value_kwh_export = int(current.get("kwh_export", 0))
    except:
        current_value_d = 0
        current_value_price_d = 0
        current_value_kwh_export = 0
    
    # Mengisikan nilai harga dan eaf komponen A serta daya netto
    col1, col2 = st.columns(2)
    with col1:
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        val_price_d_fmt = f"{current_value_price_d:,.2f}".replace(",", ".")
        price_d_str = st.text_input(
            "Pricing Komponen D (Rp/kWh)",
            value = val_price_d_fmt if current_value_price_d > 0 else "",
            placeholder = "Contoh: 2.19",
            key = "input_modal_d_1",
            help = "Masukkan nilai price komponen d",
        )

        # Parse nilai menggunakan helper robust
        price_d, error_msg = parse_numeric(price_d_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if price_d >= 0 and not error_msg:
            st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(price_d, 2)}</div>',
                    unsafe_allow_html=True,
                )
    
    with col2:
        # Gunakan text_input untuk angka besar agar lebih fleksibel
        kwh_export_fmt = f"{current_value_kwh_export}".replace(",", ".")
        kwh_export_str = st.text_input(
            "KWh Produksi Export",
            value = kwh_export_fmt if current_value_kwh_export > 0 else "",
            placeholder = "Contoh: 311.000.000 kWh",
            key = "input_modal_d_2",
            help = "Tips: Anda bisa memasukkan angka dengan titik pemisah ribuan agar lebih mudah terbaca.",
        )

        # Parse nilai menggunakan helper robust
        kwh_export, error_msg = parse_numeric(kwh_export_str)

        if error_msg:
            st.error(error_msg)

        # Tampilkan preview format yang SANGAT JELAS
        if kwh_export >= 0 and not error_msg:
            st.markdown(
                    f'<div style="color: #0284c7; font-size: 0.85rem; font-weight: 600; margin-top: -10px;">✅ Terbaca: {format_id(kwh_export, 0)} kWh</div>',
                    unsafe_allow_html=True,
                )
    
    komponen_d = price_d*kwh_export
    
    # TAMPILKAN HASIL
    st.markdown("#### 📊 Hasil Perhitungan")

    # TAMPILKAN RUMUS UNTUK TRANSPARANSI
    formula_html = f"""
    <div style="background: #fef3c7; padding: 12px 16px; border-radius: 8px; border: 1px solid #f59e0b; margin-bottom: 15px;">
        <div style="font-size: 13px; color: #92400e; font-weight: 600; margin-bottom: 8px;">📐 Rumus Perhitungan:</div>
        <div style="font-size: 12px; color: #78350f; font-family: monospace; line-height: 1.6;">
            <b>Komponen A:</b> Rp {price_d:,.2f} × {kwh_export:,.0f} = <b style="color:#166534"> {komponen_d:,.0f}</b><br/>
        </div>
    </div>
    """
    st.markdown(formula_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "💾 Simpan",
            use_container_width=True,
            type="primary",
            key="save_d",
            disabled=(error_msg is not None),
        ):
        
            if GSHEET_AVAILABLE:
                # Siapkan payload
                payload = {
                    # Hasil Hitungan Utama
                    "price_d": price_d,
                    "kwh_export": kwh_export,
                    "komponen_d": komponen_d
                }

                with st.spinner("Menyimpan data..."):
                    if update_detailed_row(payload):

                        # Set alert (tanpa emoji karena st.toast sudah ada icon)
                        st.session_state.app_alert = {
                            "type": "success",
                            "msg": "Komponen D berhasil disimpan!",
                        }

                        # Clear SEMUA cache data agar GSheet terbaca ulang
                        st.cache_data.clear()

                        st.rerun()
                    else:
                        st.error("Gagal menyimpan ke database.")

    with col2:
        if st.button("❌ Batal", use_container_width=True, key="cancel_d"):
            st.rerun()


@st.dialog("⚠️ Reset Data", width="small")
def modal_reset_data():
    """Modal konfirmasi reset data kembali ke 0."""
    st.warning("Apakah Anda yakin ingin mereset data ke awal?")
    st.write("Data input manual akan dihapus dan kembali ke nilai default sistem.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "✅ Ya, Reset",
            use_container_width=True,
            type="primary",
            key="confirm_reset",
        ):
            with st.spinner("Mereset data..."):
                # Reset logic: Hapus baris row saat ini
                if delete_current_period_row():
                    st.session_state.app_alert = {
                        "type": "success",
                        "msg": "Data direset ke default!",
                    }
                else:
                    st.session_state.app_alert = {
                        "type": "warning",
                        "msg": "Tidak ada data untuk direset.",
                    }

                st.cache_data.clear()
                st.rerun()
    with col2:
        if st.button("❌ Batal", use_container_width=True, key="cancel_reset"):
            st.rerun()


# ============ PERSISTENSI TEMA ============
# Data Loading
link_file_tampilan = "https://docs.google.com/spreadsheets/d/16hZccWcjepE-Ac9Qd-9kBpJiJ8zhu2ON/export?format=csv"
link_file = "https://docs.google.com/spreadsheets/d/16hZccWcjepE-Ac9Qd-9kBpJiJ8zhu2ON/export?format=xlsx"
df_tampilan = pd.read_csv(link_file_tampilan)
df = pd.read_excel(link_file)
df_selain_bulan = df.drop("Bulan", axis=1)

# Mengaktifkan style
custom_style()

# ============ WARNA ADAPTIF UNTUK BOX (Netral - Bekerja di Light & Dark) ============
# Warna ini dipilih agar kontras baik di kedua mode tema Streamlit
BOX_BG = "rgba(14, 165, 233, 0.1)"  # Transparan dengan hint biru
BOX_BORDER = "1px solid rgba(14, 165, 233, 0.3)"
BOX_SHADOW = "0 4px 20px rgba(0, 0, 0, 0.1)"
TITLE_COLOR = "#0ea5e9"  # Sky blue - kontras di kedua tema
LABEL_COLOR_1 = "#06b6d4"  # Cyan
LABEL_COLOR_2 = "#ec4899"  # Pink
TEXT_COLOR = "inherit"  # Ikut warna teks Streamlit native
SUBTEXT_COLOR = "inherit"
RUMUS_BG = "rgba(14, 165, 233, 0.1)"
RUMUS_TEXT = "inherit"


# Menentukan nilai indeks awal
n_awal = 5

# Nilai akurasi model
akurasi_keras = 94.40
akurasi_elastic = 93.88
akurasi_ridge = 93.16
akurasi_knn = 92.04


# Nilai error model
error_keras = 63.14
error_elastic = 68.52
error_ridge = 73.91
error_knn = 85.59


# Membuka model
modelku_elastic = pickle.load(open("model_bpp_elastic.pkl", "rb"))
modelku_ridge = pickle.load(open("model_bpp_ridge.pkl", "rb"))
modelku_knn = pickle.load(open("model_bpp_knn.pkl", "rb"))
modelku_keras = load_model("model_bpp.keras")


# Membuka scaler khusus untuk model keras
tf.keras.utils.set_random_seed(0)
scaler = pickle.load(open("preprocess_bpp_columntransformer.pkl", "rb"))


# Membuka explainer shap
shap_values_keras = pickle.load(open("shap_values_keras.pkl", "rb"))
shap_values_elastic = pickle.load(open("shap_values_elastic.pkl", "rb"))
shap_values_ridge = pickle.load(open("shap_values_ridge.pkl", "rb"))
shap_values_knn = pickle.load(open("shap_values_knn.pkl", "rb"))


# Bagian Judul Halaman Utama
st.title("⚡ Aplikasi Simulasi BPP (Biaya Pokok Produksi)")
st.caption(
    "Alat bantu pengambilan keputusan berbasis data untuk early warning system BPP"
)
tab1, tab2, tab3 = st.tabs(
    ["🔍 Eksplorasi Data", "🤖 Simulasi & Insight Model", "📈 Penjelasan Model"]
)


# -------------------------------------------------------------------------------------------------------
#                                           MENU SEBELAH KIRI
# -------------------------------------------------------------------------------------------------------

# Untuk Menu Sidebar (Sisi Sebelah Kiri)
with st.sidebar:
    # Sinkronisasi tema dari localStorage dengan auto-rerun pattern
    # streamlit_js_eval mengembalikan None pada panggilan pertama, nilai pada panggilan kedua
    if "_theme_synced" not in st.session_state:
        # Request localStorage value (akan return None pada panggilan pertama)
        localstorage_theme = streamlit_js_eval(
            js_expressions="localStorage.getItem('bpp_theme')",
            key="sync_theme_from_localstorage",
        )

        if localstorage_theme is not None:
            # Value tersedia (panggilan kedua), sinkronisasi tema
            st.session_state._theme_synced = True
            if localstorage_theme in ["dark", "light"]:
                if st.session_state.get("theme") != localstorage_theme:
                    st.session_state.theme = localstorage_theme
                    st.rerun()
        # Jika None, biarkan Streamlit rerender dan coba lagi
        # (tidak perlu explicit rerun, Streamlit akan handle)

    st.image(
        "https://www.megabagus.id/wp-content/uploads/2025/10/logo-pln-ip.jpg",
        use_container_width=True,
    )
    st.title("Panel Kontrol")

    # Tombol reset
    # custom_style()
    if st.button("🔄 Reset Aplikasi"):
        st.session_state.clear()
        st.rerun()

    # Garis pemisah
    st.divider()

    # Keterangan akurasi tiap model dengan glass effect
    st.markdown(
        f"""
    <div style="
        /* background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(6, 182, 212, 0.08) 100%); */
        background: rgba(14, 165, 233, 0.05);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(14, 165, 233, 0.2);
        margin-bottom: 10px;
    ">
        <div style="font-size:14px; color:inherit; font-weight:600; margin-bottom: 10px;">
            ⭐ Akurasi 4 Model Terbaik:
        </div>
        <ol style="margin-left: 15px; color: inherit; font-size: 13px; line-height: 1.8;">
            <li>Neural Network = <span style="color:#0ea5e9; font-weight:600;">{akurasi_keras}%</span></li>
            <li>Elastic Net = <span style="color:#0ea5e9; font-weight:600;">{akurasi_elastic}%</span></li>
            <li>Ridge Regression = <span style="color:#0ea5e9; font-weight:600;">{akurasi_ridge}%</span></li>
            <li>KNN = <span style="color:#0ea5e9; font-weight:600;">{akurasi_knn}%</span></li>
        </ol>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Garis pemisah
    st.divider()

    # Keterangan Data Simulasi dengan glass effect
    st.markdown(
        """
    <div style="
        /* background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(234, 88, 12, 0.08) 100%); */
        background: rgba(245, 158, 11, 0.05);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(245, 158, 11, 0.2);
    ">
        <div style="font-size:14px; color:#fbbf24; font-weight:600; margin-bottom: 8px;">
            ⚙️ Data Simulasi
        </div>
        <ul style="margin-left: 15px; color: inherit; font-size: 13px; line-height: 1.8;">
            <li>Masukkan data sebagai dasar prediksi.</li>
            <li>Nilai awal = nilai bulan terakhir.</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Dua enter
    st.write("")
    st.write("")

    # Nilai Beban Pembelian Tenaga Listrik
    b_ptl = st.number_input(
        str(df.columns[n_awal + 1]), value=df.iloc[-1, n_awal + 1], step=1
    )
    nilai_kanan(b_ptl)

    # Nilai Beban Sewa
    b_sewa = st.number_input(
        str(df.columns[n_awal + 2]), value=df.iloc[-1, n_awal + 2], step=1
    )
    nilai_kanan(b_sewa)

    # Nilai Beban Biosolar
    b_biosolar = st.number_input(
        str(df.columns[n_awal + 3]), value=df.iloc[-1, n_awal + 3], step=1
    )
    nilai_kanan(b_biosolar)

    # Tombol Trigger Modal Rincian Komponen C
    if st.button(
        "🧮 Input Detail Komponen C (Batubara & Biomassa)", use_container_width=True
    ):
        modal_detail_komponen_c()

    # Nilai Beban Batubara & Biomassa
    # PRIORITAS: 1. Session State (baru disimpan), 2. GSheet Database, 3. DataFrame CSV (fallback)
    val_bb_default = float(df.iloc[-1, n_awal + 4])
    val_bio_default = float(df.iloc[-1, n_awal + 5])

    # Ambil nilai terbaru dari GSheet jika tersedia
    if GSHEET_AVAILABLE:
        try:
            gsheet_row = get_current_period_row()
            if isinstance(gsheet_row, pd.Series):
                gsheet_row = gsheet_row.to_dict()
            if gsheet_row:
                gsheet_bb = gsheet_row.get("komponen_c_batubara", 0)
                gsheet_bio = gsheet_row.get("komponen_c_biomassa", 0)
                if gsheet_bb and float(gsheet_bb) > 0:
                    val_bb_default = float(gsheet_bb)
                if gsheet_bio and float(gsheet_bio) > 0:
                    val_bio_default = float(gsheet_bio)
        except:
            pass

    # Override jika session state ada (baru simpan di Modal C)
    if "b_batubara" in st.session_state and st.session_state["b_batubara"] > 0:
        val_bb_default = float(st.session_state["b_batubara"])
    if "b_biomassa" in st.session_state and st.session_state["b_biomassa"] > 0:
        val_bio_default = float(st.session_state["b_biomassa"])

    b_batubara = st.number_input(
        str(df.columns[n_awal + 4]),
        value=int(val_bb_default),
        step=1,
        disabled=True,
        help="ℹ️ Untuk mengubah, gunakan tombol 'Input Detail Komponen C' di atas.\nNilai ini dari database (read-only).",
    )
    nilai_kanan(b_batubara)

    b_biomassa = st.number_input(
        str(df.columns[n_awal + 5]),
        value=int(val_bio_default),
        step=1,
        disabled=True,
        help="ℹ️ Untuk mengubah, gunakan tombol 'Input Detail Komponen C' di atas.\nNilai ini dari database (read-only).",
    )
    nilai_kanan(b_biomassa)

    # Nilai Beban Kimia
    b_kimia = st.number_input(
        str(df.columns[n_awal + 6]), value=df.iloc[-1, n_awal + 6], step=1
    )
    nilai_kanan(b_kimia)

    # Nilai Beban Minyak
    b_minyak = st.number_input(
        str(df.columns[n_awal + 7]), value=df.iloc[-1, n_awal + 7], step=1
    )
    nilai_kanan(b_minyak)

    # Nilai Beban Pemeliharaan
    b_pemeliharaan = st.number_input(
        str(df.columns[n_awal + 8]), value=df.iloc[-1, n_awal + 8], step=1
    )
    nilai_kanan(b_pemeliharaan)

    # Nilai Beban Kepegawaian
    b_kepegawaian = st.number_input(
        str(df.columns[n_awal + 9]), value=df.iloc[-1, n_awal + 9], step=1
    )
    nilai_kanan(b_kepegawaian)

    # Nilai Beban Penyusutan Aset Tetap
    b_penyusutan = st.number_input(
        str(df.columns[n_awal + 10]), value=df.iloc[-1, n_awal + 10], step=1
    )
    nilai_kanan(b_penyusutan)

    # Nilai Beban Penyusutan Aset Tetap (Sewa)
    b_penyusutan_s = st.number_input(
        str(df.columns[n_awal + 11]), value=df.iloc[-1, n_awal + 11], step=1
    )
    nilai_kanan(b_penyusutan_s)

    # Nilai Beban Administrasi
    b_administrasi = st.number_input(
        str(df.columns[n_awal + 12]), value=df.iloc[-1, n_awal + 12], step=1
    )
    nilai_kanan(b_administrasi)

    # Nilai Beban Emisi Carbon
    b_emisi = st.number_input(
        str(df.columns[n_awal + 13]), value=df.iloc[-1, n_awal + 13], step=1
    )
    nilai_kanan(b_emisi)

    # Nilai Fee EPI
    b_fee = st.number_input(
        str(df.columns[n_awal + 14]), value=df.iloc[-1, n_awal + 14], step=1
    )
    nilai_kanan(b_fee)

    # Nilai Lain-lain
    b_lain = st.number_input(
        str(df.columns[n_awal + 15]), value=df.iloc[-1, n_awal + 15], step=1
    )
    nilai_kanan(b_lain)

    # ============ SECTION: INPUT PENJUALAN MULTI-DIVISI ============
    st.divider()
    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.08) 100%);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(34, 197, 94, 0.3);
        margin-bottom: 10px;
    ">
        <div style="font-size:14px; color:#059669; font-weight:600; margin-bottom: 8px;">
            📊 Input Penjualan (Multi-Divisi)
        </div>
        <div style="font-size: 12px; color: inherit;">
            Nilai Penjualan dihitung dari Komponen A + B + C + D yang diinput oleh masing-masing divisi.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Cek apakah Google Sheets tersedia
    if GSHEET_AVAILABLE:
        try:
            # Ambil data dari Google Sheets
            penjualan_data = get_penjualan_value()
            component_status = get_component_status()

            # Fallback logic jika data kosong
            if penjualan_data["source"] == "none":
                # Gunakan 0 (Reset -> 0)
                total_penjualan = 0
            else:
                total_penjualan = penjualan_data["total"]

            # Status indikator
            status_a = "✅" if component_status["komponen_a"] else "⏳"
            status_b = "✅" if component_status["komponen_b"] else "⏳"
            status_c_bb = "✅" if component_status["komponen_c_batubara"] else "⏳"
            status_c_bio = "✅" if component_status["komponen_c_biomassa"] else "⏳"
            status_d = "✅" if component_status["komponen_d"] else "⏳"

            # Alert berdasarkan kelengkapan data
            if penjualan_data["is_current_complete"]:
                # Menggunakan data input terkini (Real-time).
                # tidak perlu ditampilkan alert ini.
                pass
            elif penjualan_data["source"] == "last_complete":
                st.markdown(
                    '<div class="full-width-alert alert-warning">⏳ Data saat ini belum lengkap. Model menggunakan data input terakhir yang lengkap.</div>',
                    unsafe_allow_html=True,
                )
            elif penjualan_data["source"] == "none":
                st.markdown(
                    '<div class="full-width-alert alert-warning" style="background-color: #e0f2fe; color: #0369a1; border-color: #bae6fd;">ℹ️ Belum ada input dari divisi. Total Penjualan 0.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("❌ Status data tidak valid.")

            # Tombol-tombol untuk input komponen
            st.markdown("**Input per Komponen:**")

            # Layout 1 Kolom (Full Width)
            if st.button(
                f"{status_a} Komponen A", use_container_width=True, key="btn_komp_a"
            ):
                modal_komponen_a()

            if st.button(
                f"{status_b} Komponen B", use_container_width=True, key="btn_komp_b"
            ):
                modal_komponen_b()

            if st.button(
                f"{status_c_bb} Komponen C (Batubara)",
                use_container_width=True,
                key="btn_komp_c_bb",
            ):
                modal_komponen_c_batubara()

            if st.button(
                f"{status_c_bio} Komponen C (Biomassa)",
                use_container_width=True,
                key="btn_komp_c_bio",
            ):
                modal_komponen_c_biomassa()

            if st.button(
                f"{status_d} Komponen D", use_container_width=True, key="btn_komp_d"
            ):
                modal_komponen_d()

            st.write("")

            # Display nilai total (read-only) with SUPER Premium UI
            st.markdown(
                f"""
                <div style="
                    margin-top: 15px; 
                    margin-bottom: 15px; 
                    padding: 15px; 
                    background: rgba(34, 197, 94, 0.1); 
                    border-radius: 12px; 
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    text-align: center;
                ">
                    <div style="font-size: 14px; color: inherit; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Total Penjualan (kWh)
                    </div>
                    <div style="font-size: 20px; color: #059669; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2;">
                        {total_penjualan:,.0f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Rumus transparansi with Card Style - Larger Font
            comp = penjualan_data["components"]
            st.markdown(
                f"""
                <div style="
                    font-size: 12px; 
                    color: {RUMUS_TEXT}; 
                    margin-top: 10px; 
                    padding: 14px; 
                    background: {RUMUS_BG}; 
                    border: 1px solid rgba(148, 163, 184, 0.2); 
                    border-radius: 8px;
                ">
                    <div style="font-weight: 700; margin-bottom: 8px; color: inherit; border-bottom: 1px solid rgba(148, 163, 184, 0.2); padding-bottom: 4px;">
                        Rincian Rumus (A + B + C + D)
                    </div>
                    <div style="margin-top: 8px; font-family: 'Consolas', 'Monaco', monospace; color: inherit; font-size: 13px; line-height: 1.6;">
                        <div style="display: flex; justify-content: space-between;"><span>A</span> <span>{comp['A']:,.0f}</span></div>
                        <div style="display: flex; justify-content: space-between;"><span>B</span> <span>{comp['B']:,.0f}</span></div>
                        <div style="display: flex; justify-content: space-between;"><span>C (BB)</span> <span>{comp['C_BB']:,.0f}</span></div>
                        <div style="display: flex; justify-content: space-between;"><span>C (Bio)</span> <span>{comp['C_Bio']:,.0f}</span></div>
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #64748b; padding-bottom: 2px;"><span>D</span> <span>{comp['D']:,.0f}</span></div>
                        <div style="display: flex; justify-content: space-between; margin-top: 4px; color: #059669; font-weight: bold;"><span>TOTAL</span> <span>{total_penjualan:,.0f}</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            # st.sidebar.subheader("🕵️ Debug Session State")
            # st.sidebar.write(st.session_state)

            if st.button(
                "🔄 Reset Data",
                use_container_width=True,
                key="btn_reset_data",
                type="secondary",
            ):
                modal_reset_data()

            # --- GLOBAL ALERT AREA ---
            # Menampilkan alert sebagai TOAST (Auto-dismiss) sesuai request user
            if "app_alert" in st.session_state and st.session_state.app_alert:
                alert = st.session_state.app_alert
                msg = alert.get("msg", "")
                type_ = alert.get("type", "success")

                if type_ == "success":
                    st.toast(msg, icon="✅")
                elif type_ == "warning":
                    st.toast(msg, icon="⚠️")
                elif type_ == "error":
                    st.toast(msg, icon="❌")

                # Bersihkan alert agar tidak muncul terus menerus
                st.session_state.app_alert = None

            # Gunakan nilai dari Google Sheets untuk model
            b_penjualan = total_penjualan

        except Exception as e:
            st.error(f"Gagal terhubung ke Google Sheets: {str(e)}")
            # Fallback ke input manual
            b_penjualan = st.number_input(
                str(df.columns[n_awal - 3]), value=df.iloc[-1, n_awal - 3], step=1
            )
            nilai_kanan(b_penjualan)
    else:
        # Fallback jika Google Sheets tidak tersedia
        st.info("ℹ️ Koneksi Google Sheets tidak tersedia. Menggunakan input manual.")
        b_penjualan = st.number_input(
            str(df.columns[n_awal - 3]), value=df.iloc[-1, n_awal - 3], step=1
        )
        nilai_kanan(b_penjualan)

    # Spasi
    st.write("")

    # Bagian Copyright
    sidebar_footer()


# -------------------------------------------------------------------------------------------------------
#                                       LAYAR UTAMA
# -------------------------------------------------------------------------------------------------------

# Tab bagian pertama
with tab1:

    # ----------------------
    #     MELIHAT TABEL
    # ----------------------

    # Judul awal
    st.subheader("Eksplorasi Data")

    # Tampilan tabel
    st.dataframe(df_tampilan)

    # Catatan kecil untuk user
    st.caption(
        "Note: Data ini diupdate melalui file spreadsheet, silakan lakukan update untuk data terbaru"
    )

    # Garis pemisah
    st.divider()

    # ----------------------
    #    SCATTER PLOT
    # ----------------------

    # Judul awal
    st.subheader("Visualisasi Scatter Plot")

    # Pilihan variabel dari dataframe (jika datasetnya itu besar)
    x_var = st.selectbox("Pilih variabel X", df_selain_bulan.columns)
    y_var = st.selectbox("Pilih variabel Y", df_selain_bulan.columns)

    st.write(" ")

    # Opsi garis regresi
    tampil_regresi = st.checkbox("Tampilkan garis regresi", value=False)

    # Penentuan jumlah kolom
    col1, col2 = st.columns([2, 1], gap="large")

    # Kolom pertama
    with col1:

        # Style seaborn
        sns.set_style("white")

        # Menyiapkan canvasnya
        fig, ax = plt.subplots(figsize=(4, 3))

        # Scatter seaborn (lebih halus dan estetis)
        sns.scatterplot(
            data=df,
            x=x_var,
            y=y_var,
            s=15,  # ukuran marker kecil
            color="#2252F0",  # warna marker (bisa diganti)
            ax=ax,
        )

        # Jika user memilih, tampilkan garis regresi
        if tampil_regresi:
            sns.regplot(
                data=df,
                x=x_var,
                y=y_var,
                scatter=False,  # supaya tidak menggandakan scatter
                ax=ax,
                color="#e63946",  # warna garis regresi
                line_kws={"linewidth": 1.2},
            )

        # Hilangkan border sisi atas & kanan
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Rapikan garis sumbu
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)

        # Label
        ax.set_xlabel(f"{x_var}", fontsize=6)
        ax.set_ylabel(f"{y_var}", fontsize=6)
        ax.set_title(f"{x_var} vs {y_var}", fontsize=7)

        # ukuran tick
        ax.tick_params(axis="both", labelsize=6)

        # Kecilkan tulisan scientific notaion (misal: 1e10)
        ax.xaxis.offsetText.set_fontsize(6)
        ax.yaxis.offsetText.set_fontsize(6)

        # Memunculkan visualisasinya
        st.pyplot(fig, use_container_width=False)

    # Kolom kedua
    with col2:

        # Penulisan variabel terpilih dengan glass design
        st.markdown(
            f"""
        <div style="
            padding: 20px;
            border-radius: 16px;
            background: {BOX_BG};
            border: {BOX_BORDER};
            box-shadow: {BOX_SHADOW};
            backdrop-filter: blur(10px);
            ">
            <h4 style="margin-top: 0; margin-bottom: 12px; color:{TITLE_COLOR}; font-family: 'Poppins', sans-serif; font-weight: 600;">📌 Variabel yang Dipilih</h4>
            <p style="font-size:14px; margin:0; color: {SUBTEXT_COLOR}; line-height: 1.8;">
            <b style="color:{LABEL_COLOR_1};">Sumbu X:</b> <span style="color:{TEXT_COLOR};">{x_var}</span><br>
            <b style="color:{LABEL_COLOR_2};">Sumbu Y:</b> <span style="color:{TEXT_COLOR};">{y_var}</span>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Garis pemisah
    st.divider()

    # ----------------------
    #    LINE CHART
    # ----------------------

    # Judul awal
    st.subheader("Visualisasi Line Chart")

    # Pilih variabel Y untuk line chart
    y_line = st.selectbox(
        "Pilih variabel untuk Line Chart (Sumbu Y)", df_selain_bulan.columns
    )

    # Penentuan kolom
    col1, col2 = st.columns([2, 1], gap="large")

    # Kolom pertama
    with col1:

        fig = px.line(
            df,
            x="Bulan",
            y=y_line,
            markers=True,
        )

        # Ganti warna line & marker (optional)
        fig.update_traces(
            line=dict(color="#1f77b4", width=2), marker=dict(size=6, color="#CC7F3D")
        )

        # Hilangkan background grid agar clean
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            margin=dict(l=20, r=20, t=30, b=20),
        )

        # Sumbu dengan garis halus
        fig.update_xaxes(showline=True, linewidth=1, linecolor="black", tickangle=45)
        fig.update_yaxes(showline=True, linewidth=1, linecolor="black")

        # Memunculkan visualnya
        st.plotly_chart(fig, use_container_width=True)

    # Kolom kedua
    with col2:

        # Keterangan variabel terpilih dengan glass design
        st.markdown(
            f"""
        <div style="
            padding: 20px;
            border-radius: 16px;
            background: {BOX_BG};
            border: {BOX_BORDER};
            box-shadow: {BOX_SHADOW};
            backdrop-filter: blur(10px);
        ">
            <h4 style="margin-top: 0; margin-bottom: 12px; color:{TITLE_COLOR}; font-family: 'Poppins', sans-serif; font-weight: 600;">📊 Variabel Line Chart</h4>
            <p style="font-size:14px; margin:0; color: {SUBTEXT_COLOR}; line-height: 1.8;">
            <b style="color:{LABEL_COLOR_1};">Sumbu X:</b> <span style="color:{TEXT_COLOR};">Bulan</span><br>
            <b style="color:{LABEL_COLOR_2};">Sumbu Y:</b> <span style="color:{TEXT_COLOR};">{y_line}</span>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ----------------------
    #    Histogram
    # ----------------------

    # Judul awal
    st.subheader("Visualisasi Histogram")

    # Pilih variabel
    y_dist = st.selectbox(
        "Pilih variabel untuk Distribution Plot", df_selain_bulan.columns
    )

    # Penentuan kolom
    col1, col2 = st.columns([2, 1], gap="large")

    # Kolom pertama
    with col1:

        # Ambil data
        data = df_selain_bulan[y_dist].dropna()

        # Hitung KDE
        kde = gaussian_kde(data)
        x_range = np.linspace(data.min(), data.max(), 200)
        y_kde = kde(x_range)

        # Buat figure
        fig_hist_kde = go.Figure()

        # Histogram
        fig_hist_kde.add_trace(
            go.Histogram(
                x=data, nbinsx=20, marker_color="#1f77b4", opacity=0.6, name="Histogram"
            )
        )

        # Density Line
        fig_hist_kde.add_trace(
            go.Scatter(
                x=x_range,
                y=y_kde
                * len(data)
                * (data.max() - data.min())
                / 20,  # skala supaya sebanding
                mode="lines",
                line=dict(color="#e63946", width=2),
                name="KDE Curve",
            )
        )

        # Styling
        fig_hist_kde.update_layout(
            plot_bgcolor="white",
            showlegend=True,
            margin=dict(l=20, r=20, t=30, b=20),
            yaxis_title="Frekuensi",
            xaxis_title=y_dist,
        )
        fig_hist_kde.update_xaxes(showline=True, linecolor="black")
        fig_hist_kde.update_yaxes(showline=True, linecolor="black")

        st.plotly_chart(fig_hist_kde, use_container_width=True)

    with col2:
        st.markdown(
            f"""
        <div style="
            padding: 20px;
            border-radius: 16px;
            background: {BOX_BG};
            border: {BOX_BORDER};
            box-shadow: {BOX_SHADOW};
            backdrop-filter: blur(10px);
        ">
            <h4 style="margin:0 0 12px 0; color:{TITLE_COLOR}; font-family: 'Poppins', sans-serif; font-weight: 600;">📊 Distribution + KDE</h4>
            <p style="font-size:14px; color:{SUBTEXT_COLOR}; margin:0; line-height: 1.6;">
            <b style="color:{LABEL_COLOR_1};">Variabel:</b> <span style="color:{TEXT_COLOR};">{y_dist}</span><br>
            <span style="color:{SUBTEXT_COLOR}; font-size: 13px;">Histogram menunjukkan frekuensi, kurva merah menunjukkan estimasi distribusi kontinu.</span>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ----------------------
    #    Boxplot
    # ----------------------

    # Judul awal
    st.subheader("Visualisasi Boxplot")

    # Pemilihan variabel
    y_box = st.selectbox("Pilih variabel untuk Boxplot", df_selain_bulan.columns)

    # Penentuan kolom
    col1, col2 = st.columns([2, 1], gap="large")

    # Kolom pertama
    with col1:
        fig_box = px.box(df, y=y_box, color_discrete_sequence=["#e83e8c"])
        fig_box.update_layout(showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig_box, use_container_width=True)

    # Kolom kedua
    with col2:
        st.markdown(
            f"""
        <div style="
            padding: 20px;
            border-radius: 16px;
            background: {BOX_BG};
            border: {BOX_BORDER};
            box-shadow: {BOX_SHADOW};
            backdrop-filter: blur(10px);
        ">
            <h4 style="margin:0 0 12px 0; color:{TITLE_COLOR}; font-family: 'Poppins', sans-serif; font-weight: 600;">📦 Boxplot</h4>
            <p style="font-size:14px; color:{SUBTEXT_COLOR}; margin:0; line-height: 1.6;">
            <b style="color:{LABEL_COLOR_1};">Sumbu Y:</b> <span style="color:{TEXT_COLOR};">{y_box}</span><br>
            <b style="color:{LABEL_COLOR_2};">Insight:</b> <span style="color:{SUBTEXT_COLOR};">Menemukan outlier dan penyebaran nilai.</span>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ----------------------
    #    Heatmap
    # ----------------------

    # Judul awal
    st.subheader("Korelasi Heatmap")

    # Penentuan kolom
    col1, col2 = st.columns([2, 1], gap="large")

    # kolom pertama
    with col1:
        fig_corr, ax_corr = plt.subplots(figsize=(6, 5))
        sns.heatmap(
            df_selain_bulan.corr(),
            cmap="coolwarm",
            annot=True,  # tampilkan nilai korelasi
            fmt=".2f",  # 2 angka desimal
            annot_kws={"size": 4},  # ukuran font angka annotasi
            cbar=True,  # menyalakan color bar
            cbar_kws={"shrink": 0.7},  # tinggi colorbar
            ax=ax_corr,
        )
        cbar = ax_corr.collections[0].colorbar
        cbar.ax.tick_params(labelsize=4)
        ax_corr.tick_params(axis="both", labelsize=4)
        ax_corr.set_title("Correlation Heatmap", fontsize=8)
        st.pyplot(fig_corr, use_container_width=False)

    # Kolom kedua
    with col2:
        st.markdown(
            f"""
        <div style="
            padding: 20px;
            border-radius: 16px;
            background: {BOX_BG};
            border: {BOX_BORDER};
            box-shadow: {BOX_SHADOW};
            backdrop-filter: blur(10px);
        ">
            <h4 style="margin:0 0 12px 0; color:{TITLE_COLOR}; font-family: 'Poppins', sans-serif; font-weight: 600;">🔗 Korelasi Antar Variabel</h4>
            <p style="font-size:14px; color:{SUBTEXT_COLOR}; margin:0; line-height: 1.6;">
            <b style="color:{LABEL_COLOR_2};">Insight:</b> <span style="color:{SUBTEXT_COLOR};">Lihat variabel mana yang paling berpengaruh terhadap BPP.</span>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )


# Tab bagian kedua
with tab2:

    # Penentuan model
    pilihan_model = st.selectbox(
        "Pilih Model", ("Neural Network", "Elastic", "Ridge", "KNN")
    )

    # Penentuan kolom
    col1, col2 = st.columns([1, 2], gap="large", border=True)

    # Kolom pertama
    with col1:

        # Judul pertama
        st.subheader("Simulasi Prediksi BPP")

        # Keterangan instruksi
        st.write(
            "Silakan atur nilai setiap beban di menu sebelah kiri untuk melakukan simulasi prediksi BPP"
        )

        # Menggabungkan data input
        data = {
            str(df.columns[n_awal + 1]): b_ptl,
            str(df.columns[n_awal + 2]): b_sewa,
            str(df.columns[n_awal + 3]): b_biosolar,
            str(df.columns[n_awal + 4]): b_batubara,
            str(df.columns[n_awal + 5]): b_biomassa,
            str(df.columns[n_awal + 6]): b_kimia,
            str(df.columns[n_awal + 7]): b_minyak,
            str(df.columns[n_awal + 8]): b_pemeliharaan,
            str(df.columns[n_awal + 9]): b_kepegawaian,
            str(df.columns[n_awal + 10]): b_penyusutan,
            str(df.columns[n_awal + 11]): b_penyusutan_s,
            str(df.columns[n_awal + 12]): b_administrasi,
            str(df.columns[n_awal + 13]): b_emisi,
            str(df.columns[n_awal + 14]): b_fee,
            str(df.columns[n_awal + 15]): b_lain,
            str(df.columns[n_awal - 3]): b_penjualan,
        }

        kolom = list(data.keys())
        df_final = pd.DataFrame([data.values()], columns=kolom)
        df_final_scaling = scaler.transform(df_final)

        # Memprediksi model (Unconditional)
        if pilihan_model == "Neural Network":
            hasil = round(float(modelku_keras.predict(df_final_scaling)), 2)
            nilai_error = error_keras
        elif pilihan_model == "Elastic":
            hasil = round(float(modelku_elastic.predict(df_final)), 2)
            nilai_error = error_elastic
        elif pilihan_model == "Ridge":
            hasil = round(float(modelku_ridge.predict(df_final)), 2)
            nilai_error = error_ridge
        else:
            hasil = round(float(modelku_knn.predict(df_final)), 2)
            nilai_error = error_knn

        # Mengeluarkan prediksi
        st.metric(
            label="Estimasi Prediksi BPP",
            value=f"~ {hasil} ± {nilai_error}",
            help="Nilai ini merepresentasikan nilai BPP berdasarkan semua nilai variabel yang sudah diinput",
        )

        # Melihat detail data awal
        with st.expander("Lihat detail input mentah yang dikirim ke model"):
            st.dataframe(data)

        # Keterangan tips
        custom_caption(
            "Tips: Perhatikan Plot SHAP Summary, naikkan nilai variabel yang berperan positif dan turunkan nilai yang berperan negatif untuk mendapatkan nilai BPP yang dikehendaki!",
            font_size="16px",
            color="#8F4D21",
        )

    # Kolom kedua
    with col2:

        # Tulisan teks
        st.write(
            "Visualisasi berikut adalah hasil analisis dari semua rentang data yang ada sesuai model yang dipilih"
        )

        # Jika dipilih model Neural Network
        if pilihan_model == "Neural Network":

            # Plot pertama
            st.subheader("🔹 Plot SHAP Bar")
            fig1, ax1 = plt.subplots()
            shap.plots.bar(shap_values_keras, max_display=20, show=False)
            ax1.set_title(
                "Model Neural Network - Urutan Bobot Pengaruh Setiap Variabel"
            )
            st.pyplot(fig1)

            # Plot kedua
            st.subheader("🔹 Plot SHAP Summary")
            fig2, ax2 = plt.subplots()
            shap.summary_plot(shap_values_keras, show=False)
            ax2.set_title("Model Neural Network - Interaksi Variabel Terhadap BPP")
            st.pyplot(fig2)

        # Jika dipilih model elastic
        elif pilihan_model == "Elastic":

            # Plot pertama
            st.subheader("🔹 Plot SHAP Bar")
            fig1, ax1 = plt.subplots()
            shap.plots.bar(shap_values_elastic, max_display=20, show=False)
            ax1.set_title("Model Elastic - Urutan Bobot Pengaruh Setiap Variabel")
            st.pyplot(fig1)

            # Plot kedua
            st.subheader("🔹 Plot SHAP Summary")
            fig2, ax2 = plt.subplots()
            shap.summary_plot(shap_values_elastic, show=False)
            ax2.set_title("Model Elastic - Interaksi Variabel Terhadap BPP")
            st.pyplot(fig2)

        # Jika dipilih model ridge
        elif pilihan_model == "Ridge":

            # Plot pertama
            st.subheader("🔹 Plot SHAP Bar")
            fig1, ax1 = plt.subplots()
            shap.plots.bar(shap_values_ridge, max_display=20, show=False)
            ax1.set_title("Model Ridge - Urutan Bobot Pengaruh Setiap Variabel")
            st.pyplot(fig1)

            # Plot kedua
            st.subheader("🔹 Plot SHAP Summary")
            fig2, ax2 = plt.subplots()
            shap.summary_plot(shap_values_ridge, show=False)
            ax2.set_title("Model Ridge - Interaksi Variabel Terhadap BPP")
            st.pyplot(fig2)

        # Jika dipilih knn
        else:

            # Plot pertama
            st.subheader("🔹 Plot SHAP Bar")
            fig1, ax1 = plt.subplots()
            shap.plots.bar(shap_values_knn, max_display=20, show=False)
            ax1.set_title("Model KNN - Urutan Bobot Pengaruh Setiap Variabel")
            st.pyplot(fig1)

            # Plot kedua
            st.subheader("🔹 Plot SHAP Summary")
            fig2, ax2 = plt.subplots()
            shap.summary_plot(shap_values_knn, show=False)
            ax2.set_title("Model KNN - Interaksi Variabel Terhadap BPP")
            st.pyplot(fig2)

# Tab ketiga
with tab3:

    # Rentang waktu
    rentang_waktu = [
        "Jan 2023",
        "Feb 2023",
        "Mar 2023",
        "Apr 2023",
        "Mei 2023",
        "Jun 2023",
        "Jul 2023",
        "Agu 2023",
        "Sep 2023",
        "Okt 2023",
        "Nov 2023",
        "Des 2023",
        "Jan 2024",
        "Feb 2024",
        "Mar 2024",
        "Apr 2024",
        "Mei 2024",
        "Jun 2024",
        "Jul 2024",
        "Agu 2024",
        "Sep 2024",
        "Okt 2024",
        "Nov 2024",
        "Des 2024",
        "Jan 2025",
        "Feb 2025",
        "Mar 2025",
        "Apr 2025",
        "Mei 2025",
        "Jun 2025",
        "Jul 2025",
        "Agu 2025",
        "Sep 2025",
    ]

    # Pemilihan model
    pilihan_model2 = st.selectbox(
        "Pilih Model",
        (
            "Neural Network (NN)",
            "Elastic Net",
            "Ridge Regression",
            "K-Nearest Neighbors",
        ),
    )

    # pemilihan urutan waktu
    pilihan_waktu = st.selectbox("Pilih waktu yang mau diinvestigasi", (rentang_waktu))
    index_pilihan = rentang_waktu.index(pilihan_waktu)

    # Jika yang terpilih neural network
    if pilihan_model2 == "Neural Network (NN)":

        # Plot Waterfall
        st.write(f"Nilai BPP Asli = {df.BPP[index_pilihan]:.2f}")
        st.write(f"Error model {str(pilihan_model2)} = ± {error_keras}")
        st.subheader("🔹 Plot SHAP Bar")
        fig, ax = plt.subplots()
        shap.plots.waterfall(
            shap_values_keras[index_pilihan], max_display=20, show=False
        )
        ax.set_title("Model Neural Network - Pengaruh Setiap Variabel Terhadap BPP")
        st.pyplot(fig)

        st.markdown(
            f"<b>Cara Kerja Model {pilihan_model2}</b>:", unsafe_allow_html=True
        )

        st.markdown(
            """
        Model Neural Network bekerja dengan meniru cara kerja otak manusia dalam mengenali pola. 
        Data input masuk ke dalam neurons pada input layer, kemudian diproses secara bertahap melalui beberapa hidden 
        layer yang masing-masing berisi node yang melakukan operasi matematika (perkalian bobot, penambahan bias, dan aktivasi). 
        Pada setiap layer, model belajar menyesuaikan bobot (weight) berdasarkan seberapa besar kesalahannya dalam memprediksi output, 
        proses ini disebut training dan dilakukan menggunakan metode backpropagation. Semakin sering model dilatih, bobot akan 
        menyesuaikan sehingga pola dan hubungan kompleks dalam data dapat dipelajari dan menghasilkan prediksi atau keputusan yang semakin akurat.
        """
        )

    # Jika yang terpilih elastic
    elif pilihan_model2 == "Elastic Net":

        # Plot Waterfall
        st.write(f"Nilai BPP Asli = {df.BPP[index_pilihan]:.2f}")
        st.write(f"Error model {str(pilihan_model2)} = ± {error_elastic}")
        st.subheader("🔹 Plot SHAP Bar")
        fig, ax = plt.subplots()
        shap.plots.waterfall(
            shap_values_elastic[index_pilihan], max_display=20, show=False
        )
        ax.set_title("Model Elastic Net - Pengaruh Setiap Variabel Terhadap BPP")
        st.pyplot(fig)

        st.markdown(
            f"<b>Cara Kerja Model {pilihan_model2}</b>:", unsafe_allow_html=True
        )

        st.markdown(
            """
        Model Elastic Net Regression bekerja dengan menggabungkan dua metode regularisasi, 
        yaitu L1 (Lasso) dan L2 (Ridge), untuk menghasilkan model regresi yang stabil dan tidak mudah overfitting. 
        Dalam proses pelatihannya, Elastic Net mencari garis regresi yang paling sesuai dengan pola data, sambil menambahkan 
        penalti pada nilai koefisien agar tidak terlalu besar. Penalti L1 membantu menghilangkan atau mengecilkan beberapa 
        koefisien sehingga model menjadi lebih sederhana (feature selection), sedangkan penalti L2 membantu menjaga stabilitas 
        koefisien terutama ketika terdapat fitur yang saling berkorelasi. Dengan kombinasi kedua penalti ini, Elastic Net 
        mampu memberikan hasil prediksi yang baik pada dataset dengan banyak variabel dan hubungan antar fitur yang kompleks.
        """
        )

    # Jika yang terpilih ridge
    elif pilihan_model2 == "Ridge Regression":

        # Plot Waterfall
        st.write(f"Nilai BPP Asli = {df.BPP[index_pilihan]:.2f}")
        st.write(f"Error model {str(pilihan_model2)} = ± {error_ridge}")
        st.subheader("🔹 Plot SHAP Bar")
        fig, ax = plt.subplots()
        shap.plots.waterfall(
            shap_values_ridge[index_pilihan], max_display=20, show=False
        )
        ax.set_title("Model Ridge Regression - Pengaruh Setiap Variabel Terhadap BPP")
        st.pyplot(fig)

        st.markdown(
            f"<b>Cara Kerja Model {pilihan_model2}</b>:", unsafe_allow_html=True
        )

        st.markdown(
            """
        Ridge Regression bekerja dengan menambahkan penalti L2 pada proses pelatihan regresi linier untuk mencegah model 
        memiliki koefisien yang terlalu besar. Saat mencari hubungan terbaik antara variabel input dan output, Ridge tetap 
        meminimalkan error prediksi, namun juga menambahkan batasan agar koefisien tidak berkembang secara ekstrem, terutama 
        ketika data memiliki multikolinearitas (fitur saling berkorelasi). Dengan cara ini, model menjadi lebih stabil, tidak 
        mudah overfitting, dan mampu memberikan hasil prediksi yang lebih konsisten meskipun data input memiliki banyak variabel 
        atau data yang tersedia relatif sedikit.
        """
        )

    # Jika yang terpilih knn
    else:

        # Plot Waterfall
        st.write(f"Nilai BPP Asli = {df.BPP[index_pilihan]:.2f}")
        st.write(f"Error model {str(pilihan_model2)} = ± {error_knn}")
        st.subheader("🔹 Plot SHAP Bar")
        fig, ax = plt.subplots()
        shap.plots.waterfall(shap_values_knn[index_pilihan], max_display=20, show=False)
        ax.set_title("Model KNN - Pengaruh Setiap Variabel Terhadap BPP")
        st.pyplot(fig)

        st.markdown(
            f"<b>Cara Kerja Model {pilihan_model2}</b>:", unsafe_allow_html=True
        )

        st.markdown(
            """
        KNN Regression bekerja dengan cara memprediksi nilai suatu data baru berdasarkan nilai dari k tetangga terdekat dalam 
        data pelatihan. Untuk melakukan prediksi, model akan menghitung jarak antara data baru dan semua data yang ada di dataset 
        (misalnya menggunakan jarak Euclidean), lalu memilih k data yang jaraknya paling dekat. Nilai prediksi akhir diperoleh dari 
        rata-rata nilai target dari tetangga-tetangga terpilih tersebut. Karena tidak ada proses pelatihan berbentuk penyesuaian parameter, 
        KNN disebut sebagai lazy learning, dan performanya sangat bergantung pada pemilihan nilai k serta skala data (sehingga normalisasi 
        biasanya penting). Model ini sederhana namun efektif, terutama ketika hubungan antar variabel bersifat lokal atau tidak linear.
        """
        )

    # Menambahkan garis pemisah
    garis_pemisah()

    # Keterangan tambahan dengan glass styling
    st.markdown(
        f"""
    <div style="
        background: {BOX_BG};
        border-radius: 16px;
        padding: 20px;
        border: {BOX_BORDER};
        box-shadow: {BOX_SHADOW};
        margin-top: 20px;
    ">
        <div style="font-size:15px; color:{TITLE_COLOR}; font-weight:600; margin-bottom: 12px; font-family: 'Poppins', sans-serif;">
            📋 Keterangan:
        </div>
        <ul style="margin-left: 15px; color: {SUBTEXT_COLOR}; font-size: 14px; line-height: 1.9;">
            <li>Nilai yang ditampilkan di grafik merupakan nilai sesuai waktu yang dipilih.</li>
            <li>Nilai <span style="color: {LABEL_COLOR_1}; font-weight: 600;">f(x)</span> adalah nilai prediksi BPP yang dihasilkan oleh model.</li>
            <li>Nilai <span style="color: {LABEL_COLOR_2}; font-weight: 600;">E[<i>f(X)</i>]</span> adalah nilai rata-rata dari prediksi semua rentang waktu yang dihasilkan oleh model.</li>
            <li>Tanda <span style="color: #ef4444; font-weight: 600;">−</span> dan <span style="color: #10b981; font-weight: 600;">+</span> adalah arah pengaruh dari setiap variabel dari nilai rata-rata dasarnya.</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )
