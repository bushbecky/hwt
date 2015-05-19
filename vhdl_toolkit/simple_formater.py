
import re, io
from vhdl_formater import get_indent

indentIncr = ["^entity", "^port\s*\(", "^architecture", "^if", "^port\s+map\s*\(", "^process", "^component", "\S+\s*:\s*process"]
indentDecr = ["^end", "^\)"]
indentPeak = ["^begin", "^elsif", "^else"]

indentIncr = list(map(lambda x: re.compile(x, re.IGNORECASE), indentIncr))
indentDecr = list(map(lambda x: re.compile(x, re.IGNORECASE), indentDecr))
indentPeak = list(map(lambda x: re.compile(x, re.IGNORECASE), indentPeak))

def formatVhdl(vhdlString):
    indent = 0
    lines = []
    def getIndent(i):
        return get_indent(i * 4)
    for l in vhdlString.split("\n"):
        l = l.strip()
        if any([ x.match(l) for x in indentDecr ]):
            indent -= 1
            lines.append(getIndent(indent) + l)
        elif any([ x.match(l) for x in indentIncr ]):
            lines.append(getIndent(indent) + l)
            indent += 1
        elif any([ x.match(l) for x in indentPeak ]):
            lines.append(getIndent(indent - 1) + l)
        else:
            lines.append(getIndent(indent) + l)
    return "\n".join(lines)
