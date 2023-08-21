# Buddhabroute server

Server for collecting and computing checkpoint from https://github.com/epsln/Buddhabroute-client

# install
```
useradd -md /opt/buddhabroute/ buddhabroute
apt install git nginx python3-virtualenv python3-pip
cd /opt/buddhabroute/
git clone [URL] buddhabroute-server
cd /opt/buddhabroute/buddhabroute-server
virtualenv .
source bin/activate
pip install -r requirements
cp configs/nginx.conf /etc/nginx/nginx.conf
cp configs/gunicorn.service /etc/systemd/system/
systemctl enable -now nginx.service gunicorn.service
```
