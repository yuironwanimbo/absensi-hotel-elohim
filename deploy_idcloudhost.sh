#!/bin/bash
# Deployment script for IdCloudhost VPS

set -e

APP_DIR="/var/www/absensi"

echo "Installing dependencies..."
apt update
apt install -y python3-pip python3-venv nginx git curl \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1

echo "Cloning project..."
mkdir -p $APP_DIR
cd $APP_DIR
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/yuironwanimbo/absensi-hotel-elohim.git .
fi

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt gunicorn

# Setup environment
mkdir -p $APP_DIR/instance
cat > $APP_DIR/.env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:////$APP_DIR/instance/hotel_attendance.db
HOTEL_LAT=-2.576
HOTEL_LNG=140.516
RADIUS_METERS=100
EOF

# Setup systemd service
tee > /etc/systemd/system/absensi.service << EOF
[Unit]
Description=Absensi Hotel Flask App
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable absensi
systemctl start absensi

# Setup Nginx
tee > /etc/nginx/sites-available/absensi << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/absensi /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "Deployment selesai! Akses via http://IP_SERVER_ANDA"