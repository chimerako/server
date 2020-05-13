#!/bin/bash

if [[ ! -f ${HOME}/.rtorrent.rc ]]; then
  echo "${HOME}/.rtorrent.rc not found! You must have rTorrent installed for your user."
  exit 1
fi

torrentid=$1
torrentname=$2
torrentpath=$3

tmpdir="${HOME}/tmp/d2r.$$"
logdir="${HOME}/log"

##############################################################
# Some config.
##############################################################
#Configurable sleep duration.
sleepdur=1800
#Destination directory
destination="/mnt/local/storage"

##############################################################
# Some setup. Should not need to adjust these variables.
##############################################################
dc="deluge-console"
dcv=$(deluge-console -v | grep deluge | awk '{printf $2}' | sed 's/.dev0//g')
dcp=$(grep daemon_port "${HOME}"/.config/deluge/core.conf | awk '{printf $2}' | sed 's/,//g')
deluge_state_dir=${HOME}/.config/deluge/state
#Location of rfr.pl https://github.com/liaralabs/kb-scripts/raw/master/deluge-to-rtorrent/rfr.pl
rtfr=${HOME}/bin/rfr.pl
#Location of pyrocore rtxmlrpc (installed via github method)
rtxmlrpc=${HOME}/bin/rtxmlrpc
##############################################################

if [[ -n $sleepdur ]]; then
  sleep ${sleepdur}
fi

case $dcv in
  1.3.*)
    dc="deluge-console connect 127.0.0.1:$dcp;"
    track="^Tracker status:"
    argsinfo=
    argsrm=
  ;;
  2.0.*)
    dc="deluge-console -p $dcp "
    track="^Tracker:"
    argsinfo="-v"
    argsrm="-c"
  ;;
esac

function on_exit() {
    rm -rf "${tmpdir}"
}

#trap on_exit EXIT

function set_tracker {
  case $1 in
    *alpharatio*)
          tracker=ar
      ;;
    *empire*|*stackoverflow*|*iptorrent*)
          tracker=ipt
      ;;
    *torrentleech*)
          tracker=tl
      ;;
        *)
          tracker=$1
          ;;
  esac
}

mkdir -p $logdir

echo "Starting transfer for $torrentname with ID $torrentid at $torrentpath" >> $logdir/d2r.log

tracker_line=$($dc "info $torrentid ${argsinfo}" | grep "$track" | awk -F: '{print $2}' | tr -d " ")
set_tracker "$tracker_line"
ratio=$($dc "info $torrentid ${argsinfo}" | grep Ratio: | awk -F "Ratio: " '{print $2}')
if [[ $dcv == "1.3."* ]]; then
  torrent_download_dir=$3
else
  torrent_download_dir=$($dc "info $torrentid -v" | grep "^Download Folder:" | awk -F: '{print $2}' | tr -d " ")
fi
#echo $tracker
#echo $ratio
#echo $ratio_rounded_down

mkdir -p "$tmpdir"

cp "${deluge_state_dir}"/"${torrentid}".torrent "${tmpdir}"

$rtfr -b "$torrent_download_dir" -d "${tmpdir}"/"${torrentid}"_fast.torrent "${deluge_state_dir}"/"${torrentid}".torrent

if [[ $? -ne 0 ]]; then
  echo "Something went wrong when converting the torrent file with $(basename "${rtfr}")"
  echo "exiting..."
  rm -rf "$tmpdir"
  exit 10
fi

# remove the torrent from deluge
$dc "rm $torrentid ${argsrm}"

$rtxmlrpc load.start '' "${tmpdir}"/"${torrentid}"_fast.torrent \
        "d.directory.set=\"$torrent_download_dir\"" "d.priority.set=2"
sleep 3
$rtxmlrpc d.custom1.set "${torrentid}" "${tracker}"
$rtxmlrpc d.custom.set "${torrentid}" deluge_ratio "${ratio}"
basepath="$($rtxmlrpc d.base_path "${torrentid}")"
#destination="${destination}"
#rtxmlrpc d.multicall2 '' "$torrentid" \
#  'd.base_path=' \
#  "d.directory.set=\"$destination\"" \
#  "execute=mv,-u,(d.base_path),\"$destination\"" \
#  'd.open='
$rtxmlrpc "d.directory.set=$torrentid,$destination"
mv "$basepath" "$destination"
$rtxmlrpc d.resume "$torrentid"
rm -rf "$tmpdir"
