# Midi to Datapack
 A Python script converting from a .midi file to a format usable in Minecraft: Create Mod to create in-game tracks for pipe organs.

Run the script from the terminal with the arguments: (string) MIDI file path, (string) output nickname, (int) the number of 16th notes one repeater tick should represent, and (int) the number of blocks apart each layer should be. 

Each y-layer in the generated .mcfunction represents one voice. It is recommended to space each layer 3 blocks apart so you have room to move between them for any maintainence or troubleshooting.

In order to use the generated creation, you need to build a Create pipe organ with at least 37 pipes, from F# 2 to F# 5, although it was designed for my Create organ which includes a Nazard (1 octave and a perfect fifth higher than the 8') and a Tierce stop (1 octave and a major third higher than the 8'), for more decorated registrations similar to real-world organs. 

Attach a Redstone Link set to the Receiver mode with the wrench to each pipe. Set the note in the Freq. 2 slot as follows:
            "red_wool",          # F#
            "orange_wool",       # G
            "yellow_wool",       # G#
            "lime_wool",         # A
            "green_wool",        # A#
            "cyan_wool"          # B
            "light_blue_wool",   # C
            "blue_wool",         # C#
            "blue_terracotta",   # D (indigo)
            "purple_wool",       # D#
            "magenta_wool",      # E
            "pink_wool",         # F
Set Freq. 1 according to the "stop", or in this case, rank. 
            narrow diameter: iron_block
            standard diameter: gold_block
            maximal diameter: copper_block
            tierce: emerald_block
            nazard: amethyst_block

While this is a handy tool which will save a considerable amount of time in converting MIDIs into blocks, it is not perfect. The tool is designed to do the majority of the work, but fine-tuning by an organist in-game is usually necessary due to the complexity of the task. The most common error is that notes held for too long will sometimes fail to stop due to their redstone signal not reaching the latch. The solution to this is usually to either shorten the note or to boost the signal with more repeaters, but both have tradeoffs and cannot be automated because the decision is situational to the specific piece being arranged.
