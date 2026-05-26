import "@testing-library/jest-dom/vitest";

// Wave 13 #9: useETA.test.ts uses console.assert(cond, msg) for its 15 white-box checks.
// Native console.assert only PRINTS on failure — it never throws — so under a test runner a
// failed assertion would silently "pass". We override console.assert to throw on a falsy
// condition so the existing assertions become real test failures (no rewrite of the 15 tests).
const originalAssert = console.assert.bind(console);
console.assert = (condition?: unknown, ...data: unknown[]): void => {
  if (!condition) {
    const msg = data.map((d) => (typeof d === "string" ? d : JSON.stringify(d))).join(" ");
    throw new Error(`Assertion failed: ${msg || "(no message)"}`);
  }
  // keep native behaviour for the passing path (no-op, matches console.assert)
  void originalAssert;
};
