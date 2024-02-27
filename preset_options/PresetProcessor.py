from csv import DictReader
import csv
from typing import List, Dict
from Model import Model
from preset_options.Preset import Preset


class PresetProcessor:
    """PresetProcessor Class."""

    model: Model
    ALL_PARAMS: List[str]

    csv: List[Dict[str, str]]
    columns: Dict[str, List[int]]
    rows: List[Dict[str, int]]
    all_row: Dict[str, str]

    def __init__(self, model: Model):
        """Processor for parsing preset data."""
        self.model = model
        self.ALL_PARAMS = ['Motor']
        for param in model.ALL_PARAMS:
            self.ALL_PARAMS.append(param)

    def processPreset(self, filename: str) -> Preset:
        # open a handle to the data file
        with open(filename, "r", encoding="utf8") as file_handle:
            # read that file
            csv_reader = DictReader(file_handle)
            # read each row of the csv line by line
            result: List[Dict[str, str]] = []
            for row in csv_reader:
                result.append(row)
            self.csv = result

        # create column based dictionary of data
        self.create_columns()
        # use rows to create row based list format of data
        self.create_rows()

        return Preset(self.columns, self.rows, self.all_row)

    def create_preset(self, filename: str):
        with open(f'Presets/{filename}.csv', 'w') as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(self.ALL_PARAMS)
            write_list: List[int] = []
            for i in range(30):
                if i not in self.model.live_motors:
                    writer.writerow(
                        [i, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0])
                else:
                    write_list = []
                    write_list.append(i)
                    for param in self.model.ALL_PARAMS:
                        write_list.append(
                            self.model.live_motors[i].write_params[param])
                    writer.writerow(write_list)
            final_row = ['All']
            for i in range(1, len(write_list)):
                final_row.append(str(write_list[i]))
            writer.writerow(final_row)

    def create_columns(self):
        self.columns = {}
        for row in self.csv:
            if(row['Motor'] == 'All'):
                self.all_row = row
                del self.all_row['Motor']
            else:
                for key in row:
                    if key not in self.columns:
                        self.columns[key] = []
                    self.columns[key].append(int(row[key]))

    def create_rows(self):
        self.rows = []
        for i in range(30):
            self.rows.append({})
            for key in self.columns:
                if key != 'Motor':
                    self.rows[i][key] = (self.columns[key][i])
