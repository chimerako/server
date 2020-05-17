#!/bin/bash

# Change the below output location to any folder owned by your user for which you have write permissions
OUTPUT="/home/chimerako/log/"

torrentid=$1
torrentname=$2
torrentpath=$3

ddport=$(grep '"daemon_port": [0-9]*' ~/.config/deluge/core.conf | awk -F ': ' '{print $2}' | awk -F ',' '{print $1}')

x=1
while [ $x -le 1000 ]
do
  sleep 5
  #echo "Running $x times" >> "${OUTPUT}/reannounce.log"
  #echo "TorrentID: $torrentid" >> "${OUTPUT}/reannounce.log"
  line=$(deluge-console -d localhost -p $ddport info -d $torrentid | grep "Tracker status")
  #echo $line >> "${OUTPUT}/reannounce.log"
  case "$line" in *Unregistered*|*unregistered*|*Sent*|*End*of*file*|*Bad*Gateway*|*Error*)
        deluge-console -d localhost -p $ddport update_tracker $torrentid >> "${OUTPUT}/deluge.output" 2>&1
        ;;
    *)
        #echo "Found working torrent: $torrentname $torrentpath $torrentid" >> "${OUTPUT}/reannounce.log" 2>&1
        exit 1
        ;;
  esac
  x=$(( $x + 1 ))
done
