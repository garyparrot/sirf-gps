import serial
import time
from sirf_decoder import SiRF_receiver

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

    # Setting Message Rate
    sirf.setMessageRate(30, 1)
    sirf.setMessageRate(28, 1)

    # Ask version
    sirf.askVersion()

    while ser:
        try:
            msg = sirf.readMessage()
            if type(msg) == type({}) and msg["mid"] in transTable:
                transTable[msg["mid"]](msg)
        except Exception as err:
            print(err)


transTable = {
        2  : lambda msg: print("Your location: x,y,z = (%d,%d,%d)" % (msg["xposition"], msg["yposition"], msg["zposition"])),
        11 : lambda msg: print("[GPS Receiver] Request %d acknowledged." % msg["ackId"]),
        12 : lambda msg: print("[GPS Receiver] Request %d rejected." % msg["nackId"]),
        28 : lambda msg: print("Satellite %3d : pseudorange = (%e)" % (msg["satelliteID"], msg["pseudorange"])),
        30 : lambda msg: print("Satellite %3d : x,y,z = (%e,%e,%e)" % (msg["satelliteID"], msg["xposition"], msg["yposition"], msg["zposition"])),
        255: lambda msg: print("[GPS Receiver]", msg["output"]),
}

if __name__ == "__main__":
    main()
