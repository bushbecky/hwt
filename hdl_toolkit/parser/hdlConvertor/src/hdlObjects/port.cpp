#include "port.h"

PyObject * Port::toJson() const {
	PyObject *d = PyDict_New();
	PyDict_SetItemString(d, "direction",
			PyUnicode_FromString(Direction_toString(direction)));
	PyDict_SetItemString(d, "variable", variable->toJson());
	Py_IncRef(d);
	return d;
}

void Port::dump(int indent) const {
	mkIndent(indent) << "{\n";
	indent += INDENT_INCR;
	dumpVal("direction", indent, Direction_toString(direction)) << ",\n";
	dumpKey("variable", indent);
	variable->dump(indent);
	mkIndent(indent - INDENT_INCR) << "\n}";
}
