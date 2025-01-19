import sys
from ctypes import *
import ctypes.util

kCFStringEncodingUTF8 = 0x08000100

cf = CDLL(ctypes.util.find_library("CoreFoundation"))
_prototype = CFUNCTYPE(c_void_p, c_void_p, c_char_p, c_uint32)
_paramflags = (
    (1, "alloc", None),
    (1, "cStr"),
    (1, "encoding", kCFStringEncodingUTF8),
)
CFStringCreateWithCString = _prototype(("CFStringCreateWithCString", cf),
                                       _paramflags)


class MIDIPacket(Structure):
    _pack_ = 1
    _fields_ = [("timestamp", c_uint64),
                ("length", c_uint16),
                ("data", c_ubyte * 17)]


class MIDIPacketList(Structure):
    _fields_ = [("numPackets", c_uint32),
                ("packet", MIDIPacket * 100)]


midi = CDLL(ctypes.util.find_library("CoreMIDI"))
_prototype = CFUNCTYPE(c_int16, c_void_p, c_void_p, c_void_p, POINTER(c_uint32))
_paramflags = (
    (1, "name"),
    (1, "notifyProc", None),
    (1, "notifyRefCon", None),
    (1, "outClient"),
)
MIDIClientCreate = _prototype(("MIDIClientCreate", midi), _paramflags)

_prototype = CFUNCTYPE(c_int16, c_uint32, c_void_p, POINTER(c_uint32))
_paramflags = (
    (1, "client"),
    (1, "name"),
    (1, "outSrc"),
)
MIDIOutputPortCreate = _prototype(("MIDIOutputPortCreate", midi), _paramflags)

_prototype = CFUNCTYPE(c_int16, c_uint32, c_void_p, c_void_p, c_void_p, POINTER(c_uint32))
_paramflags = (
    (1, "client"),
    (1, "name"),
    (1, "readProc", None),
    (1, "refCon", None),
    (1, "outPort"),
)
MIDIInputPortCreate = _prototype(("MIDIInputPortCreate", midi), _paramflags)

_prototype = CFUNCTYPE(c_uint32, c_uint32)
_paramflags = (
    (1, "destIndex"),
)
MIDIGetDestination = _prototype(("MIDIGetDestination", midi), _paramflags)

_prototype = CFUNCTYPE(c_uint32, c_uint32)
_paramflags = (
    (1, "srcIndex"),
)
MIDIGetSource = _prototype(("MIDIGetSource", midi), _paramflags)

_prototype = CFUNCTYPE(c_uint32, c_uint32, c_uint32, c_void_p)
_paramflags = (
    (1, "port"),
    (1, "source"),
    (1, "connRefCon", None),
)
MIDIPortConnectSource = _prototype(("MIDIPortConnectSource", midi), _paramflags)

_prototype = CFUNCTYPE(POINTER(MIDIPacket), POINTER(MIDIPacketList))
_paramflags = (
    (1, "pktlist"),
)
MIDIPacketListInit = _prototype(("MIDIPacketListInit", midi), _paramflags)

_prototype = CFUNCTYPE(POINTER(MIDIPacket), POINTER(MIDIPacketList), c_uint32,
                       POINTER(MIDIPacket), c_uint64, c_uint32,
                       POINTER(c_ubyte))
_paramflags = (
    (1, "pktlist"),
    (1, "listSize"),
    (1, "curPacket"),
    (1, "time", 0),
    (1, "nData"),
    (1, "data"),
)

MIDIPacketListAdd = _prototype(("MIDIPacketListAdd", midi), _paramflags)

_prototype = CFUNCTYPE(c_int16, c_uint32, c_uint32, POINTER(MIDIPacketList))
_paramflags = (
    (1, "port"),
    (1, "dest"),
    (1, "pktlist"),
)

MIDISend = _prototype(("MIDISend", midi), _paramflags)

def readProc(pktlist, readProcRefCon, srcConnRefCon):
    packet  = pktlist.contents.packet[0]
    print(packet.timestamp, packet.length,
          packet.data[0], packet.data[1], packet.data[2])

CALLBACKFUNC = CFUNCTYPE(None, POINTER(MIDIPacketList), c_void_p, c_void_p)
callback = CALLBACKFUNC(readProc)

_prototype = CFUNCTYPE(c_int16, c_uint32)
_paramflags = (
    (1, "dest"),
)
MIDIFlushOutput = _prototype(("MIDIFlushOutput", midi), _paramflags)

_prototype = CFUNCTYPE(c_int16, c_uint32)
_paramflags = (
    (1, "client"),
)
MIDIClientDispose = _prototype(("MIDIClientDispose", midi), _paramflags)


class AudioComponentDescription(ctypes.Structure):
    _fields_ = [("componentType", ctypes.c_uint32),
                ("componentSubType", ctypes.c_uint32),
                ("componentManufacturer", ctypes.c_uint32),
                ("componentFlags", ctypes.c_uint32),
                ("componentFlagsMask", ctypes.c_uint32)]


def fatal(message):
    print(message)
    sys.exit(1)


