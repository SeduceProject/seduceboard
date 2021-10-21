# SeDuCe Dashboard
To run the dashboard web interface, please use the [Dashboard
Project](https://github.com/SeduceProject/dashboard).
The [bin/app.py](/bin/app.py) web interface is deprecated !

[https://seduceboard.readthedocs.io](https://seduceboard.readthedocs.io)

## Installation

## Configuration

## Development

### Run tests and get the coverage

#### Tests

First, start influxdb
```shell script
influxd
```

Then run the tests:
```shell script
python3 run_tests.py
```

#### Coverage
To get the coverage:
```shell script
coverage run --omit="tests/*,bin/*,misc/*" --source . run_tests.py
```

Get a report of the coverage
```shell script
coverage report
```



## Contact
