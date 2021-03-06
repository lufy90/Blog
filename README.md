# ssblog

## About this app
This is a very simple dajngo blog app.
Only appropriate for linux OS
Django version: 1.10.4 
OS: Centos 7.0
Python: 2.7 
Requires:
pip install django-tinymce uwsgi pymysql django-ratelimit-backend 


## Try this app:
1. Clone the codes to your linux:
```# git clone git@github.com:lufy90/Blog```
2. Edit the setting.py about the host address, change ```ALLOWD_HOSTS``` to your
address:
```
# vim blog/setting.py
ALLOWED_HOSTS = [u'192.168.10.10']
```
3. Create database, default make a sqlite3 database at app root dir.
```
./manage.py migrate
```
   Some times this only creates the application admin tables, tables of `home` will not be created. This could be solved by:
```
./manage.py makemigrations
./manage.py migrate
```
4. Then you can run the server within Blog directory:
```# ./manager runserver 0.0.0.0:8000```
5. Create super user
```# ./manager.py createsuperuser ```
6. Change user password
```# ./manager.py changepassword ```

## Deploy this app as your real blog:
The former trying steps are just for preview. If you're
 willing to make it run as a real blog, then do the next steps:
1. touch mysql config file:
```
# cat /etc/my-blog.cnf
[client]
database = <dbname>
user = <dbuser>
password = <dbpassword>
default-character-set = utf8
```
2. Edit ```blog/setting```, set the ```DATABASES``` to be using ```db_mysql```: 
```DATABASES = db_mysql```

3. Then run:
```#./start.sh```

If you have the right firewall and network configuration, now the site can be 
visited from browser:
http://192.168.10.10:8000

## Sample for nginx setting:
```
# cat blog.conf
upstream django {
    server unix:///home/Blog/socket/blog.sock;
}
server {
    listen      80;
    server_name blog.com;
    charset     utf-8;
    client_max_body_size 75M;
    location /static {
        alias /home/Blog/home/static;
    }
    location / {
        uwsgi_pass  django;
        include     /home/Blog/blog/uwsgi_params;
    }
}
```
## Sample for mysql config:
```
# cat /etc/blog.cnf
[client]
database = <dbname>
user = <dbuser>
password = <dbpassword>
default-character-set = utf8
```

## Note
20190727
Do more limitations on making comments
1. Text length
2. Key words filter, with customised validation in /home/models.py

20191008
Change model.py for adapting python3.6 and django 2.2.6, on centos 8
Change pymsyql to mysqlclient, for resolving the following issue:
ISSUE: django.core.exceptions.ImproperlyConfigured: mysqlclient 1.3.13 or newer is required; you have 0.9.3.
Changed files on host lufy.org:
1. blog/__init__.py       -- about pymysql
2. home/models.py         -- about foreign keys
