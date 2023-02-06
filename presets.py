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
        elif (name is None and not file is None):
            if (not Path(file).is_file()):
                raise FileNotFoundError("Preset file does not exist!", file)
            self.file = file
            self.load_from_file()
        elif (not name is None and Path(file).is_dir()):
            self.name = name
            self.load_defaults()
            self.file = (Path(file) / f"{uuid.uuid4()}.json")
            self.parameter_set_name = self.parameter_set.set_name
            self.save_to_file()
        else:
            raise FileNotFoundError("Invalid directory!")

    def diff(self):
        with open(self.file, 'r') as f:
            data = json.load(f)
            if (("name" in data) and ("parameter_set" in data) and ("parameters" in data)):
                if (self.parameter_set_name != data["parameter_set"]):
                    raise ValueError("Incorrect parameter set for preset!")

                if (self.name != data["name"]):
                    return True
                for p in self.parameter_set.parameter_names:
                    if (not p in self.params):
                        raise ValueError("Missing parameter in file!")
                    if (self.values[p] != data["parameters"][p]):
                        return True
            else:
                raise ValueError("File content is not valid!")
        return False

    def load_defaults(self):
        self.values = dict()
        for p in self.parameter_set:
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

    def delete_file(self):
        Path(self.file).unlink(missing_ok=True)

    def rename(self, name: str):
        self.name = name


class PresetList:
    def __init__(self, parameter_set: ParameterSet, directory: str):
        self.parameter_set = parameter_set
        self.directory = directory

        self.dirpath = Path(directory)
        self.dirpath.mkdir(parents=True, exist_ok=True)

        self.presets = dict()

        self.load_dir_files()
        if (not 'default' in self.presets):
            self.add_preset(self.parameter_set.default(), 'default')

    def load_dir_files(self):
        self.presets = dict()
        for f in self.dirpath.iterdir():
            print(f"{f} - {'dir' if f.is_dir() else 'file'}")
            if (f.is_file()):
                try:
                    p = Preset(self.parameter_set, file=str(f))
                    self.presets[p.name] = p
                except ValueError:
                    print(f"{f} is not a valid preset file")

    def __contains__(self, item):
        return item in self.presets

    def __getitem__(self, item) -> Preset:
        return self.presets[item]

    def __setitem__(self, key, value):
        self.presets[key] = value

    def __iter__(self):
        for x in self.presets.values():
            yield x

    def add_preset(self, parameters: ParameterSet, name: str):
        if (name in self):
            raise NameError("Name already exists!")
        if (parameters.set_name != self.parameter_set.set_name):
            raise ValueError(
                f"Invalid paramater set assignment from {parameters.set_name} to {self.parameter_set.set_name}")
        preset = Preset(self.parameter_set, name=name, file=self.directory)
        for p in parameters:
            preset.values[p.name] = p.value
        preset.save_to_file()
        self.presets[name] = preset

    def remove_preset(self, name: str):
        if (not name in self):
            raise NameError("No such preset!")
        self[name].delete_file()
        del self.presets[name]

    def rename_preset(self, name: str, new_name: str):
        if (not name in self):
            raise NameError("No such preset!")
        if (new_name in self):
            raise NameError("New name already exists!")
        self[name].rename(new_name)
        self[new_name] = self[name]
        del self.presets[name]
        self[new_name].save_to_file()
