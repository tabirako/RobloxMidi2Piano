# --- Virtual Piano Setup (5 octaves) ---

import tkinter as tk
from tkinter import ttk 

root = tk.Tk()
root.title('test')

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(row=0, column=0, sticky="nsew")

piano_frame = ttk.Frame(mainframe)
piano_frame.grid(row=4, column=0, columnspan=3, pady=10)

note_buttons = {}

# White and black key layout
white_notes = [0, 2, 4, 5, 7, 9, 11]  # semitone offsets
black_notes = [1, 3, -1, 6, 8, 10, -1]  # -1 = no black key above

start_note = 48  # C3
num_keys = 61    # 5 octaves

white_index = 0
for midi_note in range(start_note, start_note + num_keys):
    semitone = midi_note % 12
    if semitone in white_notes:
        # White key
        btn = tk.Label(piano_frame, text="", width=3, height=8,
                       relief="raised", bg="white", bd=1)
        btn.grid(row=0, column=white_index, padx=1, pady=1, sticky="s")
        note_buttons[midi_note] = btn
        white_index += 1

# Add black keys (overlay)
white_index = 0
for midi_note in range(start_note, start_note + num_keys):
    semitone = midi_note % 12
    if semitone in white_notes:
        # Place black key if exists
        black_offset = black_notes[white_notes.index(semitone)]
        if black_offset != -1:
            black_note = midi_note + (black_offset - semitone)
            if start_note <= black_note < start_note + num_keys:
                btn = tk.Label(piano_frame, text="", width=2, height=5,
                               relief="raised", bg="black", fg="white", bd=1)
                btn.place(in_=piano_frame, relx=(white_index/52), rely=0, anchor="n")
                note_buttons[black_note] = btn
        white_index += 1

root.mainloop()
