"use client";

import { forwardRef } from "react";

interface InviteCodeInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
}

const InviteCodeInput = forwardRef<HTMLInputElement, InviteCodeInputProps>(
  ({ value, onChange, error, disabled }, ref) => {
    return (
      <div>
        <input
          ref={ref}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value.toUpperCase())}
          placeholder="请输入邀请码"
          disabled={disabled}
          className={`w-full bg-bg-tertiary rounded-lg px-4 py-3 text-center text-lg tracking-widest text-text-primary placeholder:text-text-muted placeholder:tracking-normal outline-none transition-colors disabled:opacity-50 ${
            error
              ? "ring-2 ring-error"
              : "focus:ring-2 focus:ring-brand-primary/50"
          }`}
        />
        {error && (
          <p className="text-error text-sm mt-2 text-center">{error}</p>
        )}
      </div>
    );
  }
);

InviteCodeInput.displayName = "InviteCodeInput";

export default InviteCodeInput;
