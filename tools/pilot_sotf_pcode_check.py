"""Optional independent instruction-decoder / numeric host check via pypcode.

Run from the repo root after `python -m pip install pypcode==4.1.0` (or record the
installed version). Executes Ghidra SLEIGH P-code for emitted shims AND the actual
GM interpolation bytes. This small interpreter is not an ECU emulator.
"""
import importlib.metadata
import json
import math
from pathlib import Path
import random
import struct

import pypcode

import pilot_sotf_9844 as P
from e41_export_integrity import Export


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def float_value(value, size):
    return struct.unpack('>f' if size == 4 else '>d', value.to_bytes(size, 'big'))[0]


def float_bits(value, size=4):
    return int.from_bytes(struct.pack('>f' if size == 4 else '>d', value), 'big')


class Machine:
    def __init__(self, context, image, cache):
        self.context, self.image, self.cache = context, image, cache
        self.export = Export(image)
        self.spaces = {'register': {}, 'unique': {}, 'ram': {}}
        self.return_address = 0x12345678

    def value(self, node):
        if node.space.name == 'const':
            return node.offset
        storage = self.spaces[node.space.name]
        return int.from_bytes(bytes(storage.get(node.offset + i, 0) for i in range(node.size)), 'big')

    def assign(self, node, value):
        value &= (1 << (node.size * 8)) - 1
        storage = self.spaces[node.space.name]
        for i, byte in enumerate(value.to_bytes(node.size, 'big')):
            storage[node.offset + i] = byte

    def register(self, name, value=None):
        node = self.context.registers[name]
        if value is None:
            return self.value(node)
        self.assign(node, value)

    def read_ram(self, address, size):
        memory = self.spaces['ram']
        if all(address + i in memory for i in range(size)):
            return int.from_bytes(bytes(memory[address + i] for i in range(size)), 'big')
        at = self.export.file_offset(address, size)
        return int.from_bytes(self.image[at:at + size], 'big')

    def run(self, pc, stop=None):
        instructions = 0
        while pc != (self.return_address if stop is None else stop):
            instructions += 1
            if instructions > 256:
                raise AssertionError('Instruction budget exceeded')
            at = self.export.file_offset(pc, 4)
            key = (pc, bytes(self.image[at:at + 4]))
            if key not in self.cache:
                translation = self.context.translate(key[1], base_address=pc,
                                                     max_instructions=1)
                self.cache[key] = translation.ops
            ops = self.cache[key]
            next_pc = pc + ops[0].inputs[0].size
            self.spaces['unique'] = {}
            index = 0
            while index < len(ops):
                op = ops[index]
                name = op.opcode.name
                inp, out = op.inputs, op.output
                if name == 'IMARK':
                    index += 1
                    continue
                if name in ('BRANCH', 'CBRANCH', 'RETURN', 'CALL'):
                    take = name != 'CBRANCH' or self.value(inp[1]) != 0
                    if take:
                        if inp[0].space.name == 'const' and name != 'RETURN':
                            index += signed(inp[0].offset, inp[0].size * 8)
                            continue
                        next_pc = self.value(inp[0]) if name == 'RETURN' else inp[0].offset
                        break
                elif name == 'STORE':
                    address, value = self.value(inp[1]), self.value(inp[2])
                    for i, byte in enumerate(value.to_bytes(inp[2].size, 'big')):
                        self.spaces['ram'][address + i] = byte
                elif name == 'LOAD':
                    self.assign(out, self.read_ram(self.value(inp[1]), out.size))
                else:
                    values = [self.value(node) for node in inp]
                    a = values[0]
                    b = values[1] if len(values) > 1 else None
                    if name in ('COPY', 'INT_ZEXT'):
                        result = a
                    elif name == 'INT_SEXT':
                        result = signed(a, inp[0].size * 8)
                    elif name == 'INT_ADD':
                        result = a + b
                    elif name == 'INT_SUB':
                        result = a - b
                    elif name == 'INT_MULT':
                        result = a * b
                    elif name == 'INT_AND':
                        result = a & b
                    elif name == 'INT_OR':
                        result = a | b
                    elif name == 'INT_XOR':
                        result = a ^ b
                    elif name == 'INT_LEFT':
                        result = a << b
                    elif name == 'INT_RIGHT':
                        result = a >> b
                    elif name == 'INT_NEGATE':
                        result = ~a
                    elif name == 'INT_2COMP':
                        result = -a
                    elif name == 'INT_EQUAL':
                        result = int(a == b)
                    elif name == 'INT_NOTEQUAL':
                        result = int(a != b)
                    elif name == 'INT_LESS':
                        result = int(a < b)
                    elif name == 'INT_LESSEQUAL':
                        result = int(a <= b)
                    elif name == 'INT_SLESS':
                        result = int(signed(a, inp[0].size * 8) < signed(b, inp[1].size * 8))
                    elif name == 'BOOL_NEGATE':
                        result = int(not a)
                    elif name == 'FLOAT_INT2FLOAT':
                        result = float_bits(float(signed(a, inp[0].size * 8)), out.size)
                    elif name == 'FLOAT_TRUNC':
                        result = math.trunc(float_value(a, inp[0].size))
                    elif name == 'FLOAT_NAN':
                        result = int(math.isnan(float_value(a, inp[0].size)))
                    elif name == 'FLOAT_NEG':
                        result = float_bits(-float_value(a, inp[0].size), out.size)
                    elif name.startswith('FLOAT_'):
                        x, y = float_value(a, inp[0].size), float_value(b, inp[1].size)
                        if name == 'FLOAT_EQUAL':
                            result = int(x == y)
                        elif name == 'FLOAT_LESS':
                            result = int(x < y)
                        elif name == 'FLOAT_ADD':
                            result = float_bits(x + y, out.size)
                        elif name == 'FLOAT_SUB':
                            result = float_bits(x - y, out.size)
                        elif name == 'FLOAT_MULT':
                            result = float_bits(x * y, out.size)
                        else:
                            raise NotImplementedError(name)
                    else:
                        raise NotImplementedError(name)
                    self.assign(out, result)
                index += 1
            pc = next_pc
        return instructions


