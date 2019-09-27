/* eslint-env browser */
/* global $, Highcharts*/
/* eslint-disable no-console */

Highcharts.setOptions({
    global: {
        useUTC: false
    }
});

function hc_create_chart(hc_options) {

    let hc_series_index = {},
        hc_last_successful_update = undefined,
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
        hc_snap_to_right_edge = false;

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

    function generic_data_loader(chart, series_names, streaming = false, compute_data_url_func, process_data_func) {

        if (series_names.length > 0 && !streaming) {
            chart.showLoading("Loading data from server...");
        }

        let update_count = 0;
        for (let serie_name of series_names) {

            if (selected_sensor !== undefined && selected_sensor !== serie_name) {
                continue;
            }

            if (!(serie_name in hc_series_index)) {
                add_serie(serie_name, chart);
            }

            let hc_time_range = compute_time_range(serie_name, streaming, chart);

            let data_url = compute_data_url_func(serie_name, hc_time_range, downsample_scale, enable_data_downsample);

            $.getJSON(data_url, function (temperature_obj) {

                let name = serie_name;
                let serie_data = process_data_func(temperature_obj);

                if (serie_data.data.length > 0) {

                    if (name in hc_series_index) {
                        let hc_serie = find_serie_by_name(name, chart)[0];

                        if (!streaming) {
                            hc_serie.setData(serie_data.data, false, {}, false);
                            if (get_current_ymax(chart) < serie_data.max) {
                                chart.yAxis[0].setExtremes(0, serie_data.max);
                            }
                        } else {
                            serie_data.data.forEach(function (x) {
                                hc_serie.addPoint(x);
                            });
                        }
                        hc_series_index[name]["end_date_format"] = new Date(serie_data.data.slice(-1)[0][0]).toISOString();
                        chart.navigator.series[0].setData(navigator_data);
                    }
                }

                update_count += 1;
                hc_last_successful_update = new Date();

                if (streaming) {
                    let extremes = chart.xAxis[0].getExtremes();
                    chart.xAxis[0].setExtremes(extremes.min, extremes.dataMax);
                }

                console.log("update_count: "+update_count+"/"+series_names.length);
                if (update_count === series_names.length || selected_sensor !== undefined) {
                    chart.hideLoading();
                }
            });
        }
    }

    function load_multitree_data(chart, streaming = false) {
        let series_names = hc_options["multitree_selected_sensors_getter"]();
        return generic_data_loader(chart, series_names, streaming, compute_multitree_data_url, data => process_json_data(data, "values"));
    }

    function load_aggregated_data(chart, streaming = false) {
        let series_names = [sensor_type];
        return generic_data_loader(chart, series_names, streaming, compute_aggregated_data_url, data => process_json_data(data["range"], "means"));
    }

    function load_sensors_data(chart, streaming = false) {
        if (selected_sensor === undefined) {
            if ("multitree_selected_sensors_getter" in hc_options) {
                let sensors = hc_options["multitree_selected_sensors_getter"]();
                if (sensors.length > 0) {
                    return generic_data_loader(chart, sensors, streaming, compute_data_url, data => process_json_data(data, "values"));
                }
            }
            // let sensor_url = "/sensors";
            // if (sensor_type !== "*") {
            //     sensor_url = "/sensors/" + sensor_type;
            // }
            // $.getJSON(sensor_url, function (sensors_json) {
            //     let sensors = sensors_json["sensors"];
            //     return generic_data_loader(chart, sensors, streaming, compute_data_url, data => process_json_data(data, "values"));
            // });
        } else {
            let sensors = [selected_sensor];
            return generic_data_loader(chart, sensors, streaming, compute_data_url, data => process_json_data(data, "values"));

        }
    }

    function get_series_names(hc_chart) {
        return hc_chart.series.filter(s => !s.name.includes("Navigator ")).map(s => s.name);
    }

    function find_serie_by_name(name, hc_chart) {
        return hc_chart.series.filter(s => s.name === name);
    }

    function load_data(chart, streaming = false) {
        if (hc_options["sensor_type"] === "multitree_consumptions") {
            load_multitree_data(chart, streaming);
        } else {
            if (aggregated) {
                load_aggregated_data(chart, streaming);
            } else {
                load_sensors_data(chart, streaming);
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
        let serie_index = (hc_chart.series.map(function (x) {
            return x.name;
        })).indexOf(serie_name);
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
        return hc_chart.xAxis[0].min !== undefined && hc_chart.xAxis[0].max !== undefined;
    }

    function compute_time_range(sensor_name, streaming, hc_chart) {
        let result = "";
        if (can_compute_time_range(hc_chart)) {
            let hc_start_date = new Date(hc_chart.xAxis[0].min);
            let hc_end_date = new Date(hc_chart.xAxis[0].max);

            let start_date_format = hc_start_date.toISOString();
            let end_date_format = hc_end_date.toISOString();

            if (hc_snap_to_right_edge) {
                result = "?start_date=" + start_date_format + "&zoom_ui=true";
            } else {
                result = "?start_date=" + start_date_format + "&end_date=" + end_date_format + "&zoom_ui=true";
            }
            if (streaming) {
                result = "?start_date=" + hc_series_index[sensor_name]["end_date_format"] + "&zoom_ui=true";
            }
        }
        return result;
    }

    function compute_multitree_data_url(sensor_name, hc_time_range, downsample_scale, enable_data_downsample) {
        if (!enable_data_downsample) {
            return "/multitree_sensor_data/" + sensor_name + "/aggregated" + hc_time_range;
        }
        return "/multitree_sensor_data/" + sensor_name + "/aggregated/" + downsample_scale + hc_time_range;
    }

    function compute_aggregated_data_url(sensor_type, hc_time_range, downsample_scale, enable_data_downsample) {
        if (!enable_data_downsample) {
            return "/data/hardcoded/" + sensor_type + "/hourly" + hc_time_range;
        }
        return "/data/hardcoded/" + sensor_type + "/" + downsample_scale + hc_time_range;
    }

    function compute_data_url(sensor_name, hc_time_range, downsample_scale, enable_data_downsample) {
        if (!enable_data_downsample) {
            return "/sensor_data/" + sensor_name + hc_time_range;
        }
        return "/sensor_data/" + sensor_name + "/aggregated/" + downsample_scale + hc_time_range;
    }

    /**
     *  This function returns the most recent time timestamp used by the navigator
     */
    function get_navigator_max_timestamp() {
        return Math.max(...navigator_data.map(d => d[0]));
    }

    /**
     *  This function returns the max Y value in a given Highcharts object
     *
     *  @param {Highchart Object} hc_chart - an Highchart object
     */
    function get_current_ymax(hc_chart) {
        return hc_chart.yAxis[0].getExtremes().dataMax;
    }

    /**
     *  This function prepares some data returned by the SeDuCe API. The data is prepared for
     *  being used by "data_loader" functions.
     *
     *  @param {Dict} json_data - a dictionary build from the JSON data returned by the SeDuCe API
     *  @param {String} key - key of the values in the 'json_data' dict
     */
    function process_json_data(json_data, key) {
        let timestamps = json_data["timestamps"].slice();
        let data_is_downsampled = json_data["is_downsampled"];

        let values = undefined;

        if (data_is_downsampled) {
            timestamps.pop();
        }

        if (key in json_data) {
            values = json_data[key];
        } else {
            if (!data_is_downsampled) {
                values = json_data["values"];
            } else {
                values = json_data["means"];
            }
        }

        let yMin = undefined;
        let yMax = undefined;

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
        };
    }


    /**
     *  This function is an event handler called right after a user has
     *  changed the time interval selected in the navigator
     *
     *  @param {Event} e - an Event generated by Highcharts
     */
    function afterSetExtremes(e) {
        let chart = e.target.chart;
        let current_xaxis_min_date = new Date(chart.xAxis[0].min);
        let current_xaxis_max_date = new Date(chart.xAxis[0].max);

        let xaxisTimeSize = current_xaxis_max_date - current_xaxis_min_date;

        if (!isNaN(xaxisTimeSize)) {
            if (xaxisTimeSize > 29 * 24 * 3600 * 1000) {
                enable_data_downsample = true;
                downsample_scale = "daily";
            } else if (xaxisTimeSize > 24 * 3600 * 1000) {
                enable_data_downsample = true;
                downsample_scale = "hourly";
            } else if (xaxisTimeSize > 3600 * 1000) {
                enable_data_downsample = true;
                downsample_scale = "minutely";
            } else {
                console.log("enable_data_downsample = false");
                enable_data_downsample = false;
            }
        }

        if (e.trigger === "zoom" || e.trigger === "navigator") {
            let closeToRightBorder = Math.abs(e.max - e.dataMax) < 120 * 1000;
            chart.xAxis[0].setExtremes(e.min, e.max, false);
            console.log("closeToRightBorder: "+closeToRightBorder);
            console.log("e.min: "+new Date(e.min));
            console.log("e.max: "+new Date(e.max));
            hc_snap_to_right_edge = closeToRightBorder;
            load_data(chart,
                false,
                {
                    min: e.min,
                    max: e.max,
                    snapToRightEdge: closeToRightBorder
                });
        }
    }

    if (navigator_data_url === undefined) {
        navigator_data_url = "/data/hourly";
    }

    $.getJSON(navigator_data_url, function (data) {

        // prepare data that will be used by the navigator
        navigator_data = data["range"]["timestamps"].map(function (e, i) {
            let timestamp = Date.parse(e);
            return [timestamp, data["range"]["means"][i]];
        });

        // Display the chart
        let chart = Highcharts.stockChart(div_id, {
            chart: {
                type: "line",
                zoomType: "x",
                panning: true,
                panKey: "shift"
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
                type: "datetime",
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

        /*  Load an empty serie in order to make the navigator initialize */

        // generate data for empty serie
        let empty_data_serie = data["range"]["timestamps"].map(function (e) {
            let timestamp = Date.parse(e);
            return [timestamp, 0];
        });

        // create the empty serie
        chart.addSeries({
            name: "InvisibleSerie",
            data: empty_data_serie,
            lineWidth: 0,
            linkedTo: ":previous",
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
                pointFormat: ""
            },
        });

        // show last hour of data
        let xMax = navigator_data[navigator_data.length - 1][0];
        chart.xAxis[0].setExtremes(xMax - 3600 * 1000, xMax);

        // show data aggregated by minutes (by default)
        enable_data_downsample = true;
        downsample_scale = "minutely";

        // Minimal data (for the navigator) has been loaded, we notify that no more loading is pending
        chart.hideLoading();

        // Ask asynchronously the first loading of series and their display
        setTimeout(function (){
            load_data(chart);
        }, 200);

        // Update with live data
        setInterval(function () {
            // The user is viewing what is happening now
            if (hc_snap_to_right_edge) {
                load_data(chart, true);
            }
        }, 500);

        // Periodically update data of the navigator (bottom bar)
        setInterval(function () {
            // If nothing is display, don't do anything
            if (Object.keys(hc_series_index).length === 0) {
                return;
            }
            let last_navigator_timestamp = navigator_data.slice(-2)[0][0];
            // If the navigator's data is empty (i.e. the navigator has not been displayed yet), don't do anything
            if (last_navigator_timestamp === undefined) {
                return;
            }

            // Format the most recent date of navigator in a format that can be understood by the SeDuCe API
            let last_navigator_date = new Date(last_navigator_timestamp);
            let last_navigator_date_str = last_navigator_date.toISOString();

            // Ask the SeDuce API for more recent data
            $.getJSON(navigator_data_url + "?start_date=" + last_navigator_date_str, function (data) {
                let additional_navigator_data = data["range"]["timestamps"].map(function (e, i) {
                    let timestamp = Date.parse(e);
                    return [timestamp, data["range"]["means"][i]];
                });
                navigator_data.pop();
                navigator_data.push(...additional_navigator_data);
                let unique_sorted_navigator_data = [];
                let unique_sorted_navigator_data_index = {};
                for (let i in navigator_data) {
                    let timestamp = navigator_data[i][0];
                    if (!(timestamp in unique_sorted_navigator_data_index || navigator_data[i][1] === null)) {
                        unique_sorted_navigator_data_index[timestamp] = true;
                        unique_sorted_navigator_data.push(navigator_data[i]);
                    }
                }
                navigator_data = unique_sorted_navigator_data;
                chart.navigator.series[0].setData(navigator_data);
            });
        }, 500);


        // Check outdated graph due to a lose of connection
        setInterval(function () {
            let current_xaxis_max_date = new Date(chart.xAxis[0].max);
            let last_navigator_update = new Date(navigator_data.slice(-2)[0][0]);
            if (hc_last_successful_update < current_xaxis_max_date && last_navigator_update > current_xaxis_max_date) {
                load_data(chart);
            }
        }, 500);


        // Delete unselected series
        if (hc_options["sensor_type"] === "multitree_consumptions" || "multitree_selected_sensors_getter" in hc_options) {
            setInterval(function () {
                for (let serie_name of get_series_names(chart)) {
                    if (!hc_options["multitree_selected_sensors_getter"]().includes(serie_name)) {
                        console.log("I am going to delete \"" + serie_name + "\"");
                        remove_serie(serie_name, chart);
                    }
                }
            }, 100);
        }


        // Check if a new serie has been selected
        if (hc_options["sensor_type"] === "multitree_consumptions" || "multitree_selected_sensors_getter" in hc_options) {
            setInterval(function () {
                for (let serie_name of hc_options["multitree_selected_sensors_getter"]()) {
                    if (!get_series_names(chart).includes(serie_name)) {
                        console.log("I am going to add \"" + serie_name + "\"");
                        load_data(chart);
                    }
                }
            }, 100);
        }

        // Debug if a new serie has been selected
        if (hc_options["sensor_type"] === "multitree_consumptions" || "multitree_selected_sensors_getter" in hc_options) {
            setInterval(function () {
                let navigator_max_timestamp = get_navigator_max_timestamp();
                let navigator_max_datetime = new Date(navigator_max_timestamp);
                console.log("Navigator.maxDate = " + navigator_max_datetime);
                console.log("hc_snap_to_right_edge = " + hc_snap_to_right_edge);
                console.log("downsample_scale = " + downsample_scale);
            }, 500);
        }

    });
}
