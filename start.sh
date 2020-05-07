#!/bin/bash
# filename: start.sh
# Author: lufei
# Date: 20200429 14:57:16


inst_needed() {
    echo $su_pass | su - root -c "yum install platform-python-devel \
	    nginx mariadb-server mariadb-connector-c-devel gcc -y "
    $pip  install --user Django django-ratelimit-backend \
        django-tinymce uWSGI mysqlclient
}


gen_files() {
    local ng_tmp=/tmp/nginx.tmp
    local my_tmp=/tmp/mysql.tmp
    cat > $ng_tmp << eof
# blog.conf
upstream django {
    server unix://$socket;
}
server {
    listen      $port;
    server_name $server_name;
    charset     utf-8;
    client_max_body_size 75M;
    location /static {
        alias $blog_root/home/static;
    }
    location / {
        uwsgi_pass  django;
	client_body_temp_path $nginx_temp_path;
        include     $blog_root/blog/uwsgi_params;
    }
}
eof
    cat > $my_tmp << eof
[client]
database = $db_name
user = $db_user
password = $db_pass
default-character-set = utf8
eof
    echo $su_pass | su - root -c "mv $ng_tmp $nginx_cnf_file"
    echo $su_pass | su - root -c "mv $my_tmp $mysql_cnf_file"
}

customise_setting() {
    echo "set ALLOWED_HOSTS to $server_name"
    sed -i "s/ALLOWED_HOSTS\(.*\)/ALLOWED_HOSTS = [u\"$server_name\"]/g" \
	    $blog_root/blog/settings.py
    echo "set DEBUG to False"
    sed -i 's/DEBUG\(.*\)/DEBUG = False/g' $blog_root/blog/settings.py
    echo "set DATABASES to db_mysql"
    sed -i 's/DATABASES\(.*\)/DATABASES = db_mysql/g' \
	    $blog_root/blog/settings.py

}

start_blog() {
    DATE=`date +%Y%m%d`
    cd $blog_root
    /home/xx01/.local/bin/uwsgi --ini $blog_root/blog.ini --daemonize \
	    $blog_root/log/uwsgi-${DATE}.log
    
}

start_server() {
    echo $su_pass | su - root -c "systemctl start nginx"
    echo $su_pass | su - root -c "systemctl start mariadb"
    start_blog
}

restart() {
    DATE=`date +%Y%m%d`
    killall -9 uwsgi
    start_blog
}


set_env() {
    echo $su_pass | su - root -c "setsebool -P httpd_read_user_content 1"
    echo $su_pass | su - root -c "firewall-cmd --add-service=http --permanent; \
        firewall-cmd --reload"
}

backup() {
    DATE=`date +%Y%m%d`
    mysqldump --defaults-file=$mysql_cnf_file --databases $db_name \
         > /tmp/${db_name}-${DATE}.sql

}

send() {
    backup
    local remail=$1
    local msg="backup for $server_name."
    echo $msg | mail -s "Today's Backup -- from lufy.org" -a \
         /tmp/${db_name}-${DATE}.sql $remail
    ## unfinished ..
}
deploy() {
    read -s -p "Enter root password: " su_pass
    read -s -p "Enter db password: " db_pass
    inst_needed
    gen_files
    customise_setting
    set_env
    start_blog
}

help() {
    local execution=$0
    cat << eof
Usage:
$execution OPTION

OPTIONS:
deploy               deploy from minimal OS
help                 show help
restart              restart blog
send <emailaddr>     send backup email, e.g. $execution send lufy@lufy.org
...   
eof
}

main() {
    blog_root=`pwd`
    pip=pip3
    mysql_cnf_file=/etc/blog.cnf
    db_name=blog
    db_user=blogadmin

    nginx_cnf_file=/etc/nginx/conf.d/blog.conf
    socket=$blog_root/socket/blog.sock
    port=80
    server_name=lufy.org
    ## nginx cannot access tmp directory in user home
    nginx_temp_path=/var/lib/nginx/tmp/

    local op=${1--h}
    shift
    if [ $op == "-h" ]; then
        op=help
    fi
    $op $@
}

if [ $0 == "./start.sh" ]; then
    main $@
fi

## issues
# port issue
# nginx cannot access socket file in  user home

## mysql operations
#  create user
#  create database
#  grant user

## then
# ./manage.py makemigrations
# ./manage.py migrate

# ln  /home/xx01/.local/lib/python3.6/site-packages/django/contrib/admin/static/admin/ home/static/ -s
# ln /home/xx01/.local/lib/python3.6/site-packages/tinymce/static/django_tinymce/ -s home/static/
# ln /home/xx01/.local/lib/python3.6/site-packages/tinymce/static/tinymce/ -s home/static/
# set user username in /etc/nginx/nginx.conf
