"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";
import PricingToggle from "@/components/ui/PricingToggle";
import PricingCard from "@/components/ui/PricingCard";

const plans = [
  {
    name: "Free",
    description: "免费体验",
    monthlyPrice: 0,
    yearlyPrice: 0,
    cta: "免费开始",
    ctaHref: "/#cta",
    features: [
      "每月 2 个故事额度",
      "基础画风（3种）",
      "单章节故事（≤6张图）",
      "标准分辨率输出",
      "社区支持",
    ],
  },
  {
    name: "Pro",
    description: "创作者之选",
    monthlyPrice: 49,
    yearlyPrice: 441,
    cta: "立即订阅",
    ctaHref: "/#cta",
    recommended: true,
    features: [
      "每月 20 个故事额度",
      "全部画风（80+种）",
      "多章节故事（≤3章，每章≤15张图）",
      "高分辨率输出",
      "角色一致性增强",
      "自定义角色设定",
      "优先生成队列",
      "邮件支持",
    ],
  },
  {
    name: "Max",
    description: "专业无限",
    monthlyPrice: 149,
    yearlyPrice: 1341,
    cta: "联系我们",
    ctaHref: "/contact",
    features: [
      "无限故事额度",
      "全部画风 + 自定义风格",
      "无限章节",
      "超高分辨率输出",
      "角色一致性增强 Pro",
      "自定义角色 + 场景库",
      "最高优先生成",
      "视频导出功能",
      "API 接入",
      "专属客服 + 1对1支持",
    ],
  },
];

const pricingFAQ = [
  {
    q: "可以随时切换套餐吗？",
    a: "可以。升级立即生效，降级在当前计费周期结束后生效。",
  },
  {
    q: "故事额度用完了怎么办？",
    a: "你可以升级到更高套餐，或等待下月额度刷新。Free 用户也可以单独购买额外额度。",
  },
  {
    q: "支持哪些支付方式？",
    a: "支持微信支付、支付宝、银行卡。企业用户可申请对公转账。",
  },
  {
    q: "有企业定制方案吗？",
    a: "有。如需企业级解决方案，请联系我们获取专属报价。",
  },
];

export default function PricingContent() {
  const [isYearly, setIsYearly] = useState(false);

  return (
    <div className="container-lg section-padding">
      <PageHero
        title="简单透明的定价"
        subtitle="选择适合你的方案，开始创作精彩故事"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-10"
      >
        <PricingToggle isYearly={isYearly} onChange={setIsYearly} />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-20"
      >
        {plans.map((plan) => (
          <PricingCard key={plan.name} {...plan} isYearly={isYearly} />
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="max-w-3xl mx-auto mb-16"
      >
        <h2 className="text-2xl font-bold text-center mb-8">定价常见问题</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {pricingFAQ.map((item) => (
            <div key={item.q} className="bg-bg-secondary rounded-xl p-5">
              <h4 className="font-semibold mb-2">{item.q}</h4>
              <p className="text-text-secondary text-sm">
                {item.q === "有企业定制方案吗？" ? (
                  <>
                    有。如需企业级解决方案，请
                    <Link href="/contact" className="text-brand-primary hover:underline">
                      联系我们
                    </Link>
                    获取专属报价。
                  </>
                ) : (
                  item.a
                )}
              </p>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-center"
      >
        <Link href="/faq" className="text-text-tertiary hover:text-brand-primary transition-colors text-sm">
          有其他问题？查看常见问题 →
        </Link>
      </motion.div>
    </div>
  );
}
