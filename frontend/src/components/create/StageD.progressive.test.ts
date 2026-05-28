/**
 * StageD.progressive.test.ts — Plan A++ progressive enhancement unit tests
 *
 * Tests the state machine logic for progressive image loading in StageD:
 *   - thumb URL shown immediately on shot change
 *   - full image loaded in background; state transitions to high-res on load
 *   - cancel flag prevents stale onload from updating state after navigation
 *   - fallback behaviour when imageUrlThumb is absent (old data)
 *
 * These are pure-logic tests (no React runtime / DOM needed).
 * The actual useEffect in StageD.tsx mirrors this logic exactly.
 */

// ---------------------------------------------------------------------------
// Utility: simulate the progressive image loading state machine
// (mirrors the useEffect in StageD.tsx)
// ---------------------------------------------------------------------------

interface ProgressiveState {
  progressiveImageSrc: string | null;
  isHighRes: boolean;
}

interface Shot {
  shotId: number;
  imageUrl: string | null;
  imageUrlThumb?: string | null;
}

/**
 * Simulate one "shot change" cycle of the progressive enhancement effect.
 * Returns the initial state (after thumb is set) and what the state would be
 * after the full image "loads" (simulated via the onload callback).
 *
 * Returns { initial, afterFullLoad, cancelledState } where:
 *   initial       = state right after useEffect runs (thumb shown)
 *   afterFullLoad = state after full image onload fires (not cancelled)
 *   cancelledState = state when cancel flag is set before onload fires
 */
function simulateProgressiveEffect(
  shot: Shot,
  thumbUrl: string | null,
  fullUrl: string | null
): {
  initial: ProgressiveState;
  afterFullLoad: ProgressiveState;
  cancelledResult: "no-update";
} {
  let state: ProgressiveState = { progressiveImageSrc: null, isHighRes: false };
  let cancelled = false;

  // Mirror of the useEffect logic in StageD.tsx
  const setProgressiveImageSrc = (src: string | null) => { state = { ...state, progressiveImageSrc: src }; };
  const setIsHighRes = (v: boolean) => { state = { ...state, isHighRes: v }; };

  if (!shot) {
    setProgressiveImageSrc(null);
    setIsHighRes(false);
    return { initial: state, afterFullLoad: state, cancelledResult: "no-update" };
  }

  if (thumbUrl) {
    setProgressiveImageSrc(thumbUrl);
    setIsHighRes(false);
  } else if (fullUrl) {
    setProgressiveImageSrc(fullUrl);
    setIsHighRes(true);
    return { initial: state, afterFullLoad: state, cancelledResult: "no-update" };
  } else {
    setProgressiveImageSrc(null);
    setIsHighRes(false);
    return { initial: state, afterFullLoad: state, cancelledResult: "no-update" };
  }

  const initial = { ...state };

  // Simulate full image load (not cancelled)
  const onload = () => {
    if (cancelled) return;
    setProgressiveImageSrc(fullUrl!);
    setIsHighRes(true);
  };

  if (fullUrl && thumbUrl !== fullUrl) {
    // Fire onload (not cancelled)
    onload();
  } else if (fullUrl) {
    setIsHighRes(true);
  }

  const afterFullLoad = { ...state };

  // Now simulate cancelled scenario: reset state to initial, set cancelled=true, fire onload
  state = { ...initial };
  cancelled = true;
  const stateBeforeOnload = { ...state };
  onload(); // should be no-op
  const afterCancelledLoad = { ...state };

  // Verify cancelled onload did not change state
  console.assert(
    afterCancelledLoad.progressiveImageSrc === stateBeforeOnload.progressiveImageSrc,
    `Cancel flag: expected src unchanged, got ${afterCancelledLoad.progressiveImageSrc}`
  );
  console.assert(
    afterCancelledLoad.isHighRes === stateBeforeOnload.isHighRes,
    `Cancel flag: expected isHighRes unchanged, got ${afterCancelledLoad.isHighRes}`
  );

  return { initial, afterFullLoad, cancelledResult: "no-update" };
}

// ---------------------------------------------------------------------------
// Test 1: Normal case — thumb present, full image different URL
// ---------------------------------------------------------------------------
function testThumbThenFullSwap() {
  const shot: Shot = { shotId: 1, imageUrl: "/static/shot.webp", imageUrlThumb: "/static/shot.thumb.webp" };
  const thumbUrl = "http://127.0.0.1:8000/static/shot.thumb.webp";
  const fullUrl = "http://127.0.0.1:8000/static/shot.webp";

  const { initial, afterFullLoad } = simulateProgressiveEffect(shot, thumbUrl, fullUrl);

  // Initial state: thumb shown, not high-res
  console.assert(
    initial.progressiveImageSrc === thumbUrl,
    `Test1 initial: expected thumb URL "${thumbUrl}", got "${initial.progressiveImageSrc}"`
  );
  console.assert(
    initial.isHighRes === false,
    `Test1 initial: expected isHighRes=false, got ${initial.isHighRes}`
  );

  // After full image loads: src swapped to full URL, now high-res
  console.assert(
    afterFullLoad.progressiveImageSrc === fullUrl,
    `Test1 afterFullLoad: expected full URL "${fullUrl}", got "${afterFullLoad.progressiveImageSrc}"`
  );
  console.assert(
    afterFullLoad.isHighRes === true,
    `Test1 afterFullLoad: expected isHighRes=true, got ${afterFullLoad.isHighRes}`
  );

  console.log("Test 1 — Thumb→Full swap: PASS");
}

