#!/bin/bash -e

sudo apt update
sudo apt-get install sysstat

sudo sed -i 's/ENABLED=.*/ENABLED="true"/g' /etc/default/sysstat

sudo rm -f /etc/cron.d/sysstat

cat <<EOF > /etc/cron.d/sysstat
# The first element of the path is a directory where the debian-sa1
# script is located
PATH=/usr/lib/sysstat:/usr/sbin:/usr/sbin:/usr/bin:/sbin:/bin

# Activity reports every 2 minutes everyday
*/2 * * * * root command -v debian-sa1 > /dev/null && debian-sa1 1 1

# Additional run at 23:59 to rotate the statistics file
59 23 * * * root command -v debian-sa1 > /dev/null && debian-sa1 60 2

EOF

sudo sed -i 's/HISTORY=.*/HISTORY=10/g' /etc/sysstat/sysstat

sudo service sysstat restart
