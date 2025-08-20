import pandas as pd
from pandas import DataFrame
from typing import Optional
from ...utils.func import extract_before_parenthesis


class Accommodations:
    data = None
    _inited = False
    def __init__(self, path="../database/accommodations/clean_accommodations_2022.csv"):
        self.path = path
        if not self._inited:
            self._inited = True
            self.__class__.data = pd.read_csv(self.path).dropna()[
                [
                    "NAME",
                    "price",
                    "room type",
                    "house_rules",
                    "minimum nights",
                    "maximum occupancy",
                    "review rate number",
                    "city",
                ]
            ]
            print("Accommodations loaded.")

    def load_db(self):
        self.data = pd.read_csv(self.path).dropna()

    def run(self,
            city: str,
            ) -> DataFrame:
        """Search for accommodations by city."""
        results = self.data[self.data["city"] == city]
        if len(results) == 0:
            return "There is no attraction in this city."

        return results

    def run_for_annotation(self,
            city: str,
            ) -> DataFrame:
        """Search for accommodations by city."""
        results = self.data[self.data["city"] == extract_before_parenthesis(city)]
        return results
