"""
Created on 2024-08-24

@author: wf
"""

import datetime
import logging
import sqlite3


class DatetimeAdapter:
    """Class for converting date and time formats with optional lenient error handling."""

    def __init__(self, lenient: bool = False):
        """Initialize with optional lenient error handling."""
        self.lenient = lenient

    def _handle_input(self, val: bytes) -> str:
        """Validate and decode the input bytes into string."""
        if not isinstance(val, bytes):
            raise TypeError("Input must be a byte string.")
        return val.decode()

    def _handle_error(self, error: Exception, val: bytes):
        """Handle errors based on the lenient mode."""
        if self.lenient:
            logging.warning(f"Failed to convert {val}: {error}")
            return None
        else:
            raise error

    def convert_date(self, val: bytes) -> datetime.date:
        """Convert ISO 8601 date byte string to a datetime.date object."""
        try:
            decoded_date = self._handle_input(val)
            dt = datetime.date.fromisoformat(decoded_date)
            return dt
        except Exception as e:
            return self._handle_error(e, val)

    def convert_datetime(self, val: bytes) -> datetime.datetime:
        """Convert ISO 8601 datetime byte string to a datetime.datetime object."""
        try:
            decoded_datetime = self._handle_input(val)
            return datetime.datetime.fromisoformat(decoded_datetime)
        except Exception as e:
            return self._handle_error(e, val)

    def convert_timestamp(self, val: bytes) -> datetime.datetime:
        """Convert Unix epoch timestamp byte string to a datetime.datetime object."""
        try:
            decoded_string = self._handle_input(val)
            timestamp_float = float(decoded_string) / 10**6
            dt = datetime.datetime.fromtimestamp(timestamp_float)
            return dt
        except ValueError as _ve:
            try:
                dt = datetime.datetime.fromisoformat(decoded_string)
                return dt
            except Exception as e:
                return self._handle_error(e, val)
        except Exception as e:
            return self._handle_error(e, val)


class SQLiteApiFixer:
    """
    Class to register SQLite adapters
    and converters using a DatetimeAdapter instance.
    """

    _instance = None  # Singleton instance

    def __init__(self, lenient: bool = True):
        """Private constructor to initialize the singleton instance."""
        self.adapter = DatetimeAdapter(lenient=lenient)
        self.register_converters()
        self.register_adapters()

    @classmethod
    def install(cls, lenient: bool = True):
        """Install the singleton instance and register SQLite adapters and converters."""
        if cls._instance is None:
            cls._instance = cls(lenient=lenient)
        return cls._instance

    def register_adapters(self):
        """Register the necessary SQLite adapters."""
        sqlite3.register_adapter(datetime.date, self.adapt_date_iso)
        sqlite3.register_adapter(datetime.datetime, self.adapt_datetime_iso)
        sqlite3.register_adapter(bool, self.adapt_boolean)

    def register_converters(self):
        """Register the necessary SQLite converters."""
        sqlite3.register_converter("date", self.adapter.convert_date)
        sqlite3.register_converter("datetime", self.adapter.convert_datetime)
        sqlite3.register_converter("timestamp", self.adapter.convert_timestamp)
        sqlite3.register_converter("boolean", self.convert_boolean)

    @staticmethod
    def adapt_date_iso(val: datetime.date):
        """Adapt datetime.date to ISO 8601 date."""
        return val.isoformat()

    @staticmethod
    def adapt_datetime_iso(val: datetime.datetime):
        """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
        return val.isoformat()

    @staticmethod
    def adapt_boolean(val: bool):
        """Adapt boolean to int."""
        return 1 if val else 0

    @staticmethod
    def convert_boolean(val: bytes):
        """Convert 0 or 1 to boolean."""
        return bool(int(val))
