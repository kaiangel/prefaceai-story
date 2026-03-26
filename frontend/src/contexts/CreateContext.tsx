"use client";

import { createContext, useContext, useReducer, type ReactNode, type Dispatch } from "react";
import type { CreateState, CreateAction } from "@/types/create";

const initialState: CreateState = {
  currentStage: "input",
  // Stage A
  idea: "",
  documentFile: null,
  documentText: "",
  length: "short",
  aspectRatio: "2:3",
  stylePreset: "korean_webtoon",
  customStyleImage: null,
  customStyleImageUrl: null,
  customStyleKeywords: [],
  customStyleAnalysis: null,
  characters: [],
  scenes: [],
  // Stage B
  outline: null,
  outlineConfirmed: false,
  // Stage C: Generation + Checkpoints
  generationStatus: "idle",
  generationProgress: 0,
  generationMessage: "",
  generationLog: [],
  generationSubPhase: "text-gen",
  previewCharacters: [],
  previewScenes: [],
  charactersConfirmed: false,
  scenesConfirmed: false,
  shots: [],
  // Stage D
  bgm: null,
  // Stage E
  deliveryFormat: "comic",
  // Continuation
  continuationMode: null,
  continuationPrompt: "",
  previousStoryId: null,
};

function createReducer(state: CreateState, action: CreateAction): CreateState {
  switch (action.type) {
    case "SET_STAGE":
      return { ...state, currentStage: action.payload };

    case "SET_IDEA":
      return { ...state, idea: action.payload };

    case "SET_DOCUMENT":
      return { ...state, documentFile: action.payload.file, documentText: action.payload.text };

    case "SET_LENGTH":
      return {
        ...state,
        length: action.payload,
        // Reset continuation if not epic
        continuationMode: action.payload === "epic" ? state.continuationMode : null,
        continuationPrompt: action.payload === "epic" ? state.continuationPrompt : "",
      };

    case "SET_ASPECT_RATIO":
      return { ...state, aspectRatio: action.payload };

    case "SET_STYLE_PRESET":
      // Mutually exclusive: preset clears custom
      return {
        ...state,
        stylePreset: action.payload,
        customStyleImage: action.payload ? null : state.customStyleImage,
        customStyleImageUrl: action.payload ? null : state.customStyleImageUrl,
        customStyleKeywords: action.payload ? [] : state.customStyleKeywords,
      };

    case "SET_CUSTOM_STYLE":
      // Mutually exclusive: custom clears preset
      return {
        ...state,
        customStyleImage: action.payload.image,
        customStyleImageUrl: action.payload.imageUrl,
        customStyleKeywords: action.payload.keywords,
        customStyleAnalysis: action.payload.analysis ?? null,
        stylePreset: action.payload.image ? null : state.stylePreset,
      };

    case "ADD_CHARACTER":
      if (state.characters.length >= 5) return state;
      return { ...state, characters: [...state.characters, action.payload] };

    case "REMOVE_CHARACTER":
      return { ...state, characters: state.characters.filter((c) => c.id !== action.payload) };

    case "UPDATE_CHARACTER":
      return {
        ...state,
        characters: state.characters.map((c) =>
          c.id === action.payload.id ? { ...c, ...action.payload.updates } : c
        ),
      };

    case "ADD_SCENE":
      if (state.scenes.length >= 8) return state;
      return { ...state, scenes: [...state.scenes, action.payload] };

    case "REMOVE_SCENE":
      return { ...state, scenes: state.scenes.filter((s) => s.id !== action.payload) };

    case "SET_OUTLINE":
      return { ...state, outline: action.payload, outlineConfirmed: false };

    case "CONFIRM_OUTLINE":
      return { ...state, outlineConfirmed: true };

    case "UPDATE_OUTLINE_TITLE":
      if (!state.outline) return state;
      return { ...state, outline: { ...state.outline, title: action.payload } };

    case "UPDATE_OUTLINE_SUMMARY":
      if (!state.outline) return state;
      return { ...state, outline: { ...state.outline, summary: action.payload } };

    case "UPDATE_OUTLINE_CHARACTER":
      if (!state.outline) return state;
      return {
        ...state,
        outline: {
          ...state.outline,
          characters: state.outline.characters.map((c) =>
            c.id === action.payload.id ? { ...c, ...action.payload.updates } : c
          ),
        },
      };

    case "UPDATE_PLOT_POINTS":
      if (!state.outline) return state;
      return { ...state, outline: { ...state.outline, plotPoints: action.payload } };

    case "ADD_PLOT_POINT":
      if (!state.outline) return state;
      return {
        ...state,
        outline: {
          ...state.outline,
          plotPoints: [...state.outline.plotPoints, action.payload],
        },
      };

    case "DELETE_PLOT_POINT":
      if (!state.outline) return state;
      return {
        ...state,
        outline: {
          ...state.outline,
          plotPoints: state.outline.plotPoints.filter((p) => p.id !== action.payload),
        },
      };

    case "SELECT_ENDING":
      if (!state.outline) return state;
      return {
        ...state,
        outline: {
          ...state.outline,
          endings: state.outline.endings.map((e) => ({
            ...e,
            isSelected: e.id === action.payload,
          })),
        },
      };

    case "SET_MOOD":
      if (!state.outline) return state;
      return { ...state, outline: { ...state.outline, mood: action.payload } };

    case "SET_GENERATION_SUB_PHASE":
      return { ...state, generationSubPhase: action.payload };

    case "SET_PREVIEW_CHARACTERS":
      return { ...state, previewCharacters: action.payload };

    case "SET_PREVIEW_SCENES":
      return { ...state, previewScenes: action.payload };

    case "UPDATE_PREVIEW_CHARACTER":
      return {
        ...state,
        previewCharacters: state.previewCharacters.map((c) =>
          c.id === action.payload.id ? { ...c, ...action.payload.updates } : c
        ),
      };

    case "UPDATE_PREVIEW_SCENE":
      return {
        ...state,
        previewScenes: state.previewScenes.map((s) =>
          s.id === action.payload.id ? { ...s, userEdit: action.payload.userEdit } : s
        ),
      };

    case "CONFIRM_CHARACTERS":
      return { ...state, charactersConfirmed: true };

    case "CONFIRM_SCENES":
      return { ...state, scenesConfirmed: true };

    case "START_GENERATION":
      return { ...state, generationStatus: "generating", generationProgress: 0, generationMessage: "", generationLog: [] };

    case "UPDATE_GENERATION_PROGRESS":
      return {
        ...state,
        generationProgress: action.payload.progress,
        generationMessage: action.payload.message,
        generationLog: [
          ...state.generationLog,
          { timestamp: Date.now(), message: action.payload.message, progress: action.payload.progress },
        ],
      };

    case "GENERATION_COMPLETE":
      return { ...state, generationStatus: "complete", generationProgress: 100, shots: action.payload };

    case "GENERATION_ERROR":
      return { ...state, generationStatus: "error", generationMessage: action.payload };

    case "UPDATE_SHOT_TEXT":
      return {
        ...state,
        shots: state.shots.map((s) =>
          s.shotId === action.payload.shotId
            ? {
                ...s,
                [action.payload.field]: action.payload.value,
              }
            : s
        ),
      };

    case "REGENERATE_SHOT":
      return {
        ...state,
        shots: state.shots.map((s) =>
          s.shotId === action.payload ? { ...s, imageUrl: null } : s
        ),
      };

    case "DELETE_SHOT":
      return {
        ...state,
        shots: state.shots.filter((s) => s.shotId !== action.payload),
      };

    case "SET_BGM":
      return { ...state, bgm: action.payload };

    case "SET_DELIVERY_FORMAT":
      return { ...state, deliveryFormat: action.payload };

    case "SET_CONTINUATION_MODE":
      return { ...state, continuationMode: action.payload };

    case "SET_CONTINUATION_PROMPT":
      return { ...state, continuationPrompt: action.payload };

    case "RESET":
      return initialState;

    default:
      return state;
  }
}

interface CreateContextValue {
  state: CreateState;
  dispatch: Dispatch<CreateAction>;
}

const CreateContext = createContext<CreateContextValue | null>(null);

export function CreateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(createReducer, initialState);

  return (
    <CreateContext.Provider value={{ state, dispatch }}>
      {children}
    </CreateContext.Provider>
  );
}

export function useCreate(): CreateContextValue {
  const ctx = useContext(CreateContext);
  if (!ctx) throw new Error("useCreate must be used within CreateProvider");
  return ctx;
}
