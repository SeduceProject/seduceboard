AGGREGATES_CONFIG = {
    "wattmeters": {
        "type": "wattmeter",
        "filter_expression": "sensor='watt_cooler_b232_1' or sensor='watt_cooler_ext_1'",
        "aggregate_function_level1": "sum",
        "aggregate_function_level2": "mean",
        "aggregate_frequency": "10s"
    },
    "socomecs": {
        "type": "socomec",
        "filter_expression": "sensor='socomec_capacitor' or sensor='socomec_servers' or sensor='socomec_cooling'",
        "aggregate_function_level1": "sum",
        "aggregate_function_level2": "mean",
        "aggregate_frequency": "30s"
    },
    "external_temperature": {
        "type": "temperature",
        "filter_expression": "location='room exterior' and unit='celsius'",
        "aggregate_function_level1": "mean",
        "aggregate_function_level2": "mean",
        "aggregate_frequency": "30s"
    }
}
