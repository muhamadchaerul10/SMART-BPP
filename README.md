# ⚡ Dashboard BPP Suralaya Unit 8: Early Warning System

## 🏢 Overview Project
Project ini dikembangkan untuk PT. PLN Indonesia Power Suralaya Unit 8 sebagai alat bantu pengambilan keputusan strategis (*Decision Support System*) terkait **Biaya Pokok Produksi (BPP)**. 

Aplikasi ini berfungsi sebagai **Early Warning System** yang memungkinkan manajemen untuk melakukan simulasi dan prediksi biaya produksi listrik berdasarkan variabel-variabel input yang dinamis (seperti harga bahan bakar, biaya pemeliharaan, dll).

## 🎯 Tujuan Utama
1.  **Prediksi Akurat**: Mengestimasi nilai BPP bulan depan menggunakan pendekatan Machine Learning.
2.  **Simulasi Biaya**: Memberikan kemampuan "What-If Analysis" untuk melihat dampak perubahan komponen biaya terhadap total BPP.
3.  **Transparansi Model**: Menjelaskan faktor-faktor apa saja yang mempengaruhi kenaikan/penurunan BPP menggunakan metode SHAP (SHapley Additive exPlanations).

---

## 🛠️ Arsitektur Teknis

Project ini dibangun menggunakan stack teknologi modern berbasis Python:

*   **Framework**: Streamlit
*   **Data Processing**: Pandas, NumPy
*   **Machine Learning**: TensorFlow (Keras), Scikit-Learn
*   **Visualization**: Plotly Interactive, Seaborn, Matplotlib

### Model Prediksi
Sistem ini mengintegrasikan **Ensemble Learning** dengan 4 model algoritma untuk memastikan akurasi prediksi terbaik:
1.  **Neural Network (Deep Learning)**: Untuk menangkap pola non-linear yang kompleks.
2.  **Elastic Net Regression**: Untuk menangani data dengan banyak fitur dan korelasi.
3.  **Ridge Regression**: Untuk stabilitas model pada data dengan multikolinearitas.
4.  **K-Nearest Neighbors (KNN)**: Untuk pendekatan berbasis instan/kesamaan data.

---

## 📂 Struktur Aplikasi

*   **`bpp_app.py`**: Main entry point aplikasi. Berisi logika utama dashboard dan interaksi user interface.
*   **`config.py`**: Modul konfigurasi untuk pengaturan environment dan parameter global.
*   **`style.py`**: Modul UI/UX yang menangani styling CSS, tema (Dark/Light mode), dan komponen visual kustom.

---

## 🚀 Cara Menjalankan Aplikasi

### Prasyarat
Pastikan Python 3.11+ telah terinstal di sistem Anda.

### Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### Menjalankan Server
```bash
streamlit run bpp_app.py
```
Aplikasi akan dapat diakses melalui browser di `http://localhost:8501`.

### Konfigurasi Database (Google Sheets)
Agar aplikasi dapat terhubung ke database Google Sheets, Anda perlu mengatur kredensial:

1.  Duplikasi file template config:
    ```bash
    cp .streamlit/secrets.example.toml .streamlit/secrets.toml
    ```
2.  Buka file `.streamlit/secrets.toml` dan isi dengan kredensial Google Service Account Anda (JSON Key) serta URL Spreadsheet.
3.  **Penting**: Jangan pernah mengupload file `secrets.toml` yang berisi kunci asli ke repository publik.

---

## 💡 Fitur Unggulan

*   **Dual Theme Support**: Mendukung mode Gelap (Dark) dan Terang (Light) untuk kenyamanan penggunaan di berbagai kondisi pencahayaan.
*   **Real-time Simulation**: Perhitungan ulang prediksi BPP secara instan saat parameter input diubah.
*   **Explainable AI (XAI)**: Visualisasi interpretasi model menggunakan SHAP Values (Waterfall plot, Summary plot) untuk auditabilitas keputusan mesin.

---

**PLN Indonesia Power Suralaya Unit 8**
*Simulasi & Prediksi BPP Dashboard Team*
