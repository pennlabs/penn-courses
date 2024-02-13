@builtin "number.ne"
@builtin "whitespace.ne"
@builtin "string.ne"

@{%
const unwrapConnector = (type) => (d) => {
	const rest = d[4];
	let clauses = [d[3]];
	for (let i in rest) {
		clauses.push(rest[i][3])
	}
	if (clauses.length === 1) return d[3];
	return { type, clauses }
}

const extractArray = (d) => {
    let output = [d[2]];
    for (let i in d[3]) {
        output.push(d[3][i][3]);
    }
    return output;
}
%}

q -> _ "<Q:" clause ">" _ {% (d) => d[2] %}

clause -> condition {% id %}
	   | and_clause {% id %}
	   | or_clause {% id %}
	   | not_clause {% id %}
	  # NOTE: XOR clauses are not supported (yet...)

connector_clause -> and_clause {% id %}
				| or_clause {% id %}


condition -> _ "(" string _ "," _ value _ ")" _ {% (d) => ({ type: "LEAF", key: d[2], value: d[6] }) %}
and_clause -> _ "(AND:" _ clause (_ "," _ clause):* _ ")" _ {% unwrapConnector("AND") %}
or_clause -> _ "(OR:" _ clause (_ "," _ clause):* ")" _ {% unwrapConnector("OR") %}
not_clause -> _ "(NOT" _ connector_clause _ ")" _ {% (d) => ({ type: "NOT", clause: d[3] }) %}

value -> primitive {% id %}
      | array {% id %}

primitive -> string {% id %}
          | int {% id %}
          | jsonfloat {% id %}
          | none {% id %}

array -> "[" _ "]" {% (d) => [] %}
    | "[" _ primitive (_ "," _ primitive):* _ "]" {% extractArray %}

none -> _ "None" _ {% (d) => null %}
string -> dqstring {% id %}# escapable strings
	  | sqstring {% id %}