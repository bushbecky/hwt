import opcode


class Opcode(int):
    __str__ = __repr__ = lambda s: opcode.opname[s]

opmap = dict((name.replace('+', '_'), Opcode(code)) for name, code in opcode.opmap.items())


POP_TOP = 1
ROT_TWO = 2
ROT_THREE = 3
DUP_TOP = 4
DUP_TOP_TWO = 5
NOP = 9
UNARY_POSITIVE = 10
UNARY_NEGATIVE = 11
UNARY_NOT = 12
UNARY_INVERT = 15
BINARY_POWER = 19
BINARY_MULTIPLY = 20
BINARY_MODULO = 22
BINARY_ADD = 23
BINARY_SUBTRACT = 24
BINARY_SUBSCR = 25
BINARY_FLOOR_DIVIDE = 26
BINARY_TRUE_DIVIDE = 27
INPLACE_FLOOR_DIVIDE = 28
INPLACE_TRUE_DIVIDE = 29
STORE_MAP = 54
INPLACE_ADD = 55
INPLACE_SUBTRACT = 56
INPLACE_MULTIPLY = 57
INPLACE_MODULO = 59
STORE_SUBSCR = 60
DELETE_SUBSCR = 61
BINARY_LSHIFT = 62
BINARY_RSHIFT = 63
BINARY_AND = 64
BINARY_XOR = 65
BINARY_OR = 66
INPLACE_POWER = 67
GET_ITER = 68
PRINT_EXPR = 70
LOAD_BUILD_CLASS = 71
YIELD_FROM = 72
INPLACE_LSHIFT = 75
INPLACE_RSHIFT = 76
INPLACE_AND = 77
INPLACE_XOR = 78
INPLACE_OR = 79
BREAK_LOOP = 80
WITH_CLEANUP = 81
RETURN_VALUE = 83
IMPORT_STAR = 84
YIELD_VALUE = 86
POP_BLOCK = 87
END_FINALLY = 88
POP_EXCEPT = 89
STORE_NAME = 90
DELETE_NAME = 91
UNPACK_SEQUENCE = 92
FOR_ITER = 93
UNPACK_EX = 94
STORE_ATTR = 95
DELETE_ATTR = 96
STORE_GLOBAL = 97
DELETE_GLOBAL = 98
LOAD_CONST = 100
LOAD_NAME = 101
BUILD_TUPLE = 102
BUILD_LIST = 103
BUILD_SET = 104
BUILD_MAP = 105
LOAD_ATTR = 106
COMPARE_OP = 107
IMPORT_NAME = 108
IMPORT_FROM = 109
JUMP_FORWARD = 110
JUMP_IF_FALSE_OR_POP = 111
JUMP_IF_TRUE_OR_POP = 112
JUMP_ABSOLUTE = 113
POP_JUMP_IF_FALSE = 114
POP_JUMP_IF_TRUE = 115
LOAD_GLOBAL = 116
CONTINUE_LOOP = 119
SETUP_LOOP = 120
SETUP_EXCEPT = 121
SETUP_FINALLY = 122
LOAD_FAST = 124
STORE_FAST = 125
DELETE_FAST = 126
RAISE_VARARGS = 130
CALL_FUNCTION = 131
MAKE_FUNCTION = 132
BUILD_SLICE = 133
MAKE_CLOSURE = 134
LOAD_CLOSURE = 135
LOAD_DEREF = 136
STORE_DEREF = 137
DELETE_DEREF = 138
CALL_FUNCTION_VAR = 140
CALL_FUNCTION_KW = 141
CALL_FUNCTION_VAR_KW = 142
SETUP_WITH = 143
LIST_APPEND = 145
SET_ADD = 146
MAP_ADD = 147
LOAD_CLASSDEREF = 148
EXTENDED_ARG = 144


