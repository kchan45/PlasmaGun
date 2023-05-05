"""
Main script for running data aquisition with manually-given inputs

Written/Modified By: Kimberly Chan
(c) 2023 GREMI, University of Orleans
(c) 2023 Mesbah Lab, University of California, Berkeley
"""

import sys
sys.dont_write_bytecode = True
import numpy as np
from seabreeze.spectrometers import Spectrometer, list_devices
import time
import os
from datetime import datetime
import asyncio
import pandas as pd
from picosdk.ps2000a import ps2000a as ps
import ctypes
import matplotlib.pyplot as plt

## import user functions
from utils.oscilloscope import Oscilloscope
from utils.async_measure import async_measure

TEST = False          # for testing the code without any devices connected; the code will generate dummy data; mainly for development purposes
################################################################################
# USER OPTIONS (you may change these)
################################################################################
# variables that WILL change the function of the data collection
save_backup = True          # whether [True] or not [False] to save a compressed H5 backup file every 10 iterations
async_collection = True     # whether [True] or not [False] to collect data asynchronously, if this is True, then collect_osc and collect_spec will be automatically set to True regardless of the settings in the following two lines
collect_spec = True         # whether [True] or not [False] to collect data from the spectrometer
collect_osc = True          # whether [True] or not [False] to collect data from the oscilloscope
samplingTime = 0.5          # sampling time in seconds
# n_iterations = input("Number of iterations?:") # number of sampling iterations
n_iterations = 11


# variables that will NOT change the function of the data collection (for note-taking purposes)
DEFAULT_EMAIL = "kchan45@berkeley.edu"          # the default email address to send the data to
set_v = 85.0             # voltage in Volts
set_freq = 1000.0        # frequency in hertz
set_flow = 0.5          # flow rate in liters per minute
set_gap = 5.0           # distance reactor to target in mm
set_target = input("Target?:")
addl_notes = "chicken I"

plot_last_data = True       # whether [True] or not [False] to plot the data from the final iteration of the data collection

## OPTIONAL Configurations for the spectrometer - in case the settings for the spectrometer need to be customized
integration_time = 200000       # in microseconds

## OPTIONAL Configurations for the oscilloscope - in case the settings for the oscilloscope need to be customized
mode = 'block'  # use block mode to capture the data using a trigger; the other option is 'streaming'
# for block mode, you may wish to change the following:
pretrigger_size = 200      # size of the data buffer before the trigger, default is 2000, in units of samples
posttrigger_size = 800     # size of the data buffer after the trigger, default is 8000, in units of samples
# for streaming mode, you may wish to change the following:
single_buffer_size = 500    # size of a single buffer, default is 500
n_buffers = 10              # number of buffers to acquire, default is 10
timebase = 2              # timebase for the measurement resolution, 127 corresponds to 1us, default is 8

# see oscilloscope_test.py for more information on defining the channels
channelA = {"name": "A",
            "enable_status": 1,
            "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
            "range": ps.PS2000A_RANGE['PS2000A_10V'],
            "analog_offset": 0.0,
            }
channelB = {"name": "B",
            "enable_status": 1,
            "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
            "range": ps.PS2000A_RANGE['PS2000A_20V'],
            "analog_offset": 0.0,
            }
channelC = {"name": "C",
            "enable_status": 1,
            "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
            "range": ps.PS2000A_RANGE['PS2000A_20V'],
            "analog_offset": 0.0,
            }
channelD = {"name": "D",
            "enable_status": 0,
            "coupling_type": ps.PS2000A_COUPLING['PS2000A_DC'],
            "range": ps.PS2000A_RANGE['PS2000A_5V'],
            "analog_offset": 0.0,
            }
# put all desired channels into a list (vector with square brackets) named 'channels'
channels = [channelA, channelB, channelC]

