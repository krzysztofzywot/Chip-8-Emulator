from emulator import Emulator
import sys

if len(sys.argv) == 2:
    is_debug_mode = sys.argv[2].capitalize()
    if is_debug_mode == "True":
        is_debug_mode = True
    elif is_debug_mode == "False":
        is_debug_mode = False
    else:
        sys.exit(1)
else:
    is_debug_mode = False

emu = Emulator("Pong.ch8", debug_mode=is_debug_mode)
emu.start()