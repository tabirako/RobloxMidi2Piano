import rtmidi

import tkinter as tk
from tkinter import ttk

import time
import keyboard


midi_in = rtmidi.MidiIn()
ports = midi_in.get_ports()

print(ports)


ports_dict = {k[:-2]: v for (v,k) in enumerate(midi_in.get_ports())}

midi_in.open_port(0)

print(midi_in.is_port_open())


watchdog = time.time()
watchdog_time = 15*60 # second

# start at 36, end at 96
piano = ['1','1','2','2','3','4','4','5','5','6','6','7',
         '8','8','9','9','0','q','q','w','w','e','e','r',
         't','t','y','y','u','i','i','o','o','p','p','a',
         's','s','d','d','f','g','g','h','h','j','j','k',
         'l','l','z','z','x','c','c','v','v','b','b','n',
         'm'] 
natural_mask = [1,0,1,0,1,1,0,1,0,1,0,1]
extra_octave = 1

while True:
    msg_and_dt = midi_in.get_message()
    if msg_and_dt:
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
                  
        watchdog = time.time() # reset timer
    else:
        time.sleep(0.001)
        if time.time()-watchdog > watchdog_time:
            break
midi_in.close_port()


if midi_in.is_port_open():
    midi_in.close_port()