from crc import crc_16_bytes
from datetime import datetime

ID = [[0x10], [0x11]]
OBC_ID = 0x08

SRC_BITS = 8
DEST_BITS = 8
FTYPE_BITS = 1
FCNT_BITS = 8

pad_bits = 29 - SRC_BITS - DEST_BITS - FTYPE_BITS - FCNT_BITS


def init_payload_send(test=True, subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x00]
    length = [0x01]
    param = [0x01 if test else 0x00]

    return pack(preamble, ftype, cid, cmd_id, length, param)


def init_payload_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x00]
    length = [0x02]

    return unpack(frames, ftype, cid, cmd_id, length)


def pma_test_send(params, subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x07]
    length = [0x16]
    param = params

    return pack(preamble, ftype, cid, cmd_id, length, param)


def ppu_test_send(params, subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x08]
    length = [0x0C]
    param = params

    return pack(preamble, ftype, cid, cmd_id, length, param)


def set_time_send(yr, month, day, hour, mins, secs, subsys=0):
    t = datetime(yr, month, day, hour, mins, secs)

    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x01]
    length = [0x13]
    # param = t.strftime("%Y-%m-%dT%H:%M:%S")
    param = [int(i) for i in bytes(t.isoformat(), 'utf-8')]

    return pack(preamble, ftype, cid, cmd_id, length, param)


def start_operation_send(param=0, subsys=0):  # 0 for thruster 1, 1 for thruster 2, 2 for custom ignition
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x02]
    length = [0x01]
    param = [0x01 if param == 0 else (0x02 if param == 1 else 0x03)]

    return pack(preamble, ftype, cid, cmd_id, length, param)


def set_time_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x01]
    length = [0x02]

    return unpack(frames, ftype, cid, cmd_id, length)


def start_operation_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x02]
    length = [0x04]

    return unpack(frames, ftype, cid, cmd_id, length)


def stop_operation_send(subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x03]
    length = [0x01]
    param = [0x00]

    return pack(preamble, ftype, cid, cmd_id, length, param)


def stop_operation_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x03]
    length = [0x02]

    return unpack(frames, ftype, cid, cmd_id, length)


# Retry counter (0x01 ~ 0x03) Retry counter to cut off the power
# Power off time count (0x01~0xFF) Remaining time count to cut off the power. One count is 100 milliseconds
def stop_payload_send(retry_count=0x03, pwroff_delay=0xff, subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x04]
    length = [0x02]
    param = [bounded(retry_count, 0x01, 0x03), bounded(pwroff_delay, 0x01, 0xff)]

    return pack(preamble, ftype, cid, cmd_id, length, param)


def stop_payload_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x04]
    length = [0x02]

    return unpack(frames, ftype, cid, cmd_id, length)


def data_get_send(repeat=False, interval_count=0x0001, size=0x009A, addr=0xA010, subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x05]
    length = [0x08]

    intv_bytes = bounded(interval_count, 0x0001, 0xffff).to_bytes(2, 'big')
    size_bytes = bounded(size, 0x0001, 0xffff).to_bytes(2, 'big')
    addr_bytes = addr.to_bytes(2, 'big')

    param = [0x01, 0x01 if repeat else 0x00, intv_bytes[0], intv_bytes[1], size_bytes[0], size_bytes[1], addr_bytes[0],
             addr_bytes[1]]

    return pack(preamble, ftype, cid, cmd_id, length, param)


def data_get_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x05]
    length = [0xA2]

    return unpack(frames, ftype, cid, cmd_id, length)


def data_send_send(data, addr=0xA010, subsys=0):
    preamble = [0x58, 0x44, 0x41, 0x54]
    ftype = [0x01]
    cid = ID[subsys]
    cmd_id = [0x00, 0x06]
    length = [0x44]

    size = len(data)
    if size > 90:
        return None
    size_bytes = bounded(size, 0x0001, 0xffff).to_bytes(2, 'big')
    addr_bytes = addr.to_bytes(2, 'big')

    param = [0x01, 0x00, 0x00, 0x01, size_bytes[0], size_bytes[1], addr_bytes[0], addr_bytes[1]] + list(data)

    return pack(preamble, ftype, cid, cmd_id, length, param)


