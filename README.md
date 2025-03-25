# Midi to Datapack
 A Python script converting from a .midi file to a format usable in Minecraft: Create Mod to create in-game tracks for pipe organs.

Run the script from the terminal with the arguments: (string) MIDI file path, (string) output nickname, (int) the number of 16th notes one repeater tick should represent, and (int) the number of blocks apart each layer should be. 

Each layer represents one voice. 

In order to use the generated creation, you need to build a pipe organ with at least 37 pipes, from F# 2 to F# 5. 

Attach a Redstone Link set to the Receiver mode with the wrench. Set the note in the Freq. 2 slot as follows:
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
