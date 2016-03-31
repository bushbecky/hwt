class RecordTypes:
    """Schematic object record types"""
    SCH_COMPONENT = b"1"
    PIN = b"2"
    LABEL = b"4"
    BEZIER = b"5"
    POLYLINE = b"6"
    POLYGON = b"7"
    ELLIPSE = b"8"
    ROUND_RECTANGLE = b"10"
    ELLIPTICAL_ARC = b"11"
    ARC = b"12"
    LINE = b"13"
    RECTANGLE = b"14"
    SHEET_SYMBOL = b"15"
    POWER_OBJECT = b"17"
    PORT = b"18"
    NO_ERC = b"22"
    NET_LABEL = b"25"
    WIRE = b"27"
    TEXT_FRAME = b"28"
    JUNCTION = b"29"
    IMAGE = b"30"
    SHEET = b"31"
    SHEET_NAME = b"32"
    SHEET_FILE_NAME = b"33"
    DESIGNATOR = b"34"
    PARAMETER = b"41"

class PinElectricalTypes:
    """Signal types for a pin"""
    INPUT = b"0"
    IO = b"1"
    OUTPUT = b"2"
    OPEN_COLLECTOR = b"3"
    PASSIVE = b"4"
    HI_Z = b"5"
    OPEN_EMITTER = b"6"
    POWER = b"7"

class PowerObjectStyleTypes:
    """Symbols for remote connections to common rails"""
    ARROW = b"1"
    BAR = b"2"
    GND = b"4"

class ParameterReadOnlyStateTypes:
    NAME = b"1"

class SheetStyleTypes:
    """Preset sheet sizes"""
    A4 = b"0"
    A3 = b"1"
    A = b"5"
    B = b"6"
    C = b"7"
