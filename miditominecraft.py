import pretty_midi
from PIL import Image, ImageDraw
import math
import sys

MIDI_FILES = sys.argv[1:-3]  # takes up to 4 voice midi files (haven't tested with more)
yheight = int(sys.argv[-1])
noteUnit = sys.argv[-2]
filename = sys.argv[-3]
OUTPUT_IMAGE = f"{filename}.png"

PIXELS_PER_NOTE = 1
NOTE_UNIT = int(noteUnit) / 16  
LOWEST_NOTE = 42 # F#2 (the big fat pipe stacked all the way up)
HIGHEST_NOTE = 78   # F#5 (skinny pipe at 1)
NOTE_RANGE = 37
BACKGROUND_COLOR = (255, 255, 255)

COLOR_MAP = {
    0:  (173, 216, 230),  # C - light blue
    1:  (0, 0, 139),      # C# - dark blue
    2:  (75, 0, 130),     # D - indigo
    3:  (128, 0, 128),    # D# - purple
    4:  (255, 0, 255),    # E - magenta
    5:  (255, 192, 203),  # F - pink
    6:  (255, 0, 0),      # F# - red
    7:  (255, 165, 0),    # G - orange
    8:  (255, 255, 0),    # G# - yellow
    9:  (0, 255, 0),      # A - lime
    10: (0, 128, 0),      # A# - green
    11: (0, 255, 255),    # B - cyan
}

all_voices = []
max_time = 0

for midi_path in MIDI_FILES:
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    tempo = midi_data.get_tempo_changes()[1][0]
    spb = 60.0 / tempo

    for instrument in midi_data.instruments:
        voice_notes = []
        for note in instrument.notes:
            if LOWEST_NOTE <= note.pitch <= HIGHEST_NOTE:
                start_beat = note.start / spb
                end_beat = note.end / spb
                max_time = max(max_time, end_beat)
                voice_notes.append((note.pitch, start_beat, end_beat))
        if voice_notes:
            all_voices.append(voice_notes)

total_beats = max_time
image_width = math.ceil(total_beats / NOTE_UNIT)
image = Image.new('RGB', (image_width, NOTE_RANGE), BACKGROUND_COLOR)
draw = ImageDraw.Draw(image)

for notes in all_voices:
    for pitch, start_beat, end_beat in notes:
        x0 = int(start_beat / NOTE_UNIT)
        x1 = int(end_beat / NOTE_UNIT)
        y = HIGHEST_NOTE - pitch
        color = COLOR_MAP[pitch % 12]
        draw.rectangle([x0, (y), (x1 - 1), (y)], fill=color)

image.save(OUTPUT_IMAGE)
    
print(f"whatever the fuck you've created has been spit out at {OUTPUT_IMAGE}")

mcfunction_lines = []


