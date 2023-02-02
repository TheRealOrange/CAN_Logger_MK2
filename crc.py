""" Util module for generating CRC-16 checksums
"""

crc_table = []

#with open('lookup.txt', 'r') as f:
#    for line in f.readlines():
#        crc_table.extend(line.split())

gen_poly = 0x8005
bits = 16

bitmask = (1<<bits)-1
for i in range(0, 256):
    b = i<<(bits-8)
    for j in range(8):
        if (b & (1<<(bits-1))):
            b = ((b << 1) ^ gen_poly) & bitmask
        else:
            b = (b << 1) & bitmask
    crc_table.append(b)


def crc_16(arr: bytearray) -> str:
    """Get CRC-16 checksum for data"""
    crc = 0
    for byte in arr:
        lookup_index = ((crc >> 8) ^ byte) & 0xff
        crc = ((crc << 8) & 0xffff) ^ crc_table[lookup_index]
    return f'{crc:0>4X}'


def crc_16_bytes(arr: bytes) -> bytes:
    """Get CRC-16 checksum for data"""
    crc = 0
    for byte in arr:
        lookup_index = ((crc >> 8) ^ byte) & 0xff
        crc = ((crc << 8) & 0xffff) ^ crc_table[lookup_index]
    return crc.to_bytes(2, "big")
