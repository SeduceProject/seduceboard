/**
 * Load new data depending on the selected min and max
 */

Highcharts.setOptions({
	global: {
		useUTC: false
	}
});

function hc_create_chart(hc_options) {

    let hc_series_index = {},
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
        hc_enable_streaming = false,
        hc_snap_to_right_edge = false,
        hc_time_range = "";

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

    function load_multitree_data(chart, streaming=false, range_options={}) {

        // if (! streaming) {
        //     chart.showLoading('Loading data from server...');
        // }

        let sensors = hc_options["multitree_selected_sensors_getter"]();
        for (sensor_name of sensors) {

            if (selected_sensor !== undefined && selected_sensor !== sensor_name) {
                continue;
            }

            if (! (sensor_name in hc_series_index)) {
                add_serie(sensor_name, chart);
            }

            let hc_time_range = compute_time_range(sensor_name, range_options, streaming, chart);
            let data_url = compute_data_url(sensor_name, hc_time_range, downsample_scale, enable_data_downsample);
            let update_count = 0;

            $.getJSON(data_url, function(temperature_obj) {

                let name = temperature_obj["sensor_name"];
                let serie_data = process_json_data(temperature_obj);

                if (serie_data.data.length > 0) {

                    if (name in hc_series_index) {
                        let hc_serie = find_serie_by_name(name, chart)[0];

                        if (! streaming) {
                            hc_serie.setData(serie_data.data, animation=false, updatePoints=false);
                            if (get_current_ymax(chart) < serie_data.max) {
                                chart.yAxis[0].setExtremes(0, serie_data.max);
                            }
//                            chart.xAxis[0].setExtremes(range_options["min"], range_options["max"]);
                        } else {
                            serie_data.data.forEach(function (x) {
                                hc_serie.addPoint(x);
                            });
                        }

                        hc_series_index[name]["end_date_format"] = new Date(serie_data.data.slice(-1)[0][0]).toISOString();
                        chart.navigator.series[0].setData(navigator_data);
                    }
                }

                update_count +=1;
                hc_last_successful_update = new Date();

                if (! streaming) {
                    // if (update_count === sensors.length || selected_sensor !== undefined) {
                    //     chart.hideLoading();
                    // }
                } else {
                    let extremes = chart.xAxis[0].getExtremes();
                    chart.xAxis[0].setExtremes(extremes.min, extremes.dataMax);
                }
            });
        }
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
        if (chart.xAxis[0].min !== undefined && chart.xAxis[0].max !== undefined) {
            hc_start_date = new Date(chart.xAxis[0].min);
            hc_end_date = new Date(chart.xAxis[0].max);

            let start_date_format = hc_start_date.toISOString();
            let end_date_format = hc_end_date.toISOString();

            hc_time_range = "?start_date="+start_date_format+"&end_date="+end_date_format+"&zoom_ui=true";
            if (streaming) {
                if (hc_series_index[serie_name]["end_date_format"] !== undefined) {
                    hc_time_range = "?start_date="+hc_series_index[serie_name]["end_date_format"]+"&end_date="+end_date_format+"&zoom_ui=true";
                }
            }
        }

        data_url = "/data/hardcoded/"+sensor_type+"/hourly"+hc_time_range;
        if (downsample_scale !== undefined) {
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

                if (yMax === undefined || means[i] > yMax) {
                    yMax = means[i];
                }
                if (yMin === undefined || means[i] < yMin) {
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
            } else {
                var extremes = chart.xAxis[0].getExtremes();
                chart.xAxis[0].setExtremes(extremes.min, extremes.dataMax);
            }
        });
    }

    function load_sensors_data(chart, streaming=false, range_options={}) {

        if (! streaming) {
            chart.showLoading('Loading data from server...');
        }

        var sensor_url = "/sensors";
        if (sensor_type !== "*") {
            sensor_url = "/sensors/"+sensor_type;
        }

        $.getJSON(sensor_url, function(sensor_obj) {
            let sensors = sensor_obj["sensors"];
            var yMin = undefined;
            var yMax = undefined;
            for (i in sensors) {

                var sensor_name = sensors[i];

                if (selected_sensor !== undefined && selected_sensor !== sensor_name) {
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
                if (chart.xAxis[0].min !== undefined && chart.xAxis[0].max !== undefined) {
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

                    let temperature_data = timestamps.map(function (e, i) {
                        let timestamp = Date.parse(e);
                        if (yMax === undefined || values[i] > yMax) {
                            yMax = values[i];
                        }
                        if (yMin === undefined || values[i] < yMin) {
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
                        if (update_count === sensors.length || selected_sensor !== undefined) {
                            chart.hideLoading();
                        }
                    } else {
                        var extremes = chart.xAxis[0].getExtremes();
                        chart.xAxis[0].setExtremes(extremes.min, extremes.dataMax);
                    }
                });
            }
        });
    }

    function get_series_names(hc_chart) {
        return hc_chart.series.filter(s => ! s.name.includes("Navigator ")).map(s => s.name);
    }

    function find_serie_by_name(name, hc_chart) {
        return hc_chart.series.filter(s => s.name === name);
    }

    function load_data(chart, streaming=false, range_options={}) {
        if (hc_options["sensor_type"] === "multitree_consumptions") {
            load_multitree_data(chart, streaming, range_options);
        } else {
            if (aggregated) {
                load_aggregated_data(chart, streaming, range_options);
            } else {
                load_sensors_data(chart, streaming, range_options);
            }
        }
    }

    function remove_serie(serie_name, hc_chart) {
        find_serie_by_name(serie_name, hc_chart).map(s => s.remove(true));
        return delete hc_series_index[serie_name];
    }

    function add_serie(serie_name, hc_chart) {
        hc_chart.addSeries({
            "name": serie_name,
            "showInNavigator": false,
            "data": [],
            dataGrouping: {
                enabled: false
            }
        });
        let serie_index = (hc_chart.series.map(function(x){return x.name;})).indexOf(serie_name);
        hc_series_index[serie_name] = {
            "sensor_name": serie_name,
            "serie_id": serie_index,
            "end_date_format": undefined
        };
    }

    function can_compute_time_range(hc_chart) {
        if (hc_chart === undefined || hc_chart.xAxis[0].length === 0) {
            return false;
        }
        return hc_chart.xAxis[0].min !== undefined && hc_chart.xAxis[0].max !== undefined
    }

    function compute_time_range(sensor_name, range_options, streaming, hc_chart) {
        var result = "";
        if (can_compute_time_range(hc_chart)) {
            hc_start_date = new Date(hc_chart.xAxis[0].min);
            hc_end_date = new Date(hc_chart.xAxis[0].max);

            let start_date_format = hc_start_date.toISOString();
            let end_date_format = hc_end_date.toISOString();

            if (hc_snap_to_right_edge) {
                result = "?start_date="+start_date_format+"&zoom_ui=true";
            } else {
                result = "?start_date="+start_date_format+"&end_date="+end_date_format+"&zoom_ui=true";
            }
            if (streaming) {
                result = "?start_date="+hc_series_index[sensor_name]["end_date_format"]+"&zoom_ui=true";
            }
        }
        return result;
    }

    function compute_data_url(sensor_name, hc_time_range, downsample_scale, enable_data_downsample) {
        if (!enable_data_downsample) {
            return "/multitree_sensor_data/"+sensor_name+"/aggregated"+hc_time_range;
        }
        return "/multitree_sensor_data/"+sensor_name+"/aggregated/"+downsample_scale+hc_time_range;
    }

    function get_navigator_max_timestamp() {
        return Math.max(...navigator_data.map(d => d[0]));
    }

    function get_current_ymax(hc_chart) {
        return hc_chart.yAxis[0].getExtremes().dataMax;
    }

    function process_json_data(json_data) {
        let timestamps = json_data["timestamps"].slice();
        let data_is_downsampled = json_data["is_downsampled"];

        var values = undefined;

        if (data_is_downsampled) {
            timestamps.pop();
        }

        if (!data_is_downsampled) {
            values = json_data["values"];
        } else {
            values = json_data["means"];
        }

        var yMin = undefined;
        var yMax = undefined;

        let serie_data = timestamps.map(function (e, i) {
            let timestamp = Date.parse(e);
            if (yMax === undefined || values[i] > yMax) {
                yMax = values[i];
            }

            if (yMin === undefined || values[i] < yMin) {
                yMin = values[i];
            }
            return [timestamp, values[i]];
        });

        return {
            min: yMin,
            max: yMax,
            data: serie_data
        }
    }

    function afterSetExtremes(e) {
        let chart = e.target.chart;
        let current_xaxis_min_date = new Date(chart.xAxis[0].min);
        let current_xaxis_max_date = new Date(chart.xAxis[0].max);

        var xaxisTimeSize = current_xaxis_max_date - current_xaxis_min_date;

        if (! isNaN(xaxisTimeSize)) {
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
                console.log("ICCICICI");
                enable_data_downsample = false;
            }
        }

        if (e.trigger === "zoom" || e.trigger === "navigator") {
            var max_timestamp = get_navigator_max_timestamp();
            let closeToRightBorder = Math.abs(e.max - e.dataMax) < 120 * 1000;
            chart.xAxis[0].setExtremes(e.min, e.max, false);
            console.log(closeToRightBorder);
            console.log(new Date(e.min));
            console.log(new Date(e.max));
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

    if (navigator_data_url === undefined) {
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
            legend: {
                enabled: true,
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
                },
            });

            // show last hour of data
            chart.xAxis[0].setExtremes(xMax - 3600 * 1000, xMax);
        }

        // show data aggregated by minutes (by default)
        enable_data_downsample = true;
        if (hc_options["sensor_type"] !== "multitree_consumptions" && aggregated) {
            downsample_scale = "minutely";
        } else {
            downsample_scale = "hourly";
        }


        chart.hideLoading();
        load_data(chart);

        // Streaming function
        setInterval(function() {
            if (hc_snap_to_right_edge) {
                load_data(chart, true);
            }
        }, 5000);

        // Update navigator function
        setInterval(function() {
            let last_navigator_timestamp = navigator_data.slice(-2)[0][0];
            if(last_navigator_timestamp === undefined) {
                return;
            }
            let last_navigator_date = new Date(last_navigator_timestamp);
            let last_navigator_date_str = last_navigator_date.toISOString();

            if (Object.keys(hc_series_index).length === 0) {
                return;
            }

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
                    if (! (timestamp in unique_sorted_navigator_data_index || navigator_data[i][1] === null)) {
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


        // Delete unselected series
        if (hc_options["sensor_type"] === "multitree_consumptions") {
            setInterval(function() {
                for (serie_name of get_series_names(chart)) {
                    if (! hc_options["multitree_selected_sensors_getter"]().includes(serie_name)) {
                        console.log("I am going to delete \""+serie_name+"\"");
                        remove_serie(serie_name, chart);
                    }
                }
            }, 100);
        }


        // Check if a new serie has been selected
        if (hc_options["sensor_type"] === "multitree_consumptions") {
            setInterval(function() {
                for (serie_name of hc_options["multitree_selected_sensors_getter"]()) {
                    if (! get_series_names(chart).includes(serie_name)) {
                        console.log("I am going to add \""+serie_name+"\"");
                        load_data(chart);
                    }
                }
            }, 100);
        }

        // Debug if a new serie has been selected
        if (hc_options["sensor_type"] === "multitree_consumptions") {
            setInterval(function() {
                let navigator_max_timestamp = get_navigator_max_timestamp();
                let navigator_max_datetime = new Date(navigator_max_timestamp);
                console.log("Navigator.maxDate = "+navigator_max_datetime);
                console.log("hc_snap_to_right_edge = "+hc_snap_to_right_edge);
                console.log("downsample_scale = "+downsample_scale);
            }, 5000);
        }

    });

}