for voice_index, voice_notes in enumerate(all_voices):
    # Voice-local state
    y = 3 + voice_index * int(sys.argv[-1])  # vertical stacking

    xtrue = 1
    ztrue = 0
    flip_flop = False
    last_latch_z = -1
    SPAN = 64
    direction = 1
    snake_pending = False
    first_note = True
    stuck_oob = False
    last_end_tick = 0

    for pitch, start_beat, end_beat in voice_notes:
        x0 = int(start_beat / NOTE_UNIT)
        x1 = int(end_beat / NOTE_UNIT)

        # Fill silence before this note, if needed
        gap_ticks = max(0, int((x0 - last_end_tick) / 2))
        while gap_ticks > 0:
            delay = min(4, gap_ticks)

            mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{ztrue} stone")
            mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{ztrue} repeater[facing={'west' if direction == 1 else 'east'},delay={delay}]")

            if last_latch_z is not None:
                mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{last_latch_z} stone")
                mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{last_latch_z} redstone_wire")

            xtrue += direction
            gap_ticks -= delay

        note_duration_beats = end_beat - start_beat
        total_ticks = max(1, int((note_duration_beats / NOTE_UNIT) / 2))
        
        # Only snake when truly at the end of a row, and not right after a jump
        if not first_note and not snake_pending and not stuck_oob and (xtrue >= SPAN or xtrue <= 0):        
            snake_pending = True
            stuck_oob = True  # Prevent re-triggering out of bounds
            direction *= -1  # Flip X direction

        if snake_pending:
            # Build a jump bridge at current xtrue
            for dz in range(7):
                mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{ztrue + dz - 1} stone")
                mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{ztrue + dz - 1} redstone_wire")
            xtrue += direction
            ztrue += 5
            snake_pending = False

        # AFTER jump is resolved, safely update Z reference
        z = ztrue

        if not (xtrue >= SPAN or xtrue <= 0):
            stuck_oob = False

        # Determine latch/wire direction
        latch_z = ztrue-1 if not flip_flop else ztrue + 1
        latch_facing = "south" if not flip_flop else "north"
        wire_z = ztrue+1 if not flip_flop else ztrue - 1  # opposite side

        # Redstone wire to start the line
        mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{z} stone")
        mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{z} redstone_wire")

        # Latch + side wire + stones
        mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{latch_z} stone")
        mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{latch_z} create:powered_latch[facing={latch_facing}]")

        # Determine frequency block based on octave
        if pitch < 54:
            octave_block = "minecraft:copper_block"
        elif pitch < 66:
            octave_block = "minecraft:gold_block"
        else:
            octave_block = "minecraft:iron_block"

        # Determine pitch color block for Frequency 2
        wool_color_map = [
            "light_blue_wool",   # C
            "blue_wool",         # C#
            "blue_terracotta",   # D (indigo)
            "purple_wool",       # D#
            "magenta_wool",      # E
            "pink_wool",         # F
            "red_wool",          # F#
            "orange_wool",       # G
            "yellow_wool",       # G#
            "lime_wool",         # A
            "green_wool",        # A#
            "cyan_wool"          # B
        ]
        note_color_block = f"minecraft:{wool_color_map[pitch % 12]}"
        if pitch == 78:
            note_color_block = "minecraft:white_wool"

        # Place the Redstone Link two blocks offset from the redstone line (aligned with latch_z)
        link_z = ztrue-2 if not flip_flop else ztrue + 2
        mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{link_z} stone")
        mcfunction_lines.append(
            f"setblock ~{xtrue} ~{y} ~{link_z} create:redstone_link[facing=up]{{"
            f'FrequencyFirst:{{id:"{octave_block}",Count:1b}},'
            f'FrequencyLast:{{id:"{note_color_block}",Count:1b}},'
            f"Transmitting:1b}}"
        )

        mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{wire_z} stone")
        mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{wire_z} redstone_wire")

        # Track latch position for repeater-side wires
        last_latch_z = latch_z
        flip_flop = not flip_flop
        xtrue += direction

        # Start placing repeaters
        remaining_ticks = total_ticks
        while remaining_ticks > 0:
            delay = min(4, remaining_ticks)

            # Repeater and supporting stone
            mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{z} stone")
            mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{z} repeater[facing={'west' if direction == 1 else 'east'},delay={delay}]")

            # Side wire aligned with last latch, and its stone base
            mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{last_latch_z} stone")
            mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{last_latch_z} redstone_wire")

            xtrue += direction
            remaining_ticks -= delay
        first_note = False
        last_end_tick = x1

    # Determine latch/wire direction
    latch_z = ztrue-1 if not flip_flop else ztrue + 1
    latch_facing = "south" if not flip_flop else "north"
    wire_z = ztrue+1 if not flip_flop else ztrue - 1  # opposite side

    # Redstone wire to start the line
    mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{z} stone")
    mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{z} redstone_wire")

    mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{wire_z} stone")
    mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{wire_z} redstone_wire")

    # Track latch position for repeater-side wires
    last_latch_z = latch_z
    flip_flop = not flip_flop
    xtrue += direction

    # Side wire aligned with last latch, and its stone base
    mcfunction_lines.append(f"setblock ~{xtrue} ~{y - 1} ~{last_latch_z} stone")
    mcfunction_lines.append(f"setblock ~{xtrue} ~{y} ~{last_latch_z} redstone_wire")

with open(f"{filename}.mcfunction", "w") as f:
    f.write("\n".join(mcfunction_lines))

print(f"Redstone structure exported as {filename}.mcfunction")