"use client";

import { motion } from "framer-motion";
import { BookOpen, Lightbulb, Settings, HelpCircle } from "lucide-react";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const categories = [
  {
    icon: BookOpen,
    title: "入门指南",
    description: "从注册到创作第一个故事，手把手教你上手",
    href: "/tutorials",
  },
  {
    icon: Lightbulb,
    title: "创作技巧",
    description: "如何写出更好的创意提示，提升作品质量",
    href: "/tutorials",
  },
  {
    icon: Settings,
    title: "账号管理",
    description: "套餐升级、密码修改、账号设置相关问题",
    href: "/faq",
  },
  {
    icon: HelpCircle,
    title: "常见问题",
    description: "最常被问到的问题和解答",
    href: "/faq",
  },
];

export default function HelpContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero title="帮助中心" subtitle="快速找到你需要的答案" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto mb-16"
      >
        {categories.map((cat) => (
          <Link
            key={cat.title}
            href={cat.href}
            className="group bg-bg-secondary rounded-xl p-6 hover:-translate-y-1 transition-all duration-fast hover:shadow-lg"
          >
            <div className="w-12 h-12 rounded-lg bg-brand-primary/10 flex items-center justify-center mb-4 group-hover:bg-brand-primary/20 transition-colors">
              <cat.icon className="w-6 h-6 text-brand-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">{cat.title}</h3>
            <p className="text-text-tertiary text-sm">{cat.description}</p>
          </Link>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-center"
      >
        <p className="text-text-tertiary mb-4">找不到答案？直接联系我们</p>
        <Link href="/contact" className="btn-primary">
          联系我们
        </Link>
      </motion.div>
    </div>
  );
}
