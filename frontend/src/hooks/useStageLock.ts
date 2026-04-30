// D.14 F-Lock-Family: shared lock hook for outline/characters/scenes stages
// When generationStatus is "generating" or "complete", these stages are locked
// — the user can no longer edit or confirm; a banner + "返回创作进度" is shown.

import { useCreate } from "@/contexts/CreateContext";

export function useStageLock() {
  const { state } = useCreate();
  const isLocked =
    state.generationStatus === "generating" ||
    state.generationStatus === "complete";
  return isLocked;
}
