"""
Created on 2024-01-21

@author: wf
"""

import json
import urllib.request
from dataclasses import field
from datetime import date
from typing import Any, Dict, List, Optional

from basemkit.yamlable import DateConvert, lod_storable
from slugify import slugify


@lod_storable
class Royal:
    """
    Represents a member of the royal family, with various personal details.

    Attributes:
        name (str): The full name of the royal member.
        wikidata_id (str): The Wikidata identifier associated with the royal member.
        number_in_line (Optional[int]): The number in line to succession, if applicable.
        born_iso_date (Optional[str]): The ISO date of birth.
        died_iso_date (Optional[str]): The ISO date of death, if deceased.
        last_modified_iso (str): ISO timestamp of the last modification.
        age (Optional[int]): The age of the royal member.
        of_age (Optional[bool]): Indicates whether the member is of legal age.
        wikidata_url (Optional[str]): URL to the Wikidata page of the member.
    """

    name: str
    wikidata_id: str
    number_in_line: Optional[int] = None
    born_iso_date: Optional[str] = None
    died_iso_date: Optional[str] = None
    lastmodified_iso: Optional[str] = None
    age: Optional[int] = field(init=None)
    of_age: Optional[bool] = field(init=None)
    wikidata_url: Optional[str] = field(init=None)

    def __post_init__(self):
        """
        init calculated fields
        """
        end_date = self.died if self.died else date.today()
        self.age = int((end_date - self.born).days / 365.2425)
        self.of_age = self.age >= 18
        if self.wikidata_id:
            self.wikidata_url = f"https://www.wikidata.org/wiki/{self.wikidata_id}"

    @property
    def identifier(self) -> str:
        """
        Generates a unique identifier for the Royal instance.
        The identifier is a combination of a slugified name and the Wikidata ID (if available).
        """
        slugified_name = slugify(self.name, lowercase=False, regex_pattern=r"[^\w\-]")
        if self.wikidata_id:
            return f"{slugified_name}-{self.wikidata_id}"
        return slugified_name

    @property
    def born(self) -> date:
        """Return the date of birth from the ISO date string."""
        born_date = DateConvert.iso_date_to_datetime(self.born_iso_date)
        return born_date

    @property
    def died(self) -> Optional[date]:
        """Return the date of death from the ISO date string, if available."""
        died_date = DateConvert.iso_date_to_datetime(self.died_iso_date)
        return died_date


@lod_storable
class Royals:
    """
    Represents a collection of Royal family members.

    Attributes:
        members (List[Royal]): A list of Royal family members.
    """

    members: List[Royal] = field(default_factory=list)

    @classmethod
    def get_samples(cls) -> dict[str, "Royals"]:
        """
        Returns a dictionary of named samples
        for 'specification by example' style
        requirements management.

        Returns:
            dict: A dictionary with keys as sample names and values as `Royals` instances.
        """
        samples = {
            "QE2 heirs up to number in line 5": Royals(
                members=[
                    Royal(
                        name="Elizabeth Alexandra Mary Windsor",
                        born_iso_date="1926-04-21",
                        died_iso_date="2022-09-08",
                        wikidata_id="Q9682",
                        number_in_line=-1,  # for deceased or unranked
                        lastmodified_iso="2022-09-08",
                    ),
                    Royal(
                        name="Charles III of the United Kingdom",
                        born_iso_date="1948-11-14",
                        number_in_line=0,
                        wikidata_id="Q43274",
                        lastmodified_iso="2022-09-08",
                    ),
                    Royal(
                        name="William, Duke of Cambridge",
                        born_iso_date="1982-06-21",
                        number_in_line=1,
                        wikidata_id="Q36812",
                        lastmodified_iso="2022-09-08",
                    ),
                    Royal(
                        name="Prince George of Wales",
                        born_iso_date="2013-07-22",
                        number_in_line=2,
                        wikidata_id="Q13590412",
                        lastmodified_iso="2022-09-08",
                    ),
                    Royal(
                        name="Princess Charlotte of Wales",
                        born_iso_date="2015-05-02",
                        number_in_line=3,
                        wikidata_id="Q18002970",
                        lastmodified_iso="2022-09-08",
                    ),
                    Royal(
                        name="Prince Louis of Wales",
                        born_iso_date="2018-04-23",
                        number_in_line=4,
                        wikidata_id="Q38668629",
                        lastmodified_iso="2022-09-08",
                    ),
                    Royal(
                        name="Harry Duke of Sussex",
                        born_iso_date="1984-09-15",
                        number_in_line=5,
                        wikidata_id="Q152316",
                        lastmodified_iso="2022-09-08",
                    ),
                ]
            )
        }
        return samples


