"""Parse this E41 export's own range descriptors and check/repair its checksums.

This handles the additive word sum and CRC described by the supplied files.
It does not inspect or change signature verification or ECU access controls.
Addresses below are export-declared CPU addresses, not a live MMU observation.
"""
from dataclasses import dataclass
import struct


def _crc_table():
    result = []
    for value in range(256):
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
        result.append(value)
    return result


CRC_TABLE = _crc_table()


def crc16_arc(data):
    crc = 0
    for byte in data:
        crc = (crc >> 8) ^ CRC_TABLE[(crc ^ byte) & 255]
    return crc


def missing_ranges(blocks, coverage):
    gaps = []
    for start, end in blocks:
        cursor = start
        for lo, hi in sorted(coverage):
            if hi < start or lo > end:
                continue
            lo, hi = max(lo, start), min(hi, end)
            if lo < cursor:
                raise ValueError('Overlapping coverage ranges')
            if cursor < lo:
                gaps.append((cursor, lo - 1))
            cursor = hi + 1
        if cursor <= end:
            gaps.append((cursor, end))
    return gaps


@dataclass
class Segment:
    name: str
    blocks: list
    crc_ranges: list
    sum_ranges: list
    checksum_cpu: int = 0
    crc_cpu: int = 0


class Export:
    def __init__(self, data):
        if len(data) < 0x132 or data[:2] != b'\xAA\x55':
            raise ValueError('Not the expected E41 export framing')
        self.data = data
        self.segments = []
        self.mapping = []
        at, file_at = 0x32, 0
        calibration_count = data[at + 3]
        if not 1 <= calibration_count <= 16:
            raise ValueError('Invalid calibration segment count')
        for i in range(calibration_count + 1):
            counts = data[at:at + 3]
            if len(counts) != 3 or any(not 1 <= n <= 32 for n in counts):
                raise ValueError('Invalid range descriptor count')
            at += 4
            groups = []
            for count in counts:
                ranges = []
                for _ in range(count):
                    lo, hi = struct.unpack_from('>II', data, at)
                    if hi < lo or lo % 2 or hi % 2 != 1:
                        raise ValueError('Invalid word-aligned range')
                    ranges.append((lo, hi))
                    at += 8
                groups.append(ranges)
            seg = Segment('program' if i == 0 else f'calibration_{i}', *groups)
            sum_gaps = missing_ranges(seg.blocks, seg.sum_ranges)
            crc_gaps = missing_ranges(seg.blocks, seg.crc_ranges)
            if len(sum_gaps) != 1 or sum_gaps[0][1] != sum_gaps[0][0] + 1:
                raise ValueError('Expected one additive checksum word')
            seg.checksum_cpu = sum_gaps[0][0]
            other = [g for g in crc_gaps if g != sum_gaps[0]]
            if len(crc_gaps) != 2 or len(other) != 1 or other[0][1] != other[0][0] + 1:
                raise ValueError('Expected one CRC word plus additive word exclusions')
            seg.crc_cpu = other[0][0]
            self.segments.append(seg)
            for lo, hi in seg.blocks:
                if any(not (hi < a or lo > z) for a, z, _ in self.mapping):
                    raise ValueError('Overlapping transfer blocks')
                self.mapping.append((lo, hi, file_at))
                file_at += hi - lo + 1
        if file_at != len(data):
            raise ValueError('Declared transfer lengths do not equal export size')
        self.descriptor_end = at
        for seg in self.segments:
            for lo, hi in seg.crc_ranges + seg.sum_ranges:
                self.file_offset(lo, hi - lo + 1)

    def file_offset(self, cpu, size=1):
        for lo, hi, offset in self.mapping:
            if lo <= cpu and cpu + size - 1 <= hi:
                return offset + cpu - lo
        raise ValueError(f'CPU range not in one transfer block: {cpu:#x}+{size:#x}')

    def read_ranges(self, ranges, data=None):
        data = self.data if data is None else data
        return b''.join(data[self.file_offset(lo, hi - lo + 1):
                             self.file_offset(lo, hi - lo + 1) + hi - lo + 1]
                        for lo, hi in ranges)

    def audit(self, data=None):
        data = self.data if data is None else data
        results = []
        for seg in self.segments:
            raw = self.read_ranges(seg.sum_ranges, data)
            expected_sum = (-sum(struct.unpack(f'>{len(raw) // 2}H', raw))) & 65535
            expected_crc = crc16_arc(self.read_ranges(seg.crc_ranges, data))
            stored_sum = int.from_bytes(data[self.file_offset(seg.checksum_cpu):
                                            self.file_offset(seg.checksum_cpu) + 2], 'big')
            stored_crc = int.from_bytes(data[self.file_offset(seg.crc_cpu):
                                            self.file_offset(seg.crc_cpu) + 2], 'little')
            results.append(dict(segment=seg.name, blocks=seg.blocks,
                                checksum_cpu=seg.checksum_cpu, crc_cpu=seg.crc_cpu,
                                stored_sum=stored_sum, expected_sum=expected_sum,
                                stored_crc=stored_crc, expected_crc=expected_crc,
                                sum_valid=stored_sum == expected_sum,
                                crc_valid=stored_crc == expected_crc))
        return results

    def repair(self, data):
        if len(data) != len(self.data):
            raise ValueError('Export length changed')
        result = bytearray(data)
        for seg in self.segments:
            crc = crc16_arc(self.read_ranges(seg.crc_ranges, result))
            offset = self.file_offset(seg.crc_cpu)
            result[offset:offset + 2] = crc.to_bytes(2, 'little')
            raw = self.read_ranges(seg.sum_ranges, result)
            checksum = (-sum(struct.unpack(f'>{len(raw) // 2}H', raw))) & 65535
            offset = self.file_offset(seg.checksum_cpu)
            result[offset:offset + 2] = checksum.to_bytes(2, 'big')
        return bytes(result)
