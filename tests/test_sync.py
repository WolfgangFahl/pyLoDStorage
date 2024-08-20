"""
Created on 2023-12-27

@author: wf
"""

from lodstorage.sync import Sync, SyncPair
from tests.basetest import Basetest


class TestSync(Basetest):
    """
    test Synchronization utitity
    """

    def test_Sync(self):
        """
        Test the Sync class with lists of dictionaries, using distinct keys for left and right data sources.
        """
        debug = self.debug
        # Define lists of dictionaries for both local and wikidata to simulate data sources
        local_data = [
            {"id_l": "1", "lvalue": "a"},
            {"id_l": "2", "lvalue": "b"},
            {"id_l": "4", "lvalue": "d"},
            {"id_l": "5", "lvalue": "e"},
        ]
        wikidata_data = [
            {"id_r": "1", "wvalue": "a"},
            {"id_r": "2", "wvalue": "b"},
            {"id_r": "3", "wvalue": "c"},
        ]

        # Create a SyncPair object with the given names, data, and key fields
        pair = SyncPair(
            title="Local to Wikidata Sync",
            l_name="local",
            r_name="wikidata",
            l_data=local_data,
            r_data=wikidata_data,
            l_key="lvalue",
            r_key="wvalue",
            l_pkey="id_l",
            r_pkey="id_r",
        )

        # Initialize the Sync object with the SyncPair
        sync = Sync(pair)

        # Print the status table
        if debug:
            print("Status Table:")
            print(sync.status_table())

        # Iterate through directions and print the keys for each direction
        for direction in sync.directions:
            keys = sync.get_keys(direction)
            if debug:
                print(f"Keys for direction {direction}: {keys}")

        # Assert keys that are only in local (left) but not in wikidata (right)
        assert sync.get_keys("→") == {
            "d",
            "e",
        }, "Mismatch in keys present only in local data"

        # Assert keys that are in both local (left) and wikidata (right)
        assert sync.get_keys("↔") == {
            "a",
            "b",
        }, "Mismatch in keys present in both data sets"

        # Assert keys that are only in wikidata (right) but not in local (left)
        assert sync.get_keys("←") == {"c"}, "Mismatch in keys present only in wikidata"

        # Test unique values in local and wikidata
        local_test_value = "d"  # Value that is unique to local data
        wikidata_test_value = "c"  # Value that is unique to wikidata

        # Assert that get_record_by_key returns the correct record for the local data
        local_record_by_key = sync.get_record_by_key("←", local_test_value)
        assert (
            local_record_by_key is not None
            and local_record_by_key["lvalue"] == local_test_value
        ), "get_record_by_key failed for local data"

        # Assert that get_record_by_key returns the correct record for the wikidata
        wikidata_record_by_key = sync.get_record_by_key("→", wikidata_test_value)
        assert (
            wikidata_record_by_key is not None
            and wikidata_record_by_key["wvalue"] == wikidata_test_value
        ), "get_record_by_key failed for wikidata"

        # Testing get_record_by_pkey - the key should be the primary key 'id_l' or 'id_r'
        local_pkey = "4"  # Primary Key that is unique to local data
        wikidata_pkey = "3"  # Primary Key that is unique to wikidata

        # Retrieve a specific record by primary key from both datasets
        local_pkey_record = sync.get_record_by_pkey("←", local_pkey)
        wikidata_pkey_record = sync.get_record_by_pkey("→", wikidata_pkey)

        # Assert the primary key records are correctly retrieved
        assert (
            local_pkey_record is not None and local_pkey_record["id_l"] == local_pkey
        ), "get_record_by_pkey failed for local data"
        assert (
            wikidata_pkey_record is not None
            and wikidata_pkey_record["id_r"] == wikidata_pkey
        ), "get_record_by_pkey failed for wikidata"

        try:
            invalid_side = "invalid_side"
            sync.get_record_by_pkey(invalid_side, "1")  # Deliberately incorrect
            assert False, "Expected ValueError for invalid side not raised"
        except ValueError as e:
            if debug:
                print(f"Caught expected ValueError for side: {str(e)}")

        # Provoke ValueError by passing an invalid direction to get_keys
        try:
            invalid_direction = "invalid_direction"
            sync.get_keys(invalid_direction)  # Deliberately incorrect
            assert False, "Expected ValueError for invalid direction not raised"
        except ValueError as e:
            if debug:
                print(f"Caught expected ValueError for direction: {str(e)}")
