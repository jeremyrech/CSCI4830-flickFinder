#!/bin/bash
set -e  # exit on error

USER_NAME=$(whoami)
IP=$(curl -s ifconfig.me)
DIR_WORKSPACE=CSCI4830-flickFinder

### configure gunicorn ###
# create gunicorn socket
sudo tee /etc/systemd/system/gunicorn.socket > /dev/null << EOF
[Unit]
Description=Python and Django

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
EOF

# configure gunicorn service
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

# enable and start Gunicorn:
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn.service





### Configuring Nginx ###
# create Nginx config
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

# Run collectstatic to Gather Static Files
python manage.py collectstatic --noinput

# Update File Permission
cd /home/$USER_NAME/$DIR_WORKSPACE/static/
sudo chmod +x ~/
sudo find . -type d -exec chmod 755 {} \;
sudo find . -type f -exec chmod 644 {} \;
sudo chown -R www-data:www-data .

# enable Nginix config
sudo ln -s /etc/nginx/sites-available/djangoProject /etc/nginx/sites-enabled/

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo ufw allow 'Nginx Full'
