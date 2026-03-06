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
  Palette,
} from "lucide-react";
import { useCreate } from "@/contexts/CreateContext";
import { MOOD_OPTIONS } from "@/types/create";
import type { PlotPoint } from "@/types/create";

function PlotPointItem({
  point,
  onDescriptionChange,
  onDelete,
}: {
  point: PlotPoint;
  onDescriptionChange: (value: string) => void;
  onDelete: () => void;
}) {
  const controls = useDragControls();

  return (
    <Reorder.Item
      value={point}
      dragListener={false}
      dragControls={controls}
      className="flex items-start gap-2 bg-bg-secondary rounded-lg p-3 border border-white/5 group"
    >
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
    </Reorder.Item>
  );
}

export default function StageB() {
  const { state, dispatch } = useCreate();
  const { outline } = state;
  const [editingCharId, setEditingCharId] = useState<string | null>(null);

  if (!outline) return null;

  const handleConfirm = () => {
    dispatch({ type: "CONFIRM_OUTLINE" });
    dispatch({ type: "SET_STAGE", payload: "generate" });
  };

  const handleBack = () => {
    dispatch({ type: "SET_STAGE", payload: "input" });
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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-2xl mx-auto"
      >
        {/* Back button */}
        <button
          onClick={handleBack}
          className="flex items-center gap-1 text-text-muted hover:text-text-secondary text-sm mb-6 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          返回修改创意
        </button>

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
              {outline.plotPoints.map((point) => (
                <PlotPointItem
                  key={point.id}
                  point={point}
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

          {/* Mood Selector */}
          <motion.section
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Palette className="w-4 h-4 text-brand-primary" />
              <h2 className="text-sm font-medium text-text-secondary">
                情绪基调
                <span className="text-text-muted font-normal ml-1">（可选）</span>
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {MOOD_OPTIONS.map((mood) => (
                <button
                  key={mood}
                  onClick={() =>
                    dispatch({
                      type: "SET_MOOD",
                      payload: outline.mood === mood ? "" : mood,
                    })
                  }
                  className={`px-3 py-1.5 rounded-full text-xs border transition-all ${
                    outline.mood === mood
                      ? "border-brand-primary/50 bg-brand-primary/10 text-brand-primary"
                      : "border-white/10 text-text-muted hover:border-white/20"
                  }`}
                >
                  {mood}
                </button>
              ))}
            </div>
          </motion.section>

          {/* Confirm Button */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="pt-2"
          >
            <button
              onClick={handleConfirm}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3.5 text-base"
            >
              <Sparkles className="w-4 h-4" />
              确认并开始生成
            </button>
            <p className="text-center text-text-muted text-xs mt-3">
              不满意？可以直接修改上方内容，也可以返回重新输入
            </p>
          </motion.div>
        </div>
      </motion.div>
    </main>
  );
}
