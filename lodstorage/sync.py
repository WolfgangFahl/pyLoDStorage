"""
Created on 2023-12-27

@author: wf
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from tabulate import tabulate


@dataclass
class SyncPair:
    """
       A class to represent a pair of data sources for synchronization.

       Attributes:
           title (str): The title of the synchronization pair.
           l_name (str): Name of the left data source (e.g., 'local').
           r_name (str): Name of the right data source (e.g., 'wikidata').
           l_data (List[Dict[str, Any]]): A list of dictionaries from the left data source.
           r_data (List[Dict[str, Any]]): A list of dictionaries from the right data source.
           l_key (str): The field name in the left data source dictionaries used as a unique identifier for synchronization.
           r_key (str): The field name in the right data source dictionaries used as a unique identifier for synchronization.
           l_pkey(str): the primary key field of the left data source
           r_pkey(str): the primary key field of the right data source

    Example usage:
    l_data = [{'id_l': '1', 'value': 'a'}, {'id_l': '2', 'value': 'b'}]
    r_data = [{'id_r': '2', 'value': 'b'}, {'id_r': '3', 'value': 'c'}]
    pair = SyncPair("Title", "local", "wikidata", l_data, r_data, 'id_l', 'id_r')
    sync = Sync(pair)
    print(sync.status_table())
    """

    title: str
    l_name: str
    r_name: str
    l_data: List[Dict[str, Any]]
    r_data: List[Dict[str, Any]]
    l_key: str
    r_key: str
    l_pkey: Optional[str] = None
    r_pkey: Optional[str] = None
    # Add dictionaries for quick primary key access
    l_by_pkey: Dict[str, Dict[str, Any]] = field(init=False)
    r_by_pkey: Dict[str, Dict[str, Any]] = field(init=False)

    def __post_init__(self):
        # Set the l_pkey to l_key if not provided
        if self.l_pkey is None:
            self.l_pkey = self.l_key
        # Set the r_pkey to r_key if not provided
        if self.r_pkey is None:
            self.r_pkey = self.r_key
        self.l_by_pkey = {d[self.l_pkey]: d for d in self.l_data if self.l_pkey in d}
        self.r_by_pkey = {d[self.r_pkey]: d for d in self.r_data if self.r_pkey in d}


class Sync:
    """
    A class to help with synchronization between two sets of data, each represented as a list of dictionaries.
    """

    def __init__(self, pair: SyncPair):
        """
        Initialize the Sync class with the given Synchronization Pair.
        """
        self.pair = pair
        self.sync_dict = self._create_sync_dict()
        self.directions = ["←", "↔", "→"]
        self.sides = {"left": ["←", "l", "left"], "right": ["→", "r", "right"]}

    def handle_direction_error(self, direction: str):
        invalid_direction_msg = (
            f"Invalid direction '{direction}'. Use {', '.join(self.directions)}."
        )
        raise ValueError(invalid_direction_msg)

    def handle_side_error(self, side: str):
        invalid_side_msg = f"Invalid side '{side}'. Use {', '.join(self.sides['left'])} for left or {', '.join(self.sides['right'])} for right."
        raise ValueError(invalid_side_msg)

    def _create_sync_dict(self) -> dict:
        """
        Create a dictionary representing the synchronization state between left and right data sources.
        """
        l_keys = {d[self.pair.l_key] for d in self.pair.l_data if self.pair.l_key in d}
        r_keys = {d[self.pair.r_key] for d in self.pair.r_data if self.pair.r_key in d}

        sync_dict = {
            "←": r_keys - l_keys,  # Present in right but not in left
            "↔": l_keys.intersection(r_keys),  # Present in both
            "→": l_keys - r_keys,  # Present in left but not in right
        }
        return sync_dict

    def get_record_by_pkey(self, side: str, pkey: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a record by primary key from the appropriate data source as specified by direction.

        Args:
            side (str): The side of data source, "←","l" or "left" for left and "→","r" or "right" for right.
            pkey (str): The primary key of the record to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The record if found, otherwise None.
        """
        record = None
        if side in self.sides["left"]:  # retrieve from left
            record = self.pair.l_by_pkey.get(pkey)
        elif side in self.sides["right"]:  # retrieve from right
            record = self.pair.r_by_pkey.get(pkey)
        else:
            self.handle_side_error(side)
        return record

    def get_record_by_key(self, side: str, key: str) -> dict:
        """
        Retrieves a record by the given unique key from the appropriate data source as specified by direction.

        Args:
            side (str): The side of data source, "←","l" or "left" for left and "→","r" or "right" for right.
            key (str): The unique key of the record to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The record if found, otherwise None.

        Raises:
            ValueError: If the provided direction is invalid.
        """
        record = None
        if side in ["←", "l", "left"]:
            record = next(
                (item for item in self.pair.l_data if item[self.pair.l_key] == key),
                None,
            )
        elif side in ["→", "r", "right"]:
            record = next(
                (item for item in self.pair.r_data if item[self.pair.r_key] == key),
                None,
            )
        else:
            self.handle_side_error(side)
        return record

    def get_keys(self, direction: str) -> set:
        """
        Get the keys for a given direction of synchronization.
        """
        if direction in self.sync_dict:
            return self.sync_dict[direction]
        else:
            self.handle_direction_error(direction)

    def status_table(self, tablefmt: str = "grid") -> str:
        """
        Create a table representing the synchronization status.
        """
        total_records = sum(len(keys) for keys in self.sync_dict.values())
        if total_records == 0:  # Avoid division by zero
            total_records = 1

        table_data = []
        for direction, keys in self.sync_dict.items():
            num_records = len(keys)
            percentage = (num_records / total_records) * 100
            table_data.append(
                {
                    "left": self.pair.l_name,
                    "↔": direction,
                    "right": self.pair.r_name,
                    "#": num_records,
                    "%": f"{percentage:7.2f}%",
                }
            )

        markup = tabulate(
            table_data,
            headers="keys",
            tablefmt=tablefmt,
            colalign=("right", "center", "left", "right", "right"),
        )
        return markup
