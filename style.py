import streamlit as st

# ============================================================================
#              STYLING VISUAL PREMIUM - APLIKASI BPP SURALAYA
# ============================================================================


def custom_style():
    """
    Menerapkan custom CSS untuk tampilan premium dan modern.
    Termasuk: Background gradient, efek glassmorphism, animasi halus, dan tipografi modern.
    """
    st.markdown(
        """
        <style>
        /* ============== IMPOR FONT GOOGLE ============== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700;800&display=swap');

        /* ============== VARIABEL UTAMA ============== */
        :root {
            --primary-gradient: linear-gradient(135deg, #1a365d 0%, #2d5a87 50%, #3b82f6 100%);
            --sidebar-gradient: linear-gradient(180deg, #0f172a 0%, #1e3a5f 50%, #164e63 100%);
            --accent-color: #0ea5e9;
            --accent-glow: rgba(14, 165, 233, 0.4);
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --card-bg: rgba(255, 255, 255, 0.08);
            --card-border: rgba(255, 255, 255, 0.1);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            /* --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.15); */
            --shadow-soft: none;
            /* --shadow-glow: 0 0 20px rgba(14, 165, 233, 0.3); */
            --shadow-glow: none;
        }

        /* ============== STYLING GLOBAL ============== */
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            /* Background sekarang mengikuti tema native Streamlit */
        }
        
        /* Area konten utama - mengikuti tema native Streamlit */
        .main {
            /* Background sekarang mengikuti tema native Streamlit */
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background: transparent !important;
        }
        
        /* Warna teks mengikuti tema native Streamlit */
        .main, .main p, .main span, .main div, .main label, .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
            /* color: inherit - mengikuti tema native */
        }
        
        /* Styling Tab - mengikuti tema native dengan sedikit enhancement */
        .stTabs [data-baseweb="tab-list"] {
            border-radius: 12px !important;
            padding: 4px !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
            color: #ffffff !important;
        }
        
        /* Styling DataFrame / Tabel - mengikuti tema native */
        .stDataFrame, .dataframe {
            /* Background mengikuti tema native */
        }
        
        .stDataFrame th, .dataframe th {
            background: rgba(14, 165, 233, 0.2) !important;
        }
        
        .stDataFrame td, .dataframe td {
            /* Background mengikuti tema native */
        }
        
        /* Styling Selectbox, Input, dan Widget lainnya - mengikuti tema native */
        .stSelectbox > div > div,
        .stTextInput > div > div,
        .stNumberInput > div > div {
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
        }
        
        /* Subheader dan teks markdown - mengikuti tema native */
        .stSubheader, .stMarkdown {
            /* color: mengikuti tema native */
        }

        /* ============== STYLING SIDEBAR ============== */
        section[data-testid="stSidebar"] {
            /* Background sidebar mengikuti tema native Streamlit */
            border-right: 1px solid rgba(128, 128, 128, 0.2);
        }

        section[data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
            padding: 1.5rem 1rem;
        }

        /* Gambar Sidebar - Posisi Tengah */
        section[data-testid="stSidebar"] .stImage {
            display: flex;
            justify-content: center;
            width: 100%;
        }

        /* Tombol Sidebar - Posisi Tengah (kecuali tombol collapse) */
        section[data-testid="stSidebar"] .stButton {
            display: flex;
            justify-content: center;
            width: 100%;
        }
        
        /* Tombol collapse sidebar - kembalikan ke posisi default */
        section[data-testid="stSidebar"] [data-testid="stSidebarNavCollapseIcon"],
        section[data-testid="stSidebar"] [data-testid="collapsedControl"] {
            all: unset !important;
        }
        
        /* Reset posisi tengah untuk tombol pertama di sidebar (collapse) */
        section[data-testid="stSidebar"] > div:first-child > button:first-of-type {
            display: block !important;
            margin: 0 !important;
            width: auto !important;
        }

        /* Judul Sidebar - mengikuti tema native */
        section[data-testid="stSidebar"] h1 {
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
            font-size: 1.4rem !important;
            text-align: center !important;
            width: 100%;
            margin-bottom: 0.5rem;
            text-shadow: none;
        }

        /* Label Sidebar - mengikuti tema native */
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown p {
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }

        /* Garis Pemisah Sidebar */
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.15) !important;
            margin: 1.2rem 0;
        }

        /* Kontainer Logo dengan Efek Kaca */
        section[data-testid="stSidebar"] img {
            border-radius: 16px;
            /* box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); */
            box-shadow: none;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            max-width: 100% !important;
            height: auto !important;
            object-fit: contain !important;
        }

        section[data-testid="stSidebar"] img:hover {
            transform: scale(1.02);
            /* box-shadow: 0 12px 40px rgba(14, 165, 233, 0.3); */
            box-shadow: none;
        }

        /* ============== STYLING TOMBOL ============== */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%) !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 12px 28px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            border: none !important;
            /* box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4); */
            box-shadow: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            letter-spacing: 0.3px;
        }

        /* Sidebar buttons in Dark Mode - force 2-line wrap like light mode */
        section[data-testid="stSidebar"] .stButton > button {
            padding: 8px 12px !important;
            white-space: normal !important;
            display: flex !important;
            width: 100% !important;
            min-height: 44px !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button p {
            white-space: normal !important;
            line-height: 1.2 !important;
        }

        div.stButton > button:first-child:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 50%, #991b1b 100%) !important;
            transform: translateY(-2px) !important;
            /* box-shadow: 0 8px 25px rgba(239, 68, 68, 0.5) !important; */
            box-shadow: none !important;
        }

        div.stButton > button:first-child:active {
            transform: translateY(0) scale(0.98) !important;
        }

        /* ============== STYLING INPUT ANGKA ============== */
        div[data-baseweb="input"] > div {
            /* Background mengikuti tema native Streamlit */
            border-radius: 12px !important;
            padding: 8px 14px !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            box-shadow: none;
            transition: all 0.3s ease !important;
        }

        div[data-baseweb="input"] > div:focus-within {
            border-color: var(--accent-color) !important;
            box-shadow: none !important;
        }

        input[type=number] {
            /* color mengikuti tema native Streamlit */
            font-size: 15px !important;
            font-weight: 500 !important;
            background-color: transparent !important;
            font-family: 'Inter', monospace !important;
        }

        /* Fix Placeholder Color */
        input::placeholder, textarea::placeholder {
            color: #94a3b8 !important;
            opacity: 1;
        }

        /* ============== STYLING LABEL ============== */
        label[data-testid="stWidgetLabel"] > div {
            font-size: 14px !important;
            /* color mengikuti tema native Streamlit */
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: 0.2px;
        }

        /* ============== STYLING SELECTBOX ============== */
        /* Kontainer utama selectbox */
        div.stSelectbox div[data-baseweb="select"] > div {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            padding: 0 16px !important;
            min-height: 44px !important;
            height: 44px !important;
            display: flex !important;
            align-items: center !important;
            transition: all 0.3s ease !important;
        }

        /* Paksa SEMUA teks di dalam selectbox agar terlihat */
        div.stSelectbox div[data-baseweb="select"] * {
            color: #00e5ff !important;
            font-size: 15px !important;
            font-weight: 600 !important;
        }

        /* Kontainer nilai - flexbox tengah */
        div.stSelectbox div[data-baseweb="select"] > div > div,
        div.stSelectbox div[data-baseweb="select"] > div > div > div {
            overflow: visible !important;
            text-overflow: clip !important;
            white-space: nowrap !important;
            color: #00e5ff !important;
            display: flex !important;
            align-items: center !important;
            height: 100% !important;
        }

        /* Teks placeholder/nilai secara spesifik */
        div.stSelectbox [data-baseweb="select"] [class*="ValueContainer"],
        div.stSelectbox [data-baseweb="select"] [class*="singleValue"],
        div.stSelectbox [data-baseweb="select"] [class*="placeholder"] {
            color: #00e5ff !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            /* text-shadow: 0 0 1px rgba(0, 229, 255, 0.3); */
            text-shadow: none;
            display: flex !important;
            align-items: center !important;
            margin: 0 !important;
            padding: 0 !important;
            top: auto !important;
            transform: none !important;
            position: relative !important;
        }

        div.stSelectbox div[data-baseweb="select"] > div:hover {
            border-color: #00e5ff !important;
            /* box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.2) !important; */
            box-shadow: none !important;
        }

        /* Kontainer daftar dropdown - mengikuti tema native */
        div[data-baseweb="popover"] > div {
            /* background mengikuti tema native Streamlit */
            border-radius: 12px !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            box-shadow: none !important;
            max-height: 400px !important;
            overflow-y: auto !important;
        }

        /* Daftar menu dropdown - mengikuti tema native */
        ul[role="listbox"] {
            /* background mengikuti tema native Streamlit */
        }

        /* Opsi dropdown - mengikuti tema native */
        li[role="option"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important;
            padding: 14px 18px !important;
            transition: all 0.2s ease !important;
            white-space: nowrap !important;
            overflow: visible !important;
            line-height: 1.5 !important;
            /* color mengikuti tema native Streamlit */
            background: transparent !important;
        }

        li[role="option"]:hover {
            background: rgba(14, 165, 233, 0.2) !important;
        }

        li[role="option"][aria-selected="true"] {
            background: linear-gradient(90deg, #0ea5e9 0%, #0284c7 100%) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Styling teks yang dipilih - mengikuti tema native */
        div.stSelectbox span[data-baseweb="tag"] {
            /* color mengikuti tema native Streamlit */
            font-weight: 600 !important;
        }

        /* ============== STYLING TAB ============== */
        .stTabs [data-baseweb="tab-list"] {
            /* background mengikuti tema native Streamlit */
            border-radius: 16px;
            padding: 6px;
            gap: 8px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            border-radius: 12px !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            /* color mengikuti tema native Streamlit */
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            border: none !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            /* color mengikuti tema native Streamlit */
            background: rgba(128, 128, 128, 0.1) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent-color) 0%, #0284c7 100%) !important;
            color: #ffffff !important;
            box-shadow: none !important;
        }
        
        /* Active tab hover - gunakan teks gelap karena background akan lebih terang */
        .stTabs [aria-selected="true"]:hover {
            color: #0c4a6e !important;
        }

        /* Konten panel tab */
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 2rem;
        }

        /* ============== STYLING DATAFRAME ============== */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden;
            /* box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); */
            box-shadow: none;
        }

        /* ============== STYLING EXPANDER ============== */
        .streamlit-expanderHeader {
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.6) 100%) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }

        .streamlit-expanderHeader:hover {
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.8) 100%) !important;
            border-color: var(--accent-color) !important;
        }

        /* ============== STYLING METRIK ============== */
        [data-testid="stMetric"] {
            /* background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%); */
            background: rgba(14, 165, 233, 0.05);
            border-radius: 16px;
            padding: 1.2rem 1.5rem;
            border: 1px solid rgba(14, 165, 233, 0.2);
            /* box-shadow: 0 4px 20px rgba(14, 165, 233, 0.1); */
            box-shadow: none;
            transition: all 0.3s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            /* box-shadow: 0 8px 30px rgba(14, 165, 233, 0.2); */
            box-shadow: none;
        }

        [data-testid="stMetricLabel"] {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            color: var(--accent-color) !important;
            font-size: 14px !important;
        }

        [data-testid="stMetricValue"] {
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
            font-size: 1.8rem !important;
            /* color mengikuti tema native Streamlit */
        }

        /* ============== STYLING SUBHEADER ============== */
        .main h2, .main h3 {
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
            font-weight: 700 !important;
            /* background: linear-gradient(135deg, #1e3a5f 0%, #0ea5e9 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text; */
            color: #0ea5e9 !important;
            letter-spacing: -0.5px;
        }

        /* ============== STYLING JUDUL ============== */
        .main h1 {
            font-family: 'Poppins', sans-serif !important;
            font-weight: 800 !important;
            font-size: 2.2rem !important;
            font-size: 2.2rem !important;
            /* background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 50%, #14b8a6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text; */
            color: #0ea5e9 !important;
            letter-spacing: -0.5px;
            margin-bottom: 0.5rem !important;
        }

        /* ============== STYLING KOLOM ============== */
        div[data-testid="column"]:first-child {
            border-right: 2px solid rgba(14, 165, 233, 0.2);
        }

        div[data-testid="column"] {
            padding: 0 1.5rem;
        }

        /* ============== STYLING CHECKBOX ============== */
        .stCheckbox > label {
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            color: #cbd5e1 !important;
        }

        .stCheckbox > label > span[data-baseweb="checkbox"] {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
            border-radius: 6px !important;
            border: 2px solid rgba(255, 255, 255, 0.2) !important;
            transition: all 0.3s ease !important;
        }

        .stCheckbox > label > span[data-baseweb="checkbox"]:hover {
            border-color: var(--accent-color) !important;
        }

        /* ============== STYLING KETERANGAN ============== */
        .stCaption, .main small {
            font-family: 'Inter', sans-serif !important;
            color: #64748b !important;
            font-size: 13px !important;
        }

        /* ============== ANIMASI ============== */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 var(--accent-glow); }
            50% { box-shadow: 0 0 0 10px rgba(14, 165, 233, 0); }
        }

        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }

        /* ============== STYLING SCROLLBAR ============== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #334155 0%, #1e293b 100%);
            border-radius: 10px;
            border: 2px solid rgba(15, 23, 42, 0.5);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #475569 0%, #334155 100%);
        }

        /* ============== KOLOM BERBINGKAI ============== */
        div[data-testid="stHorizontalBlock"][data-testid*="border"] {
            border-radius: 16px;
            border: 1px solid rgba(14, 165, 233, 0.2);
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
            padding: 1.5rem;
            /* box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); */
            box-shadow: none;
        }
        
        /* ============== PERBAIKAN TOMBOL COLLAPSE - POJOK KANAN ATAS ============== */
        /* Target tombol collapse/expand sidebar secara spesifik (BUKAN tombol header!) */
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapsedControl"],
        section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] [data-testid="collapsedControl"] {
            position: absolute !important;
            top: 0.5rem !important;
            right: 0.5rem !important;
            left: auto !important;
            margin: 0 !important;
            z-index: 999 !important;
        }
        
        /* Pastikan tombol collapse sidebar terlihat jelas */
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapsedControl"] button,
        section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] [data-testid="collapsedControl"] button {
            background: rgba(30, 41, 59, 0.9) !important;
            border: 1px solid rgba(14, 165, 233, 0.4) !important;
            color: #0ea5e9 !important;
            padding: 6px !important;
            border-radius: 8px !important;
            /* box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important; */
            box-shadow: none !important;
        }
        
        /* Warna ikon tombol collapse - khusus sidebar saja */
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapsedControl"] svg,
        section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg,
        section[data-testid="stSidebar"] [data-testid="collapsedControl"] svg {
            fill: #0ea5e9 !important;
            stroke: #0ea5e9 !important;
            color: #0ea5e9 !important;
        }
        
        /* Tombol header (chevron < di sidebar) - hanya berlaku di sidebar */
        section[data-testid="stSidebar"] button[kind="header"],
        section[data-testid="stSidebar"] [data-testid="stBaseButton-header"] {
            position: absolute !important;
            top: 10px !important;
            right: 10px !important;
            left: auto !important;
            margin: 0 !important;
            background: rgba(30, 41, 59, 0.95) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            color: #0ea5e9 !important;
            z-index: 999 !important;
        }
        
        section[data-testid="stSidebar"] button[kind="header"] svg,
        section[data-testid="stSidebar"] [data-testid="stBaseButton-header"] svg {
            fill: #0ea5e9 !important;
            color: #0ea5e9 !important;
        }

        /* ============== PERBAIKAN TOOLTIP ICON (HIGH CONTRAST) ============== */
        /* Target SVG Path langsung untuk coverage maksimal */
        [data-testid="stTooltipIcon"] svg, 
        [data-testid="stTooltipIcon"] > div > svg,
        .stTooltipIcon svg,
        [data-testid="stTooltipIcon"] svg path,
        [data-testid="stTooltipIcon"] svg circle,
        button[data-testid="stTooltipHoverTarget"] svg {
            fill: #fff !important; /* Sky 700 - Gelap untuk Light Mode */
            color: #0369a1 !important;
            stroke: #0369a1 !important;
            opacity: 1 !important;
        }
        
        /* Tambahkan background circle transparan agar lebih pop */
        [data-testid="stTooltipIcon"] {
            background: rgba(14, 165, 233, 0.15);
            border-radius: 50%;
            width: 18px !important;
            height: 18px !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Hover State */
        [data-testid="stTooltipIcon"]:hover svg {
            fill: #2563eb !important; /* Blue 600 */
        }
        [data-testid="stTooltipIcon"]:hover {
            background: rgba(37, 99, 235, 0.2);
        }
        
        /* Tooltip Popup Content - visible in both Light and Dark modes */
        [data-testid="stTooltipContent"],
        div[data-baseweb="tooltip"] > div {
            /* Mengikuti tema native, text inherit */
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            border-radius: 8px !important;
        }

        </style>
    """,
        unsafe_allow_html=True,
    )


