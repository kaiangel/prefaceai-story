"use client";

import { motion } from "framer-motion";
import { Check, X, Crown, Zap, Sparkles } from "lucide-react";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

interface PlanFeature {
  label: string;
  free: boolean | string;
  pro: boolean | string;
  max: boolean | string;
}

const FEATURES: PlanFeature[] = [
  { label: "故事数/月", free: "1-2 个", pro: "~30 个", max: "不限" },
  { label: "篇幅", free: "仅快闪", pro: "快闪 + 短篇", max: "全部（含中篇）" },
  { label: "风格", free: "基础 3 种", pro: "全部 15 种", max: "全部 + 未来新增 + 自定义" },
  { label: "生成排队", free: "标准", pro: "优先", max: "最优先" },
  { label: "导出素材", free: true, pro: true, max: true },
  { label: "视频合成", free: false, pro: false, max: true },
  { label: "API 接口", free: false, pro: false, max: true },
  { label: "专属客服", free: false, pro: false, max: true },
];

const PLANS = [
  {
    key: "free",
    name: "Free",
    subtitle: "免费体验",
    price: "¥0",
    period: "",
    icon: Zap,
    iconColor: "text-text-muted",
    borderColor: "border-white/10",
    cta: "免费开始",
    ctaStyle: "border border-white/10 text-text-secondary hover:bg-white/5",
    ctaHref: "/#cta",
    badge: null,
  },
  {
    key: "pro",
    name: "Pro",
    subtitle: "邀请码用户专享",
    price: "¥XX",
    period: "/月",
    icon: Crown,
    iconColor: "text-accent-gold",
    borderColor: "border-brand-primary/30",
    cta: "已激活",
    ctaStyle: "bg-brand-primary text-white cursor-default opacity-80",
    ctaHref: null,
    badge: "当前方案",
  },
  {
    key: "max",
    name: "Max",
    subtitle: "专业无限",
    price: "¥XX",
    period: "/月",
    icon: Sparkles,
    iconColor: "text-accent-purple",
    borderColor: "border-accent-purple/30",
    cta: "即将推出",
    ctaStyle: "border border-accent-purple/30 text-accent-purple cursor-default opacity-60",
    ctaHref: null,
    badge: "即将推出",
  },
];

const pricingFAQ = [
  { q: "可以随时切换套餐吗？", a: "可以。升级立即生效，降级在当前计费周期结束后生效。" },
  { q: "故事额度用完了怎么办？", a: "你可以升级到更高套餐，或等待下月额度刷新。" },
  { q: "支持哪些支付方式？", a: "支持微信支付、支付宝、银行卡。企业用户可申请对公转账。" },
  { q: "有企业定制方案吗？", a: "有。如需企业级解决方案，请联系我们获取专属报价。" },
];

function FeatureCell({ value }: { value: boolean | string }) {
  if (typeof value === "string") return <span className="text-sm text-text-secondary">{value}</span>;
  return value ? <Check className="w-4 h-4 text-success mx-auto" /> : <X className="w-4 h-4 text-text-muted/30 mx-auto" />;
}

export default function PricingContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero
        title="简单透明的定价"
        subtitle="选择适合你的方案，开始创作精彩故事"
      />

      {/* Plan Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-16"
      >
        {PLANS.map((plan, idx) => (
          <motion.div
            key={plan.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + idx * 0.1 }}
            className={`relative bg-bg-secondary rounded-xl border p-6 ${plan.borderColor}`}
          >
            {plan.badge && (
              <span className={`absolute top-3 right-3 text-[10px] px-2 py-0.5 rounded-full font-medium ${
                plan.key === "pro" ? "bg-brand-primary/15 text-brand-primary" : "bg-accent-purple/15 text-accent-purple"
              }`}>
                {plan.badge}
              </span>
            )}
            <plan.icon className={`w-8 h-8 mb-3 ${plan.iconColor}`} />
            <h3 className="text-xl font-bold text-text-primary">{plan.name}</h3>
            <p className="text-xs text-text-muted mb-4">{plan.subtitle}</p>
            <div className="mb-6">
              <span className="text-3xl font-bold text-text-primary">{plan.price}</span>
              {plan.period && <span className="text-text-muted text-sm">{plan.period}</span>}
            </div>
            {plan.ctaHref ? (
              <Link href={plan.ctaHref} className={`block w-full py-2.5 rounded-lg text-sm font-medium text-center transition-colors ${plan.ctaStyle}`}>
                {plan.cta}
              </Link>
            ) : (
              <div className={`w-full py-2.5 rounded-lg text-sm font-medium text-center ${plan.ctaStyle}`}>
                {plan.cta}
              </div>
            )}
          </motion.div>
        ))}
      </motion.div>

      {/* Feature Comparison Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="max-w-4xl mx-auto mb-16"
      >
        <h2 className="text-xl font-bold text-center mb-6">功能对比</h2>
        <div className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-4 gap-4 px-4 py-3 border-b border-white/5 text-xs text-text-muted">
            <div>功能</div>
            <div className="text-center">Free</div>
            <div className="text-center text-brand-primary font-medium">Pro</div>
            <div className="text-center">Max</div>
          </div>
          {/* Rows */}
          {FEATURES.map((feat) => (
            <div key={feat.label} className="grid grid-cols-4 gap-4 px-4 py-3 border-b border-white/5 last:border-0 items-center">
              <div className="text-sm text-text-secondary">{feat.label}</div>
              <div className="text-center"><FeatureCell value={feat.free} /></div>
              <div className="text-center"><FeatureCell value={feat.pro} /></div>
              <div className="text-center"><FeatureCell value={feat.max} /></div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* FAQ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="max-w-3xl mx-auto mb-16"
      >
        <h2 className="text-xl font-bold text-center mb-6">常见问题</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pricingFAQ.map((item) => (
            <div key={item.q} className="bg-bg-secondary rounded-xl p-5">
              <h4 className="font-semibold text-sm mb-2">{item.q}</h4>
              <p className="text-text-secondary text-sm">{item.a}</p>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="text-center"
      >
        <Link href="/faq" className="text-text-tertiary hover:text-brand-primary transition-colors text-sm">
          有其他问题？查看常见问题 →
        </Link>
      </motion.div>
    </div>
  );
}
