import LZString from "lz-string";

export const compress = (data : string) : string =>
  "compressed:" + LZString.compress(JSON.stringify(data));

export const decompress = (data : string) : string =>
  JSON.parse(LZString.decompress(data.substring("compressed:".length)));
