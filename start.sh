#!/bin/bash
DATE=`date +%Y%m%d`
uwsgi --ini blog.ini --daemonize /tmp/uwsgi-$DATE.log
