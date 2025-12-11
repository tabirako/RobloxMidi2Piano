import rtmidi

import tkinter as tk
from tkinter import ttk

#import time
import keyboard
import queue

midi_in = rtmidi.MidiIn()
current_port = None
midi_queue = queue.Queue()

ports = midi_in.get_ports()

#print(ports)

ports_dict = {k[:-2]: v for (v,k) in enumerate(midi_in.get_ports())}
sleep_time = 10 # CONST float sleep_time = 10 # milliseconds

# start at 36, end at 96
piano = ['1','1','2','2','3','4','4','5','5','6','6','7',
         '8','8','9','9','0','q','q','w','w','e','e','r',
         't','t','y','y','u','i','i','o','o','p','p','a',
         's','s','d','d','f','g','g','h','h','j','j','k',
         'l','l','z','z','x','c','c','v','v','b','b','n',
         'm'] 
natural_mask = [1,0,1,0,1,1,0,1,0,1,0,1]

# --- MIDI callback (runs in background thread) ---
def midi_callback(event, data=None):
    midi_queue.put(event)  # push message into queue

# --- MIDI garbage collection (runs after the windows is closed) --- 
def on_close():
    global current_port
    if current_port is not None:
        midi_in.close_port()
        print("MIDI port closed cleanly")
    root.destroy()

# --- Process MIDI messages in main thread ---
def process_midi_queue():
    while not midi_queue.empty():
        message, deltatime = midi_queue.get() # deltatime is a throwaway variable here
        status = message[0]
        note = message[1] # actual note being played
        velocity = message[2] if len(message) > 2 else 0

        converted_note = note # for playing on virtual piano and gui update since we only have 5 octaves

        ## example for Octave shift
        """
        if octave_var.get():
            if note > 95:
                note = note%12 + 84
            elif note < 36:
                note = note%12 + 36
        """
        ## end example for Octave shift

        if status & 0xF0 == 0x90 and velocity > 0:
            # Code 0x9_ : Note On _ = channel number, 16 channels, 0-f
            log_text.insert(tk.END, f"Note ON {note}\n")

            if octave_var.get() == True:
                if note > 95:
                    converted_note = note%12 + 84
                elif note < 36:
                    converted_note = note%12 + 36

            if converted_note<36 or converted_note>96:
                log_text.see(tk.END)
                continue

            note_buttons[converted_note].config(bg="red")

            # TODO: send keyboard event here
            if natural_mask[note%12]: # white keys
                keyboard.press(piano[converted_note-36])
            else: # black keys
                keyboard.press("shift")
                keyboard.press(piano[converted_note-36])
                keyboard.release("shift")
                    
            if mode_var.get() == "keydown": # keydown only
                keyboard.release(piano[converted_note-36]) 

        if status & 0xF0 == 0x80 or (status & 0xF0 == 0x90 and velocity == 0):
            # Code 0x8_ : Note Off _ = channel number, 16 channels, 0-f
            log_text.insert(tk.END, f"Note OFF {note}\n")

            if octave_var.get() == True:
                if note > 95:
                    converted_note = note%12 + 84
                elif note < 36:
                    converted_note = note%12 + 36

            if converted_note<36 or converted_note>96:
                log_text.see(tk.END)
                continue

            if natural_mask[converted_note%12]: # white keys
                note_buttons[converted_note].config(bg="white")
            else: # black keys
                note_buttons[converted_note].config(bg="black")

            if mode_var.get() == "both": # keydown and keyup
                 #TODO: send keyboard event here
                keyboard.release(piano[converted_note-36]) 

        log_text.see(tk.END)

    root.after(sleep_time, process_midi_queue)  # schedule next check


# --- GUI callbacks ---
def refresh_devices():
    devices = midi_in.get_ports()
    device_combo['values'] = devices
    if devices:
        device_combo.current(0)
    log_text.insert(tk.END, f"Found devices: {devices}\n")

def select_device(event=None):
    global current_port
    if current_port is not None:
        midi_in.close_port()
    idx = device_combo.current()
    if idx >= 0:
        midi_in.open_port(idx)
        midi_in.set_callback(midi_callback)
        current_port = idx
        log_text.insert(tk.END, f"Opened device: {device_combo.get()}\n")

def stop_device():
    global current_port
    if current_port is not None:
        midi_in.close_port()
        log_text.insert(tk.END, "Closed current MIDI port\n")
        current_port = None
    midi_in.close_port()

def toggle_octave():
    log_text.insert(tk.END, f"Octave shift {'ON' if octave_var.get() else 'OFF'}\n")

def toggle_mode():
    log_text.insert(tk.END, f"Mode: {mode_var.get()}\n")


# --- GUI setup ---

root = tk.Tk()
root.title("MIDI to Keyboard Mapper")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(row=0, column=0, sticky="nsew")

