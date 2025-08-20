from pandas import DataFrame

class Cities:
    data = None
    _inited = False
    def __init__(self ,path="../database/background/citySet_with_states.txt") -> None:
        self.path = path
        if not self._inited:
            self._inited = True
            self.load_data()
            print("Cities loaded.")

    def load_data(self):
        cityStateMapping = open(self.path, "r").read().strip().split("\n")
        self.__class__.data = {}
        for unit in cityStateMapping:
            city, state = unit.split("\t")
            if state not in self.__class__.data:
                self.__class__.data[state] = [city]
            else:
                self.__class__.data[state].append(city)

    def run(self, state) -> dict:
        if state not in self.data:
            return ValueError("Invalid State")
        else:
            return self.data[state]
