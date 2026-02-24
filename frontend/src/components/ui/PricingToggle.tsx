"use client";

import { motion } from "framer-motion";

interface PricingToggleProps {
  isYearly: boolean;
  onChange: (isYearly: boolean) => void;
}

export default function PricingToggle({ isYearly, onChange }: PricingToggleProps) {
  return (
    <div className="flex items-center justify-center gap-3">
      <span
        className={`text-sm font-medium transition-colors ${
          !isYearly ? "text-text-primary" : "text-text-tertiary"
        }`}
      >
        月付
      </span>
      <button
        onClick={() => onChange(!isYearly)}
        className="relative w-14 h-7 rounded-full bg-bg-tertiary transition-colors"
        aria-label="切换月付/年付"
      >
        <motion.div
          className="absolute top-0.5 w-6 h-6 rounded-full bg-brand-primary"
          animate={{ left: isYearly ? "calc(100% - 1.625rem)" : "0.125rem" }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
        />
      </button>
      <span
        className={`text-sm font-medium transition-colors ${
          isYearly ? "text-text-primary" : "text-text-tertiary"
        }`}
      >
        年付
      </span>
      {isYearly && (
        <motion.span
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-xs font-medium text-success bg-success/10 px-2 py-0.5 rounded-full"
        >
          省25%
        </motion.span>
      )}
    </div>
  );
}