# see oscilloscope_test.py for more information on defining the buffers
# a buffer must be defined for every channel that is defined above
bufferA = {"name": "A",
           "segment_index": 0,
           "ratio_mode": ps.PS2000A_RATIO_MODE['PS2000A_RATIO_MODE_NONE'],
           }
bufferB = {"name": "B"}
bufferC = {"name": "C"}
bufferD = {"name": "D"}
# put all buffers into a list (vector with square brackets) named 'buffers'
buffers = [bufferA, bufferB, bufferC]

# see /test/oscilloscope_test.py for more information on defining the trigger (TODO)
# a trigger is defined to capture the specific pulse characteristics of the plasma
trigger = {"enable_status": 1,
           "source": ps.PS2000A_CHANNEL['PS2000A_CHANNEL_A'],
           "threshold": 1024, # in ADC counts
           "direction": ps.PS2000A_THRESHOLD_DIRECTION['PS2000A_RISING'],
           "delay": 0, # in seconds
           "auto_trigger": 200} # in milliseconds

signal = {"offsetVoltage": 1000000, # voltage offset, in microvolts
          "pk2pk": 2000000, # peak-to-peak voltage of waveform signal (in microvolts)
          "freq": set_freq, # frequency of the wavform signal (in Hertz)
          "waveform": ctypes.c_int16(1), # type of waveform generated
          }
          # (0) PS2000A_SINE          sine wave
          # (1) PS2000A_SQUARE        square wave
          # (2) PS2000A_TRIANGLE      triangle wave
          # (3) PS2000A_RAMP_UP       rising sawtooth
          # (4) PS2000A_RAMP_DOWN     falling sawtooth
          # (5) PS2000A_SINC          sin(x)/x
          # (6) PS2000A_GAUSSIAN      Gaussian
          # (7) PS2000A_HALF_SINE     half (full-wave rectified) sine


################################################################################
# PREPARE NOTES AND SET UP FILES FOR DATA COLLECTION
# Recommended: Do NOT edit beyond this section
################################################################################
if async_collection:
    collect_osc = True
    collect_spec = True

## collect time stamp for data collection
timeStamp = datetime.now().strftime('%Y_%m_%d_%H'+'h%M''m%S'+'s')
print('Timestamp for save files: ', timeStamp)

# set save location
directory = os.getcwd()
saveDir = directory+"/data/"+timeStamp+"_"+addl_notes+"_"+set_target+"/"
if not os.path.exists(saveDir):
	os.makedirs(saveDir, exist_ok=True)
print('\nData will be saved in the following directory:')
print(saveDir)

# notes to write to files
line1 = f"# Data Timestamp: {timeStamp}\n"
line2 = f"# Input Parameters: Target = {set_target}; Voltage = {set_v} Volts; Frequency = {set_freq} Hertz; Gap = {set_gap} mm; Carrier gas flow rate = {set_flow}; liters/minute.\n"
line3 = f"# {addl_notes}\n"
lines = [line1, line2, line3]
# create a TXT file to save just the notes. The name of the text file is notes.txt
f = open(saveDir+"notes.txt", 'a')
for line in lines:
    f.write(line)

# create a CSV file to save the spectrometer data. The name of the CSV file is [timestamp]_spectra_data.csv
# notes are appended to the top of the file
if collect_spec:
    f1 = open(saveDir+timeStamp+"_spectra_data.csv", 'a')
    for line in lines:
        f1.write(line)

# create a CSV file to save the oscilloscope data. The name of the CSV file is [timestamp]_osc_data.csv
# notes are appended to the top of the file
if collect_osc:
    f2 = open(saveDir+timeStamp+"_osc_data.csv", 'a')
    for line in lines:
        f2.write(line)

################################################################################
# CONNECT TO DEVICES
################################################################################
# Spectrometer
if collect_spec:
    if not TEST:
        # for testing this code, it is not required to connect to the device;
        # if you wish to test the connection to the device, please use the spectrometer_test.py
        # this code detects the first available spectrometer connected to the computer
        # devices = list_devices()
        # print(devices)
        # spec = Spectrometer(devices[0])
        spec = Spectrometer.from_first_available()
        spec.integration_time_micros(integration_time)
    else:
        spec = None

