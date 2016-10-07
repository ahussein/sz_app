#!/bin/bash

sudo su -
# install mongodb

apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
echo "deb http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.3 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.4.list
apt-get update
apt-get install -y mongodb-org-unstable

cat > /lib/systemd/system/mongod.service <<EOF
[Unit]
Description=High-performance, schema-free document-oriented database
After=network.target
Documentation=https://docs.mongodb.org/manual

[Service]
User=mongodb
Group=mongodb
ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf

[Install]
WantedBy=multi-user.target
EOF

/usr/bin/mongod --quiet --config /etc/mongod.conf&

# install pip and virtualenv
apt-get install -y python-pip
pip install --upgrade pip
pip install virtualenv

cd /opt/sz_app/app
env/bin/pip install -r requirements.txt