#!/bin/bash
# Make a schedule with 'crontab -e':
# 10 2 * * * cd /home/blog/Blog/; ./start.sh


cd $(dirname $0)
mkdir ./log -p
mkdir ./socket -p

for p in `pgrep uwsgi`
do
kill -9 $p
done

DATE=`date +%Y%m%d`
uwsgi --ini blog.ini --daemonize $PWD/log/uwsgi-${DATE}.log
