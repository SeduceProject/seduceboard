/**
 * Load new data depending on the selected min and max
 */

Highcharts.setOptions({
	global: {
		useUTC: false
	}
});

function hc_create_chart(hc_options) {

    var hc_series_index = {},
        hc_last_successful_update = undefined,
        hc_redraw = false,
        navigator_data = [],
        enable_data_downsample = false,
        downsample_scale = undefined,
        div_id = "container",
        plot_title = "Title",
        plot_subtitle = "SubTitle",
        plot_type = "line",
        sensor_type = "*",
        aggregated = false,
        show_range = false,
        navigator_data_url = undefined,
        selected_sensor = undefined,
        hc_enable_streaming = true,
        hc_snap_to_right_edge = true;

    if ("div_id" in hc_options) {
        div_id = hc_options["div_id"];
    }

    if ("title" in hc_options) {
        plot_title = hc_options["title"];
    }

    if ("subtitle" in hc_options) {
        plot_subtitle = hc_options["subtitle"];
    }

    if ("plot_type" in hc_options) {
        plot_type = hc_options["plot_type"];
    }

    if ("sensor_type" in hc_options) {
        sensor_type = hc_options["sensor_type"];
    }

    if ("aggregated" in hc_options) {
        aggregated = hc_options["aggregated"];
    }

    if ("show_range" in hc_options) {
        show_range = hc_options["show_range"];
    }

    if ("navigator_data_url" in hc_options) {
        navigator_data_url = hc_options["navigator_data_url"];
    }

    if ("selected_sensor" in hc_options) {
        selected_sensor = hc_options["selected_sensor"];
    }

    function load_aggregated_data(chart, streaming=false, range_options={}) {

        if (! streaming) {
            chart.showLoading('Loading data from server...');
        }

        let serie_name = sensor_type+"_aggregated";

        if (! (serie_name in hc_series_index)) {

            hc_series_index[serie_name] = {};

            chart.addSeries({
                name: serie_name,
                data: [],
                zIndex: 1,
                "showInNavigator": false,
                marker: {
                    fillColor: 'white',
                    lineWidth: 2,
                    lineColor: Highcharts.getOptions().colors[0]
                },
                dataGrouping: {
                    enabled: false
                }
            });

            if (show_range) {
                chart.addSeries({
                    name: serie_name+"_range",
                    data: [],
                    type: 'arearange',
                    lineWidth: 0,
                    linkedTo: ':previous',
                    color: Highcharts.getOptions().colors[0],
                    fillOpacity: 0.3,
                    zIndex: 0,
                    marker: {
                        enabled: false
                    },
                    dataGrouping: {
                        enabled: false
                    }
                });
            }

            let series_names = (chart.series.map(function(x){return x.name;}));
            let serie_index = series_names.indexOf(serie_name);
            let serie_range_index = serie_index + 1;
            hc_series_index[serie_name] = {
                "sensor_name": serie_name,
                "serie_id": serie_index,
                "end_date_format": undefined
            };

            if (show_range) {
                hc_series_index[serie_name+"_range"] = {
                    "sensor_name": serie_name+"_range",
                    "serie_id": serie_range_index,
                    "end_date_format": undefined
                };
            }
        }

        hc_time_range = "";
        if (chart.xAxis[0].min != undefined && chart.xAxis[0].max != undefined) {
            hc_start_date = new Date(chart.xAxis[0].min);
            hc_end_date = new Date(chart.xAxis[0].max);

            let start_date_format = hc_start_date.toISOString();
            let end_date_format = hc_end_date.toISOString();

            hc_time_range = "?start_date="+start_date_format+"&end_date="+end_date_format+"&zoom_ui=true";
            if (streaming) {
                if (hc_series_index[serie_name]["end_date_format"] != undefined) {
                    hc_time_range = "?start_date="+hc_series_index[serie_name]["end_date_format"]+"&end_date="+end_date_format+"&zoom_ui=true";
                }
            }
        }

        data_url = "/data/hardcoded/"+sensor_type+"/hourly"+hc_time_range;
        if (downsample_scale != undefined) {
            data_url = "/data/hardcoded/"+sensor_type+"/"+downsample_scale+hc_time_range;
        }

        var update_count = 0;

        $.getJSON(data_url, function(temperature_obj) {
            var yMin = undefined;
            var yMax = undefined;

            let name = sensor_type+"_aggregated";
            let timestamps = temperature_obj["range"]["timestamps"];
            let data_is_downsampled = true;

            var means = undefined;
            var ranges = undefined;

            if (data_is_downsampled) {
                timestamps.pop();
            }

            means = temperature_obj["range"]["means"];
            mins = temperature_obj["range"]["mins"];
            maxs = temperature_obj["range"]["maxs"];

            let temperature_data = timestamps.map(function (e, i) {
                let timestamp = Date.parse(e);

                if (yMax == undefined || means[i] > yMax) {
                    yMax = means[i];
                }
                if (yMin == undefined || means[i] < yMin) {
                    yMin = means[i];
                }
                return [timestamp, means[i]];
            });

            let range_data = timestamps.map(function (e, i) {
                let timestamp = Date.parse(e);
                return [timestamp, mins[i], maxs[i]];
            });

            if (temperature_data.length > 0) {
                let serie_id = hc_series_index[name]["serie_id"];

                if (! streaming) {
                    chart.series[serie_id].setData(temperature_data, animation=false, updatePoints=false);
                    chart.yAxis[0].setExtremes(yMin, yMax);
                } else {
                    temperature_data.forEach(function (x) {
                        chart.series[serie_id].addPoint(x);
                    });
                }

                if (show_range) {
                    let range_serie_id = hc_series_index[name+"_range"]["serie_id"];

                    if (! streaming) {
                        chart.series[range_serie_id].setData(range_data, animation=false, updatePoints=false);
                    } else {
                        range_data.forEach(function (x) {
                            chart.series[range_serie_id].addPoint(x);
                        });
                    }
                }

                hc_series_index[name]["end_date_format"] = new Date(temperature_data.slice(-1)[0][0]).toISOString();
                chart.navigator.series[0].setData(navigator_data);
            }

            update_count +=1;
            hc_last_successful_update = new Date();

            if (! streaming) {
                chart.hideLoading();
            }
        });
    }

    function load_sensors_data(chart, streaming=false, range_options={}) {

        if (! streaming) {
            chart.showLoading('Loading data from server...');
        }

        var sensor_url = "/sensors";
        if (sensor_type != "*") {
            sensor_url = "/sensors/"+sensor_type;
        }

        $.getJSON(sensor_url, function(sensor_obj) {
            let sensors = sensor_obj["sensors"];
            var yMin = undefined;
            var yMax = undefined;
            for (i in sensors) {

                var sensor_name = sensors[i];

                if (selected_sensor != undefined && selected_sensor != sensor_name) {
                    continue;
                }

                if (! (sensor_name in hc_series_index)) {
                    chart.addSeries({
                        "name": sensor_name,
                        "showInNavigator": false,
                        "data": [],
                        dataGrouping: {
                            enabled: false
                        }
                    });
                    let serie_index = (chart.series.map(function(x){return x.name;})).indexOf(sensor_name);
                    hc_series_index[sensor_name] = {
                        "sensor_name": sensor_name,
                        "serie_id": serie_index,
                        "end_date_format": undefined
                    };
                }

                hc_time_range = "";
                if (chart.xAxis[0].min != undefined && chart.xAxis[0].max != undefined) {
                    hc_start_date = new Date(chart.xAxis[0].min);
                    hc_end_date = new Date(chart.xAxis[0].max);

                    let start_date_format = hc_start_date.toISOString();
                    let end_date_format = hc_end_date.toISOString();

                    if (hc_snap_to_right_edge || "snapToRightEdge" in range_options && range_options["snapToRightEdge"]) {
                        hc_time_range = "?start_date="+start_date_format+"&zoom_ui=true";
                    } else {
                        hc_time_range = "?start_date="+start_date_format+"&end_date="+end_date_format+"&zoom_ui=true";
                    }
                    if (streaming) {
                        hc_time_range = "?start_date="+hc_series_index[sensor_name]["end_date_format"]+"&zoom_ui=true";
                    }
                }

                if (!enable_data_downsample) {
                    data_url = "/sensor_data/"+sensor_name+hc_time_range;
                } else {
                    data_url = "/sensor_data/"+sensor_name+"/aggregated/"+downsample_scale+hc_time_range;
                }

                var update_count = 0;

                $.getJSON(data_url, function(temperature_obj) {

                    let name = temperature_obj["sensor_name"];
                    let timestamps = temperature_obj["timestamps"];
                    let data_is_downsampled = temperature_obj["is_downsampled"];

                    var values = undefined;

                    if (data_is_downsampled) {
                        timestamps.pop();
                    }

                    if (!data_is_downsampled) {
                        values = temperature_obj["values"];
                    } else {
                        values = temperature_obj["means"];
                    }

//                    var yMax = undefined;
                    let temperature_data = timestamps.map(function (e, i) {
                        let timestamp = Date.parse(e);
                        if (yMax == undefined || values[i] > yMax) {
                            yMax = values[i];
                        }
                        if (yMin == undefined || values[i] < yMin) {
                            yMin = values[i];
                        }
                        return [timestamp, values[i]];
                    });

                    if (temperature_data.length > 0) {
                        let serie_id = hc_series_index[name]["serie_id"];

                        if (! streaming) {
                            chart.series[serie_id].setData(temperature_data, animation=false, updatePoints=false);
                            chart.yAxis[0].setExtremes(yMin, yMax);
                            chart.xAxis[0].setExtremes(range_options["min"], range_options["max"]);
                        } else {
                            temperature_data.forEach(function (x) {
                                chart.series[serie_id].addPoint(x);
                            });
                        }

                        hc_series_index[name]["end_date_format"] = new Date(temperature_data.slice(-1)[0][0]).toISOString();
                        chart.navigator.series[0].setData(navigator_data);
                    }

                    update_count +=1;
                    hc_last_successful_update = new Date();

                    if (! streaming) {
                        if (update_count == sensors.length || selected_sensor != undefined) {
                            chart.hideLoading();
                        }
                    }
                });
            }
        });
    }

    function load_data(chart, streaming=false, range_options={}) {
        if (aggregated) {
            load_aggregated_data(chart, streaming, range_options);
        } else {
            load_sensors_data(chart, streaming, range_options);
        }
    }

    function afterSetExtremes(e) {
        let chart = e.target.chart;
        let current_xaxis_min_date = new Date(chart.xAxis[0].min);
        let current_xaxis_max_date = new Date(chart.xAxis[0].max);

        var xaxisTimeSize = current_xaxis_max_date - current_xaxis_min_date;
        var old_value_enable_data_downsample = enable_data_downsample;
        if (xaxisTimeSize > 29 * 24 * 3600 * 1000) {
            enable_data_downsample = true;
            downsample_scale = "daily";
        } else if (xaxisTimeSize > 24 * 3600 * 1000) {
            enable_data_downsample = true;
            downsample_scale = "hourly";
        } else if (xaxisTimeSize > 1 * 3600 * 1000) {
            enable_data_downsample = true;
            downsample_scale = "minutely";
        } else {
            enable_data_downsample = false;
        }

        if (e.trigger == "zoom" || e.trigger == "navigator") {
            let closeToRightBorder = Math.abs(e.max - e.dataMax) < 120 * 1000;
            chart.xAxis[0].setExtremes(e.min, e.max, false);
            hc_snap_to_right_edge = closeToRightBorder;
            load_data(chart,
                      false,
                      {
                          min: e.min,
                          max: e.max,
                          snapToRightEdge: closeToRightBorder
                      });
        } else {
            return;
        }
    }

    if (navigator_data_url == undefined) {
        navigator_data_url = "/data/hourly";
    }

    $.getJSON(navigator_data_url, function (data) {

        navigator_data = data["range"]["timestamps"].map(function (e, i) {
            let timestamp = Date.parse(e);
            return [timestamp, data["range"]["means"][i]];
        });

        let xMin = navigator_data[0][0];
        let xMax = navigator_data[navigator_data.length - 1][0];

        var chart = Highcharts.stockChart(div_id, {
            chart: {
                type: 'line',
                zoomType: 'x',
                panning: true,
                panKey: 'shift'
            },

            navigator: {
                series: {
                    data: navigator_data
                }
            },
            scrollbar: {
                liveRedraw: false
            },
            xAxis: {
                showFirstLabel: true,
                showLastLabel: true,
                type: 'datetime',
                ordinal: false,
                events: {
                    afterSetExtremes: afterSetExtremes
                }
            },

            yAxis: {
                floor: 0,
                ordinal: false
            },
            rangeSelector: {
                selected: 1
            },
            series: []
        });

        if (aggregated) {

            var empty_data_serie = data["range"]["timestamps"].map(function (e, i) {
                let timestamp = Date.parse(e);
                return [timestamp, 0];
            });

            // Load an empty serie in order to make the navigator initialize
            chart.addSeries({
                name: "InvisibleSerie",
                data: empty_data_serie,
                lineWidth: 0,
                linkedTo: ':previous',
                color: Highcharts.getOptions().colors[0],
                fillOpacity: 0.3,
                zIndex: 0,
                marker: {
                    enabled: false
                },
                dataGrouping: {
                    enabled: false
                },
                tooltip: {
                    pointFormat: ''
                }
            });

            // show last hour of data
            chart.xAxis[0].setExtremes(xMax - 3600 * 1000, xMax);
        }

        // show data aggregated by minutes (by default)
        enable_data_downsample = true;
        downsample_scale = "minutely";

        chart.hideLoading();

//        return;
        load_data(chart);

        // Streaming function
        setInterval(function() {
            if (hc_snap_to_right_edge) {
                load_data(chart, true);
                let current_extremes = chart.xAxis[0].getExtremes();

                chart.xAxis[0].setExtremes(current_extremes.min, current_extremes.max + 3 * 1000);
            }
        }, 5000);

        // Update navigator function
        setInterval(function() {
            let last_navigator_timestamp = navigator_data.slice(-2)[0][0];
            if(last_navigator_timestamp == undefined) {
                return;
            }
            let last_navigator_date = new Date(last_navigator_timestamp);
            let last_navigator_date_str = last_navigator_date.toISOString();

            $.getJSON(navigator_data_url+'?start_date='+last_navigator_date_str, function (data) {
                let additional_navigator_data = data["range"]["timestamps"].map(function (e, i) {
                    let timestamp = Date.parse(e);
                    return [timestamp, data["range"]["means"][i]];
                });
                navigator_data.pop();
                navigator_data.push(...additional_navigator_data);
                var unique_sorted_navigator_data = [];
                var unique_sorted_navigator_data_index = {};
                for (i in navigator_data) {
                    let timestamp = navigator_data[i][0];
                    if (! (timestamp in unique_sorted_navigator_data_index || navigator_data[i][1] == null)) {
                        unique_sorted_navigator_data_index[timestamp] = true;
                        unique_sorted_navigator_data.push(navigator_data[i]);
                    }
                }
                navigator_data = unique_sorted_navigator_data;
                chart.navigator.series[0].setData(navigator_data);
            });
        }, 5000);


        // Check outdated graph due to a lose of connection
        setInterval(function() {
            let current_xaxis_max_date = new Date(chart.xAxis[0].max);
            let last_navigator_update = new Date(navigator_data.slice(-2)[0][0]);
            if (hc_last_successful_update < current_xaxis_max_date && last_navigator_update > current_xaxis_max_date) {
                load_data(chart);
            }
        }, 5000);

    });

}
