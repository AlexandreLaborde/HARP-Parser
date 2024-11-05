from functools import lru_cache
import string
import struct
from typing import List
import pandas as pd
import csv


class PayloadLookup:
    """
    Utility class for looking up the appropriate data format character
    based on the payload type byte.

    Author: Alexandre Laborde
    Version: 1.0
    Date: October 28, 2024
    """
    DATA_CHARS = {
        0x01: 'B',  # unsigned 1
        0x81: 'b',  # signed 1
        0x02: 'H',  # unsigned 2
        0x82: 'h',  # signed 2
        0x04: 'I',  # unsigned 4
        0x84: 'i',  # signed 4
        0x08: 'Q',  # unsigned 8
        0x88: 'q',  # signed 8
        0x44: 'f'   # float 4
    }

    @lru_cache(maxsize=None)
    def get_payload_string(self, has_timestamp: bool, count: int, payload: bytes) -> str:
        """
        Generates a format string for unpacking the payload data based on the
        presence of a timestamp and the number of data elements.

        Args:
            has_timestamp (bool): Whether the payload contains a timestamp.
            count (int): The number of data elements in the payload.
            payload (bytes): The raw payload data.

        Returns:
            str: The format string for unpacking the payload data.
        """
        char_code = self.__get_data_char(payload)
        if has_timestamp:
            return f'<IH{char_code * count}'
        return f'<{char_code * count}'

    def __get_data_char(self, payload: bytes) -> str:
        """
        Retrieves the appropriate data format character based on the payload type byte.

        Args:
            payload (bytes): The raw payload data.

        Returns:
            str: The data format character.
        """
        return self.DATA_CHARS[(payload & 0xC0) | (payload & 0x0F)]


class HarpParser():
    """
    Parser for the HARP (HArdware Research Platform) data format.

    Author: Alexandre Laborde
    Version: 1.0.1
    Date: November 5, 2024
    """

    HAS_TIMESTAMP = 0x10
    SIZE_MASK = 0x0F
    MICROSECOND_TO_SECOND = 32e-6
    NAN = float('nan')

    def __init__(self):
        self.payload_lookup = PayloadLookup()

    def __read_data(self, filepath: string) -> bytes:
        """
        Reads the raw data from the specified file path.

        Args:
            filepath (str): The path to the file containing the HARP data.

        Returns:
            bytes: The raw data read from the file.
        """
        file = open(filepath, "rb")
        data = file.read()
        file.close()
        return data

    def __unpack_message_types_to_process(self, processRead: bool, processWrite: bool, processEvent: bool) -> List:
        """
        Determines the message types to process based on the provided flags.

        Args:
            processRead (bool): Whether to process read messages.
            processWrite (bool): Whether to process write messages.
            processEvent (bool): Whether to process event messages.

        Returns:
            List: The list of message types to process.
        """
        types_to_process = []
        if processRead:
            types_to_process.append(1)
        if processWrite:
            types_to_process.append(2)
        if processEvent:
            types_to_process.append(3)
            return types_to_process

    def to_list(self, filepath: string, processRead=True, processWrite=True, processEvent=True) -> List[List]:
        """
        Parses the HARP data from the specified file path and returns the data as a list of lists.

        Args:
            filepath (str): The path to the file containing the HARP data.
            processRead (bool, optional): Whether to process read messages. Defaults to True.
            processWrite (bool, optional): Whether to process write messages. Defaults to True.
            processEvent (bool, optional): Whether to process event messages. Defaults to True.

        Returns:
            List[List]: The parsed HARP data as a list of lists.
        """
        data = self.__read_data(filepath)

        types_to_process = self.__unpack_message_types_to_process(
            processRead, processWrite, processEvent)

        message_start = 0
        message_end = 0
        EOF = len(data)

        next_message_start = 0
        processed_data = []

        while (next_message_start < EOF):

            message_start = next_message_start
            message_end = message_start + data[message_start + 1] + 1
            next_message_start = message_end + 1

            message = data[message_start: message_end]
            message_type = message[0]

            if message_type in types_to_process:

                # message_length = message[1]
                message_address = message[2]
                # message_port = message[3]
                # message_checksum = message[-1]

                payload_type = message[4]
                payload = message[5::]
                payload_has_timestamp = payload_type & HarpParser.HAS_TIMESTAMP
                payload_length = (len(payload) - (6 if payload_has_timestamp else 0)
                                  ) // (payload_type & HarpParser.SIZE_MASK)

                format = self.payload_lookup.get_payload_string(
                    payload_has_timestamp, payload_length, payload_type)
                unpacked_data = list(struct.unpack(format, payload))

                if payload_has_timestamp:
                    seconds = float(unpacked_data[0])
                    microseconds = float(unpacked_data[1])
                    timestamp = seconds + \
                        (microseconds * HarpParser.MICROSECOND_TO_SECOND)

                    processed_data.append(
                        [message_type, message_address, timestamp] + unpacked_data[2:])
                else:
                    processed_data.append(
                        [message_type, message_address, HarpParser.NAN] + unpacked_data)

        return processed_data

    def to_dataframe(self, filepath: string, processRead=True, processWrite=True, processEvent=True) -> pd.DataFrame:
        """
        Parses the HARP data from the specified file path and returns a pandas DataFrame.

        Args:
            filepath (str): The path to the file containing the HARP data.
            processRead (bool, optional): Whether to process read messages. Defaults to True.
            processWrite (bool, optional): Whether to process write messages. Defaults to True.
            processEvent (bool, optional): Whether to process event messages. Defaults to True.

        Returns:
            pandas.DataFrame: The parsed HARP data as a pandas DataFrame.
        """

        data = self.to_list(filepath, processRead, processWrite, processEvent)

        messages = [(row[:3] if len(row) >= 3 else [None]*3) for row in data]
        payloads = [row[3:] if len(row) > 3 else [] for row in data]

        df = pd.DataFrame(messages,
                          columns=['message_type', 'message_address', 'timestamp']).astype({
                              'message_type': 'bytes', 'message_address': 'bytes', 'timestamp': 'float'})
        df['payload'] = payloads

        return df

    def to_csv(self, filepath: string, csv_filepath: string, processRead=True, processWrite=True, processEvent=True):
        """
        Parses the HARP data from the specified file path and writes it to a CSV file.

        Args:
            filepath (str): The path to the file containing the HARP data.
            csv_filepath (str): The path to the output CSV file.
            processRead (bool, optional): Whether to process read messages. Defaults to True.
            processWrite (bool, optional): Whether to process write messages. Defaults to True.
            processEvent (bool, optional): Whether to process event messages. Defaults to True.
        """
        data = self.to_list(filepath, processRead, processWrite, processEvent)

        with open(csv_filepath, mode='w') as csv_file:
            csv_file_writer = csv.writer(
                csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_file_writer.writerow(
                ['Command', 'RegisterAddress', 'Timestamp', 'DataElement0'])
            csv_file_writer.writerows(data)
