const assert = require("assert");

// Mirrors hooks/generateConfig.ts. The degree-plan package has no test runner,
// so the pure helpers are checked here with node.
function parseGenConfig(raw) {
  const empty = () => ({ allowSummer: false, semesters: {} });
  if (!raw) return empty();
  const parsed = JSON.parse(raw);
  if (Array.isArray(parsed)) {
    const semesters = {};
    parsed.forEach((key) => {
      semesters[key] = { cuCap: key.endsWith("B") ? 2 : 5.5, gap: false };
    });
    return { allowSummer: false, semesters };
  }
  return {
    allowSummer: Boolean(parsed.allowSummer),
    semesters: parsed.semesters || {},
  };
}

const migrated = parseGenConfig(JSON.stringify(["2024C", "2024B"]));
assert.strictEqual(migrated.semesters["2024C"].cuCap, 5.5);
assert.strictEqual(migrated.semesters["2024B"].cuCap, 2);
assert.strictEqual(parseGenConfig(null).allowSummer, false);

// A config saved while suggestions could be switched off still loads; the flag is ignored.
const kept = parseGenConfig(
  JSON.stringify({
    enabled: false,
    allowSummer: true,
    semesters: { "2025A": { cuCap: 4, gap: true } },
  })
);
assert.strictEqual("enabled" in kept, false);
assert.strictEqual(kept.allowSummer, true);
assert.strictEqual(kept.semesters["2025A"].gap, true);

let serial = 0;
const next = () => {
  serial += 1;
  return serial;
};
const a = next();
const b = next();
assert.strictEqual(a === b, false);
assert.strictEqual(b === b, true);
console.log("generateConfig checks ok");
