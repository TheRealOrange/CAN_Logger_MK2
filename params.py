import csv
import time
from pathlib import Path


class Parameter:
    def __init__(self, name: str, byte_len: int, signed: bool, units: str, offset: int, param_min: int, param_max: int,
                 default: int = 0, check: bool = True):
        self.name = name
        self.byte_len = byte_len
        self.signed = signed
        self.units = units
        self.offset = offset
        self.min = param_min
        self.max = param_max
        self.default = default
        self._value = self.default
        self.check = check

        if (self.min > self.max):
            raise ValueError("Parameter minimum must be smaller than maximum!", self.name, self.min, self.max)
        if (self.default > self.max or self.default < self.min):
            raise ValueError("Parameter default value must be within min/max bounds!", self.name, self.min, self.max,
                             self.default)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, a):
        if (self.check and (a > self.max or a < self.min)):
            raise ValueError("Attempted to set a value not within bounds for parameter!", self.name, self.min, self.max,
                             a)
        self._value = a

    def from_bytes(self, bytes):
        val = int.from_bytes(bytes, byteorder='big', signed=self.signed)
        self.value = val

    def __bytes__(self):
        return self._value.to_bytes(self.byte_len, byteorder='big', signed=self.signed)

    def __repr__(self):
        return f"{self.name:<33}-> value: {self.value:>5} | units: {self.units:>5} | offset: {self.offset:>3} | bounds: ({self.min:>5}, {self.max:>5}) | default: {self.default:>5}"


class ParameterSet:
    def __init__(self, file: str, name: str, bytes: int = None, pad: int = 1, check=True):
        self.file = file
        self.set_name = name
        self.params = dict()
        self._pad = pad
        self.check = check
        if (not Path.is_file(Path(file))):
            raise FileNotFoundError("Parameter file does not exist!", file)

        max_offset = 0
        max_offset_bytelen = 0
        with open(file, encoding='utf-8-sig', mode='r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            n = 0
            for row in csv_reader:
                if (n != 0):
                    if (row[3] == "SPARE"):
                        continue
                    name = row[0]
                    byte_len = int(row[1])
                    signed = bool(int(row[2]))
                    units = row[3]
                    offset = int(row[4])
                    param_min = int(row[5])
                    param_max = int(row[6])
                    default = int(row[7])
                    if (name in self.params):
                        raise AttributeError("Parameter already exists in parameter list!", name)
                    self.params[name] = Parameter(name, byte_len, signed, units, offset, param_min, param_max, default,
                                                  check=(False if (units == "ERR" or not self.check) else True))
                    if (self.params[name].offset > max_offset):
                        max_offset = self.params[name].offset
                        max_offset_bytelen = self.params[name].byte_len
                n += 1

        self.min_len = max_offset + max_offset_bytelen
        if (bytes is None):
            self._bytes = self.min_len
        elif (self.min_len > bytes):
            raise ValueError("Specified byte length is not sufficient to contain parameters!", self.min_len, bytes)
        else:
            self._bytes = bytes

    @property
    def byte_length(self):
        return self._bytes

    @property
    def parameter_names(self):
        return list(self.params.keys())

    @property
    def values(self):
        out = dict()
        for key, param in self.params.items():
            out[param.name] = param.value
        return out

    def default(self):
        new_ps = ParameterSet(self.file, self.set_name, self._bytes, self._pad)
        for p in new_ps:
            p.value = p.default
        return new_ps

    def __getitem__(self, item) -> Parameter:
        return self.params[item]

    def __setitem__(self, key, value):
        self.params[key].value = value

    def __iter__(self):
        for x in self.params.values():
            yield x

    def __repr__(self):
        out = f"Parameter Set {self.set_name} from file {self.file}\n"
        for p in self.params.values():
            out += str(p) + "\n"
        return out

    def pack(self):
        out = bytearray([0xff if self._pad else 0x0] * self._bytes)
        for key, param in self.params.items():
            byte_start = param.offset
            byte_end = param.offset + param.byte_len
            out[byte_start:byte_end] = bytes(param)
        return out

    def unpack(self, data: bytearray):
        if (len(data) < self.min_len):
            raise AttributeError("Given data is too small to be unpacked into parameter set!", self.min_len, len(data))

        for key, param in self.params.items():
            byte_start = param.offset
            byte_end = param.offset + param.byte_len
            param.from_bytes(data[byte_start:byte_end])


class ParameterLog:
    def __init__(self, parameter_set: ParameterSet, logdir=None):
        self.parameter_set = parameter_set
        self.data = dict()
        self.time = []
        self.names = self.parameter_set.parameter_names
        for n in self.names:
            self.data[n] = []

        self.csv = False
        if (not (logdir is None)):
            Path(logdir).mkdir(parents=True, exist_ok=True)
            self.filename = Path(logdir) / time.strftime("%Y_%b_%d-%H_%M_%S.csv")
            self.file = open(str(self.filename), 'w', newline='')
            self.writer = csv.writer(self.file)
            self.writer.writerow(["time"] + self.names)
            self.file.flush()
            self.csv = True

        self.start_time = time.time()

    def log_datapoint(self, data, t=None):
        if (t is None):
            t = time.time()
        row = [t]
        self.parameter_set.unpack(data)
        vals = self.parameter_set.values
        for p in self.names:
            self.data[p].append(vals[p])
            row.append(vals[p])
        self.time.append(t)
        if (self.csv):
            self.writer.writerow(row)
            #print(row)
            self.file.flush()

    def get_data_series(self, name, elapsed=True):
        return [i for i in self.data[name]], [(i-self.start_time if elapsed else i) for i in self.time]
