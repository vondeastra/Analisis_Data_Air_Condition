# 🌫️ Air Quality Dashboard

Dashboard interaktif berbasis **Streamlit** untuk menganalisis kualitas udara berdasarkan station, waktu, musim, dan kategori PM2.5.

---

## 📁 Struktur Folder

```text
submission/
├── dashboard/
│   ├── dashboard.py
│   └── main_data.csv
├── data/
│   ├── data_1.csv
│   └── data_2.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

---

## ⚙️ Setup Environment - Anaconda

Buka **Anaconda Prompt**, lalu jalankan:

```bash
conda create --name main-ds python=3.12
conda activate main-ds
pip install -r requirements.txt
```

Jika environment sudah pernah dibuat:

```bash
conda activate main-ds
```

---

## ⚙️ Setup Environment - Terminal / VS Code

Jika menggunakan terminal biasa:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 Cara Menjalankan Dashboard

Pastikan berada di folder `submission`, lalu jalankan:

```bash
streamlit run dashboard/dashboard.py
```

---

## 🌐 Akses Dashboard

Setelah dijalankan, buka di browser:

```text
http://localhost:8501
```

---

## ⚠️ Catatan

* Pastikan file `main_data.csv` berada di folder `dashboard/`
* Jangan mengubah struktur folder
* Gunakan Python versi 3.10 atau lebih baru
* Jika terjadi error, pastikan semua library sudah terinstall

---

## 👨‍💻 Author

**Muhammad Devin Rahadi**
Project: Analisis Data Kualitas Udara
