#/bin/bash
handle_nginx() {
    echo 'checking for diff with nginx.conf...'
    if ! diff configs/nginx.conf /etc/nginx/nginx.conf; then
        while true; do
            read -p "Do you wish to copy new file ? [y/n] >" yn
            case $yn in
                [Yy]* ) 
                    echo 'cp configs/nginx.conf /etc/nginx/nginx.conf';
                    sudo cp configs/nginx.conf /etc/nginx/nginx.conf;
                    echo 'nginx -s reload';
                    sudo nginx -s reload;
                    break;;
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
            read -p "Do you wish to copy new file ? [y/n] >" yn
            case $yn in
                [Yy]* ) 
                    echo 'cp configs/gunicorn.service /etc/systemd/system/gunicorn.service';
                    sudo cp configs/gunicorn.service /etc/systemd/system/gunicorn.service;
                    echo 'systemctl daemon-reload && sudo systemctl restart gunicorn.service';
                    sudo systemctl daemon-reload && sudo systemctl restart gunicorn.service;
                    break;;
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

git branch
echo 'pulling in 5 sec'
#sleep 5
git pull
handle_nginx
handle_gunicorn