class CoreMidiDevice:
    def __init__(self):
        name = CFStringCreateWithCString(None, "mplay", kCFStringEncodingUTF8)
        outputPort = CFStringCreateWithCString(None, "Output port",
                                               kCFStringEncodingUTF8)
        inputPort = CFStringCreateWithCString(None, "Input port",
                                              kCFStringEncodingUTF8)

        self.client = c_uint32()
        if MIDIClientCreate(name, None, None, byref(self.client)) != 0:
            fatal('cannot create MIDI client')

        self.port = c_uint32()
        if MIDIOutputPortCreate(self.client, outputPort, byref(self.port)) != 0:
            fatal('cannot create MIDI output port')

        self.dest = MIDIGetDestination(0)
        if self.dest == 0:
            fatal('cannot get MIDI destination')

        self.input_port = c_uint32()
        if MIDIInputPortCreate(self.client, inputPort, callback, None,
                               byref(self.input_port)) != 0:
            print('cannot create MIDI input port')
        else:
            self.src = MIDIGetSource(0)
            if self.src == 0:
                print('cannot get MIDI source')
            else:
                if MIDIPortConnectSource(self.input_port, self.src, None) != 0:
                    fatal('cannot connect MIDI input source')

        self.pktlist = MIDIPacketList()

    def midievent(self, buf):
        pktlist = MIDIPacketListInit(byref(self.pktlist))
        packet = pktlist.contents

        packet.timestamp = 0
        packet.length = len(buf)
        for i in range(packet.length):
            packet.data[i] = buf[i]
        MIDIPacketListAdd(self.pktlist, 100, packet, 0,
                          packet.length, packet.data)

        if MIDISend(self.port, self.dest, byref(self.pktlist)) != 0:
            fatal('cannot send MIDI packet')

    def mididataset1(self, address, data):
        sysex = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        sysex[0] = 0xf0
        sysex[1] = 0x41
        sysex[2] = 0x10
        sysex[3] = 0x42
        sysex[4] = 0x12
        sysex[5] = (address >> 16) & 0xff
        sysex[6] = (address >> 8) & 0xff
        sysex[7] = address & 0xff
        sysex[8] = data
        sysex[9] = 128 - (sum(sysex[5:9]) % 128)
        sysex[10] = 0xf7
        self.midievent(sysex)

    def close(self):
        MIDIFlushOutput(self.port)
        MIDIClientDispose(self.client)


class DLSSynth:
    def FOUR_CHAR_CODE(self, code):
        value = 0
        for i in range(4):
            value += ord(code[i]) << (3 - i) * 8
        return value

    def __init__(self):
        audio = CDLL(ctypes.util.find_library("AudioToolbox"))
        self.au = CDLL(ctypes.util.find_library("AudioUnit"))

        outGraph = c_void_p()
        audio.NewAUGraph(byref(outGraph))

        cd = AudioComponentDescription()
        cd.componentManufacturer = self.FOUR_CHAR_CODE('appl')
        cd.componentFlags = 0
        cd.componentFlagsMask = 0
        cd.componentType = self.FOUR_CHAR_CODE('aumu')
        cd.componentSubType = self.FOUR_CHAR_CODE('dls ')
        synthNode = c_void_p()
        audio.AUGraphAddNode(outGraph, byref(cd), byref(synthNode))

        cd.componentType = self.FOUR_CHAR_CODE('aufx')
        cd.componentSubType = self.FOUR_CHAR_CODE('lmtr')
        limiterNode = c_void_p()
        audio.AUGraphAddNode(outGraph, byref(cd), byref(limiterNode))

        cd.componentType = self.FOUR_CHAR_CODE('auou')
        cd.componentSubType = self.FOUR_CHAR_CODE('def ')
        outNode = c_void_p()
        audio.AUGraphAddNode(outGraph, byref(cd), byref(outNode))

        audio.AUGraphOpen(outGraph)
        audio.AUGraphConnectNodeInput(outGraph, synthNode, 0, limiterNode, 0)
        audio.AUGraphConnectNodeInput(outGraph, limiterNode, 0, outNode, 0)

        self.outSynth = c_void_p()
        audio.AUGraphNodeInfo(outGraph, synthNode, 0, byref(self.outSynth))

        audio.AUGraphInitialize(outGraph)
        audio.AUGraphStart(outGraph)

    def midievent(self, buf):
        nbytes = len(buf)
        me = buf[0]
        byte1 = buf[1] if nbytes > 1 else 0
        byte2 = buf[2] if nbytes > 2 else 0
        byte3 = 0
        self.au.MusicDeviceMIDIEvent(self.outSynth, me, byte1, byte2, byte3)

    def mididataset1(self, address, data):
        sysex = (ctypes.c_ubyte * 11)()
        sysex[0] = 0xf0
        sysex[1] = 0x41
        sysex[2] = 0x10
        sysex[3] = 0x42
        sysex[4] = 0x12
        sysex[5] = (address >> 16) & 0xff
        sysex[6] = (address >> 8) & 0xff
        sysex[7] = address & 0xff
        sysex[8] = data
        sysex[9] = 128 - (sum(sysex[5:9]) % 128)
        sysex[10] = 0xf7
        self.au.MusicDeviceSysEx(self.outSynth, sysex, 11)

    def close(self):
        pass


class midiDevice:
    def __init__(self):
        #FAU: 20210102: Disabling the use of Midi Devices that are creating error type Need to look further at CFStringCreateWithCString
        #if MIDIGetDestination(0) != 0:
        #    self.device = CoreMidiDevice()
        #else:
        #    self.device = DLSSynth()
        self.device = DLSSynth()

    def midievent(self, buf):
        self.device.midievent(buf)

    def mididataset1(self, address, data):
        self.device.mididataset1(address, data)

    def close(self):
        self.device.close()
