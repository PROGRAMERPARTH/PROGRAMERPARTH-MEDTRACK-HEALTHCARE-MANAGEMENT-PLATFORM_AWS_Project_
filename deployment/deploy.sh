#!/usr/bin/env bash
# ==============================================================================
# MedTrack AWS EC2 Deployment Script (Amazon Linux 2023 / RHEL / Ubuntu)
# ==============================================================================
set -euo pipefail

APP_DIR="/var/www/medtrack"
VENV_DIR="${APP_DIR}/venv"
APP_USER="ec2-user"

echo "==> [1/6] Updating system packages & installing dependencies..."
if command -v dnf &> /dev/null; then
    sudo dnf update -y
    sudo dnf install -y python3.11 python3.11-pip python3.11-devel nginx git
elif command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv nginx git
fi

echo "==> [2/6] Setting up project directory and virtualenv..."
sudo mkdir -p ${APP_DIR}
sudo chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv ${VENV_DIR}
fi

source ${VENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r ${APP_DIR}/requirements.txt

echo "==> [3/6] Setting up environment variables..."
if [ ! -f "${APP_DIR}/.env" ]; then
    cp ${APP_DIR}/.env.example ${APP_DIR}/.env
    echo "Generated default .env file from .env.example. Please review AWS and SECRET_KEY values."
fi

echo "==> [4/6] Configuring Nginx..."
sudo cp ${APP_DIR}/deployment/nginx.conf /etc/nginx/conf.d/medtrack.conf
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "==> [5/6] Configuring systemd Gunicorn service..."
sudo cp ${APP_DIR}/deployment/medtrack.service /etc/systemd/system/medtrack.service
sudo systemctl daemon-reload
sudo systemctl enable medtrack
sudo systemctl restart medtrack

echo "==> [6/6] Verifying service health..."
sleep 2
curl -f http://127.0.0.1/health || (echo "Health check failed!" && exit 1)

echo "=============================================================================="
echo "MedTrack successfully deployed and operational on AWS EC2!"
echo "Health Check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo 'localhost')/health"
echo "=============================================================================="
