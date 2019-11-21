import unittest
from emulator import Emulator


class TestEmulator(unittest.TestCase):

    def setUp(self):
        self.emu = Emulator("test.ch8", False)
        self.emu.map_opcodes_to_functions()

    def test_loading_program(self):
        self.emu.load_program_into_memory()

        expected_results = [0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF]
        for i in range(8):
            self.assertEqual(self.emu.memory[512 + i], expected_results[i])

    def test_00EE(self):
        self.emu.stack[0] = 0x0123
        self.emu.stack_pointer = 1
        self.emu.current_opcode = 0x00EE
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x0123)
        self.assertEqual(self.emu.stack_pointer, 0)

        self.emu.stack_pointer = 15
        self.emu.current_opcode = 0x00EE
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.stack_pointer, 14)

    def test_1NNN(self):
        self.emu.current_opcode = 0x1012
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x012)

    def test_2NNN(self):
        self.emu.current_opcode = 0x2012
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.stack_pointer, 1)
        self.assertEqual(self.emu.stack[self.emu.stack_pointer - 1], 0x202)
        self.assertEqual(self.emu.pc, 0x012)

    def test_3XNN(self):
        # V[1] = 14, nn = 14, next instruction should be skipped.
        self.emu.registers[1] = 0x14
        self.emu.current_opcode = 0x3114
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x204)

        # V[1] = 14, nn = 13, next instruction should not be skipped.
        self.emu.current_opcode = 0x3113
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x206)

    def test_4XNN(self):
        # V[1] = 14, nn = 14, next instruction should not be skipped.
        self.emu.registers[1] = 0x14
        self.emu.current_opcode = 0x4114
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 14, nn = 13, next instruction should be skipped.
        self.emu.current_opcode = 0x4113
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x206)

    def test_5XY0(self):
        # V[1] = A, V[2] = A, next instruction should be skipped.
        self.emu.registers[1] = 0xA
        self.emu.registers[2] = 0xA
        self.emu.current_opcode = 0x5120
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x204)

        # V[1] = A, V[2] = B, next instruction should not be skipped.
        self.emu.registers[1] = 0xA
        self.emu.registers[2] = 0xB
        self.emu.current_opcode = 0x5120
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x206)

    def test_6XNN(self):
        # V[1] should be AB.
        self.emu.current_opcode = 0x61AB
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0xAB)

    def test_7XNN(self):
        # V[1] is initially equal to 0x3. After adding NN = 0x4, V[1] should equal 0x7.
        self.emu.registers[1] = 0x3
        self.emu.current_opcode = 0x7104
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x7)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0xE6. NN = 0x1E. 0x104 cannot be stored on 8 bits, so V[1] should equal 0x4.
        self.emu.registers[1] = 0xE6
        self.emu.current_opcode = 0x711E
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x4)
        self.assertEqual(self.emu.pc, 0x204)

    def test_8XY0(self):
        # V[2] = 0x2. V[1] should equal V[2].
        self.emu.registers[2] = 0x2
        self.emu.current_opcode = 0x8120
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x2)
        self.assertEqual(self.emu.pc, 0x202)

    def test_8XY1(self):
        # V[1] = 0x1F, V[2] = 0x72. V[1] should equal 0x7F.
        self.emu.registers[1] = 0x1F
        self.emu.registers[2] = 0x72
        self.emu.current_opcode = 0x8121
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x7F)
        self.assertEqual(self.emu.pc, 0x202)

    def test_8XY2(self):
        # V[1] = 0x1F, V[2] = 0x72. V[1] should equal 0x12.
        self.emu.registers[1] = 0x1F
        self.emu.registers[2] = 0x72
        self.emu.current_opcode = 0x8122
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x12)
        self.assertEqual(self.emu.pc, 0x202)

    def test_8XY3(self):
        # V[1] = 0x1F, V[2] = 0x72. V[1] should equal 0x6D.
        self.emu.registers[1] = 0x1F
        self.emu.registers[2] = 0x72
        self.emu.current_opcode = 0x8123
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x6D)
        self.assertEqual(self.emu.pc, 0x202)

    def test_8XY4(self):
        # V[1] = 0x3, V[2] = 0x4. V[1] should equal 0x7 and V[F] should be 0x0.
        self.emu.registers[1] = 0x3
        self.emu.registers[2] = 0x4
        self.emu.current_opcode = 0x8124
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x7)
        self.assertEqual(self.emu.registers[15], 0x0)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0xE6, V[2] = 0x1E. V[1] should equal to 0x4 and V[F] should be 0x1.
        self.emu.registers[1] = 0xE6
        self.emu.registers[2] = 0x1E
        self.emu.current_opcode = 0x8124
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x4)
        self.assertEqual(self.emu.registers[15], 0x1)
        self.assertEqual(self.emu.pc, 0x204)

    def test_8XY5(self):
        # V[1] = 0x3, V[2] = 0x1. V[1] should be 0x2 and V[F] should be 0x1.
        self.emu.registers[1] = 0x3
        self.emu.registers[2] = 0x1
        self.emu.current_opcode = 0x8125
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x2)
        self.assertEqual(self.emu.registers[15], 0x1)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0x3, V[2] = 0x4. V[2] is greater than V[1] so V[1] should be 0xFF ((3 - 4) % 255 + 1). V[F] should be 0x0.
        self.emu.registers[1] = 0x3
        self.emu.registers[2] = 0x4
        self.emu.current_opcode = 0x8125
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0xFF)
        self.assertEqual(self.emu.registers[15], 0x0)
        self.assertEqual(self.emu.pc, 0x204)

    def test_8XY6(self):
        # V[1] = 0x1. V[F] should be 1 and V[1] should be 0.
        self.emu.registers[1] = 0x1
        self.emu.current_opcode = 0x8126
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x0)
        self.assertEqual(self.emu.registers[15], 0x1)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0x6, V[F] should be 0 and V[1] should be 3.
        self.emu.registers[1] = 0x6
        self.emu.current_opcode = 0x8126
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x3)
        self.assertEqual(self.emu.registers[15], 0x0)
        self.assertEqual(self.emu.pc, 0x204)

    def test_8XY7(self):
        # V[1] = 0x2, V[2] = 0x3. V[1] should be 0x1 and V[F] should be 0x1.
        self.emu.registers[1] = 0x2
        self.emu.registers[2] = 0x3
        self.emu.current_opcode = 0x8127
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0x1)
        self.assertEqual(self.emu.registers[15], 0x1)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0x5, V[2] = 0x3. V[1] should be 0xFE and V[F] should be 0x0.
        self.emu.registers[1] = 0x5
        self.emu.registers[2] = 0x3
        self.emu.current_opcode = 0x8127
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0xFE)
        self.assertEqual(self.emu.registers[15], 0x0)
        self.assertEqual(self.emu.pc, 0x204)

    def test_8XYE(self):
        # V[1] = 0xFF. V[1] should be 0xFE and V[F] should be 0x1.
        self.emu.registers[1] = 0xFF
        self.emu.current_opcode = 0x812E
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0xFE)
        self.assertEqual(self.emu.registers[15], 0x1)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0x6.  V[1] should be 0xC and V[F] should be 0x0.
        self.emu.registers[1] = 0x6
        self.emu.current_opcode = 0x812E
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.registers[1], 0xC)
        self.assertEqual(self.emu.registers[15], 0x0)
        self.assertEqual(self.emu.pc, 0x204)

    def test_9XY0(self):
        # V[1] = 0x1, V[2] = 0x1. Next instruction should not be skipped.
        self.emu.registers[1] = 0x1
        self.emu.registers[2] = 0x1
        self.emu.current_opcode = 0x9120
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0x1, V[2] = 0x2. Next instruction should be skipped.
        self.emu.registers[1] = 0x1
        self.emu.registers[2] = 0x2
        self.emu.current_opcode = 0x9120
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x206)

    def test_ANNN(self):
        # NNN = 0x4EF.
        self.emu.current_opcode = 0xA4EF
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.I, 0x4EF)
        self.assertEqual(self.emu.pc, 0x202)

    def test_BNNN(self):
        # NNN = 0x21A, V[0] = 0x2. PC should be set to 0x21C.
        self.emu.registers[0] = 0x2
        self.emu.current_opcode = 0xB21A
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.pc, 0x21C)

    def test_FX1E(self):
        # I = 0x57, V[1] = 0x2. I should be set to 0x59.
        self.emu.I = 0x57
        self.emu.registers[1] = 0x2
        self.emu.current_opcode = 0xF11E
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.I, 0x59)
        self.assertEqual(self.emu.pc, 0x202)

    def test_FX29(self):
        # V[1] = 0. I should be set to sprites base address + 0.
        self.emu.registers[1] = 0x0
        self.emu.current_opcode = 0xF129
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.I, self.emu.sprites_base_addr + 0x0)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 1. I should be set to sprites base address + 5.
        self.emu.registers[1] = 0x1
        self.emu.current_opcode = 0xF129
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.I, self.emu.sprites_base_addr + 0x5)
        self.assertEqual(self.emu.pc, 0x204)

        # V[1] = A. I should be set to sprites base address + 5 * A.
        self.emu.registers[1] = 0xA
        self.emu.current_opcode = 0xF129
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.I, self.emu.sprites_base_addr + 0x5 * 0xA)
        self.assertEqual(self.emu.pc, 0x206)

    def test_FX33(self):
        # V[1] = 0x25 (37). I should equal 0, I + 1 should equal 3 and I + 2 should equal 7.
        self.emu.registers[1] = 0x25
        self.emu.current_opcode = 0xF133
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.memory[self.emu.I], 0x0)
        self.assertEqual(self.emu.memory[self.emu.I + 1], 0x3)
        self.assertEqual(self.emu.memory[self.emu.I + 2], 0x7)
        self.assertEqual(self.emu.pc, 0x202)

        # V[1] = 0x1A5 (421). I should equal 4, I + 1 should equal 2 and I + 2 should equal 1.
        self.emu.registers[1] = 0x1A5
        self.emu.current_opcode = 0xF133
        self.emu.run_current_instruction()
        self.assertEqual(self.emu.memory[self.emu.I], 0x4)
        self.assertEqual(self.emu.memory[self.emu.I + 1], 0x2)
        self.assertEqual(self.emu.memory[self.emu.I + 2], 0x1)
        self.assertEqual(self.emu.pc, 0x204)

    def test_FX55(self):
        # X = 0x5. I = 0x21C. Registers 0 through 5 should be be stored in memory starting at location 0x21C.
        register_values = [0xA, 0x3, 0xA1, 0x25, 0x4, 0x9A]
        self.emu.I = 0x21C
        for i in range(5):
            self.emu.registers[i] = register_values[i]
        self.emu.current_opcode = 0xF555
        self.emu.run_current_instruction()
        for i in range(5):
            self.assertEqual(self.emu.memory[self.emu.I + i], register_values[i])
        self.assertEqual(self.emu.pc, 0x202)

    def test_FX65(self):
        # X = 0x5. I = 0x21C. Memory content from 0x21C to 0x21C + 5 should be be stored in registers 0 through 5.
        memory_values = [0xA, 0x3, 0xA1, 0x25, 0x4, 0x9A]
        self.emu.I = 0x21C
        for i in range(5):
            self.emu.memory[self.emu.I + i] = memory_values[i]
        self.emu.current_opcode = 0xF565
        self.emu.run_current_instruction()
        for i in range(5):
            self.assertEqual(self.emu.registers[i], memory_values[i])
        self.assertEqual(self.emu.pc, 0x202)