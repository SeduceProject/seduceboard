#!/bin/bash
###
# Compute the maximum production of electricity from the solar panels.
###
DB_NAME="mondb"
# Date syntax YYYY-MM-DD
DAYS="2021-03-17 2021-03-18 2021-03-19 2021-03-20 \
    2021-04-01 2021-04-02 2021-04-03 2021-04-04 \
    2021-04-05 2021-04-06 2021-04-07 2021-04-08 \
    2021-04-09"
# We assume the maximum production is between 10 AM and 12 PM (UTC). Be careful influx use UTC times
BEGIN_HOUR="10:00:00"
END_HOUR="12:00:00"
# if empty, compute the mean of production power and consumption power every minute
AGGREGATED=""

echo "Delete old values"
influx -database $DB_NAME -execute "drop measurement prod_1m"
influx -database $DB_NAME -execute "drop measurement cons_1m"
influx -database $DB_NAME -execute "drop measurement prod_cons"
influx -database $DB_NAME -execute "drop measurement diff_energy"


if [ -z "$AGGREGATED" ]; then
    for day in $DAYS; do
        echo "Computing max values for $day"
        # FILL(previous) will insert the previous value calculated on the last 1-minute interval
        # If no value exists (due to monitoring system failure), the same value will be repeated again and again
        query="SELECT MEAN(value) INTO prod_1m FROM sensors WHERE sensor =~ /solar.*_P_AC/ AND \
            time > '${day}T${BEGIN_HOUR}Z' and time < '${day}T${END_HOUR}Z' \
            GROUP BY time(1m),sensor;"
        influx -database $DB_NAME -execute "$query"
        query="SELECT MEAN(value) INTO cons_1m FROM sensors WHERE sensor =~ /ecotype.*/ AND \
            time > '${day}T${BEGIN_HOUR}Z' and time < '${day}T${END_HOUR}Z' \
            GROUP BY time(1m),sensor;"
        influx -database $DB_NAME -execute "$query"
    done
fi
for day in $DAYS; do
    echo "############## $day #################"
    # Get the maximum production of energy
    #query="SELECT MAX(sum) FROM (SELECT SUM(max) FROM max_prod WHERE \
    #    time > '${day}T${BEGIN_HOUR}Z' and time < '${day}T${END_HOUR}Z' GROUP BY time(1m));"

    # Sum the productions and the consumptions every 1-minute interval
    query="SELECT SUM(mean) as total_prod into prod_cons FROM prod_1m WHERE \
        time > '${day}T${BEGIN_HOUR}Z' and time < '${day}T${END_HOUR}Z' GROUP BY time(1m);"
    influx -database $DB_NAME -precision "rfc3339" -execute "$query"
    query="SELECT SUM(mean) as total_cons into prod_cons FROM cons_1m WHERE \
        time > '${day}T${BEGIN_HOUR}Z' and time < '${day}T${END_HOUR}Z' GROUP BY time(1m);"
    influx -database $DB_NAME -precision "rfc3339" -execute "$query"
done

# Create a measurement with the difference
query="SELECT total_prod - total_cons AS value INTO diff_energy FROM prod_cons"
influx -database $DB_NAME -precision "rfc3339" -execute "$query"