# Fungsi garis pemisah dengan gradient
def garis_pemisah(warna="#0ea5e9", margin_atas=8, margin_bawah=8, tebal=1):
    """
    Menampilkan garis pemisah dengan gradient modern.
    """
    st.markdown(
        f"""
        <div style="
            margin-top: {margin_atas}px;
            margin-bottom: {margin_bawah}px;
            height: {tebal}px;
            background: linear-gradient(90deg, transparent 0%, {warna} 50%, transparent 100%);
            border-radius: 2px;
        "></div>
    """,
        unsafe_allow_html=True,
    )


# Fungsi tampilan nilai rata kanan dengan style premium
def nilai_kanan(
    nilai,
    prefix="Rp",
    font_size=14,
    warna="#94a3b8",
    bold=False,
    margin_top=0,
    margin_bottom=4,
):
    """
    Menampilkan teks hasil perhitungan di Streamlit rata kanan dengan style modern.
    Auto-scale ke Milyar atau Triliun.
    """
    # Smart auto-scale (Juta, Miliar, Triliun)
    abs_val = abs(nilai) if nilai else 0
    if abs_val >= 1_000_000_000_000:  # >= 1 Triliun
        pembagi = 1_000_000_000_000
        satuan = "Triliun"
    elif abs_val >= 1_000_000_000:  # >= 1 Miliar
        pembagi = 1_000_000_000
        satuan = "Miliar"
    elif abs_val >= 1_000_000:  # >= 1 Juta
        pembagi = 1_000_000
        satuan = "Juta"
    else:  # < 1 Juta, tampilkan apa adanya
        pembagi = 1
        satuan = ""

    # Format tanpa desimal (,00)
    formatted_value = f"{prefix} {nilai / pembagi:,.2f} {satuan}".replace(",", ".")
    font_weight = "600" if bold else "400"

    st.markdown(
        f"""
        <div style='
            text-align: right;
            font-size: {font_size}px;
            color: {warna};
            font-weight: {font_weight};
            margin-top: {margin_top}px;
            margin-bottom: {margin_bottom}px;
            font-family: "Inter", monospace;
            opacity: 0.9;
            padding: 4px 8px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 6px;
        '>
            {formatted_value}
        </div>
    """,
        unsafe_allow_html=True,
    )

    garis_pemisah(warna="rgba(148, 163, 184, 0.2)", margin_atas=4, margin_bawah=4)


