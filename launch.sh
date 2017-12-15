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
    # Launching redis
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t redis bash -c "redis-server"

    ##########################################################
    # Download python dependencies
    ##########################################################
    pip install -r requirements.txt

    ##########################################################
    # Launching web application (webapp)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t webapp bash -c "python server.py"

    ##########################################################
    # Launching sensors crawler (Temperature crawler)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t temp_crawler bash -c "python temperature_serial_crawler.py --serial=/dev/ttyUSB0"

    ##########################################################
    # Launching Telegram bot that checks for failed PDUs
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t pdus_checker_telegram bash -c "python pdus_checker_telegram.py"

    ##########################################################
    # Launching sensors crawler (crawler)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t sensors_crawler bash -c "python sensors_crawler.py"

    ##########################################################
    # Launching sensors crawler (PDU crawler)
    ##########################################################
    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_10 bash -c "python pdus_crawler.py --pdu=pdu-Z1.10"
    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_11 bash -c "python pdus_crawler.py --pdu=pdu-Z1.11"

    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_20 bash -c "python pdus_crawler.py --pdu=pdu-Z1.20"
    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_21 bash -c "python pdus_crawler.py --pdu=pdu-Z1.21"

    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_40 bash -c "python pdus_crawler.py --pdu=pdu-Z1.40"
    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_41 bash -c "python pdus_crawler.py --pdu=pdu-Z1.41"

    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_50 bash -c "python pdus_crawler.py --pdu=pdu-Z1.50"
    screen $COMMON_SCREEN_ARGS -t pdu_crawler_z1_51 bash -c "python pdus_crawler.py --pdu=pdu-Z1.51"
fi

exit 0
