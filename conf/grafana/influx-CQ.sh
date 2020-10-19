#!/bin/bash

influx -database pidiou -execute "CREATE CONTINUOUS QUERY aggregated_servers_Z1_1 ON pidiou BEGIN \
  SELECT SUM(value) INTO aggregated_Z1_1 FROM sensors \
  WHERE sensor =~ /ecotype.*Z1.1/ \
  GROUP BY location, time(1s) \
END"
influx -database pidiou -execute "CREATE CONTINUOUS QUERY aggregated_servers_Z1_2 ON pidiou BEGIN \
  SELECT SUM(value) INTO aggregated_Z1_2 FROM sensors \
  WHERE sensor =~ /ecotype.*Z1.2/ \
  GROUP BY location, time(1s) \
END"
influx -database pidiou -execute "CREATE CONTINUOUS QUERY aggregated_servers_Z1_4 ON pidiou BEGIN \
  SELECT SUM(value) INTO aggregated_Z1_4 FROM sensors \
  WHERE sensor =~ /ecotype.*Z1.4/ \
  GROUP BY location, time(1s) \
END"
influx -database pidiou -execute "CREATE CONTINUOUS QUERY aggregated_servers_Z1_5 ON pidiou BEGIN \
  SELECT SUM(value) INTO aggregated_Z1_5 FROM sensors \
  WHERE sensor =~ /ecotype.*Z1.5/ \
  GROUP BY location, time(1s) \
END"
