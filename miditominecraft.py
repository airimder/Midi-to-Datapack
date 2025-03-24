import pretty_midi
from PIL import Image, ImageDraw
import math
import sys

# ========== Constants ==========
PIXELS_PER_NOTE = 1
LOWEST_NOTE = 42
HIGHEST_NOTE = 78
NOTE_RANGE = HIGHEST_NOTE - LOWEST_NOTE + 1
BACKGROUND_COLOR = (255, 255, 255)
REPEATER_MAX_DELAY = 4
SPAN = 64
SNAKE_JUMP_LENGTH = 7

COLOR_MAP = {
    0:  (173, 216, 230),  # C
    1:  (0, 0, 139),      # C#
    2:  (75, 0, 130),     # D
    3:  (128, 0, 128),    # D#
    4:  (255, 0, 255),    # E
    5:  (255, 192, 203),  # F
    6:  (255, 0, 0),      # F#
    7:  (255, 165, 0),    # G
    8:  (255, 255, 0),    # G#
    9:  (0, 255, 0),      # A
    10: (0, 128, 0),      # A#
    11: (0, 255, 255),    # B
}

WOOL_COLORS = [
    "light_blue_wool", "blue_wool", "blue_terracotta", "purple_wool", "magenta_wool",
    "pink_wool", "red_wool", "orange_wool", "yellow_wool", "lime_wool", "green_wool", "cyan_wool"
]

# ========== Argument Parsing ==========
MIDI_FILES = sys.argv[1:-3]
filename = sys.argv[-3]
note_unit = float(sys.argv[-2]) / 16
voice_height = int(sys.argv[-1])

OUTPUT_IMAGE = f"{filename}.png"
OUTPUT_MCFUNC = f"{filename}.mcfunction"

# ========== Parse MIDI ==========
all_voices = []
max_beat_time = 0

for midi_path in MIDI_FILES:
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    tempo = midi_data.get_tempo_changes()[1][0]
    seconds_per_beat = 60.0 / tempo

    for instrument in midi_data.instruments:
        notes = [
            (note.pitch, note.start / seconds_per_beat, note.end / seconds_per_beat)
            for note in instrument.notes
            if LOWEST_NOTE <= note.pitch <= HIGHEST_NOTE
        ]
        if notes:
            max_beat_time = max(max_beat_time, max(end for _, _, end in notes))
            all_voices.append(notes)

# ========== Generate Image ==========
image_width = math.ceil(max_beat_time / note_unit)
image = Image.new('RGB', (image_width, NOTE_RANGE), BACKGROUND_COLOR)
draw = ImageDraw.Draw(image)

for voice in all_voices:
    for pitch, start, end in voice:
        x0 = int(start / note_unit)
        x1 = int(end / note_unit)
        y = HIGHEST_NOTE - pitch
        color = COLOR_MAP[pitch % 12]
        draw.rectangle([x0, y, x1 - 1, y], fill=color)

image.save(OUTPUT_IMAGE)
print(f"Image saved as {OUTPUT_IMAGE}")

# ========== Generate .mcfunction ==========
mcfunction_lines = []

