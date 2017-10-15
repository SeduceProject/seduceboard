#!/usr/bin/env bash

echo "Launching the Web application for monitoring moteinos"

SCREEN_NAME="webapp_moteinos"
INFLUX_PATH="/root/influxdb-1.3.4-1/usr/bin"
INFLUX_BIN="/$INFLUX_PATH/influx"
INFLUX_DAEMON="$INFLUX_PATH/influxd"

##########################################################
# Cleaning existing screens
##########################################################
screen -X -S $SCREEN_NAME quit || true

##########################################################
# Cleaning existing screens
##########################################################
ps aux | grep "python *sensors_crawler.py" | grep -v "grep" | awk '{ print $2 }' | xargs kill -9

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
        $INFLUX_EXECUTABLE -execute "DROP DATABASE pidiou"
        $INFLUX_EXECUTABLE -execute "CREATE DATABASE pidiou"
    fi
    screen $COMMON_SCREEN_ARGS -t influxdb bash -c "$INFLUX_DAEMON_EXECUTABLE"

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
fi

exit 0
