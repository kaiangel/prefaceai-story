"use client";

import { motion } from "framer-motion";
import { Briefcase } from "lucide-react";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const jobs = [
  {
    title: "全栈工程师",
    type: "全职 · 深圳",
    description:
      "负责产品核心功能开发，参与前后端架构设计。熟悉 Python/TypeScript，有 AI 应用开发经验者优先。",
    mailto: "mailto:hr@prefaceai.mov?subject=应聘全栈工程师",
  },
  {
    title: "AI/ML 工程师",
    type: "全职 · 深圳/远程",
    description:
      "负责图像生成模型优化、Prompt 工程和角色一致性算法。熟悉 Diffusion Models / LLM 应用开发，有多模态 AI 经验者优先。",
    mailto: "mailto:hr@prefaceai.mov?subject=应聘AI/ML工程师",
  },
  {
    title: "产品运营",
    type: "全职 · 深圳",
    description:
      "负责产品在抖音、小红书等平台的内容运营和用户增长。有短视频运营经验，了解 AIGC 行业者优先。",
    mailto: "mailto:hr@prefaceai.mov?subject=应聘产品运营",
  },
];

export default function CareersContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero
        title="加入我们"
        subtitle="和我们一起，用AI重新定义故事创作"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-3xl mx-auto mb-16"
      >
        <h2 className="text-2xl font-bold mb-4">为什么加入序话Story？</h2>
        <div className="text-text-secondary leading-relaxed space-y-4">
          <p>
            我们是一支小而精的团队，相信 AI
            能让创作变得更民主化。在这里，你会和一群对技术和创意充满热情的人一起工作，共同打造下一代内容创作工具。
          </p>
          <p>我们重视：</p>
          <ul className="list-disc list-inside space-y-1 text-text-secondary">
            <li>
              <strong>自驱力</strong> — 发现问题，解决问题，不等指令
            </li>
            <li>
              <strong>创造力</strong> — 用最优雅的方案解决最复杂的问题
            </li>
            <li>
              <strong>用户思维</strong> — 一切以用户体验为出发点
            </li>
          </ul>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="max-w-3xl mx-auto space-y-6 mb-16"
      >
        <h2 className="text-2xl font-bold mb-6">开放职位</h2>
        {jobs.map((job) => (
          <div
            key={job.title}
            className="bg-bg-secondary rounded-xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Briefcase className="w-4 h-4 text-brand-primary" />
                <h3 className="text-lg font-semibold">{job.title}</h3>
              </div>
              <p className="text-sm text-text-tertiary mb-2">{job.type}</p>
              <p className="text-text-secondary text-sm">{job.description}</p>
            </div>
            <a href={job.mailto} className="btn-primary text-sm whitespace-nowrap">
              了解详情
            </a>
          </div>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="text-center space-y-4"
      >
        <p className="text-text-tertiary">
          没有匹配的职位？发送简历到{" "}
          <a
            href="mailto:hr@prefaceai.mov"
            className="text-brand-primary hover:underline"
          >
            hr@prefaceai.mov
          </a>
          ，我们始终欢迎优秀的人才。
        </p>
        <Link href="/about" className="btn-secondary inline-block">
          了解更多关于我们
        </Link>
      </motion.div>
    </div>
  );
}
