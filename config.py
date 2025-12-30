# config.py
from streamlit import set_page_config
from pandas import set_option as set_config

def apply_app_config():
    # Konfigurasi Pandas
    set_config("display.max_columns", None)
    set_config("display.max_rows", None)

    # Konfigurasi Halaman Streamlit
    set_page_config(
        page_title="Dashboard Project BPP IP Suralaya Unit 8",
        page_icon="⚡",
        layout="wide"
    )