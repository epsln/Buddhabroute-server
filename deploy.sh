#/bin/bash
handle_nginx() {
    echo 'checking for diff with nginx.conf...'
    if ! diff configs/nginx.conf /etc/nginx/nginx.conf; then
        while true; do
            read -p "Do you wish to copy new file" yn
            case $yn in
                [Yy]* ) cp configs/nginx.conf /etc/nginx/nginx.conf; nginx -s reload; break;;
                [Nn]* ) exit;;
                * ) echo "Please answer yes or no.";;
            esac
        done
    else
        echo 'No diff found on nginx.conf'
    fi
}

handle_gunicorn() {
    echo 'checking for diff with gunicorn.service'
    if ! diff configs/gunicorn.service /etc/systemd/system/gunicorn.service; then
        while true; do
            read -p "Do you wish to copy new file" yn
            case $yn in
                [Yy]* ) cp configs/gunicorn.service /etc/systemd/system/gunicorn.service; systemctl daemon-reload && systemctl restart gunicorn.service; break;;
                [Nn]* ) exit;;
                * ) echo "Please answer yes or no.";;
            esac
        done
    else
        echo 'No diff found on nginx.conf'
    fi
}

if [ $UID == 0 ] ; then
    echo 'do not run as root'
    exit
fi

cd /opt/buddhabroute/Buddhabroute-server/
git branch
echo 'pulling in 5 sec'
sleep 5
git pull
handle_nginx
handle_gunicorn
systemctl  restart gunicorn.service
