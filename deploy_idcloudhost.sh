#!/bin/bash
# Deployment script for IdCloudhost VPS

set -e

APP_DIR="/var/www/absensi"
PYTHON_VERSION="3.11"

sudo apt update
sudo apt install -y python3-pip python3-venv nginx git

sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

git clone https://github.com/yuironwanimbo/absensi-hotel-elohim.git $APP_DIR

cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:////$APP_DIR/instance/hotel_attendance.db
HOTEL_LAT=-2.576
HOTEL_LNG=140.516
RADIUS_METERS=100
EOF

# Setup systemd service
sudo tee > /etc/systemd/system/absensi.service << EOF
[Unit]
Description=Absensi Hotel Flask App
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable absensi
sudo systemctl start absensi

# Setup Nginx
sudo tee > /etc/nginx/sites-available/absensi << EOF
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

sudo ln -sf /etc/nginx/sites-available/absensi /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "Deployment selesai! Akses via IP server Anda."