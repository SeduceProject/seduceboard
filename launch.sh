#!/usr/bin/env bash

echo "Launching the Web application for monitoring moteinos"

SCREEN_NAME="webapp_moteinos"

##########################################################
# Cleaning existing screens
##########################################################
screen -X -S $SCREEN_NAME quit || true

##########################################################
# Cleaning existing screens
##########################################################
ps aux | grep "python /root/ds18b20/sensors_crawler.py" | grep -v "grep" | awk '{ print $2 }' | xargs kill -9

if [ "$1" != "kill" ]; then

    ##########################################################
    # Configure a screen
    ##########################################################
    COMMON_SCREEN_ARGS="-S $SCREEN_NAME -X screen"
    screen -AdmS $SCREEN_NAME

    ##########################################################
    # Launching InfluxDB
    ##########################################################
    if [ "$1" == "drop_db" ]; then
        /root/influxdb-1.3.4-1/usr/bin/influx -execute "DROP DATABASE pidiou"
        /root/influxdb-1.3.4-1/usr/bin/influx -execute "CREATE DATABASE pidiou"
    fi
    screen $COMMON_SCREEN_ARGS -t influxdb bash -c "/root/influxdb-1.3.4-1/usr/bin/influxd"

    sleep 10 # The DB needs some time to startup


    ##########################################################
    # Download python dependencies
    ##########################################################
    pip install -r /root/ds18b20/requirements.txt

    ##########################################################
    # Launching web application (webapp)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t webapp bash -c "python /root/ds18b20/server.py"

    ##########################################################
    # Launching web application (register)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t register bash -c "python /root/ds18b20/register.py"

    ##########################################################
    # Launching sensors crawler (crawler)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t crawler bash -c "python /root/ds18b20/sensors_crawler.py"
fi

exit 0
