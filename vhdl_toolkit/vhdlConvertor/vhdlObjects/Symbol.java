package vhdlObjects;

import java.math.BigInteger;

import org.json.JSONException;
import org.json.JSONObject;

public class Symbol {
	public SymbolType type;
	public Object value;
	public Symbol(SymbolType type, Object value) {
		this.type = type;
		this.value = value;
	}
	public JSONObject toJson() throws JSONException {
		JSONObject s = new JSONObject();
		s.put("type", SymbolType.asString(type));
		switch (type) {
			case ID :
				if (value instanceof Reference)
					s.put("value", ((Reference) value).toJson());
				else {
					s.put("value", (String) value);
				}
				break;
			case FLOAT :
				s.put("value", (Float) value);
				break;
			case INT :
				s.put("value", (BigInteger) value);
				break;
			case STRING :
				s.put("value", (String) value);
				break;
			case OPEN :
				s.put("value", JSONObject.NULL);
				break;
			default :
				s.put("value", JSONObject.NULL);
				break;
		}

		return s;
	}
}
