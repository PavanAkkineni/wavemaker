from typing import List, Dict


class Preset:
    """Class for a processed preset."""

    columns: Dict[str, List[int]]
    rows: List[Dict[str, int]]
    all_row: Dict[str, str]

    def __init__(self, columns: Dict[str, List[int]], rows: List[Dict[str, int]], all_row: Dict[str, str]):
        self.columns = columns
        self.rows = rows
        self.all_row = all_row

    def get_distinct_motor_sets(self) -> List[str]:
        return []
