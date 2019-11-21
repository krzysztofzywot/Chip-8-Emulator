import random
import pygame
import threading
import os
import numpy as np


class Emulator:

    keyboard_mapping = {
        0x1: pygame.K_1,
        0x2: pygame.K_2,
        0x3: pygame.K_3,
        0xC: pygame.K_4,
        0x4: pygame.K_q,
        0x5: pygame.K_w,
        0x6: pygame.K_e,
        0xD: pygame.K_r,
        0x7: pygame.K_a,
        0x8: pygame.K_s,
        0x9: pygame.K_d,
        0xE: pygame.K_f,
        0xA: pygame.K_z,
        0x0: pygame.K_x,
        0xB: pygame.K_c,
        0xF: pygame.K_v
    }

    standard_sprites = {
        0: [0xF0, 0x90, 0x90, 0x90, 0xF0],
        1: [0x20, 0x60, 0x20, 0x20, 0x70],
        2: [0xF0, 0x10, 0xF0, 0x80, 0xF0],
        3: [0xF0, 0x10, 0xF0, 0x10, 0xF0],
        4: [0x90, 0x90, 0xF0, 0x10, 0x10],
        5: [0xF0, 0x80, 0xF0, 0x10, 0xF0],
        6: [0xF0, 0x80, 0xF0, 0x90, 0xF0],
        7: [0xF0, 0x10, 0x20, 0x40, 0x40],
        8: [0xF0, 0x90, 0xF0, 0x90, 0xF0],
        9: [0xF0, 0x90, 0xF0, 0x10, 0xF0],
        0xA: [0xF0, 0x90, 0xF0, 0x90, 0x90],
        0xB: [0xE0, 0x90, 0xE0, 0x90, 0xE0],
        0xC: [0xF0, 0x80, 0x80, 0x80, 0xF0],
        0xD: [0xE0, 0x90, 0x90, 0x90, 0xE0],
        0xE: [0xF0, 0x80, 0xF0, 0x80, 0xF0],
        0xF: [0xF0, 0x80, 0xF0, 0x80, 0x80]
    }

    UNSIGNED_CHAR_SIZE = 256

    def __init__(self, fname, debug_mode):
        self.file = fname
        self.memory = [0] * 4096
        self.registers = [0] * 16
        self.stack = [0] * 16
        self.stack_pointer = 0
        self.pc = 512
        self.I = 0

        self.debug_mode = debug_mode

        self.opcode_to_function_mapping = None

        self.current_opcode = 0

        self.delay_timer = 0
        self.sound_timer = 0

        self.sound = None

        self.sprites_base_addr = 0

        self.main_window_size = (640, 320)
        self.main_window_debug_mode_size = (800, 320)
        self.main_window = None
        self.game_window_size = (64, 32)
        self.game_window = None
        self.game_window_scaled_size = self.main_window_size
        self.game_window_scaled = None
        self.info_bar_size = (160, self.main_window_size[1])
        self.info_bar_window = None

        self.pixels = None

        self.font = None
        self.font_name = "SourceCodePro-Black.ttf"
        self.sound_name = "beep-6.wav"

        self.run = False

    def start(self):
        """Start the emulator."""

        self.run = True
        self.map_opcodes_to_functions()
        self.load_standard_sprites()
        self.load_program_into_memory()
        self.setup_sound()
        if self.debug_mode:
            self.setup_display_debug_mode()
            self.create_thread_for_emulator_window()
            self.run_program_debug_mode()
        else:
            self.setup_display()
            self.create_thread_for_emulator_window()
            self.run_program()

    def map_opcodes_to_functions(self):
        self.opcode_to_function_mapping = {
            "00": self.instruction_00E0,
            "0E": self.instruction_00EE,
            "1": self.instruction_1nnn,
            "2": self.instruction_2nnn,
            "3": self.instruction_3xkk,
            "4": self.instruction_4xkk,
            "5": self.instruction_5xy0,
            "6": self.instruction_6xkk,
            "7": self.instruction_7xkk,
            "80": self.instruction_8xy0,
            "81": self.instruction_8xy1,
            "82": self.instruction_8xy2,
            "83": self.instruction_8xy3,
            "84": self.instruction_8xy4,
            "85": self.instruction_8xy5,
            "86": self.instruction_8xy6,
            "87": self.instruction_8xy7,
            "8E": self.instruction_8xyE,
            "9": self.instruction_9xy0,
            "A": self.instruction_Annn,
            "B": self.instruction_Bnnn,
            "C": self.instruction_Cxkk,
            "D": self.instruction_Dxyn,
            "EE": self.instruction_Ex9E,
            "E1": self.instruction_ExA1,
            "F07": self.instruction_Fx07,
            "F0A": self.instruction_Fx0A,
            "F15": self.instruction_Fx15,
            "F18": self.instruction_Fx18,
            "F1E": self.instruction_Fx1E,
            "F29": self.instruction_Fx29,
            "F33": self.instruction_Fx33,
            "F55": self.instruction_Fx55,
            "F65": self.instruction_Fx65,
        }

    def load_program_into_memory(self):
        """Loads the program into memory."""

        try:
            with open(self.file, "rb") as f:
                # Begin storing the program at location 512.
                mem_pointer = 512
                while True:
                    first_byte = f.read(1).hex()
                    if not first_byte:
                        break
                    second_byte = f.read(1).hex()

                    self.memory[mem_pointer] = int(first_byte, 16)
                    self.memory[mem_pointer + 1] = int(second_byte, 16)

                    mem_pointer += 2
        except:
            os._exit(1)

    def setup_display(self):
        """Initial display setup."""

        pygame.init()

        self.main_window = pygame.display.set_mode(self.main_window_size)
        self.game_window = pygame.Surface(self.game_window_size)
        self.game_window_scaled = pygame.Surface(self.game_window_scaled_size)
        pygame.transform.scale(self.game_window, self.game_window_scaled_size, self.game_window_scaled)
        self.pixels = np.full(shape=self.game_window_size, fill_value=0x0)

    def setup_display_debug_mode(self):
        """Initial display setup for debug mode."""

        pygame.init()

        self.font = pygame.font.Font(self.font_name, 12)

        self.main_window = pygame.display.set_mode(self.main_window_debug_mode_size)
        self.game_window = pygame.Surface(self.game_window_size)
        self.game_window_scaled = pygame.Surface(self.game_window_scaled_size)
        pygame.transform.scale(self.game_window, self.game_window_scaled_size, self.game_window_scaled)

        self.info_bar_window = pygame.Surface(self.info_bar_size)
        self.info_bar_window.fill(0x0f343b)

        self.pixels = np.full(shape=self.game_window_size, fill_value=0x0)
        self.display_info_panel()

    def setup_sound(self):
        """Sound setup."""

        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(self.sound_name)
        self.sound.set_volume(0.1)

    def create_thread_for_emulator_window(self):
        """Create and run a separate thread for emulator options (for example quitting, entering debugger mode etc)."""

        emulator_thread = threading.Thread(target=self.emulator_window)
        emulator_thread.start()

    def load_standard_sprites(self):
        """Load standard sprites into memory, starting from sprites_base_addr."""

        i = 0
        for sprite, binary_list in Emulator.standard_sprites.items():
            for row in binary_list:
                self.memory[self.sprites_base_addr + i] = row
                i += 1

    def emulator_window(self):
        """Keeps listening for events such as quitting etc."""

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    pygame.quit()
                    os._exit(0)

                if self.debug_mode:
                    if event.type == pygame.KEYDOWN:
                        # F1 = decode next opcode.
                        if event.key == pygame.K_F1:
                            self.run_program_debug_mode()

    def run_program(self):
        while self.run:
            if self.sound_timer > 0:
                self.play_sound()
            if self.delay_timer > 0:
                self.delay_screen()
            # Merge 2 bytes from memory to get the current opcode.
            self.current_opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
            self.run_current_instruction()

    def run_program_debug_mode(self):
        # Merge 2 bytes from memory to get the current opcode.
        self.current_opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        self.run_current_instruction()
        self.display_info_panel()

    def run_current_instruction(self):
        try:
            instruction_method = self.find_instruction_to_run()
            instruction_method()
        except:
            os._exit(1)

    def find_instruction_to_run(self):
        current_opcode_as_string = f"{self.current_opcode:04X}"

        first_hex_digit = current_opcode_as_string[0]
        instructions_with_two_unique_digits = ("0", "8", "E")
        if first_hex_digit in instructions_with_two_unique_digits:
            last_hex_digit = current_opcode_as_string[3]
            return self.opcode_to_function_mapping[first_hex_digit + last_hex_digit]
        elif first_hex_digit == "F":
            third_hex_digit = current_opcode_as_string[2]
            last_hex_digit = current_opcode_as_string[3]
            return self.opcode_to_function_mapping[first_hex_digit + third_hex_digit + last_hex_digit]
        else:
            return self.opcode_to_function_mapping[first_hex_digit]

    def instruction_00E0(self):
        """Clear the display."""

        self.pixels = np.full(shape=self.game_window_size, fill_value=0x0)
        self.update_display()
        self.pc += 2

    def instruction_00EE(self):
        """Return from a subroutine."""

        self.pc = self.stack[self.stack_pointer - 1]
        self.stack_pointer -= 1
        if self.stack_pointer < 0:
            self.stack_pointer = 0

    def instruction_1nnn(self):
        """Jump to location nnn."""

        nnn = self.current_opcode & 0xFFF
        self.pc = nnn

    def instruction_2nnn(self):
        """Call subroutine at nnn."""

        self.pc += 2
        nnn = self.current_opcode & 0xFFF
        self.stack[self.stack_pointer] = self.pc
        self.stack_pointer += 1
        self.pc = nnn

    def instruction_3xkk(self):
        """Skip next instruction if Vx = kk."""

        vx = (self.current_opcode >> 8) & 0xF
        kk = self.current_opcode & 0xFF
        if self.registers[vx] == kk:
            self.pc += 4
        else:
            self.pc += 2

    def instruction_4xkk(self):
        """Skip next instruction if Vx != kk."""

        vx = (self.current_opcode >> 8) & 0xF
        kk = self.current_opcode & 0xFF
        if self.registers[vx] != kk:
            self.pc += 4
        else:
            self.pc += 2

    def instruction_5xy0(self):
        """Skip next instruction if Vx = Vy."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.pc += 2
        if self.registers[vx] == self.registers[vy]:
            self.pc += 2

    def instruction_6xkk(self):
        """Set Vx = kk."""

        vx = (self.current_opcode >> 8) & 0xF
        kk = self.current_opcode & 0xFF
        self.registers[vx] = kk
        self.pc += 2

    def instruction_7xkk(self):
        """Set Vx = Vx + kk."""

        vx = (self.current_opcode >> 8) & 0xF
        kk = self.current_opcode & 0xFF
        self.registers[vx] = (self.registers[vx] + kk) % Emulator.UNSIGNED_CHAR_SIZE
        self.pc += 2

    def instruction_8xy0(self):
        """Set Vx = Vy."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[vx] = self.registers[vy]
        self.pc += 2

    def instruction_8xy1(self):
        """Set Vx = Vx OR Vy."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[vx] = self.registers[vx] | self.registers[vy]
        self.pc += 2

    def instruction_8xy2(self):
        """Set Vx = Vx AND Vy."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[vx] = self.registers[vx] & self.registers[vy]
        self.pc += 2

    def instruction_8xy3(self):
        """Set Vx = Vx XOR Vy."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[vx] = self.registers[vx] ^ self.registers[vy]
        self.pc += 2

    def instruction_8xy4(self):
        """Set Vx = Vx + Vy, set VF = carry."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[0xF] = int(self.registers[vx] + self.registers[vy] >= Emulator.UNSIGNED_CHAR_SIZE)
        self.registers[vx] = (self.registers[vx] + self.registers[vy]) % Emulator.UNSIGNED_CHAR_SIZE
        self.pc += 2

    def instruction_8xy5(self):
        """Set Vx = Vx - Vy, set VF = NOT borrow."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[0xF] = int(self.registers[vx] > self.registers[vy])
        self.registers[vx] = (self.registers[vx] - self.registers[vy]) % 256
        self.pc += 2

    def instruction_8xy6(self):
        """Set Vx = Vx SHR 1."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[0xF] = self.registers[vx] & 0x1
        self.registers[vx] = self.registers[vx] >> 0x1
        self.pc += 2

    def instruction_8xy7(self):
        """Set Vx = Vy - Vx, set VF = NOT borrow."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[0xF] = int(self.registers[vy] > self.registers[vx])
        self.registers[vx] = (self.registers[vy] - self.registers[vx]) % Emulator.UNSIGNED_CHAR_SIZE
        self.pc += 2

    def instruction_8xyE(self):
        """Set Vx = Vx SHL 1."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        self.registers[0xF] = (self.registers[vx] >> 7) & 0x1
        self.registers[vx] = (self.registers[vx] << 1) % Emulator.UNSIGNED_CHAR_SIZE
        self.pc += 2

    def instruction_9xy0(self):
        """Skip next instruction if Vx != Vy."""

        vx = (self.current_opcode >> 8) & 0xF
        vy = (self.current_opcode >> 4) & 0xF
        if self.registers[vx] != self.registers[vy]:
            self.pc += 4
        else:
            self.pc += 2

    def instruction_Annn(self):
        """The value of register I is set to nnn."""

        nnn = self.current_opcode & 0xFFF
        self.I = nnn
        self.pc += 2

    def instruction_Bnnn(self):
        """Jump to location nnn + V0."""

        nnn = self.current_opcode & 0xFFF
        self.pc = nnn + self.registers[0x0]

    def instruction_Cxkk(self):
        """Set Vx = random byte AND kk."""

        random_max_range = 255

        vx = (self.current_opcode >> 8) & 0xF
        kk = self.current_opcode & 0xFF
        rand_num = random.randrange(random_max_range)
        self.registers[vx] = rand_num & kk
        self.pc += 2

    def instruction_Dxyn(self):
        """Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision."""

        num_of_bytes = self.current_opcode & 0xF
        x_coord = self.registers[(self.current_opcode >> 8) & 0xF]
        y_coord = self.registers[(self.current_opcode >> 4) & 0xF]

        self.registers[0xF] = 0

        for i in range(num_of_bytes):
            # Get the 8 pixels and XOR them with the pixels that are already on the screen.
            # If the sprite is positioned so part of it is outside the coordinates of the display,
            # it wraps around to the opposite side of the screen.
            row = f"{self.memory[self.I + i]:08b}"

            for j in range(8):
                curr_pixel = 1 if self.pixels[(x_coord + j) % 64][(y_coord + i) % 32] == 0xFFFFFF else 0x0
                # If a pixel is unset, set the F register's flag to 1.
                if curr_pixel ^ int(row[j]) == 1:
                    self.registers[0xF] = 1

                new_pixel = curr_pixel ^ int(row[j])
                self.pixels[(x_coord + j) % 64][(y_coord + i) % 32] = 0xFFFFFF if new_pixel == 1 else 0x0

        self.update_display()
        self.pc += 2

    def instruction_Ex9E(self):
        """Skip next instruction if key with the value of Vx is pressed."""

        vx = (self.current_opcode >> 8) & 0xF
        key = Emulator.keyboard_mapping[self.registers[vx]]
        all_keys = pygame.key.get_pressed()

        self.pc += 2
        # If a key is pressed, it is represented in all_keys as True. If it's not pressed, it is False.
        if all_keys[key]:
            self.pc += 2

    def instruction_ExA1(self):
        """Skip next instruction if key with the value of Vx is not pressed."""

        vx = (self.current_opcode >> 8) & 0xF
        key = Emulator.keyboard_mapping[self.registers[vx]]
        all_keys = pygame.key.get_pressed()

        self.pc += 2
        # If a key is pressed, it is represented in all_keys as True. If it's not pressed, it is False.
        if not all_keys[key]:
            self.pc += 2

    def instruction_Fx07(self):
        """Set Vx = delay timer value."""

        vx = (self.current_opcode >> 8) & 0xF
        self.registers[vx] = self.delay_timer
        self.pc += 2

    def instruction_Fx0A(self):
        """Wait for a key press, store the value of the key in Vx."""

        vx = (self.current_opcode >> 8) & 0xF
        pressed_key = self.find_pressed_key()
        # Get the key number associated with the pressed key.
        for key, value in Emulator.keyboard_mapping.items():
            if value == pressed_key:
                key_number = key
                self.registers[vx] = key_number
                break

        self.pc += 2

    def find_pressed_key(self):
        pressed_key = None
        while True:
            # Search through all the keys dict and if any key is pressed and it is in Chip-8's keyboard,
            # set it to pressed_key.
            all_keys = pygame.key.get_pressed()
            if any(all_keys):
                for key, value in all_keys.items():
                    if value is True and key in Emulator.keyboard_mapping.values():
                        pressed_key = key
                        break
            if pressed_key:
                return pressed_key

    def instruction_Fx15(self):
        """Set delay timer = Vx."""

        vx = (self.current_opcode >> 8) & 0xF
        self.delay_timer = self.registers[vx]
        self.pc += 2

    def instruction_Fx18(self):
        """Set sound timer = Vx."""

        vx = (self.current_opcode >> 8) & 0xF
        self.sound_timer = self.registers[vx]
        self.pc += 2

    def instruction_Fx1E(self):
        """Set I = I + Vx."""

        vx = (self.current_opcode >> 8) & 0xF
        self.I += self.registers[vx]
        self.pc += 2

    def instruction_Fx29(self):
        """Set I = location of sprite for digit Vx."""

        vx = (self.current_opcode >> 8) & 0xF
        self.I = self.sprites_base_addr + 5 * self.registers[vx]
        self.pc += 2

    def instruction_Fx33(self):
        """Store BCD representation of Vx in memory locations I, I+1, and I+2."""

        vx = (self.current_opcode >> 8) & 0xF
        self.memory[self.I] = (self.registers[vx] // 100) % 10
        self.memory[self.I + 1] = (self.registers[vx] // 10) % 10
        self.memory[self.I + 2] = self.registers[vx] % 10
        self.pc += 2

    def instruction_Fx55(self):
        """Store registers V0 through Vx in memory starting at location I."""

        vx = (self.current_opcode >> 8) & 0xF
        for i in range(vx + 1):
            self.memory[self.I + i] = self.registers[i]
        self.pc += 2

    def instruction_Fx65(self):
        """Read registers V0 through Vx from memory starting at location I."""

        vx = (self.current_opcode >> 8) & 0xF
        for i in range(vx + 1):
            self.registers[i] = self.memory[self.I + i]
        self.pc += 2

    def update_display(self):
        """Refreshes the display."""

        pygame.surfarray.blit_array(self.game_window, self.pixels)
        pygame.transform.scale(self.game_window, self.game_window_scaled_size, self.game_window_scaled)

        self.main_window.blit(self.game_window_scaled, (0, 0))
        if self.debug_mode:
            self.main_window.blit(self.info_bar_window, (640, 0))
        pygame.display.update()

    def display_info_panel(self):
        self.info_bar_window.fill(0x0f343b)

        white_color = (255, 255, 255)
        v_x = 15
        v_y = 5
        registers_title_text = self.font.render("Registers", True, white_color), (v_x, v_y)
        self.info_bar_window.blit(registers_title_text)

        stack_x = 100
        stack_y = 5
        stack_title_text = self.font.render("Stack", True, white_color), (stack_x, stack_y)
        self.info_bar_window.blit(stack_title_text)

        for i in range(16):
            y_offset = 20 + 15 * i
            register_value_text = self.font.render(f"{i:X}: {hex(self.registers[i])}", True, white_color), (v_x, y_offset)
            self.info_bar_window.blit(register_value_text)

            stack_value_text = self.font.render(f"{i:X}: {hex(self.stack[i])}", True, white_color), (stack_x, y_offset)
            self.info_bar_window.blit(stack_value_text)

        extras_x = 15
        extras_y = 270
        I_value_text = self.font.render(f"I:  {hex(self.I)}", True, white_color), (extras_x, extras_y)
        sp_value_text = self.font.render(f"SP: {hex(self.stack_pointer)}", True, white_color), (extras_x, extras_y + 15)
        pc_value_text = self.font.render(f"PC: {hex(self.pc)}", True, white_color), (extras_x, extras_y + 30)
        self.info_bar_window.blit(I_value_text)
        self.info_bar_window.blit(sp_value_text)
        self.info_bar_window.blit(pc_value_text)

        opcode_x = 100
        opcode_y = 270
        current_opcode_text = self.font.render("Opcode", True, white_color), (opcode_x, opcode_y)
        current_opcode_value_text = self.font.render(f"{self.current_opcode:04X}", True, white_color), (opcode_x, opcode_y + 15)
        self.info_bar_window.blit(current_opcode_text)
        self.info_bar_window.blit(current_opcode_value_text)

        self.update_display()

    def delay_screen(self):
        while self.delay_timer > 0:
            self.delay_timer -= 1
            pygame.time.delay(17)

    def play_sound(self):
        while self.sound_timer > 0:
            self.sound_timer -= 1
            self.sound.play()
            pygame.time.delay(17)