def data_send_receive(frames, subsys=0):
    ftype = [0x00]
    cid = ID[subsys]
    cmd_id = [0x00, 0x06]
    length = [0x02]

    return unpack(frames, ftype, cid, cmd_id, length)


def pack(preamble, frame_type, subsys_id, cmd_id, length, param):
    crc_data = bytes(preamble + frame_type + subsys_id + cmd_id + length + param)
    crc = crc_16_bytes(crc_data)

    can_data = bytes(frame_type + cmd_id + length + param) + crc
    can_data_len = len(can_data)

    frame_cnt = ceildiv(can_data_len, 8)
    fragments = [can_data[i * 8:min((i + 1) * 8, len(can_data))] for i in range(frame_cnt)]

    frames = []
    for i in range(frame_cnt):
        can_id = (OBC_ID & bitmask(SRC_BITS)) << (DEST_BITS + FTYPE_BITS + FCNT_BITS + pad_bits)
        can_id |= (subsys_id[0] & bitmask(DEST_BITS)) << (FTYPE_BITS + FCNT_BITS + pad_bits)
        can_id |= ((0 if (frame_cnt == 1) else 1) & bitmask(FTYPE_BITS)) << (FCNT_BITS + pad_bits)
        can_id |= (((frame_cnt - 1) - i) & bitmask(FCNT_BITS)) << pad_bits
        can_id |= bitmask(pad_bits)

        frames.append((can_id, fragments[i]))

    return frames


def unpack(frames, frame_type, subsys_id, cmd_id, length):
    data = bytearray()
    for i in range(len(frames)):
        frame = frames[i]
        buffer = frame.id
        buffer >>= pad_bits
        frame_cnt = buffer & bitmask(FCNT_BITS)
        if frame_cnt != len(frames) - i - 1:
            return f"Identifier frame count Mismatch: Expected {len(frames) - i}, got {frame_cnt}"
        buffer >>= FCNT_BITS
        ftype = buffer & bitmask(FTYPE_BITS)
        if ftype != int(len(frames) > 1):
            return f"Identifier frame type Mismatch: Expected {int(len(frames) > 1)}, got {ftype}"
        buffer >>= FTYPE_BITS
        src_id = buffer & bitmask(SRC_BITS)
        if src_id != OBC_ID:
            return f"Identifier SRC_ID mismatch: Expected {hex(OBC_ID)}, got {hex(src_id)}"
        buffer >>= SRC_BITS
        dst_id = buffer
        if dst_id != subsys_id[0]:
            return f"Identifier DST_ID mismatch: Expected {subsys_id[0]}, got {hex(dst_id)}"
        data.extend(frame.data)

    crc = crc_16_bytes(data[:-2])

    if crc == data[-2:]:
        return f"CRC Mismatch: Expected {crc.hex()}, got {data[-2:].hex()}"

    data = data[:-2]
    if frame_type[0] != data[0]:
        return f"Frame type Mismatch: Expected {hex(frame_type[0])}, got {hex(data[0])}"
    if bytearray(cmd_id) != data[1:3]:
        return f"Command id Mismatch: Expected {bytes(cmd_id).hex()}, got {data[1:3].hex()}"
    if length[0] != data[3]:
        return f"Length Mismatch: Expected {hex(length[0])}, got {hex(data[3])}"
    return data[4:]


def bitmask(b):
    return (1 << b) - 1


def ceildiv(a, b):
    return -(a // -b)


def bounded(inp, lower, upper):
    return max(min(inp, upper), lower)


def debug_command(frames):
    for frame in frames:
        data = frame[1].hex()
        print(hex(frame[0]), [data[i:i + 2] for i in range(0, len(data), 2)], sep=', ')
