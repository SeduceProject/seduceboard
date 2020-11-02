#!/bin/bash
SERVICES=$(ls *.service | sed 's/\.service//')

if [ -z "$SERVICES" ]; then
	echo "Set default service names"
	SERVICES="api dashboard entech-crawler inrow-crawler pdu-Z1-10 pdu-Z1-11 pdu-Z1-20 pdu-Z1-21 \
		pdu-Z1-40 pdu-Z1-41 pdu-Z1-50 pdu-Z1-51 poe-crawler sensors-crawler temperature-server"
fi

for s in $SERVICES; do
	displayed=""
	info=$(systemctl list-units | grep $s | awk '{ print $2,$3,$4 }')
	if [ -z "$info" ]; then
		# The service is not running
		displayed="yes"
		if [ -e "/etc/systemd/system/$s.service" ]; then
			echo -e "- \e[31m$s\e[39m (try to start it)"
		else
			echo -e "- \e[31m$s\e[39m (no SystemD service file)"
		fi
	fi
	check=$(echo $info | grep " active")
	if [ -n "$check" ]; then
		# The service is active
		displayed="yes"
		echo -e "+ \e[32m$s\e[39m"
	fi
	check=$(echo $info | grep " failed")
	if [ -n "$check" ]; then
		# The service fails to startup
		displayed="yes"
		echo -e "- \e[31m$s\e[39m (try to restart it)"
	fi
	if [ -z "$displayed" ]; then
		# Other service status
		echo -e "+ \e[31m$s\e[39m [NOT PRINTED]"
	fi
done
