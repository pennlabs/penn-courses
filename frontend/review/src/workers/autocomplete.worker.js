import LZString from "lz-string";

export const compress = data =>
  "compressed:" + LZString.compress(JSON.stringify(data));

export const decompress = data =>
  JSON.parse(LZString.decompress(data.substring("compressed:".length)));
