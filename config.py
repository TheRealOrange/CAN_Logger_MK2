from pathlib import Path

from canlib import canlib, Frame, connected_devices
from canlib.canlib import MessageFlag

from params import ParameterSet, ParameterLog
from presets import PresetList

from driver_mk2 import *

from datetime import datetime
import logging
import sys

sent_params_file = "parameters_send.csv"
get_params_file = "parameters_get.csv"

logdir = "./logs"

DEBUGGING = False

def gen_frame(hx_id: int, hx_data: bytes) -> Frame:
    """Create a Frame from CAN id in hex and data in bytearray"""
    return Frame(hx_id, hx_data, flags=MessageFlag.EXT)


class Config:
    def __init__(self):
        self.print_log_filename = Path(logdir) / datetime.now().strftime("%Y_%b_%d-%H_%M_%S.log")
        self.targets = logging.StreamHandler(sys.stdout), logging.FileHandler(str(self.print_log_filename), encoding="utf-8")
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, handlers=self.targets, encoding="utf-8")
        self.logger = logging.getLogger(__name__)

        self.test_mode = False
        self.initialized = False
        self.logging = False
        self.sent_parameters = ParameterSet(sent_params_file, name="Sent Parameters", bytes=0x3C, pad=1)
        self.get_parameters = ParameterSet(get_params_file, name="Get Parameters", bytes=0x9A, pad=1, check=False)
        self.presets = PresetList(self.sent_parameters, "./presets")

        self.get_log: ParameterLog = None

        self.ch = None

        self.logger.info(self.sent_parameters)
        self.logger.info(self.get_parameters)

        self.logger.info('Setting up CANLib...')
        for dev in connected_devices():
            self.logger.debug(str(dev.probe_info()))

        self.set_up_channel()
        self.logger.info('CanLib setup complete!')
        self.logger.debug(f"canlib version: {str(canlib.dllversion())}")

    def exit(self):
        self.logger.info("exiting")

    def new_log(self):
        self.get_log = ParameterLog(self.get_parameters, logdir=logdir)

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
            self.logger.debug(f"{datetime.now().isoformat()} -> CAN sending: id {hex(frame[0])} | data {frame[1].hex()}")
            if (not DEBUGGING):
                self.ch.write(gen_frame(frame[0], frame[1]))

    def receive_frame(self, timeout: int) -> Frame:
        frame = self.ch.read(timeout)
        self.logger.debug(f"{datetime.now().isoformat()} -> CAN receive: id {hex(frame.id)} | data {frame.data.hex()}")
        return frame

    def poll_frames(self):
        frame = self.receive_frame(1000)
        buffer = frame.id
        buffer >>= pad_bits
        frame_cnt = buffer & ((1 << 8) - 1)

        frames = [frame]
        for i in range(frame_cnt):

            frame = self.receive_frame(-1)
            frames.append(frame)
        return frames
