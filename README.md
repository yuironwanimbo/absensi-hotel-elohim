# Sistem Absensi Hotel

Sistem absensi hotel dengan fitur face recognition dan GPS.

## Fitur
- Login karyawan
- Face Recognition untuk absen masuk/pulang
- Deteksi lokasi GPS (radius 100m dari hotel)
- Dashboard admin
- Riwayat absensi
- Export PDF/Excel
- Multi role (Admin, HRD, Karyawan)
- Keterangan terlambat otomatis

## Instalasi

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Buat database MySQL:
```sql
CREATE DATABASE hotel_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Set environment variables:
```bash
export SECRET_KEY=your-secret-key
export DATABASE_URL=mysql://user:password@localhost/hotel_attendance
```

4. Jalankan aplikasi:
```bash
python run.py
```

## Setup Karyawan

1. Daftar user baru via database atau Flask shell
2. Jalankan `python face_utils.py enroll <user_id>` untuk daftar wajah
3. User dapat login dan absen menggunakan kamera

## Teknologi
- Backend: Flask, SQLAlchemy
- Face Recognition: face_recognition, OpenCV
- Database: MySQL
- Frontend: Bootstrap 5

## Konfigurasi Lokasi Hotel
Edit file `config.py`:
```python
HOTEL_LAT = -2.576
HOTEL_LNG = 140.516
RADIUS_METERS = 100
```