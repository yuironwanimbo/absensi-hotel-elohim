# Quick IdCloudhost Setup

## Langkah 1: Order VPS
Di console IdCloudhost Anda sudah login. Pilih:
- Menu: VPS → Order VPS
- OS: Ubuntu 22.04 LTS
- Paket: Mikro (Rp50rb/tahun)
- Storage: 20GB

## Langkah 2: SSH ke Server
Setelah order, dapatkan IP dari email atau dashboard.
```bash
ssh root@IP_SERVER_ANDA
```

## Langkah 3: Deploy Script
Jalankan di server:
```bash
wget https://raw.githubusercontent.com/yuironwanimbo/absensi-hotel-elohim/main/deploy_idcloudhost.sh
chmod +x deploy_idcloudhost.sh  
./deploy_idcloudhost.sh
```

## Langkah 4: Done
Buka IP server di browser.