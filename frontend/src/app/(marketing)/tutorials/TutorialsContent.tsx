"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const steps = [
  {
    number: "01",
    title: "输入你的创意",
    description:
      `用一句话描述你想要的故事。比如\u201c一个程序员在深夜便利店遇到了童年好友\u201d。越具体越好，但简单的灵感也能创作出精彩故事。`,
    tip: `小技巧：加上情绪基调（如\u201c温馨的\u201d\u201c悬疑的\u201d）能让故事更有方向感`,
  },
  {
    number: "02",
    title: "AI 自动创作",
    description:
      "系统会自动完成故事构思、角色设计、分镜脚本编排。你可以在故事大纲阶段预览和调整角色设定、情节走向，确认后 AI 会生成全部画面。",
    tip: "整个过程只需几分钟，你可以在等待时预览故事结构",
  },
  {
    number: "03",
    title: "预览和发布",
    description:
      "生成完成后，你可以预览完整的条漫作品。对某个画面不满意？可以单独重新生成。满意后一键导出，直接发布到抖音、小红书等平台。",
    tip: "导出时可选择适配不同平台的尺寸和格式",
  },
];

export default function TutorialsContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero title="使用教程" subtitle="3步开始你的创作之旅" />

      <div className="max-w-3xl mx-auto space-y-8 mb-16">
        {steps.map((step, index) => (
          <motion.div
            key={step.number}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + index * 0.1 }}
            className="bg-bg-secondary rounded-xl p-6 lg:p-8"
          >
            <div className="flex items-start gap-4">
              <span className="text-4xl font-bold text-brand-primary/30 leading-none">
                {step.number}
              </span>
              <div className="flex-1">
                <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                <p className="text-text-secondary leading-relaxed mb-4">
                  {step.description}
                </p>
                <p className="text-sm text-brand-primary/80 bg-brand-primary/5 rounded-lg px-4 py-2">
                  {step.tip}
                </p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="flex flex-col sm:flex-row items-center justify-center gap-4"
      >
        <Link href="/#cta" className="btn-primary">
          开始创作
        </Link>
        <Link href="/faq" className="btn-secondary">
          查看常见问题
        </Link>
      </motion.div>
    </div>
  );
}