def custom_button(label, key, color="red"):
    """Custom button dengan gradient styling."""
    if color == "red":
        # bg = "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
        bg = "#ef4444"
        # bg_hover = "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)"
        bg_hover = "#dc2626"
        # glow = "rgba(239, 68, 68, 0.4)"
        glow = "none"
    elif color == "blue":
        # bg = "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)"
        bg = "#0ea5e9"
        # bg_hover = "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)"
        bg_hover = "#0284c7"
        # glow = "rgba(14, 165, 233, 0.4)"
        glow = "none"
    else:
        # bg = "linear-gradient(135deg, #475569 0%, #334155 100%)"
        bg = "#475569"
        # bg_hover = "linear-gradient(135deg, #334155 0%, #1e293b 100%)"
        bg_hover = "#334155"
        # glow = "rgba(71, 85, 105, 0.4)"
        glow = "none"

    st.markdown(
        f"""
        <style>
        .custom-btn-{key} > button {{
            background: {bg} !important;
            color: white !important;
            border-radius: 12px;
            padding: 12px 28px;
            font-size: 15px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            border: none;
            /* box-shadow: 0 4px 15px {glow}; */
            box-shadow: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .custom-btn-{key} > button:hover {{
            background: {bg_hover} !important;
            transform: translateY(-2px);
            /* box-shadow: 0 8px 25px {glow}; */
            box-shadow: none;
        }}
        .custom-btn-{key} > button:active {{
            transform: translateY(0) scale(0.98);
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(f"<div class='custom-btn-{key}'>", unsafe_allow_html=True)
    clicked = st.button(label, key=key)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked


# Fungsi footer dengan gradient dan glass effect
def sidebar_footer():
    st.sidebar.markdown(
        """
        <div style="
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            /* background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%); */
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        ">
            <p style="
                font-size: 12px;
                color: #94a3b8;
                margin: 0;
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
            ">
                © 2025 - Div. Keuangan Suralaya 8<br>
                <span style="color: #0ea5e9; font-weight: 600;">PT. PLN Indonesia Power</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Fungsi Custom Subheader dengan gradient text
def custom_subheader(text, font_size="22px", color="#0ea5e9", align="left"):
    st.markdown(
        f"""
        <h3 style="
            font-size: {font_size};
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            /* background: linear-gradient(135deg, #1e3a5f 0%, {color} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text; */
            color: {color};
            text-align: {align};
            margin-top: 16px;
            margin-bottom: 12px;
            letter-spacing: -0.3px;
        ">
            {text}
        </h3>
        """,
        unsafe_allow_html=True,
    )


# Fungsi custom_caption dengan style modern
def custom_caption(text, font_size="14px", color="#64748b", align="left", italic=False):
    style_italic = "italic" if italic else "normal"

    st.markdown(
        f"""
        <p style="
            font-size: {font_size};
            font-weight: 500;
            color: {color};
            text-align: {align};
            font-style: {style_italic};
            font-family: 'Inter', sans-serif;
            margin-top: 8px;
            margin-bottom: 8px;
            line-height: 1.6;
            padding: 12px 16px;
            /* background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(234, 88, 12, 0.05) 100%); */
            background: rgba(245, 158, 11, 0.1);
            border-left: 3px solid {color};
            border-radius: 0 8px 8px 0;
        ">
            {text}
        </p>
        """,
        unsafe_allow_html=True,
    )


# Komponen Card Informasi
def info_card(title, content, icon="📌", accent_color="#0ea5e9"):
    """
    Komponen card informasi dengan glass effect.
    """
    st.markdown(
        f"""
        <div style="
            padding: 20px;
            border-radius: 16px;
            /* background: linear-gradient(135deg, rgba(30, 58, 95, 0.3) 0%, rgba(15, 23, 42, 0.5) 100%); */
            background: rgba(30, 58, 95, 0.3);
            border: 1px solid rgba(14, 165, 233, 0.2);
            /* box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); */
            box-shadow: none;
            transition: all 0.3s ease;
        ">
            <h4 style="
                margin: 0 0 12px 0;
                color: {accent_color};
                font-family: 'Poppins', sans-serif;
                font-weight: 600;
                font-size: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <span style="font-size: 20px;">{icon}</span>
                {title}
            </h4>
            <div style="
                font-size: 14px;
                color: #cbd5e1;
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
            ">
                {content}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


# Komponen Card Metrik
def metric_card(label, value, prefix="", suffix="", delta=None, delta_color="normal"):
    """
    Custom metric card dengan style premium.
    """
    delta_html = ""
    if delta is not None:
        delta_icon = "▲" if delta > 0 else "▼" if delta < 0 else "●"
        delta_class = (
            "positive" if delta > 0 else "negative" if delta < 0 else "neutral"
        )
        delta_html = (
            f'<span class="delta {delta_class}">{delta_icon} {abs(delta):.2f}%</span>'
        )

    st.markdown(
        f"""
        <style>
        .metric-card {{
            /* background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(6, 182, 212, 0.08) 100%); */
            background: rgba(14, 165, 233, 0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(14, 165, 233, 0.2);
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            /* box-shadow: 0 12px 40px rgba(14, 165, 233, 0.2); */
            box-shadow: none;
        }}
        .metric-card .label {{
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 14px;
            color: #0ea5e9;
            margin-bottom: 8px;
        }}
        .metric-card .value {{
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 28px;
            color: #f1f5f9;
        }}
        .metric-card .delta {{
            font-size: 14px;
            font-weight: 600;
            margin-left: 8px;
        }}
        .metric-card .delta.positive {{ color: #10b981; }}
        .metric-card .delta.negative {{ color: #ef4444; }}
        .metric-card .delta.neutral {{ color: #94a3b8; }}
        </style>
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{prefix}{value}{suffix} {delta_html}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )


# ============ END OF STYLE.PY ============
# Theme switching is now handled by Streamlit's native settings (Settings -> Theme)
# CSS above is designed to be adaptive and work with both Light and Dark themes.
