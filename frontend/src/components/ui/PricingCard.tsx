"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import Link from "next/link";

interface PricingCardProps {
  name: string;
  description: string;
  monthlyPrice: number;
  yearlyPrice: number;
  isYearly: boolean;
  features: string[];
  cta: string;
  ctaHref: string;
  recommended?: boolean;
}

export default function PricingCard({
  name,
  description,
  monthlyPrice,
  yearlyPrice,
  isYearly,
  features,
  cta,
  ctaHref,
  recommended,
}: PricingCardProps) {
  const price = isYearly ? yearlyPrice : monthlyPrice;
  const monthlyEquivalent = isYearly && yearlyPrice > 0
    ? Math.round((yearlyPrice / 12) * 100) / 100
    : null;

  return (
    <div
      className={`relative rounded-2xl p-6 lg:p-8 flex flex-col ${
        recommended
          ? "bg-gradient-to-b from-brand-primary/10 to-bg-secondary ring-2 ring-brand-primary"
          : "bg-bg-secondary"
      }`}
    >
      {recommended && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-primary text-bg-primary text-xs font-bold px-3 py-1 rounded-full">
          最受欢迎
        </span>
      )}

      <div className="mb-6">
        <h3 className="text-xl font-bold mb-1">{name}</h3>
        <p className="text-text-tertiary text-sm">{description}</p>
      </div>

      <div className="mb-6">
        <div className="flex items-baseline gap-1">
          <span className="text-sm text-text-tertiary">¥</span>
          <motion.span
            key={price}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold"
          >
            {isYearly && yearlyPrice > 0
              ? yearlyPrice.toLocaleString()
              : monthlyPrice}
          </motion.span>
          <span className="text-text-tertiary text-sm">
            /{isYearly ? "年" : "月"}
          </span>
        </div>
        {monthlyEquivalent && (
          <p className="text-text-tertiary text-sm mt-1">
            约 ¥{monthlyEquivalent}/月
          </p>
        )}
      </div>

      <Link
        href={ctaHref}
        className={`block text-center py-3 rounded-lg font-medium transition-all mb-6 ${
          recommended
            ? "btn-primary"
            : "bg-bg-tertiary hover:bg-bg-elevated text-text-primary"
        }`}
      >
        {cta}
      </Link>

      <ul className="space-y-3 flex-1">
        {features.map((feature) => (
          <li key={feature} className="flex items-start gap-3 text-sm">
            <Check className="w-4 h-4 text-brand-primary flex-shrink-0 mt-0.5" />
            <span className="text-text-secondary">{feature}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
