# script to run gui 


import sys
import os
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Configure Experiment")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

run_options = ["Base Data", "Full Spectra", "Full Thermal Capture", "Oscilloscope Data", "Embedded Data"]
ttk.Label(mainframe, text="Select Options for the Run Configuration:")

collect_base_data = tk.StringVar()
check1 = ttk.Checkbutton(mainframe, text=run_options[0], variable=collect_base_data, onvalue=True, offvalue=False)
collect_full_spectra = tk.StringVar()
collect_full_thermal = tk.StringVar()
collect_oscilloscope = tk.StringVar()

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.mainloop()
