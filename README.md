# HARP-Parser
A python parser for binary HARP file data.
The HARP Parser is a Python tool for parsing data files in the HArdware Research Platform (HARP) format, developed by the Champalimaud Foundation.

## Features

- Parses HARP data files and returns the data as a list of lists or a pandas DataFrame
- Supports filtering data based on message types (read, write, event)
- Provides a utility for converting HARP data to `list`,`pandas.DataFrame` or CSV files.


## Usage

Here's an example of how to use the HARP Parser.
All the methods support filtering message types.

```python
from harp_parser import HarpParser

parser = HarpParser()


# Parse all HARP data from a file
data = parser.to_list('path/to/harp/file.bin')

# Parse and filter data by message type
read_data = parser.to_list('path/to/harp/file.bin', processWrite=False, processEvent=False)

# Parse HARP data to a pandas DataFrame
df = parser.to_dataframe('path/to/harp/file.bin')

# Write HARP data to a CSV file
parser.to_csv('path/to/harp/file.bin', 'path/to/output.csv')
```

## Documentation

Detailed documentation for the HARP Parser classes and methods can be found in the docstrings of the `harp_parser.py` file.

## Contributing

If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request on the [GitHub repository](https://github.com/AlexandreLaborde/HARP-Parser).

## Author

The HARP Parser was created by Alexandre Laborde.

## Version

Version 1.0
Date: October 28, 2024