# Oscilloscope
if collect_osc:
    if not TEST:
        # for testing this code, it is not required to connect to the device;
        # if you wish to test the connection to the device, please use the oscilloscope_test.py
        osc = Oscilloscope()
        status = osc.open_device()
        status = osc.initialize_device(channels, buffers, trigger=trigger, timebase=timebase)
    else:
        osc = None

## Startup asynchronous measurement
if async_collection:
    if os.name == "nt":
        ioloop = asyncio.ProactorEventLoop() # for subprocess' pipes on Windows
        asyncio.set_event_loop(ioloop)
    else:
        ioloop = asyncio.get_event_loop()
    # run once to initialize measurements
    tasks, runTime = ioloop.run_until_complete(async_measure(spec, osc))
    print(f"Asynchronous measurement initialized with measurement time: {runTime} sec")

input("\n\nThe devices and measurement protocol have been initialized! Press Enter/Return to continue with measurements, otherwise, use Ctrl+C to exit the program.\n")
################################################################################
# PERFORM DATA COLLECTION
################################################################################
# set up containers for data
spec_list = []
osc_list = []

# iterate through the desired number of iterations to capture the data
for i in range(int(n_iterations)):
    print(f"\nCollecting data from iteration {i} of {n_iterations}...")
    startTime = time.perf_counter()
    if i == 0:
        input("Collect background now! Plasma must be off. Press Enter when ready")
    if i == 1:
        # input("Turn on plasma to continue acquisitions. Press Enter when ready")
        status = osc.set_signal(signal)
    # collect the data
    if async_collection:
        tasks, _ = ioloop.run_until_complete(async_measure(spec, osc))
        osc_out = tasks[0].result()
        t, osc_data = osc_out
        spec_out = tasks[1].result()
        wavelengths, intensities = spec_out
    else:
        if collect_osc:
            if not TEST:
                s1 = time.perf_counter()
                t, osc_data = osc.collect_data_block()
                # print("time to collect data:", time.perf_counter() - s1)
        if collect_spec:
            if not TEST:
                wavelengths = spec.wavelengths()
                intensities = spec.intensities()

    # append the data to save containers
    if collect_osc:
        if TEST:
            if i == 0:
                osc_list.append(np.random.randn(240))
            for ch in channels:
                osc_list.append(np.random.randn(240))
        else:
            s2 = time.perf_counter()
            if i == 0:
                osc_list.append(t)
            for ch,ch_data in zip(channels,osc_data):
                assert ch["name"] == ch_data["name"]
                osc_list.append(ch_data["data"])
            # print("time to save data:", time.perf_counter() - s2)
    if collect_spec:
        if TEST:
            if i == 0:
                spec_list.append(np.random.randn(300))
            spec_list.append(np.random.randn(300))
        else:
            if i == 0:
                spec_list.append(wavelengths)
            spec_list.append(intensities)

    # save backup files of data
    if save_backup and (i%10 == 0):
        if collect_spec:
            spec_save = np.vstack(spec_list)
            df = pd.DataFrame(spec_save)
            df.to_hdf(saveDir+"data.h5", key="spec", complevel=5)

        if collect_osc:
            osc_save = np.vstack(osc_list)
            df = pd.DataFrame(osc_save)
            df.to_hdf(saveDir+"data.h5", key="osc", complevel=5)

    endTime = time.perf_counter()
    runTime = endTime-startTime
    print(f"Total Runtime of Iteration {i} was {runTime:.4f} sec...")
    if runTime < samplingTime:
        pauseTime = samplingTime - runTime
        time.sleep(pauseTime)
        print(f"      ....pausing for {pauseTime:.4f} sec.")
    elif runTime > samplingTime:
        print('WARNING: Measurement time was greater than sampling time! Data may be inaccurate.')

