"""
Utility helpers for loading mock EMRFlow data sets (patients, schedule, FAQ).

Data is stored in JSON files under src/data and loaded as Python objects with
optional deep copies to keep in-memory mutations from touching the source files.
"""

import json
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataLoader:
    """Load mock data from the repository data directory."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent / "data"

    def load_patients(self, copy_data: bool = True) -> List[Dict[str, Any]]:
        """Load patient records."""
        data = self._load_json("patients.json")
        patients = data.get("patients", data)
        return copy.deepcopy(patients) if copy_data else patients

    def load_schedule(self, copy_data: bool = True) -> Dict[str, Any]:
        """Load doctor schedule data."""
        data = self._load_json("schedule.json")
        schedule = data if isinstance(data, dict) else {"doctors": data}
        return copy.deepcopy(schedule) if copy_data else schedule

    def load_faq(self, copy_data: bool = True) -> List[Dict[str, str]]:
        """Load FAQ entries."""
        data = self._load_json("faq.json")
        faqs = data.get("faq", data)
        return copy.deepcopy(faqs) if copy_data else faqs

    def save_patients(self, patients: List[Dict[str, Any]]) -> None:
        """
        Save patient records to patients.json.

        Args:
            patients: List of patient dictionaries to save

        Raises:
            IOError: If file write fails
        """
        patients_file = self.data_dir / "patients.json"

        try:
            with open(patients_file, "w", encoding="utf-8") as f:
                json.dump({"patients": patients}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Failed to save patients: {e}")

    def _load_json(self, filename: str) -> Any:
        """Read a JSON file from the data directory."""
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


if __name__ == "__main__":
    loader = DataLoader()
    patients = loader.load_patients()
    schedule = loader.load_schedule()
    faqs = loader.load_faq()

    print(f"Loaded {len(patients)} patients")
    print(f"Loaded {len(schedule.get('doctors', []))} doctors with schedules")
    print(f"Loaded {len(faqs)} FAQ entries")
