#!/bin/bash

torrentid=$1
torrentname=$2
torrentpath=$3

x=1

ddport=$(grep '"daemon_port": [0-9]*' ~/.config/deluge/core.conf | awk -F ': ' '{print $2}' | awk -F ',' '{print $1}')
sleep 300
deluge-console -d localhost -p $ddport move $torrentid /data/long_term
