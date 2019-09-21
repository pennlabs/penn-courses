var parser = document.createElement('a');
parser.href = window.location.href;
// "http://example.com:3000/pathname/?search=test#hash";

parser.protocol; // => "http:"
parser.hostname; // => "example.com"
parser.port;     // => "3000"
parser.pathname; // => "/pathname/"
parser.search;   // => "?search=test"
parser.hash;     // => "#hash"
parser.host;     // => "example.com:3000"