################################################################################
# FINAL SAVE OF DATA
################################################################################
if collect_spec:
    spec_save = np.vstack(spec_list)
    df_spec = pd.DataFrame(spec_save)
    # print(df)
    df_spec.to_csv(f1)
    df_spec.to_hdf(saveDir+"data.h5", key="spec", complevel=8)
    f1.close()

if collect_osc:
    osc_save = np.vstack(osc_list)
    df_osc = pd.DataFrame(osc_save)
    # print(df)
    df_osc.to_csv(f2)
    df_osc.to_hdf(saveDir+"data.h5", key="osc", complevel=8)
    f2.close()

if collect_osc and not TEST:
    status = osc.stop_and_close_device()

################################################################################
# PLOT LAST COLLECTED SAMPLE
################################################################################
if plot_last_data:
    print(f"\n\nPlotting data from last sampling iteration...")

    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(10,6))
    if collect_spec:
        n_intensities = df_spec.iloc[-1]
        n_wavelengths = df_spec.iloc[0]
        ax1.plot(n_wavelengths, n_intensities, lw=2)
        ax1.set_title("Intensity Spectra from final sampling iteration.")
        ax1.set_xlabel("Wavelength (nm)")
        ax1.set_ylabel("Intensity (arb. units)")

    if collect_osc:
        n_channels = len(channels)
        n_time = df_osc.iloc[0] # time
        ch_names = ["Ch A", "Ch B", "Ch C", "Ch D"]
        colors = ["tab:blue", "tab:red", "tab:green", "tab:yellow"]
        for i in range(n_channels):
            ch_data = df_osc.iloc[i-n_channels]
            if np.any(ch_data > 1e3):
                ax3 = ax2.twinx()
                ax3.plot(n_time, ch_data/1e3, lw=2, label=ch_names[i], color=colors[i])
                ax3.set_ylabel("Voltage Signal (V)")
                ax3.legend(loc="upper right")
            else:
                ax2.plot(n_time, ch_data, lw=2, label=ch_names[i], color=colors[i])
        ax2.set_title("Oscilloscope readings from final sampling iteration")
        ax2.set_xlabel("Time (ns)")
        ax2.set_ylabel("Voltage Signal (mV)")
        ax2.legend(loc="upper left")

    plt.tight_layout()
    plt.show()


print("\n\nCompleted data collection!\n")

################################################################################
# OPTION TO SEND DATA TO EMAIL
################################################################################
send_data_to_email = input("Would you like to send the collected data to your email? [Y/n] : ")
if send_data_to_email in ["Y", "y"]:
    import email
    import smtplib
    import ssl

    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication

    subject = f"Data with timestamp: {timeStamp}"
    body = f"Please see attached for the data acquired at the timestamp: {timeStamp}."
    sender_email = "gremipg2022@gmail.com"
    password = "yozpzhkdunctesnz"

    receiver_email = str(input(f"Press Enter/Return to send to the default email address: {DEFAULT_EMAIL}\n OR\nInput an email to send data: \n") or DEFAULT_EMAIL)

    # create the multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email

    # attach body to email
    message.attach(MIMEText(body, "plain"))

    if collect_spec:
        csv_filename = saveDir+timeStamp+"_spectra_data.csv"
        with open(csv_filename, 'rb') as file:
            message.attach(MIMEApplication(file.read(), Name=timeStamp+"_spectra_data.csv"))
    if collect_osc:
        csv_filename = saveDir+timeStamp+"_osc_data.csv"
        with open(csv_filename, 'rb') as file:
            message.attach(MIMEApplication(file.read(), Name=timeStamp+"_osc_data.csv"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
print("\n--------------------------------------------------------------------------------------------")
input("\n\nProgram finished! Press Enter/Return to exit.\n")
