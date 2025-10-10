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

def midi_callback(event, data=None):
    midi_queue.put(event) 

ports_dict = {k[:-2]: v for (v,k) in enumerate(midi_in.get_ports())}
sleep_time = 10 # CONST float sleep_time = 10:

# start at 36, end at 96
piano = ['1','1','2','2','3','4','4','5','5','6','6','7',
         '8','8','9','9','0','q','q','w','w','e','e','r',
         't','t','y','y','u','i','i','o','o','p','p','a',
         's','s','d','d','f','g','g','h','h','j','j','k',
         'l','l','z','z','x','c','c','v','v','b','b','n',
         'm'] 
natural_mask = [1,0,1,0,1,1,0,1,0,1,0,1]
extra_octave = True

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
        message, deltatime = midi_queue.get()
        status = message[0]
        note = message[1]
        velocity = message[2] if len(message) > 2 else 0

        # Octave shift
        if octave_var.get():
            if note > 95:
                note -= 12
            elif note < 36:
                note += 12

        # Mode handling
        if mode_var.get() == "keydown":
            if status & 0xF0 == 0x90 and velocity > 0:
                log_text.insert(tk.END, f"Note ON {note}\n")
                # TODO: send keyboard event here

        else:
            if status & 0xF0 == 0x90 and velocity > 0:
                log_text.insert(tk.END, f"Note ON {note}\n")
            elif status & 0xF0 == 0x80 or (status & 0xF0 == 0x90 and velocity == 0):
                log_text.insert(tk.END, f"Note OFF {note}\n")
            # TODO: send keyboard event here

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

octave_var = tk.BooleanVar(value=False)
ttk.Checkbutton(mainframe, text="Octave Shift", variable=octave_var, command=toggle_octave).grid(row=1, column=0, sticky="w")

mode_var = tk.StringVar(value="keydown")
ttk.Radiobutton(mainframe, text="KeyDown only", variable=mode_var, value="keydown", command=toggle_mode).grid(row=1, column=1, sticky="w")
ttk.Radiobutton(mainframe, text="KeyDown + KeyUp", variable=mode_var, value="both", command=toggle_mode).grid(row=1, column=2, sticky="w")

log_text = tk.Text(mainframe, width=60, height=15)
log_text.grid(row=2, column=0, columnspan=3, pady=10)

# Start polling the queue
root.after(sleep_time, process_midi_queue)

root.mainloop()

root.protocol("WM_DELETE_WINDOW", on_close)


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