opcodes = set(Opcode(x) for x in opcode.opmap.values())
cmp_op = opcode.cmp_op
hasarg = set(x for x in opcodes if x >= opcode.HAVE_ARGUMENT)
hasconst = set(Opcode(x) for x in opcode.hasconst)
hasname = set(Opcode(x) for x in opcode.hasname)
hasjrel = set(Opcode(x) for x in opcode.hasjrel)
hasjabs = set(Opcode(x) for x in opcode.hasjabs)
hasjump = hasjabs | hasjrel
haslocal = set(Opcode(x) for x in opcode.haslocal)
hascompare = set(Opcode(x) for x in opcode.hascompare)
hasfree = set(Opcode(x) for x in opcode.hasfree)
hascode = set((MAKE_FUNCTION, MAKE_CLOSURE))

_se = {
    IMPORT_FROM: 1,
    DUP_TOP: 1,
    LOAD_CONST: 1,
    LOAD_NAME: 1,
    LOAD_GLOBAL: 1,
    LOAD_FAST: 1,
    LOAD_CLOSURE: 1,
    LOAD_DEREF: 1,
    BUILD_MAP: 1,

    YIELD_VALUE: 0,
    UNARY_POSITIVE: 0,
    UNARY_NEGATIVE: 0,
    UNARY_NOT: 0,
    UNARY_INVERT: 0,
    GET_ITER: 0,
    LOAD_ATTR: 0,
    IMPORT_NAME: -1,
    ROT_TWO: 0,
    ROT_THREE: 0,
    NOP: 0,
    DELETE_GLOBAL: 0,
    DELETE_NAME: 0,
    DELETE_FAST: 0,

    IMPORT_NAME: -1,
    POP_TOP: -1,
    PRINT_EXPR: -1,
    IMPORT_STAR: -1,
    DELETE_ATTR: -1,
    STORE_DEREF: -1,
    STORE_NAME: -1,
    STORE_GLOBAL: -1,
    STORE_FAST: -1,
    BINARY_POWER: -1,
    BINARY_MULTIPLY: -1,
    BINARY_FLOOR_DIVIDE: -1,
    BINARY_TRUE_DIVIDE: -1,
    BINARY_MODULO: -1,
    BINARY_ADD: -1,
    BINARY_SUBTRACT: -1,
    BINARY_SUBSCR: -1,
    BINARY_LSHIFT: -1,
    BINARY_RSHIFT: -1,
    BINARY_AND: -1,
    BINARY_XOR: -1,
    BINARY_OR: -1,
    COMPARE_OP: -1,
    INPLACE_POWER: -1,
    INPLACE_MULTIPLY: -1,
    INPLACE_FLOOR_DIVIDE: -1,
    INPLACE_TRUE_DIVIDE: -1,
    INPLACE_MODULO: -1,
    INPLACE_ADD: -1,
    INPLACE_SUBTRACT: -1,
    INPLACE_LSHIFT: -1,
    INPLACE_RSHIFT: -1,
    INPLACE_AND: -1,
    INPLACE_XOR: -1,
    INPLACE_OR: -1,

    LIST_APPEND: -2,
    DELETE_SUBSCR: -2,
    STORE_ATTR: -2,
    STORE_SUBSCR: -3,
    }

_rf = {
    CALL_FUNCTION: lambda x: -((x & 0xFF00) >> 7) - (x & 0xFF),
    CALL_FUNCTION_VAR_KW: lambda x: -((x & 0xFF00) >> 7) - (x & 0xFF) - 2,
    CALL_FUNCTION_VAR: lambda x: -((x & 0xFF00) >> 7 | 1) - (x & 0xFF),
    CALL_FUNCTION_KW: lambda x: -((x & 0xFF00) >> 7 | 1) - (x & 0xFF),

    DUP_TOP: lambda x: x,
    RAISE_VARARGS: lambda x: x,
    MAKE_FUNCTION: lambda x: x,
    UNPACK_SEQUENCE: lambda x: x - 1,
    MAKE_CLOSURE: lambda x: x - 1,
    BUILD_TUPLE: lambda x: 1 - x,
    BUILD_LIST: lambda x: 1 - x,
    BUILD_SLICE: lambda x: 1 - x}

hasflow = opcodes - set(_se) - set(_rf)
