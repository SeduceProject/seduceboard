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
    show_range = false;

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

    function load_aggregated_data(chart, streaming=false) {

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
            })

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
                })
            }

            let series_names = (chart.series.map(function(x){return x.name}))
            let serie_index = series_names.indexOf(serie_name);
            let serie_range_index = serie_index + 1;
            hc_series_index[serie_name] = {
                "sensor_name": serie_name,
                "serie_id": serie_index,
                "end_date_format": undefined,
            }

            if (show_range) {
                hc_series_index[serie_name+"_range"] = {
                    "sensor_name": serie_name+"_range",
                    "serie_id": serie_range_index,
                    "end_date_format": undefined,
                }
            }
        }

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

        data_url = "/data/hardcoded/"+sensor_type+"/hourly"+hc_time_range;
        if (downsample_scale != undefined) {
            data_url = "/data/hardcoded/"+sensor_type+"/"+downsample_scale+hc_time_range;
        }

        var update_count = 0

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
                    yMax = means[i]
                }
                if (yMin == undefined || means[i] < yMin) {
                    yMin = means[i]
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
                    })
                }

                if (show_range) {
                    let range_serie_id = hc_series_index[name+"_range"]["serie_id"];

                    if (! streaming) {
                        chart.series[range_serie_id].setData(range_data, animation=false, updatePoints=false);
                    } else {
                        range_data.forEach(function (x) {
                            chart.series[range_serie_id].addPoint(x);
                        })
                    }
                }

                hc_series_index[name]["end_date_format"] = new Date(temperature_data.slice(-1)[0][0]).toISOString();
                chart.navigator.series[0].setData(navigator_data);
            }

            update_count +=1
            hc_last_successful_update = new Date();

            if (! streaming) {
                chart.hideLoading();
            }
        });
    }

    function load_sensors_data(chart, streaming=false) {

        if (! streaming) {
            chart.showLoading('Loading data from server...');
        }

        var sensor_url = "/sensors";
        if (sensor_type != "*") {
            sensor_url = "/sensors/"+sensor_type
        }

        $.getJSON(sensor_url, function(sensor_obj) {
            let sensors = sensor_obj["sensors"];
            var yMin = undefined;
            var yMax = undefined;
            for (i in sensors) {

                var sensor_name = sensors[i];

                if (! (sensor_name in hc_series_index)) {
                    chart.addSeries({
                        "name": sensor_name,
                        "showInNavigator": false,
                        "data": [],
                        dataGrouping: {
                            enabled: false
                        }
                    })
                    let serie_index = (chart.series.map(function(x){return x.name})).indexOf(sensor_name);
                    hc_series_index[sensor_name] = {
                        "sensor_name": sensor_name,
                        "serie_id": serie_index,
                        "end_date_format": undefined,
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
                        if (hc_series_index[sensor_name]["end_date_format"] != undefined) {
                            hc_time_range = "?start_date="+hc_series_index[sensor_name]["end_date_format"]+"&end_date="+end_date_format+"&zoom_ui=true";
                        }
                    }
                }

                if (!enable_data_downsample) {
                    data_url = "/sensor_data/"+sensor_name+hc_time_range;
                } else {
                    data_url = "/sensor_data/"+sensor_name+"/aggregated/"+downsample_scale+hc_time_range;
                }

                var update_count = 0

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
                            yMax = values[i]
                        }
                        if (yMin == undefined || values[i] < yMin) {
                            yMin = values[i]
                        }
                        return [timestamp, values[i]];
                    });

                    if (temperature_data.length > 0) {
                        let serie_id = hc_series_index[name]["serie_id"];

                        if (! streaming) {
                            chart.series[serie_id].setData(temperature_data, animation=false, updatePoints=false);
                            chart.yAxis[0].setExtremes(yMin, yMax);
                        } else {
                            temperature_data.forEach(function (x) {
                                chart.series[serie_id].addPoint(x);
                            })
                        }

                        hc_series_index[name]["end_date_format"] = new Date(temperature_data.slice(-1)[0][0]).toISOString();
                        chart.navigator.series[0].setData(navigator_data);
                    }

                    update_count +=1
                    hc_last_successful_update = new Date();

                    if (! streaming) {
                        if (update_count == sensors.length) {
                            chart.hideLoading();
                        }
                    }
                });
            }
        });
    }

    function load_data(chart, streaming=false) {
        if (aggregated) {
            load_aggregated_data(chart, streaming);
        } else {
            load_sensors_data(chart, streaming);
        }
    }

    function afterSetExtremes(e) {
        load_data(e.target.chart)
    }


    $.getJSON('/data/hourly', function (data) {

        navigator_data = data["range"]["timestamps"].map(function (e, i) {
            let timestamp = Date.parse(e);
            return [timestamp, data["range"]["means"][i]];
        });

        // create the chart
        var chart = Highcharts.stockChart(div_id, {
            chart: {
                type: 'line',
                zoomType: 'xy'
            },

            navigator: {
                enabled: true,
                adaptToUpdatedData: false,
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

            title: {
                text: plot_title
            },

            subtitle: {
                text: plot_subtitle
            },

            scrollbar: {
                enabled: false
            },

            rangeSelector: {
                buttons: [{
                    type: 'hour',
                    count: 1,
                    text: '1h'
                }, {
                    type: 'day',
                    count: 1,
                    text: '1d'
                }, {
                    type: 'month',
                    count: 1,
                    text: '1m'
                }, {
                    type: 'year',
                    count: 1,
                    text: '1y'
                }, {
                    type: 'all',
                    text: 'All'
                }],
                inputEnabled: false, // it supports only days
                selected: 0 // all
            },

            xAxis: {
                showFirstLabel: true,
                showLastLabel: true,
                type: 'datetime',
                ordinal: false,
                events: {
                    afterSetExtremes: afterSetExtremes
                },
            },

            yAxis: {
                floor: 0,
                ordinal: false
            },

            series: []
        });

//        var chart = Highcharts.stockChart(div_id, {
//
//            navigator: {
//                series: {
//                    data: ADBE
//                }
//            },
//
//            rangeSelector: {
//                selected: 1
//            },
//
//            series: [{
//                name: 'MSFT',
//                data: MSFT
//            }]
//        });

//        return;
        load_data(chart);

        // Streaming function
        setInterval(function() {
            let now = (new Date()).getTime();
            if (now < chart.xAxis[0].max) {
                load_data(chart, true);
            }
        }, 3000)

        // Update navigator function
        setInterval(function() {

            let last_navigator_timestamp = navigator_data.slice(-2)[0][0];

            if(last_navigator_timestamp == undefined) {
                return;
            }

            let last_navigator_date = new Date(last_navigator_timestamp);
            let last_navigator_date_str = last_navigator_date.toISOString();

            $.getJSON('/data/hourly?start_date='+last_navigator_date_str, function (data) {
                let additional_navigator_data = data["range"]["timestamps"].map(function (e, i) {
                    let timestamp = Date.parse(e);
                    return [timestamp, data["range"]["means"][i]];
                });

                navigator_data.pop();
                navigator_data.push(...additional_navigator_data);
                var unique_sorted_navigator_data = []
                var unique_sorted_navigator_data_index = {}
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
        }, 5000)

        // Check outdated graph due to a lose of connection
        setInterval(function() {
            let current_xaxis_max_date = new Date(chart.xAxis[0].max);
            let last_navigator_update = new Date(navigator_data.slice(-2)[0][0]);
            if (hc_last_successful_update < current_xaxis_max_date && last_navigator_update > current_xaxis_max_date) {
                load_data(chart);
            }
        }, 5000)

        // Check if the data resolution is too precise. In this case, data should be downsampled
        setInterval(function() {
            let current_xaxis_min_date = new Date(chart.xAxis[0].min);
            let current_xaxis_max_date = new Date(chart.xAxis[0].max);

            var xaxisTimeSize = current_xaxis_max_date - current_xaxis_min_date;
            var old_value_enable_data_downsample = enable_data_downsample;
            if (xaxisTimeSize > 29 * 24 * 3600 * 1000) {
                enable_data_downsample = true;
                downsample_scale = "daily"
            } else if (xaxisTimeSize > 12 * 3600 * 1000) {
                enable_data_downsample = true;
                downsample_scale = "hourly"
            } else if (xaxisTimeSize > 1 * 3600 * 1000) {
                enable_data_downsample = true;
                downsample_scale = "minutely"
            } else {
                enable_data_downsample = false;
            }
            enable_data_downsample = false;
            downsample_scale = undefined;

            if (old_value_enable_data_downsample != enable_data_downsample) {
                load_data(chart)
            }
        }, 1000)

    });

}
