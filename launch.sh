#!/usr/bin/env bash

echo "Launching the Web application for monitoring moteinos"

SCREEN_NAME="webapp_moteinos"
INFLUX_BIN="influx"
INFLUX_DAEMON="influxd"

##########################################################
# Cleaning existing screens
##########################################################
screen -X -S $SCREEN_NAME quit || true

##########################################################
# Cleaning existing screens
##########################################################
ps aux | grep "python *sensors_crawler.py" | grep -v "grep" | awk '{ print $2 }' | xargs kill -9
ps aux | grep "python *pdus_crawler.py" | grep -v "grep" | awk '{ print $2 }' | xargs kill -9

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
        $INFLUX_BIN -execute "DROP DATABASE pidiou"
        $INFLUX_BIN -execute "CREATE DATABASE pidiou"
    fi
    screen $COMMON_SCREEN_ARGS -t influxdb bash -c "$INFLUX_DAEMON"

    sleep 10 # The DB needs some time to startup


    ##########################################################
    # Download python dependencies
    ##########################################################
    pip install -r requirements.txt

    ##########################################################
    # Launching web application (webapp)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t webapp bash -c "python server.py"

    ##########################################################
    # Launching web application (register)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t register bash -c "python register.py"

    ##########################################################
    # Launching sensors crawler (crawler)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t crawler bash -c "python sensors_crawler.py"

    ##########################################################
    # Launching sensors crawler (PDU crawler)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t pdu_crawler_1 bash -c "python pdus_crawler.py"
    # screen $COMMON_SCREEN_ARGS -t pdu_crawler_2 bash -c "python pdus_crawler.py"
    # screen $COMMON_SCREEN_ARGS -t pdu_crawler_3 bash -c "python pdus_crawler.py"
    # screen $COMMON_SCREEN_ARGS -t pdu_crawler_4 bash -c "python pdus_crawler.py"
fi

exit 0
