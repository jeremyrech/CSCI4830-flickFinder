#!/bin/bash
USER_NAME=$(whoami)
IP=$(curl -s ifconfig.me)
DIR_WORKSPACE=CSCI4830-flickFinder

# Enter directory and activate virtual environment
cd $HOME/$DIR_WORKSPACE
source web_environment/bin/activate

### Configure Gunicorn ###
# Create Gunicorn socket
sudo tee /etc/systemd/system/gunicorn.socket > /dev/null << EOF
[Unit]
Description=Python and Django

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
EOF

# Configure Gunicorn service
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << EOF
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=/home/$USER_NAME/$DIR_WORKSPACE
ExecStart=/home/$USER_NAME/$DIR_WORKSPACE/web_environment/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    djangoProject.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Enable and start Gunicorn:
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn

### Configuring Nginx ###
# Install Nginx
sudo apt install nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/djangoProject > /dev/null << EOF
server {
    listen 80;
    server_name $IP;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias /home/$USER_NAME/$DIR_WORKSPACE/static/;
    }

    location / {
            include proxy_params;
            proxy_pass http://unix:/run/gunicorn.sock;
        }
}
EOF

# Run collectstatic to gather static files
python manage.py collectstatic --noinput

# Update file permissions
cd /home/$USER_NAME/$DIR_WORKSPACE
sudo chmod +x ~/
sudo find static/ -type d -exec chmod 755 {} \;
sudo find static/ -type f -exec chmod 644 {} \;
sudo chown -R www-data:www-data static/

# Enable Nginix config
sudo ln -s /etc/nginx/sites-available/djangoProject /etc/nginx/sites-enabled/

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'