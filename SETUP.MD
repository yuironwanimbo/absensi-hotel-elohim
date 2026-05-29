# Setup IdCloudhost VPS

## Order VPS
1. https://console.idcloudhost.com/app/billing/create
2. Pilih: Linux → Ubuntu 22.04 LTS
3. Pilih paket Mikro (Rp50.000-100.000/tahun)

## Setelah aktif
1. Login ke console → dapatkan IP Address
2. SSH ke server:
```bash
ssh root@IP_SERVER_ANDA
```

## Install
```bash
# Update
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-venv nginx git

# Clone project
cd /var/www
git clone https://github.com/yuironwanimbo/absensi-hotel-elohim.git
cd absensi-hotel-elohim

# Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env
cat > .env << EOF
SECRET_KEY=generate-random-key-anda
DATABASE_URL=sqlite:///hotel_attendance.db
HOTEL_LAT=-2.576
HOTEL_LNG=140.516
RADIUS_METERS=100
EOF

# Test run
python run.py
```

## Setup Production
Buka terminal baru, jalankan script:
```bash
wget https://raw.githubusercontent.com/yuironwanimbo/absensi-hotel-elohim/main/deploy_idcloudhost.sh
chmod +x deploy_idcloudhost.sh
./deploy_idcloudhost.sh
```

## Test
Buka browser ke IP server Anda.