for voice_idx, notes in enumerate(all_voices):
    y = 3 + voice_idx * voice_height
    x_pos = 1
    z_pos = 0
    direction = 1
    flip = False
    pending_snake = False
    stuck_oob = False
    last_latch_z = -1
    first_note = True
    last_tick = 0

    for pitch, start, end in notes:
        start_tick = int(start / note_unit)
        end_tick = int(end / note_unit)

        # Fill gap before note
        gap_ticks = max(0, (start_tick - last_tick) // 2)
        while gap_ticks > 0:
            delay = min(REPEATER_MAX_DELAY, gap_ticks)
            mcfunction_lines += [
                f"setblock ~{x_pos} ~{y - 1} ~{z_pos} stone",
                f"setblock ~{x_pos} ~{y} ~{z_pos} repeater[facing={'west' if direction == 1 else 'east'},delay={delay}]"
            ]
            if last_latch_z != -1:
                mcfunction_lines += [
                    f"setblock ~{x_pos} ~{y - 1} ~{last_latch_z} stone",
                    f"setblock ~{x_pos} ~{y} ~{last_latch_z} redstone_wire"
                ]
            x_pos += direction
            gap_ticks -= delay

        ticks = max(1, int((end - start) / note_unit / 2))

        if not first_note and not pending_snake and not stuck_oob and (x_pos >= SPAN or x_pos <= 0):
            pending_snake = True
            stuck_oob = True
            direction *= -1

        if pending_snake:
            for dz in range(SNAKE_JUMP_LENGTH):
                dz_offset = dz - 1
                mcfunction_lines += [
                    f"setblock ~{x_pos} ~{y - 1} ~{z_pos + dz_offset} stone",
                    f"setblock ~{x_pos} ~{y} ~{z_pos + dz_offset} redstone_wire"
                ]
            x_pos += direction
            z_pos += 5
            pending_snake = False

        if not (x_pos >= SPAN or x_pos <= 0):
            stuck_oob = False

        # Latch and wire positions
        latch_z = z_pos - 1 if not flip else z_pos + 1
        wire_z = z_pos + 1 if not flip else z_pos - 1
        latch_facing = "south" if not flip else "north"

        # Redstone line start
        mcfunction_lines += [
            f"setblock ~{x_pos} ~{y - 1} ~{z_pos} stone",
            f"setblock ~{x_pos} ~{y} ~{z_pos} redstone_wire",
            f"setblock ~{x_pos} ~{y - 1} ~{latch_z} stone",
            f"setblock ~{x_pos} ~{y} ~{latch_z} create:powered_latch[facing={latch_facing}]"
        ]

        # Frequency blocks
        if pitch < 54:
            octave_block = "minecraft:copper_block"
        elif pitch < 66:
            octave_block = "minecraft:gold_block"
        else:
            octave_block = "minecraft:iron_block"

        note_color = "minecraft:" + (
            "white_wool" if pitch == 78 else WOOL_COLORS[pitch % 12]
        )

        link_z = z_pos - 2 if not flip else z_pos + 2
        mcfunction_lines += [
            f"setblock ~{x_pos} ~{y - 1} ~{link_z} stone",
            f"setblock ~{x_pos} ~{y} ~{link_z} create:redstone_link[facing=up]{{"
            f'FrequencyFirst:{{id:"{octave_block}",Count:1b}},'
            f'FrequencyLast:{{id:"{note_color}",Count:1b}},Transmitting:1b}}',
            f"setblock ~{x_pos} ~{y - 1} ~{wire_z} stone",
            f"setblock ~{x_pos} ~{y} ~{wire_z} redstone_wire"
        ]

        last_latch_z = latch_z
        flip = not flip
        x_pos += direction

        # Place repeaters
        while ticks > 0:
            delay = min(REPEATER_MAX_DELAY, ticks)
            mcfunction_lines += [
                f"setblock ~{x_pos} ~{y - 1} ~{z_pos} stone",
                f"setblock ~{x_pos} ~{y} ~{z_pos} repeater[facing={'west' if direction == 1 else 'east'},delay={delay}]",
                f"setblock ~{x_pos} ~{y - 1} ~{last_latch_z} stone",
                f"setblock ~{x_pos} ~{y} ~{last_latch_z} redstone_wire"
            ]
            x_pos += direction
            ticks -= delay

        first_note = False
        last_tick = end_tick

    # Final signal cleanup
    wire_z = z_pos + 1 if not flip else z_pos - 1
    latch_z = z_pos - 1 if not flip else z_pos + 1
    mcfunction_lines += [
        f"setblock ~{x_pos} ~{y - 1} ~{z_pos} stone",
        f"setblock ~{x_pos} ~{y} ~{z_pos} redstone_wire",
        f"setblock ~{x_pos} ~{y - 1} ~{wire_z} stone",
        f"setblock ~{x_pos} ~{y} ~{wire_z} redstone_wire",
        f"setblock ~{x_pos} ~{y - 1} ~{latch_z} stone",
        f"setblock ~{x_pos} ~{y} ~{latch_z} redstone_wire"
    ]

# Write the function file
with open(OUTPUT_MCFUNC, "w") as f:
    f.write("\n".join(mcfunction_lines))

print(f"Redstone structure saved as {OUTPUT_MCFUNC}")