def prepare(context, image, cache, base, x, y, tune=1, ready=2, enabled=1):
    machine = Machine(context, image, cache)
    for i in range(32):
        machine.register(f'r{i}', (0x10203040 + i * 0x10203) & 0xFFFFFFFF)
    machine.register('r1', 0x40030000)
    machine.register('r3', base)
    # This GM routine takes row fraction in r4 and column fraction in r5.
    for reg, value in [('r4', y), ('r5', x), ('r6', 15.0), ('r7', 14.0), ('r8', 1 / 128)]:
        machine.register(reg, float_bits(value))
    machine.register('LR', machine.return_address)
    machine.register('CTR', 0x98765432)
    for i in range(8):
        machine.register(f'cr{i}', i + 1)
    machine.spaces['ram'].update({0x4005E400: ready, 0x4005E414: tune, P.DATA_CPU: enabled})
    return machine


def run_checks():
    root = Path(__file__).resolve().parents[1]
    source = next((root / 'uploads').glob('ECM*11_10*bin')).read_bytes()
    candidate, manifest = P.build(source)
    context = pypcode.Context('PowerPC:BE:32:e200')
    cache = {}
    assembly = []
    for index in range(9):
        cpu = P.CODE_CPU + index * P.WRAPPER_STRIDE
        assembly.append(str(context.disassemble(P.wrapper(cpu, P.DATA_CPU + 32 + index * 2400), base_address=cpu)))
    checks = 0
    # Baseline-equivalence tests execute the actual GM routine on both paths.
    for index, (_, base, call) in enumerate(P.TABLES):
        for tune in range(6):
            for x, y in [(0.0, 0.0), (1.0, 1.0), (0.37, 0.63)]:
                original = prepare(context, source, cache, base, x, y, tune)
                modified = prepare(context, candidate, cache, base, x, y, tune)
                original.run(call, stop=call + 4)
                modified.run(call, stop=call + 4)
                for i in range(32):
                    assert original.register(f'r{i}') == modified.register(f'r{i}'), (index, tune, x, y, i)
                for name in ['LR', 'CTR'] + [f'cr{i}' for i in range(8)]:
                    assert original.register(name) == modified.register(name), (name, index, tune)
                checks += 1
    # Distinct synthetic copies expose wrong-position or wrong-table selection.
    changed = bytearray(candidate)
    table_indexes = {name: i for i, (name, _, _) in enumerate(P.TABLES)}
    for row in manifest['tables']:
        raw = [128 * row['tune'] + row_index * 15 + column +
               32 * table_indexes[row['name']]
               for row_index in range(16) for column in range(15)]
        struct.pack_into('>240h', changed, row['file_offset'], *raw)
    rng = random.Random(9844)
    samples = [(0.0, 0.0), (1.0, 1.0), (-0.1, 1.1)] + [(rng.random(), rng.random()) for _ in range(5)]
    selection_checks = 0
    for index, (_, base, _) in enumerate(P.TABLES):
        for tune in range(1, 6):
            for x, y in samples:
                machine = prepare(context, changed, cache, base, x, y, tune)
                machine.run(P.CODE_CPU + index * P.WRAPPER_STRIDE)
                expected = (128 * tune + 32 * index + 15 * min(1, max(0, y)) * 15 +
                            min(1, max(0, x)) * 14) / 128
                actual = float_value(machine.register('r3'), 4)
                assert math.isclose(actual, expected, rel_tol=2e-6, abs_tol=2e-6), (index, tune, x, y, actual, expected)
                selection_checks += 1
    fallback_checks = 0
    for index, (_, base, _) in enumerate(P.TABLES):
        original = prepare(context, source, cache, base, 0.37, 0.63)
        original.run(P.LOOKUP)
        for ready, tune, enabled in [(0, 1, 1), (1, 1, 1), (255, 1, 1),
                                     (2, 0, 1), (2, 6, 1), (2, 255, 1),
                                     (2, 1, 0), (2, 5, 255)]:
            machine = prepare(context, changed, cache, base, 0.37, 0.63, tune, ready, enabled)
            machine.run(P.CODE_CPU + index * P.WRAPPER_STRIDE)
            assert machine.register('r3') == original.register('r3'), (index, ready, tune, enabled)
            fallback_checks += 1
    return dict(pypcode_version=importlib.metadata.version('pypcode'),
                language='PowerPC:BE:32:e200', baseline_numeric_cases=checks,
                distinct_copy_numeric_cases=selection_checks,
                fallback_numeric_cases=fallback_checks,
                status='PASS_HOST_MODEL_ONLY',
                limitations=['Not a complete ECU emulator', 'No interrupt or timing validation',
                             'Finite interpolation cases only; exceptional floating-point behavior untested']), assembly


if __name__ == '__main__':
    report, _ = run_checks()
    print(json.dumps(report, indent=2))
