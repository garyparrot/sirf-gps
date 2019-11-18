import serial
import time
import os
from sirf_decoder import SiRF_receiver
from satemath import SatelliteInfo, calcCoordinate

# serial config for SiRF chip
serial_config = {
    "port"      : "/dev/ttyUSB0",
    "baudrate"  : 4800,
    "bytesize"  : serial.EIGHTBITS,
    "parity"    : serial.PARITY_NONE,
    "stopbits"  : serial.STOPBITS_ONE,
    "rtscts"    : False,
    "dsrdtr"    : False,
    "xonxoff"   : False,
} 

def main():
    # Setup serial
    ser = serial.Serial(**serial_config)

    # Initialize decoder
    sirf = SiRF_receiver(ser)

    # Switch to SiRF binary protocol
    sirf.switchProtocol("SiRF")

    # Enable advance output also restart it
    sirf.enableAdvancedOutput(navlib = True, debug = False)

    # Sleep for a while, wait for GPS receiver
    time.sleep(3)

    # Setting message rate
    sirf.setMessageRate(30, 1)
    sirf.setMessageRate(28, 1)

    # Ask version
    # sirf.askVersion()

    while True:
        Go(sirf)

def Go(sirf):

    # Collect satellite information
    satellites = {}
    clock_bias = None
    i = 0

    while sirf:
        if i == 10:
            sirf.pollClockStatus()
            i = 0
        i += 1
        try:
            # Read message from GPS receiver
            msg = sirf.readMessage()

            # Extract message id
            messageid = msg["mid"]
            if "satelliteID" in msg:
                sid = msg["satelliteID"]
                if sid not in satellites:
                    satellites[sid] = {}

            # Extract satellite info from message
            if messageid == 28:
                satellites[sid]["pseudorange"]      = msg["pseudorange"]
                satellites[sid]["sid"]              = msg["satelliteID"]
            if messageid == 30:
                satellites[sid]["x"]                = msg["xposition"]
                satellites[sid]["y"]                = msg["yposition"]
                satellites[sid]["z"]                = msg["zposition"]
                satellites[sid]["ionosphericDelay"] = msg["iDelay"]
                satellites[sid]["id"]               = msg["satelliteID"]
                satellites[sid]["clockBias"]        = msg["clockBias"]
            if messageid ==  7:
                clock_bias = msg["clockBias"]

            # Echo message to standard output
            if msg["mid"] in transTable:
                transTable[msg["mid"]](msg)

            # Test if we got what we need
            condition = lambda s: "x" in s and "y" in s and "z" in s and "pseudorange" in s and "ionosphericDelay" in s and s["ionosphericDelay"] != 0
            if sum([condition(satellites[s]) for s in satellites]) >= 4 and clock_bias != None:
                break

        except Exception as err:
            print("error: ",err)

    # Filte valid satellite info out
    condition = lambda s: "x" in s and "y" in s and "z" in s and "pseudorange" in s and "ionosphericDelay" in s and s["ionosphericDelay"] != 0
    satellites = list(filter(condition, [satellites[s] for s in satellites]))

    # Adjust ionospheric error and clock error
    for sate in satellites:
        sate["pseudorange"] -= sate["ionosphericDelay"]
        sate["pseudorange"] -= (clock_bias * 1e-9 - sate["clockBias"]) * 299792458

    # Create StelliteInfo
    translater = lambda s: SatelliteInfo(s["pseudorange"], s["x"], s["y"], s["z"], s["id"])
    satellites = list(map(translater, satellites))

    # Calcuate receiver x,y,z
    print("Result: ",calcCoordinate(*satellites[:4]))

transTable = {
        2  : lambda msg: print("Your location: x,y,z = (%d,%d,%d)" % (msg["xposition"], msg["yposition"], msg["zposition"])),
        # 7  : lambda msg: print("[GPS Receiver] Satellite in solution: %d, clock_bias: %e" %(msg["svs"], msg["clockBias"])),
        # 11 : lambda msg: print("[GPS Receiver] Request %d acknowledged." % msg["ackId"]),
        # 12 : lambda msg: print("[GPS Receiver] Request %d rejected." % msg["nackId"]),
        28 : lambda msg: print("Satellite %3d : pseudorange = (%e)" % (msg["satelliteID"], msg["pseudorange"])),
        30 : lambda msg: print("Satellite %3d : x,y,z = (%e,%e,%e)" % (msg["satelliteID"], msg["xposition"], msg["yposition"], msg["zposition"])),
        # 255: lambda msg: print("[GPS Receiver]", msg["output"]),
}

if __name__ == "__main__":
    main()
