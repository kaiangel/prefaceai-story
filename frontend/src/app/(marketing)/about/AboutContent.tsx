"use client";

import { motion } from "framer-motion";
import { Sparkles, Zap, Users } from "lucide-react";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const values = [
  {
    icon: Sparkles,
    title: "创意无界",
    description:
      "支持任何类型的故事——都市情感、古装武侠、科幻冒险、童话寓言。80+种画风，从写实摄影到中国水墨，任你选择。",
  },
  {
    icon: Zap,
    title: "一键成片",
    description:
      "输入一句话创意，AI 自动完成故事构思、角色设计、分镜编排和画面生成。几分钟内交付可发布的完整作品。",
  },
  {
    icon: Users,
    title: "人人可用",
    description:
      "不需要美术基础，不需要专业软件。无论你是自媒体运营者、内容创作者还是故事爱好者，都能轻松上手。",
  },
];

export default function AboutContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero title="关于序话Story" subtitle="让每个人都能讲出精彩的故事" />

      {/* Mission */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-3xl mx-auto mb-16"
      >
        <h2 className="text-2xl font-bold mb-4">我们的使命</h2>
        <div className="text-text-secondary leading-relaxed space-y-4">
          <p>
            在AI时代，创作不应该有门槛。序话Story
            诞生于一个简单的信念：每个人心中都有一个好故事，只是缺少把它呈现出来的工具。
          </p>
          <p>
            我们将专业影视制作的完整流程——从故事构思、角色设计、分镜脚本到画面生成——封装成一句话的体验。你负责想象，我们负责实现。
          </p>
        </div>
      </motion.div>

      {/* Philosophy */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="max-w-3xl mx-auto mb-16"
      >
        <h2 className="text-2xl font-bold mb-4">
          AI时代，每个人都会讲故事
        </h2>
        <div className="text-text-secondary leading-relaxed space-y-4">
          <p>
            传统的漫画创作需要美术功底，视频制作需要专业设备和剪辑技能。序话Story
            用 AI
            消除了这些壁垒，但我们没有简化专业流程——我们让 AI 代替人完成每一个专业环节。
          </p>
          <p>
            从故事大纲到角色设计，从分镜脚本到画面渲染，每一步都遵循影视制作的最佳实践。你得到的不是&ldquo;AI感&rdquo;的草稿，而是可以直接发布的专业级作品。
          </p>
        </div>
      </motion.div>

      {/* Core Values */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16"
      >
        {values.map((value) => (
          <div
            key={value.title}
            className="bg-bg-secondary rounded-xl p-6 lg:p-8"
          >
            <div className="w-12 h-12 rounded-lg bg-brand-primary/10 flex items-center justify-center mb-4">
              <value.icon className="w-6 h-6 text-brand-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-3">{value.title}</h3>
            <p className="text-text-secondary leading-relaxed">
              {value.description}
            </p>
          </div>
        ))}
      </motion.div>

      {/* Links */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="flex flex-col sm:flex-row items-center justify-center gap-4"
      >
        <Link href="/careers" className="btn-secondary">
          查看开放职位
        </Link>
        <Link href="/contact" className="btn-secondary">
          联系我们
        </Link>
      </motion.div>
    </div>
  );
}
