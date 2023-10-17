import re
import json


from dataclasses import dataclass, field
import datetime as dt


@dataclass
class Report:
    file_path: str
    data: dict = field(init=False)
    entity_name: str = field(init=False)
    entity_description: str = field(init=False)
    currency: str = field(init=False)

    def __post_init__(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.entity_name = self.get_all_facts(
            "NameOfReportingEntityOrOtherMeansOfIdentification"
        )[0]["value"].strip()

        self.currency = self.get_all_facts("Revenue")[0]["unit"]

        self.entity_description = self.get_all_facts(
            "DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities"
        )[0]["value"].strip()

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except ValueError:
            return value

    @staticmethod
    def _pascalcase_to_words(pascal_string):
        words = re.findall("[A-Z][a-z]*", pascal_string)
        return " ".join(words).capitalize()

    def get_all_facts(self, concept: str, subcomponent=False) -> list:
        records = []
        x = 0
        for key, fact in self.data["facts"].items():
            field = {
                "value": Report._to_float(fact["value"]),
                "unit": fact["dimensions"]["unit"].split(":")[1]
                if fact["dimensions"].get("unit")
                else None,
                "period_start": dt.datetime.fromisoformat(
                    fact["dimensions"]["period"].split("/")[0]
                ),
                "period_end": dt.datetime.fromisoformat(
                    fact["dimensions"]["period"].split("/")[1]
                )
                if len(fact["dimensions"]["period"].split("/")) == 2
                else None,
            }
            if subcomponent and any(
                key == f"ifrs-full:{concept}" for key in fact["dimensions"]
            ):
                field["name"] = self._pascalcase_to_words(
                    fact["dimensions"][f"ifrs-full:{concept}"].replace("ifrs-full:", "")
                )
                records.append(field)
            elif fact["dimensions"]["concept"] == f"ifrs-full:{concept}":
                field["name"]: fact["dimensions"]["concept"]
                records.append(field)
        return records

    def get_latest_fact(self, concept: str) -> dict:
        facts = self.get_all_facts(concept)
        return max(facts, key=lambda x: x["period_start"])

    def get_total_value(self, concept, period_start):
        facts = self.get_all_facts(concept, True)
        total_value = 0
        for fact in facts:
            if fact["period_start"] == period_start:
                total_value += fact["value"]
        return total_value
