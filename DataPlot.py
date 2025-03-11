import numpy as np
import serial
import time
import struct
import csv
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Change the configuration file name
configFileName = './profile_2025_02_20T16_54_45_628.cfg'

CLIport = {}
Dataport = {}
byteBuffer = np.zeros(2**15, dtype='uint8')
byteBufferLength = 0
all_frames = []

# Functions for serial config and parsing
def serialConfig(configFileName):
    global CLIport, Dataport
    CLIport = serial.Serial('COM8', 115200)
    Dataport = serial.Serial('COM7', 921600)
    with open(configFileName, 'r') as file:
        config = file.readlines()
    for i in config:
        CLIport.write((i.strip() + '\n').encode())
        print(i.strip())
        time.sleep(0.01)
    return CLIport, Dataport

def parseConfigFile(configFileName):
    configParameters = {}
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        splitWords = i.split(" ")
        numRxAnt = 4
        numTxAnt = 3
        if "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 *= 2
            digOutSampleRate = int(splitWords[11])
        elif "frameCfg" in splitWords[0]:
            chirpStartIdx = int(splitWords[1])
            chirpEndIdx = int(splitWords[2])
            numLoops = int(splitWords[3])
            numFrames = int(splitWords[4])
            framePeriodicity = float(splitWords[5])
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
    return configParameters

def decode_range_profile(buffer, configParameters):
    magic_word = b'\x02\x01\x04\x03\x06\x05\x08\x07'
    if buffer[:8] != magic_word:
        print("Incorrect Magic Word!")
        return None
    header_format = "QIIIIQ"
    header_size = struct.calcsize(header_format)
    if len(buffer) < header_size:
        return None
    header_data = struct.unpack(header_format, buffer[:header_size])
    frame_number = header_data[4]
    print(f"Frame {frame_number} received")
    offset = header_size
    while offset + 8 <= len(buffer):
        tlv_format = "II"
        tlv_size = struct.calcsize(tlv_format)
        try:
            tlv_type, tlv_length = struct.unpack(tlv_format, buffer[offset:offset + tlv_size])
        except struct.error:
            return None
        offset += tlv_size
        if offset + tlv_length > len(buffer):
            return None
        if tlv_type == 2:
            numRangeBins = configParameters.get("numRangeBins", 256)
            rangeProf = np.zeros(numRangeBins, dtype=np.uint16)
            idX = offset
            for i in range(numRangeBins):
                rangeProf[i] = int.from_bytes(buffer[idX:idX+2], byteorder='little', signed=False)
                idX += 2
            all_frames.append(rangeProf)
            return rangeProf
        offset += tlv_length
    return None

def save_to_csv():
    if not all_frames:
        print("No data available to save.")
        return
    range_values = np.arange(len(all_frames[0])) / 25
    header = ["Range (m)"] + [f"Frame {i+1}" for i in range(len(all_frames))]
    data = np.column_stack([range_values] + all_frames)
    filename = "range_power_data.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)
    print(f"Data saved successfully to {filename}")

# Initialize plot
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r-', label="Range Profile")

def init():
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Relative Power (dB)")
    ax.set_title("Real-Time Range Profile")
    ax.legend()
    return line,

# Update plot dynamically
def update(frame):
    if all_frames:
        x_values = np.arange(len(all_frames[-1])) / 25
        y_values = 2 * (all_frames[-1] / 100) - 1
        line.set_data(x_values, y_values)
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw_idle()
    return line,

# Serial communication
CLIport, Dataport = serialConfig(configFileName)
configParameters = parseConfigFile(configFileName)

# Start real-time animation
ani = animation.FuncAnimation(fig, update, init_func=init, interval=100, blit=False)

# Thread for data reception
def read_serial_data():
    count = 0
    try:
        while True:
            Dataport.reset_input_buffer()
            time.sleep(0.1)
            while Dataport.in_waiting == 0:
                time.sleep(0.1)
            new_data = Dataport.read(Dataport.in_waiting)
            range_bins = decode_range_profile(new_data, configParameters)
            if range_bins is not None:
                count += 1
                print(f"Frame {count} collected successfully.")
    except KeyboardInterrupt:
        print("\nProgram stopped by user. Saving data...")
        save_to_csv()
    finally:
        CLIport.write(('sensorStop\n').encode())
        CLIport.close()
        Dataport.close()
        print("Serial ports closed.")

# Run the serial reading thread
serial_thread = threading.Thread(target=read_serial_data, daemon=True)
serial_thread.start()
# Run the real-time plot in the main thread
plt.show(block=True)