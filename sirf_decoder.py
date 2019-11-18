import serial
import binascii
import struct

def sirf_int(byteseq, signed=True):
    return int.from_bytes(byteseq, "big", signed=signed)

def sirf_double(byteseq):
    b = byteseq
    return struct.unpack('d', bytes([b[3],b[2],b[1],b[0],b[7],b[6],b[5],b[4]]))[0]

def sirf_float(byteseq):
    return struct.unpack('f', byteseq[-1::-1])[0]

class SiRF_receiver(object):
    """SiRF decoder decode information from specified serial device"""

    def __init__(self, serial_gps):
        self.serial = serial_gps

    def pollClockStatus(self):
        """Ask Device to response a clock status message(MID 7){{{"""
        sequence = b'\x90\x00'
        message = self.encapsulate(sequence)
        
        self.sendInput(message)
        # }}}

    def setMessageRate(self, mid, rate):
        """Set setting the output rate for specific message{{{"""
        if mid > 255 or 0 > mid:
            raise Exception("No such message id")
        if rate < 0 or rate > 30:
            raise Exception("Rate must between 0 to 30")
        sequence  = b'\xa6'
        sequence += b'\x00'
        sequence += bytes([mid])
        sequence += bytes([rate])
        sequence += bytes(4)
        message = self.encapsulate(sequence)

        self.sendInput(message)
        # }}}

    def enableAdvancedOutput(self, navlib = True, debug = False):
        """Enable Advance output like raw track data, navigation library ...{{{"""
        sequence = b'\x80'
        sequence += bytes(4+4+4+4+4+2+1)
        sequence += bytes([(0x10 if navlib else 0) + (0x20 if debug else 0)])

        message = self.encapsulate(sequence)

        self.sendInput(message)

        # }}}

    def switchProtocol(self,sprotocol):
        """Switching the communicate protocol of connected SiRF chip {{{"""

        if sprotocol == "NMEA":
            payload = [ 0x81,0x02,0x01,0x01,
                        0x00,0x01,0x01,0x01,
                        0x05,0x01,0x01,0x01,
                        0x00,0x01,0x00,0x01,
                        0x00,0x00,0x00,0x01,
                        0x00,0x00,0x12,0xC0 ]
            payload = bytes(payload)
            message = self.encapsulate(payload)
        elif sprotocol == "SiRF":
            command = "$PSRF100,0,4800,8,1,0*0F\r\n"
            message = command.encode('ascii')

        # Sending the message to serial
        self.sendInput(message)

        # }}}

    def sendInput(self, message):
        """Sending Input {{{"""
        self.serial.write(message)
        self.serial.flush()

    # }}}

    def encapsulate(self,payload):
        """This method encapsulate payload into a SiRF input message {{{"""
        # The start of sequence
        sequence = b'\xa0\xa2'

        # Insert payload length
        length = len(payload)
        if length < (2**15):
            sequence += bytes([(length >> 8) & 0xff , length & 0xff])
        else:
            raise Exception("Payload is too big")

        # Insert Payload
        sequence += payload

        # calcuate checksum
        checksum = 0
        for byte in payload:
            checksum = checksum + byte
        checksum = (checksum) & (2**15-1)
        sequence += bytes([(checksum >> 8) & 0xff , checksum & 0xff])

        # The end of sequence
        sequence += b'\xb0\xb3'

        return sequence

    # }}}

    def readMessage(self):
        """Receive message {{{"""

        length, bytedata = self.readRawMessage()

        if not bytedata[0] in _sirf_decode_function:
            return { "mid": int(bytedata[0]), "rawdata": bytedata }

        return _sirf_decode_function[bytedata[0]](length, bytedata)

    # }}}

    def readRawMessage(self):
        """Receive Raw Message{{{"""

        # keep scanning for ouptut header
        scan = (0,0)
        while scan != (b'\xa0', b'\xa2'):
            scan = scan[1], self.serial.read()

        # payload
        length  = sirf_int(self.serial.read(2), signed=False)
        payload = self.serial.read(length)
        checksum = sirf_int(self.serial.read(2), signed=False)

        # checking checksum
        for byte in payload:
            checksum = checksum - int(byte)
        checksum = checksum & (2**15-1)
        if checksum != 0:
            raise Exception("Checksum failed")

        # expecting end sequence
        if self.serial.read(2) != b'\xb0\xb3':
            raise Exception('Wrong End sequence')

        return length, payload

# }}}

    def askVersion(self):
        sequence = b'\x84\x00'
        message  = self.encapsulate(sequence)
        self.sendInput(message)

def sirf_2(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "xposition"     : sirf_int(bytecode[1:5]),
            "yposition"     : sirf_int(bytecode[5:9]),
            "zposition"     : sirf_int(bytecode[9:13]),
            "xvelocity"     : sirf_int(bytecode[13:15]),
            "yvelocity"     : sirf_int(bytecode[15:17]),
            "zvelocity"     : sirf_int(bytecode[17:19]),
            "sv_in_fix"     : sirf_int(bytecode[29:30], False)
    }

def sirf_30(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "satelliteID"   : sirf_int(bytecode[1:2], False),
            "GPStime"       : sirf_int(bytecode[2:10], False),
            "xposition"     : sirf_double(bytecode[10:18]),
            "yposition"     : sirf_double(bytecode[18:26]),
            "zposition"     : sirf_double(bytecode[26:34]),
            "xvelocity"     : sirf_double(bytecode[34:42]),
            "yvelocity"     : sirf_double(bytecode[42:50]),
            "zvelocity"     : sirf_double(bytecode[50:58]),
            "clockBias"     : sirf_double(bytecode[58:66]),
            "clockdrift"    : sirf_float(bytecode[66:70]),
            "ephflag"       : sirf_int(bytecode[71:72], False),
            "iDelay"        : sirf_float(bytecode[79:83]),
    }

def sirf_11(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "ackId"         : sirf_int(bytecode[1:2], False),
    }

def sirf_12(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "nackId"        : sirf_int(bytecode[1:2], False),
    }

def sirf_6(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "version"       : bytecode[1::].decode('ascii', 'replace')
    }

def sirf_255(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "output"        : bytecode[1::].decode('ascii', 'replace')
            }

def sirf_28(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "channel"       : sirf_int(bytecode[1:2], False),
            "timetag"       : sirf_int(bytecode[2:6], False),
            "satelliteID"   : sirf_int(bytecode[6:7], False),
            "gpsstime"      : sirf_double(bytecode[7:15]),
            "pseudorange"   : sirf_double(bytecode[15:23]),
            }

def sirf_7(length, bytecode):
    return {
            "mid"           : sirf_int(bytecode[0:1], False),
            "svs"           : sirf_int(bytecode[7:8], False),
            "clockBias"     : sirf_int(bytecode[12:16], False),
            }

_sirf_decode_function = {
    2 : sirf_2,
    6 : sirf_6,
    7 : sirf_7,
    11: sirf_11,
    12: sirf_12,
    30: sirf_30,
    28: sirf_28,
    255: sirf_255,
}

# Message ID 172, Initialize GPS/Dr Navigation
