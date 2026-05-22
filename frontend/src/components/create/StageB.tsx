"use client";

import { useState } from "react";
import { motion, Reorder, useDragControls } from "framer-motion";
import {
  ChevronLeft,
  Sparkles,
  User,
  GripVertical,
  Plus,
  Trash2,
  Check,
  AlertCircle,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useCreate } from "@/contexts/CreateContext";
import { apiFetch, getStoredToken } from "@/lib/api";
import { useStageLock } from "@/hooks/useStageLock";
import { buildCreateUrl } from "@/lib/createUrl";
import type { PlotPoint } from "@/types/create";

// UX-2: Extract Arabic numerals and common Chinese number words from text
const NUMBER_REGEX = /(\d+|[零一二三四五六七八九十百千万]+(?:[零一二三四五六七八九十百千万]+)*)/g;

// UX-2: Find cross-plot number conflicts. Returns list of (number, conflicting plot indices)
function findCrossPlotNumberConflicts(
  editedIndex: number,
  editedText: string,
  allPlots: PlotPoint[]
): Array<{ num: string; conflictIndices: number[] }> {
  const editedNums = Array.from(new Set(editedText.match(NUMBER_REGEX) || []));
  const conflicts: Array<{ num: string; conflictIndices: number[] }> = [];

  for (const num of editedNums) {
    const re = new RegExp(`(?<![\\d\\u4e00-\\u9fa5])${num.replace(/\d/g, "\\d").replace(/[零一二三四五六七八九十百千万]/g, c => c)}(?![\\d\\u4e00-\\u9fa5])`, "g");
    const conflictIndices: number[] = [];
    allPlots.forEach((p, idx) => {
      if (idx !== editedIndex && re.test(p.description)) {
        conflictIndices.push(idx + 1); // 1-based plot number
      }
    });
    if (conflictIndices.length > 0) {
      conflicts.push({ num, conflictIndices });
    }
  }
  return conflicts;
}