@lod_storable
class Country:
    """
    Represents a country with its details.

    Attributes:
        name (str): The name of the country.
        country_code (str): The country code.
        capital (Optional[str]): The capital city of the country.
        timezones (List[str]): List of timezones in the country.
        latlng (List[float]): Latitude and longitude of the country.
    """

    name: str
    country_code: str
    capital: Optional[str] = None
    timezones: List[str] = field(default_factory=list)
    latlng: List[float] = field(default_factory=list)


@lod_storable
class Countries:
    """
    Represents a collection of country instances.

    Attributes:
        countries (List[Country]): A list of Country instances.
    """

    countries: List[Country]

    @classmethod
    def get_countries_erdem(cls) -> "Countries":
        """
        get Erdem Ozkol's country list
        """
        countries_json_url = "https://gist.githubusercontent.com/erdem/8c7d26765831d0f9a8c62f02782ae00d/raw/248037cd701af0a4957cce340dabb0fd04e38f4c/countries.json"
        json_str = cls.read_from_url(countries_json_url)
        countries_list = json.loads(json_str)
        countries_dict = {"countries": countries_list}
        instance = cls.from_dict(countries_dict)
        return instance

    @classmethod
    def get_samples(cls) -> dict[str, "Countries"]:
        """
        Returns a dictionary of named samples
        for 'specification by example' style
        requirements management.

        Returns:
            dict: A dictionary with keys as sample names
            and values as `Countries` instances.
        """
        samples = {"country list provided by Erdem Ozkol": cls.get_countries_erdem()}
        return samples


class Sample:
    """
    Sample dataset provider
    """

    cityList = None

    @staticmethod
    def get(dataset_name: str):
        """
        Get the given sample dataset name
        """
        samples = None
        if dataset_name == "royals":
            samples = Royals.get_samples()
        elif dataset_name == "countries":
            samples = Countries.get_samples()
        else:
            raise ValueError("Unknown dataset name")
        return samples

    @staticmethod
    def getRoyalsSample() -> Royals:
        samples = Royals.get_samples()
        all_members = []
        for royals in samples.values():
            all_members.extend(royals.members)
        royals = Royals(members=all_members)
        return royals

    @staticmethod
    def getSample(size) -> List[Dict[str, Any]]:
        """
        get a generated sample of the given size
        """
        listOfDicts = []
        for index in range(size):
            listOfDicts.append({"pkey": "index%d" % index, "cindex": index})
        return listOfDicts

    @staticmethod
    def getRoyals() -> List[Dict[str, Any]]:
        """
        compatibility for old sample module
        return list of dicts
        """
        royals_dict = Royals.get_samples()
        royals = royals_dict.get("QE2 heirs up to number in line 5")
        royals_lod = []
        for royal in royals.members:
            record = royal.to_dict()
            royals_lod.append(record)
        return royals_lod

    @staticmethod
    def getCities() -> List[Dict[str, Any]]:
        """
        get a list of city records
        compatibility for old sample module
        return list of dicts
        """
        if Sample.cityList is None:
            cityJsonUrl = "https://raw.githubusercontent.com/lutangar/cities.json/master/cities.json"
            with urllib.request.urlopen(cityJsonUrl) as url:
                Sample.cityList = json.loads(url.read().decode())
            for city in Sample.cityList:
                city["cityId"] = "%s-%s" % (city["country"], city["name"])
        return Sample.cityList
