"""
Created on 2024-01-21

@author: wf
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

from dataclasses_json import dataclass_json

from lodstorage.yamlable import yamlable


class DateConvert:
    """
    date converter
    """

    @classmethod
    def iso_date_to_datetime(cls, iso_date: str) -> datetime.date:
        date = datetime.strptime(iso_date, "%Y-%m-%d").date() if iso_date else None
        return date


@yamlable
@dataclass_json
@dataclass
class Royal:
    """
    A member of the royal family
    """

    name: str
    wikidata_id: str
    number_in_line: Optional[int] = None
    born_iso_date: Optional[str] = None
    died_iso_date: Optional[str] = None
    last_modified_iso: str = field(init=False)
    age: Optional[int] = field(init=None)
    of_age: Optional[bool] = field(init=None)
    wikidata_url: Optional[str] = field(init=None)

    def __post_init__(self):
        """
        init calculated fields
        """
        self.lastmodified = datetime.utcnow()
        self.last_modified_iso = self.lastmodified.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date = self.died if self.died else date.today()
        self.age = int((end_date - self.born).days / 365.2425)
        self.of_age = self.age >= 18
        if self.wikidata_id:
            self.wikidata_url = f"https://www.wikidata.org/wiki/{self.wikidata_id}"

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


@yamlable
@dataclass_json
@dataclass
class Royals:
    """
    A collection of Royal family members
    """

    members: List[Royal] = field(default_factory=list)


class Sample:
    """
    Sample dataset provider
    """

    @staticmethod
    def get(dataset_name: str):
        """
        Get the given sample dataset name
        """
        if dataset_name == "royals":
            return Royals(
                members=[
                    Royal(
                        name="Elizabeth Alexandra Mary Windsor",
                        born_iso_date="1926-04-21",
                        died_iso_date="2022-09-08",
                        wikidata_id="Q9682",
                    ),
                    Royal(
                        name="Charles III of the United Kingdom",
                        born_iso_date="1948-11-14",
                        number_in_line=0,
                        wikidata_id="Q43274",
                    ),
                    Royal(
                        name="William, Duke of Cambridge",
                        born_iso_date="1982-06-21",
                        number_in_line=1,
                        wikidata_id="Q36812",
                    ),
                    Royal(
                        name="Prince George of Wales",
                        born_iso_date="2013-07-22",
                        number_in_line=2,
                        wikidata_id="Q13590412",
                    ),
                    Royal(
                        name="Princess Charlotte of Wales",
                        born_iso_date="2015-05-02",
                        number_in_line=3,
                        wikidata_id="Q18002970",
                    ),
                    Royal(
                        name="Prince Louis of Wales",
                        born_iso_date="2018-04-23",
                        number_in_line=4,
                        wikidata_id="Q38668629",
                    ),
                    Royal(
                        name="Harry Duke of Sussex",
                        born_iso_date="1984-09-15",
                        number_in_line=5,
                        wikidata_id="Q152316",
                    ),
                ]
            )
        else:
            raise ValueError("Unknown dataset name")
