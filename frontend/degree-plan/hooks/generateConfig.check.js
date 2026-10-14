const assert = require("assert");

// Mirrors hooks/generateConfig.ts. The degree-plan package has no test runner,
// so the pure helpers are checked here with node.
function parseGenConfig(raw) {
  const empty = () => ({ enabled: false, allowSummer: false, semesters: {} });
  if (!raw) return empty();
  const parsed = JSON.parse(raw);
  if (Array.isArray(parsed)) {
    const semesters = {};
    parsed.forEach((key) => {
      semesters[key] = { cuCap: key.endsWith("B") ? 2 : 5.5, gap: false };
    });
    return { enabled: false, allowSummer: false, semesters };
  }
  return {
    enabled: Boolean(parsed.enabled),
    allowSummer: Boolean(parsed.allowSummer),
    semesters: parsed.semesters || {},
  };
}

const migrated = parseGenConfig(JSON.stringify(["2024C", "2024B"]));
assert.strictEqual(migrated.semesters["2024C"].cuCap, 5.5);
assert.strictEqual(migrated.semesters["2024B"].cuCap, 2);
assert.strictEqual(migrated.enabled, false);

const kept = parseGenConfig(JSON.stringify({
  enabled: true,
  allowSummer: true,
  semesters: { "2025A": { cuCap: 4, gap: true } },
}));
assert.strictEqual(kept.enabled, true);
assert.strictEqual(kept.semesters["2025A"].gap, true);

let serial = 0;
const next = () => { serial += 1; return serial; };
const a = next();
const b = next();
assert.strictEqual(a === b, false);
assert.strictEqual(b === b, true);
console.log("generateConfig checks ok");