function PlotPointItem({
  point,
  plotIndex,
  allPlots,
  onDescriptionChange,
  onDelete,
}: {
  point: PlotPoint;
  plotIndex: number;
  allPlots: PlotPoint[];
  onDescriptionChange: (value: string) => void;
  onDelete: () => void;
}) {
  const controls = useDragControls();
  // UX-2: Compute cross-plot number conflicts on every render (pure computation, no state needed)
  const conflicts = findCrossPlotNumberConflicts(plotIndex, point.description, allPlots);

  return (
    <Reorder.Item
      value={point}
      dragListener={false}
      dragControls={controls}
      className="bg-bg-secondary rounded-lg border border-white/5 group"
    >
      <div className="flex items-start gap-2 p-3">
        <div
          onPointerDown={(e) => controls.start(e)}
          className="touch-none mt-0.5 flex-shrink-0 cursor-grab active:cursor-grabbing"
        >
          <GripVertical className="w-4 h-4 text-text-muted" />
        </div>
        <input
          type="text"
          value={point.description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          placeholder="描述这个情节点..."
          className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
        />
        <button
          onClick={onDelete}
          className="w-5 h-5 flex items-center justify-center text-text-muted hover:text-red-400 sm:opacity-0 sm:group-hover:opacity-100 transition-all flex-shrink-0"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
      {/* UX-2: Cross-plot number consistency hint */}
      {conflicts.length > 0 && (
        <div className="px-3 pb-2 space-y-1">
          {conflicts.map(({ num, conflictIndices }) => (
            <div key={num} className="flex items-start gap-1.5 text-amber-400/80 text-xs">
              <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>
                数字 <strong className="text-amber-400">{num}</strong> 也出现在情节{conflictIndices.map(i => `第${i}点`).join("、")}，请确认是否需要同步修改。
              </span>
            </div>
          ))}
        </div>
      )}
    </Reorder.Item>
  );
}

// RISK-T14-13-frontend: Shape of inconsistency warnings from confirm-outline response
interface InconsistencyWarning {
  type: string;
  message: string;
  affected_field?: string;
}

export default function StageB() {
  const { state, dispatch } = useCreate();
  const router = useRouter();
  const { outline } = state;
  const [editingCharId, setEditingCharId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  // RISK-T14-13-frontend: Banner shown when backend returns inconsistency_warnings
  const [warningBanner, setWarningBanner] = useState<InconsistencyWarning[] | null>(null);

  // D.14 F-Lock-Family: lock outline editing once generation has started
  const isLocked = useStageLock();

  if (!outline) {
    // P0 hotfix v2: outline not yet loaded (hydration recovery in progress).
    // Show a loading state so user sees activity instead of blank screen.
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 text-text-secondary">
        <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-sm">正在加载故事大纲...</p>
      </div>
    );
  }

  // D.14: Build "返回创作进度" URL — prefer generating/characters/scenes based on current state
  // T22-NEW-5 (2026-05-22): "scene-preview" arm removed (R4-2 deleted); scene-refs-preview maps to "scenes"
  const progressStage =
    state.generationSubPhase === "char-preview"
      ? "characters"
      : state.generationSubPhase === "scene-refs-preview"
      ? "scenes"
      : "generating";
  const progressUrl = buildCreateUrl(state.projectId, progressStage) || "/dashboard";

  const handleConfirm = async () => {
    const token = getStoredToken();
    if (!token) {
      // [StageB] Log #1 — no token → redirect to login
      // eslint-disable-next-line no-console
      console.warn("[StageB] handleConfirm: no token → redirect /login");
      router.push("/login");
      return;
    }

    const projectId = state.projectId;
    if (!projectId) {
      // [StageB] Log #2 — projectId missing (should never happen post-StageA)
      // eslint-disable-next-line no-console
      console.error("[StageB] handleConfirm: projectId is null — project was not created in StageA");
      setSubmitError("项目未创建，请返回重新输入创意");
      return;
    }

    // [StageB] Log #3 — confirm-outline submission start
    // eslint-disable-next-line no-console
    console.log("[StageB] handleConfirm: submitting confirm-outline for projectId=", projectId,
      "title=", outline.title,
      "chars=", outline.characters.length,
      "plotPoints=", outline.plotPoints.length,
      "mood=", outline.mood,
      "user_selected_mood=", state.userSelectedMood);

    setSubmitting(true);
    setSubmitError("");
    try {
      // 1. Save user edits via confirm-outline
      const confirmResponse = await apiFetch<{ inconsistency_warnings?: InconsistencyWarning[] }>(
        `/projects/${projectId}/confirm-outline`, {
        method: "POST",
        body: JSON.stringify({
          outline: {
            title: outline.title,
            title_en: outline.titleEn,
            summary: outline.summary,
            characters: outline.characters.map(c => ({
              name: c.name,
              name_en: c.nameEn,
              description: c.description,
              personality: c.personality,
            })),
            plot_points: (() => {
              const sortedPoints = outline.plotPoints
                .sort((a, b) => a.order - b.order)
                .map(p => ({
                  description: p.description,
                  original_index: parseInt(p.id.replace("pp_", "")) - 1,
                }));
              // R6-2: Append selected_ending as a new plot_point at the end (do not replace any existing point)
              const selectedEndingDesc = outline.endings.find(e => e.isSelected)?.description || "";
              if (selectedEndingDesc) {
                sortedPoints.push({
                  description: selectedEndingDesc,
                  original_index: sortedPoints.length,
                });
              }
              return sortedPoints;
            })(),
            // B33: mood here is the LLM-inferred mood from outline; user_selected_mood comes from Stage A
            mood: outline.mood,
            user_selected_mood: state.userSelectedMood ?? null,
          },
        }),
      }, token);

      // RISK-T14-13-frontend: Show non-blocking warning banner if backend flagged inconsistencies
      if (confirmResponse?.inconsistency_warnings && confirmResponse.inconsistency_warnings.length > 0) {
        // eslint-disable-next-line no-console
        console.log("[StageB] handleConfirm: confirm-outline returned", confirmResponse.inconsistency_warnings.length, "inconsistency warnings");
        setWarningBanner(confirmResponse.inconsistency_warnings);
        setSubmitting(false);
        // Do NOT proceed to start-generation yet — user must acknowledge the warning first
        return;
      }

      // [StageB] Log #4 — confirm-outline OK, triggering start-generation
      // eslint-disable-next-line no-console
      console.log("[StageB] handleConfirm: confirm-outline OK → calling start-generation");

      // 2. Trigger pipeline generation
      await apiFetch(`/projects/${projectId}/start-generation`, {
        method: "POST",
      }, token);

      // [StageB] Log #5 — start-generation OK, transitioning to StageC
      // eslint-disable-next-line no-console
      console.log("[StageB] handleConfirm: start-generation OK → SET_STAGE generate");

      // 3. Transition to StageC
      dispatch({ type: "CONFIRM_OUTLINE" });
      dispatch({ type: "SET_STAGE", payload: "generate" });
    } catch (error) {
      // [StageB] Log #6 — submission error
      // eslint-disable-next-line no-console
      console.error("[StageB] handleConfirm: ERROR:", error instanceof Error ? error.message : error);
      setSubmitting(false);
      setSubmitError(error instanceof Error ? error.message : "确认大纲失败");
    }
  };

  const handleBack = () => {
    dispatch({ type: "SET_STAGE", payload: "input" });
  };

  // RISK-T14-13-frontend: User acknowledges warnings → dismiss banner and proceed to start-generation
  const handleAcknowledgeWarnings = async () => {
    const token = getStoredToken();
    const projectId = state.projectId;
    if (!token || !projectId) return;
    setWarningBanner(null);
    setSubmitting(true);
    try {
      await apiFetch(`/projects/${projectId}/start-generation`, {
        method: "POST",
      }, token);
      // eslint-disable-next-line no-console
      console.log("[StageB] handleAcknowledgeWarnings: start-generation OK → SET_STAGE generate");
      dispatch({ type: "CONFIRM_OUTLINE" });
      dispatch({ type: "SET_STAGE", payload: "generate" });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("[StageB] handleAcknowledgeWarnings: ERROR:", error instanceof Error ? error.message : error);
      setSubmitting(false);
      setSubmitError(error instanceof Error ? error.message : "启动生成失败");
    }
  };

  const handleAddPlotPoint = () => {
    const newPoint: PlotPoint = {
      id: `pp_${Date.now()}`,
      description: "",
      order: outline.plotPoints.length + 1,
    };
    dispatch({ type: "ADD_PLOT_POINT", payload: newPoint });
  };

  return (
    <main className="container-lg py-8 pb-24">
      {/* D.14 F-Lock-Family: lock banner when generation is in progress or complete */}
      {isLocked && (
        <div className="mb-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-between gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3">
            <p className="text-amber-400 text-sm">
              📌 大纲已确认，AI 正在创作画面。如需修改请新建项目
            </p>
            <button
              onClick={() => router.replace(progressUrl)}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition-colors whitespace-nowrap"
            >
              返回创作进度
            </button>
          </div>
        </div>
      )}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        {/* Back button — hidden when locked */}
        {!isLocked && (
        <button
          onClick={handleBack}
          className="flex items-center gap-1 text-text-muted hover:text-text-secondary text-sm mb-6 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          返回修改创意
        </button>
        )}

        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">确认故事大纲</h1>
          <p className="text-text-tertiary text-sm">
            可以直接确认，也可以调整后再生成
          </p>
        </div>

        <div className="space-y-8">
          {/* Outline Title & Summary */}
          <motion.section
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-bg-secondary rounded-xl p-5 border border-white/5"
          >
            <label className="text-sm font-medium text-text-secondary mb-2 block">
              故事标题
            </label>
            <input
              type="text"
              value={outline.title}
              onChange={(e) =>
                dispatch({ type: "UPDATE_OUTLINE_TITLE", payload: e.target.value })
              }
              className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-2 text-text-primary text-sm focus:outline-none focus:border-brand-primary/50 transition-colors"
            />

            <label className="text-sm font-medium text-text-secondary mt-4 mb-2 block">
              故事简介
            </label>
            <textarea
              value={outline.summary}
              onChange={(e) =>
                dispatch({ type: "UPDATE_OUTLINE_SUMMARY", payload: e.target.value })
              }
              rows={3}
              className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-2 text-text-primary text-sm resize-none focus:outline-none focus:border-brand-primary/50 transition-colors"
            />
          </motion.section>

          {/* Characters */}
          <motion.section
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <div className="flex items-center gap-2 mb-3">
              <User className="w-4 h-4 text-brand-primary" />
              <h2 className="text-sm font-medium text-text-secondary">角色设定</h2>
            </div>
            <div className="space-y-3">
              {outline.characters.map((char) => (
                <div
                  key={char.id}
                  className="bg-bg-secondary rounded-xl p-4 border border-white/5"
                >
                  {editingCharId === char.id ? (
                    <div className="space-y-3">
                      <div className="flex gap-3">
                        <div className="flex-1">
                          <label className="text-xs text-text-muted mb-1 block">姓名</label>
                          <input
                            type="text"
                            value={char.name}
                            onChange={(e) =>
                              dispatch({
                                type: "UPDATE_OUTLINE_CHARACTER",
                                payload: { id: char.id, updates: { name: e.target.value } },
                              })
                            }
                            className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-1.5 text-text-primary text-sm focus:outline-none focus:border-brand-primary/50"
                          />
                        </div>
                        <div className="flex-1">
                          <label className="text-xs text-text-muted mb-1 block">英文名</label>
                          <input
                            type="text"
                            value={char.nameEn}
                            onChange={(e) =>
                              dispatch({
                                type: "UPDATE_OUTLINE_CHARACTER",
                                payload: { id: char.id, updates: { nameEn: e.target.value } },
                              })
                            }
                            className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-1.5 text-text-primary text-sm focus:outline-none focus:border-brand-primary/50"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="text-xs text-text-muted mb-1 block">外貌描述</label>
                        <textarea
                          value={char.description}
                          onChange={(e) =>
                            dispatch({
                              type: "UPDATE_OUTLINE_CHARACTER",
                              payload: { id: char.id, updates: { description: e.target.value } },
                            })
                          }
                          rows={2}
                          className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-1.5 text-text-primary text-sm resize-none focus:outline-none focus:border-brand-primary/50"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-text-muted mb-1 block">性格</label>
                        <input
                          type="text"
                          value={char.personality}
                          onChange={(e) =>
                            dispatch({
                              type: "UPDATE_OUTLINE_CHARACTER",
                              payload: { id: char.id, updates: { personality: e.target.value } },
                            })
                          }
                          className="w-full bg-bg-primary border border-white/10 rounded-lg px-3 py-1.5 text-text-primary text-sm focus:outline-none focus:border-brand-primary/50"
                        />
                      </div>
                      <button
                        onClick={() => setEditingCharId(null)}
                        className="text-xs text-brand-primary hover:text-brand-primary/80 flex items-center gap-1"
                      >
                        <Check className="w-3 h-3" />
                        完成编辑
                      </button>
                    </div>
                  ) : (
                    <div
                      className="cursor-pointer hover:bg-white/[0.02] -m-4 p-4 rounded-xl transition-colors"
                      onClick={() => setEditingCharId(char.id)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-text-primary">
                          {char.name}
                          <span className="text-text-muted font-normal ml-2">{char.nameEn}</span>
                        </span>
                        <span className="text-[10px] text-text-muted hidden sm:inline">点击编辑</span>
                      </div>
                      <p className="text-xs text-text-tertiary">{char.description}</p>
                      <p className="text-xs text-text-muted mt-1">{char.personality}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.section>

          {/* Plot Points */}
          <motion.section
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-text-secondary">情节走向</h2>
              <button
                onClick={handleAddPlotPoint}
                className="text-xs text-brand-primary hover:text-brand-primary/80 flex items-center gap-1 transition-colors"
              >
                <Plus className="w-3 h-3" />
                新增情节点
              </button>
            </div>
            <Reorder.Group
              axis="y"
              values={outline.plotPoints}
              onReorder={(reordered) => {
                const updated = reordered.map((p, i) => ({ ...p, order: i + 1 }));
                dispatch({ type: "UPDATE_PLOT_POINTS", payload: updated });
              }}
              className="space-y-2"
            >
              {outline.plotPoints.map((point, plotIdx) => (
                <PlotPointItem
                  key={point.id}
                  point={point}
                  plotIndex={plotIdx}
                  allPlots={outline.plotPoints}
                  onDescriptionChange={(value) => {
                    const updated = outline.plotPoints.map((p) =>
                      p.id === point.id ? { ...p, description: value } : p
                    );
                    dispatch({ type: "UPDATE_PLOT_POINTS", payload: updated });
                  }}
                  onDelete={() => dispatch({ type: "DELETE_PLOT_POINT", payload: point.id })}
                />
              ))}
            </Reorder.Group>
          </motion.section>

          {/* Ending Options */}
          <motion.section
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <h2 className="text-sm font-medium text-text-secondary mb-3">结局选择</h2>
            <div className="space-y-2">
              {outline.endings.map((ending) => (
                <button
                  key={ending.id}
                  onClick={() => dispatch({ type: "SELECT_ENDING", payload: ending.id })}
                  className={`w-full text-left p-3 rounded-lg border transition-all text-sm ${
                    ending.isSelected
                      ? "border-brand-primary/50 bg-brand-primary/10 text-text-primary"
                      : "border-white/5 bg-bg-secondary text-text-tertiary hover:border-white/10"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                        ending.isSelected ? "border-brand-primary" : "border-white/20"
                      }`}
                    >
                      {ending.isSelected && (
                        <div className="w-2 h-2 rounded-full bg-brand-primary" />
                      )}
                    </div>
                    {ending.description}
                  </div>
                </button>
              ))}
            </div>
          </motion.section>

          {submitError && (
            <p className="text-center text-sm text-error">{submitError}</p>
          )}

          {/* RISK-T14-13-frontend: Inconsistency warning banner — non-blocking */}
          {warningBanner && warningBanner.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4"
            >
              <div className="flex items-start gap-3 mb-3">
                <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-300 mb-1">大纲存在以下提示</p>
                  <ul className="space-y-1">
                    {warningBanner.map((w, i) => (
                      <li key={i} className="text-xs text-amber-200/80">
                        {w.message}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setWarningBanner(null)}
                  className="text-xs px-3 py-1.5 rounded-lg text-amber-300 hover:bg-amber-500/10 transition-colors"
                >
                  返回修改
                </button>
                <button
                  onClick={handleAcknowledgeWarnings}
                  disabled={submitting}
                  className="text-xs px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 transition-colors disabled:opacity-60"
                >
                  知悉并继续
                </button>
              </div>
            </motion.div>
          )}

          {/* D.14: Confirm Button — hidden when locked; "返回创作进度" shown in banner above */}
          {!isLocked && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="pt-2"
          >
            <button
              onClick={handleConfirm}
              disabled={submitting}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3.5 text-base disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  正在创建任务...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  确认并开始生成
                </>
              )}
            </button>
            <p className="text-center text-text-muted text-xs mt-3">
              不满意？可以直接修改上方内容，也可以返回重新输入
            </p>
          </motion.div>
          )}
        </div>
      </motion.div>
    </main>
  );
}
