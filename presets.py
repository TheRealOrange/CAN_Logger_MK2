import json
import uuid
from pathlib import Path

from params import ParameterSet


class Preset:
    def __init__(self, parameter_set: ParameterSet, name: str = None, file: str = None):
        self.parameter_set = parameter_set
        self.values = dict()

        if (name is None and file is None):
            raise ValueError("Provide either the name or the file for the preset.")
        elif (not file is None):
            if (not Path.is_file(Path(file))):
                raise FileNotFoundError("Parameter file does not exist!", file)
            self.file = file
            self.load_from_file()
        elif (not name is None and Path(file).is_dir()):
            self.name = name
            self.load_defaults()
            self.file = (Path(file) / f"{uuid.uuid4()}.json").name
            self.save_to_file()
        else:
            raise FileNotFoundError("Invalid directory!")

    def load_defaults(self):
        self.values = dict()
        for p in self.parameter_set.params:
            self.values[p.name] = p.default

    def load_from_file(self):
        with open(self.file, 'r') as f:
            data = json.load(f)
            if (("name" in data) and ("parameter_set" in data) and ("parameters" in data)):
                self.name = data["name"]
                self.parameter_set_name = data["parameter_set"]
                self.params = data["parameters"]
                self.values = dict()

                if (self.parameter_set_name != self.parameter_set.set_name):
                    raise ValueError("Incorrect parameter set for preset!")

                for p in self.parameter_set.parameter_names:
                    if (not p in self.params):
                        raise ValueError("Missing parameter in file!")
                    self.values[p] = self.params[p]

            else:
                raise ValueError("File content is not valid!")

    def save_to_file(self):
        with open(self.file, 'w') as f:
            data = dict()
            data["name"] = self.name
            data["parameter_set"] = self.parameter_set_name
            data["parameters"] = self.values
            json.dump(data, f)


class PresetList:
    def __init__(self, parameter_set: ParameterSet, directory: str):
        self.parameter_set = parameter_set
        self.directory = directory

        self.dirpath = Path(directory)
        self.dirpath.mkdir(parents=True, exist_ok=True)

        self.presets = dict()

    def load_dir_files(self):
        self.presets = dict()
        for f in self.dirpath.iterdir():
            print(f"{f} - {'dir' if f.is_dir() else 'file'}")
            if (f.is_file()):
                try:
                    p = Preset(self.parameter_set, file=f.name)
                    self.presets[p.name] = p
                except ValueError:
                    print(f"{f} is not a valid preset file")

    def add_preset(self, parameters: ParameterSet, name: str):
        if (name in self.presets):
            raise NameError("Name already exists!")
        if (parameters.set_name != self.parameter_set.set_name):
            raise ValueError(f"Invalid paramater set assignment from {parameters.set_name} to {self.parameter_set.set_name}")
        preset = Preset(self.parameter_set, name=name, file=self.directory)
        for p in parameters.params:
            preset.params[p.name] = p.value
        preset.save_to_file()
        self.presets[name] = preset