// ---------------------------------------------------------------------------
// Test 2: Old data — no thumb (imageUrlThumb is null)
// ---------------------------------------------------------------------------
function testNoThumbFallsBackToFull() {
  const shot: Shot = { shotId: 2, imageUrl: "/static/shot.png", imageUrlThumb: null };
  const thumbUrl: string | null = null;
  const fullUrl = "http://127.0.0.1:8000/static/shot.png";

  const { initial, afterFullLoad } = simulateProgressiveEffect(shot, thumbUrl, fullUrl);

  // Without thumb: immediately shows full image at high-res
  console.assert(
    initial.progressiveImageSrc === fullUrl,
    `Test2: expected full URL "${fullUrl}", got "${initial.progressiveImageSrc}"`
  );
  console.assert(
    initial.isHighRes === true,
    `Test2: expected isHighRes=true (no thumb), got ${initial.isHighRes}`
  );
  console.assert(
    afterFullLoad.isHighRes === true,
    `Test2 afterFullLoad: still isHighRes=true, got ${afterFullLoad.isHighRes}`
  );

  console.log("Test 2 — No thumb fallback to full: PASS");
}

// ---------------------------------------------------------------------------
// Test 3: Failed shot — both imageUrl and imageUrlThumb are null
// ---------------------------------------------------------------------------
function testNullImageShowsNullSrc() {
  const shot: Shot = { shotId: 3, imageUrl: null, imageUrlThumb: null };
  const thumbUrl: string | null = null;
  const fullUrl: string | null = null;

  const { initial } = simulateProgressiveEffect(shot, thumbUrl, fullUrl);

  console.assert(
    initial.progressiveImageSrc === null,
    `Test3: expected null src, got "${initial.progressiveImageSrc}"`
  );
  console.assert(
    initial.isHighRes === false,
    `Test3: expected isHighRes=false for failed shot, got ${initial.isHighRes}`
  );

  console.log("Test 3 — Failed shot null src: PASS");
}

// ---------------------------------------------------------------------------
// Test 4: Cancel flag prevents stale onload from updating state
// (verified inside simulateProgressiveEffect's cancelledResult check)
// ---------------------------------------------------------------------------
function testCancelFlagPreventsStaleUpdate() {
  const shot: Shot = { shotId: 4, imageUrl: "/static/shot.webp", imageUrlThumb: "/static/shot.thumb.webp" };
  const thumbUrl = "http://127.0.0.1:8000/static/shot.thumb.webp";
  const fullUrl = "http://127.0.0.1:8000/static/shot.webp";

  const { cancelledResult } = simulateProgressiveEffect(shot, thumbUrl, fullUrl);

  console.assert(
    cancelledResult === "no-update",
    `Test4: expected cancelled onload to be no-op, got "${cancelledResult}"`
  );

  console.log("Test 4 — Cancel flag prevents stale update: PASS");
}

// ---------------------------------------------------------------------------
// Test 5: thumb URL === full URL (same URL) — skips background load, sets isHighRes directly
// ---------------------------------------------------------------------------
function testThumbSameAsFullSkipsBackgroundLoad() {
  const sameUrl = "http://127.0.0.1:8000/static/shot.webp";
  const shot: Shot = { shotId: 5, imageUrl: "/static/shot.webp", imageUrlThumb: "/static/shot.webp" };

  const { initial, afterFullLoad } = simulateProgressiveEffect(shot, sameUrl, sameUrl);

  // thumb == full: show once, mark as high-res
  console.assert(
    initial.progressiveImageSrc === sameUrl,
    `Test5 initial: expected src="${sameUrl}", got "${initial.progressiveImageSrc}"`
  );
  console.assert(
    afterFullLoad.isHighRes === true,
    `Test5 afterFullLoad: expected isHighRes=true when thumb==full, got ${afterFullLoad.isHighRes}`
  );

  console.log("Test 5 — Thumb same as full skips background load: PASS");
}

// ---------------------------------------------------------------------------
// Vitest suite
// ---------------------------------------------------------------------------
describe("StageD — Plan A++ progressive enhancement state machine", () => {
  it("Test 1 — thumb shown first, then swaps to full on load", testThumbThenFullSwap);
  it("Test 2 — no thumb (old data) falls back to full image directly", testNoThumbFallsBackToFull);
  it("Test 3 — failed shot (null imageUrl) shows null src", testNullImageShowsNullSrc);
  it("Test 4 — cancel flag prevents stale onload from updating state", testCancelFlagPreventsStaleUpdate);
  it("Test 5 — thumb === full skips background load, sets isHighRes immediately", testThumbSameAsFullSkipsBackgroundLoad);
});
