@builtin "number.ne"
@builtin "whitespace.ne"
@builtin "string.ne"

@{%
const unwrapConnector = (type) => (d) => {
	const clauses = d[3]
	if (clauses.length == 1) return clauses[0];
	return { type, clauses };
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

clause -> condition
	   | and_clause
	   | or_clause
	   | not_clause
	  # NOTE: XOR clauses are not supported (yet...)

connector_clause -> and_clause
				| or_clause


condition -> _ "(" string _ "," _ value _ ")" _ {% (d) => ({ type: "LEAF", key: d[2], value: d[6] }) %}
and_clause -> _ "(AND:" _ clauses _ ")" _ {% unwrapConnector("AND") %}
or_clause -> _ "(OR:" _ clauses _ ")" _ {% unwrapConnector("OR") %}
clauses -> clause {% function (d) { return d } %}
        | clauses "," clause {% function(d){ return d[0].concat(d[2]) } %} 
not_clause -> _ "(NOT" _ connector_clause _ ")" _ {% (d) => ({ type: "NOT", clause: d[3] }) %}

value -> primitive
      | array

primitive -> string
          | int
          | jsonfloat
          | none

array -> "[" _ "]" {% (d) => [] %}
    | "[" _ primitive (_ "," _ primitive):* _ "]" {% extractArray %}

none -> _ "None" _ {% (d) => null %}
string -> dqstring # escapable strings
	  | sqstring