ttk.Button(mainframe, text="Refresh Devices", command=refresh_devices).grid(row=0, column=0, padx=5, pady=5)
device_combo = ttk.Combobox(mainframe, state="readonly")
device_combo.grid(row=0, column=1, padx=5, pady=5)
device_combo.bind("<<ComboboxSelected>>", select_device)
ttk.Button(mainframe, text="Stop", command=stop_device).grid(row=0, column=2, padx=5, pady=5)

octave_var = tk.BooleanVar(value=True)
ttk.Checkbutton(mainframe, text="Octave Shift", variable=octave_var, command=toggle_octave).grid(row=1, column=0, sticky="w")

mode_var = tk.StringVar(value="keydown")
ttk.Radiobutton(mainframe, text="KeyDown only", variable=mode_var, value="keydown", command=toggle_mode).grid(row=1, column=1, sticky="w")
ttk.Radiobutton(mainframe, text="KeyDown + KeyUp", variable=mode_var, value="both", command=toggle_mode).grid(row=1, column=2, sticky="w")

log_text = tk.Text(mainframe, width=60, height=15)
log_text.grid(row=2, column=0, columnspan=3, pady=10)

# --- Virtual Piano Setup (5 octaves) ---
piano_frame = ttk.Frame(mainframe)
piano_frame.grid(row=4, column=0, columnspan=3, pady=10)

note_buttons = {}

# White and black key layout
white_notes = [0, 2, 4, 5, 7, 9, 11]  # semitone offsets
black_notes = [1, 3, -1, 6, 8, 10, -1]  # -1 = no black key above

start_note = 36  # C2 is 36
num_keys = 61    # 5 octaves
white_positions = {}  # map midi_note -> column index
white_index = 0

# Draw white keys
for midi_note in range(start_note, start_note + num_keys):
    semitone = midi_note % 12
    if semitone in white_notes:
        btn = tk.Label(piano_frame, text="", width=3, height=8,
                       relief="groove", bg="white", bd=1)
        btn.grid(row=0, column=white_index, padx=0, pady=0, sticky="s")
        note_buttons[midi_note] = btn
        white_positions[midi_note] = white_index
        white_index += 1

# Draw black keys
for midi_note in range(start_note, start_note + num_keys):
    semitone = midi_note % 12
    if semitone in white_notes:
        black_offset = black_notes[white_notes.index(semitone)]
        if black_offset != -1:
            black_note = midi_note + (black_offset - semitone)
            if start_note <= black_note < start_note + num_keys:
                # Position black key between current white and next
                col = white_positions[midi_note]
                btn = tk.Label(piano_frame, text="", width=2, height=5,
                               relief="raised", bg="black", fg="white", bd=1)
                btn.place(in_=piano_frame, relx=(col + 1)/white_index, rely=0, anchor="n")
                note_buttons[black_note] = btn

# Start polling the queue
root.after(sleep_time, process_midi_queue)

root.protocol("WM_DELETE_WINDOW", on_close)

# Auto-refresh devices once on startup
refresh_devices()

root.mainloop()

print("end of the program")

while False:
    msg_and_dt = midi_in.get_message()

    #print(msg_and_dt)
    
    # taking only KEYDOWN
    if 0x90 <= msg_and_dt[0][0] and msg_and_dt[0][0]<=0x9F:
    # Code 0x9_ : Note On _ = channel number, 16 channels, 0-f
    
        # playable region
        if msg_and_dt[0][1] >= 24 and msg_and_dt[0][1]<=108:
            # print (msg_and_dt[0][1])
            # out of zone
            if extra_octave:
                if msg_and_dt[0][1] < 36:
                    msg_and_dt[0][1] += 12

                if msg_and_dt[0][1] > 96:
                    msg_and_dt[0][1] -= 12
            
            if natural_mask[msg_and_dt[0][1]%12]: # notes with no sharps
                keyboard.press(piano[msg_and_dt[0][1]-36])
            else: # notes with sharps
                keyboard.press("shift")
                keyboard.press(piano[msg_and_dt[0][1]-36])
                keyboard.release("shift")
                
    # taking only KEYUP
    if 0x80 <= msg_and_dt[0][0] and msg_and_dt[0][0]<=0x8F:
    # Code 0x8_ : Note On _ = channel number, 16 channels, 0-f
    
        # playable region
        if msg_and_dt[0][1] >= 24 and msg_and_dt[0][1]<=108:
            # print (msg_and_dt[0][1])
            # out of zone
            if extra_octave:
                if msg_and_dt[0][1] < 36:
                    msg_and_dt[0][1] += 12

                if msg_and_dt[0][1] > 96:
                    msg_and_dt[0][1] -= 12
            
            if natural_mask[msg_and_dt[0][1]%12]: # notes with no sharps
                keyboard.release(piano[msg_and_dt[0][1]-36])
            else: # notes with sharps
                keyboard.release(piano[msg_and_dt[0][1]-36])        
                


midi_in.close_port()

