# Real-Time Range Profile Visualization using mmWave Sensor  

This project captures and visualizes real-time range profile data from a TI mmWave radar sensor. It configures the sensor, processes raw serial data, and dynamically plots range profiles using Matplotlib. The data is also logged to a CSV file for analysis.  

## Requirements  
- **TI mmWave Sensor** (e.g., IWR1443BOOST, IWR6843ISK, etc.)  
- **SDK Version:** mmWave SDK 3.6  
- Python 3.x  
- Required Libraries: `numpy`, `pyserial`, `matplotlib`, `csv`, `struct`, `threading`  

## Setup Instructions  

### 1. Flash the Board with mmWave SDK 3.6  
Before running the script, flash the board with **mmWave SDK 3.6** using **UniFlash**:  
1. Connect the board in flashing mode.  
2. Open **UniFlash** and select the correct device.  
3. Load and flash the firmware from SDK 3.6.  
4. Reset the board into functional mode.  

### 2. Install Dependencies  
Run the following command to install required Python libraries:  
```bash
pip install numpy pyserial matplotlib
```
### 3. Update Serial Port Configuration
Modify the script to match your system’s serial port settings:
```bash
CLIport = serial.Serial('COM8', 115200)
Dataport = serial.Serial('COM7', 921600)
```
Replace COM8 and COM7 with your actual serial port names.

### 4. Run the Script
Execute the script to start real-time range profile visualization:
```bash
python range_profile_visualizer.py
```

### 5. Stop and Save Data

Press Ctrl+C to stop the script. The collected data will be saved as range_power_data.csv for further analysis.

### Features
- Real-Time Data Visualization: Displays range profiles dynamically.
- Serial Communication: Configures and retrieves data from the radar sensor.
- Data Logging: Saves range profile data to CSV.
- Multithreading: Ensures smooth data collection and plotting.
