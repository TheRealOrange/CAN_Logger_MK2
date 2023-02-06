from canlib import canlib, Frame, connected_devices
from canlib.canlib import MessageFlag

from params import ParameterSet, ParameterLog
from presets import PresetList

from driver_mk2 import *

sent_params_file = "parameters_send.csv"
get_params_file = "parameters_get.csv"

DEBUGGING = False

def gen_frame(hx_id: int, hx_data: bytes) -> Frame:
    """Create a Frame from CAN id in hex and data in bytearray"""
    return Frame(hx_id, hx_data, flags=MessageFlag.EXT)


class Config:
    def __init__(self):
        self.test_mode = False
        self.initialized = False
        self.logging = False
        self.sent_parameters = ParameterSet(sent_params_file, name="Sent Parameters", bytes=0x3C, pad=1)
        self.get_parameters = ParameterSet(get_params_file, name="Get Parameters", bytes=0x9A, pad=1, check=False)
        self.presets = PresetList(self.sent_parameters, "./presets")

        self.get_log: ParameterLog = None

        self.ch = None

        print(self.sent_parameters)
        print(" ")
        print(self.get_parameters)

        print('Setting up CANLib...')
        for dev in connected_devices():
            print(dev.probe_info())

        self.set_up_channel()
        print('CanLib setup complete!')
        print("canlib version:", canlib.dllversion())

    def new_log(self):
        self.get_log = ParameterLog(self.get_parameters, logdir="./logs")

    def set_up_channel(self):
        if (not DEBUGGING):
            self.ch = canlib.openChannel(channel=0, bitrate=canlib.Bitrate.BITRATE_1M)
            self.ch.busOn()

    def remove_channel(self):
        if (not self.ch is None):
            self.ch.busOff()
            self.ch.close()

    def send_frames(self, frames):
        for frame in frames:
            print(f'{datetime.now().isoformat()} -> sending ', hex(frame[0]), frame[1].hex())
            if (not DEBUGGING):
                self.ch.write(gen_frame(frame[0], frame[1]))

    def receive_frame(self, timeout: int) -> Frame:
        frame = self.ch.read(timeout)
        print(f'{datetime.now().isoformat()} -> received', hex(frame.id), frame.data.hex())
        return frame

    def poll_frames(self):
        frame = self.receive_frame(-1)
        buffer = frame.id
        buffer >>= pad_bits
        frame_cnt = buffer & ((1 << 8) - 1)

        frames = [frame]
        for i in range(frame_cnt):

            frame = self.receive_frame(-1)
            frames.append(frame)
        return frames
