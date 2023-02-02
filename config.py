from params import ParameterSet
from presets import PresetList

sent_params_file = "parameters_send.csv"
get_params_file = "parameters_get.csv"

class Config:
    def __init__(self):
        self.test_mode = False
        self.initialized = False
        self.logging = False
        self.sent_parameters = ParameterSet(sent_params_file, name="Sent Parameters", bytes=0x44, pad=1)
        self.get_parameters = ParameterSet(get_params_file, name="Get Parameters", bytes=0xA2, pad=1)
        self.presets = PresetList(self.sent_parameters, "./presets")
