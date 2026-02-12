"use client";

import { motion } from "framer-motion";
import { Sparkles, BookOpen, Palette, Camera, ImageIcon, Video } from "lucide-react";

const stages = [
  {
    number: 1,
    title: "故事大纲",
    description: "AI理解你的创意，生成角色和情节框架",
    icon: BookOpen,
  },
  {
    number: 2,
    title: "角色设计",
    description: "生成详细的角色外貌、服装、性格设定",
    icon: Palette,
  },
  {
    number: 3,
    title: "分镜脚本",
    description: "专业镜头语言：景别、角度、构图全自动",
    icon: Camera,
  },
  {
    number: 4,
    title: "画面生成",
    description: "高质量图像生成，角色100%一致性保证",
    icon: ImageIcon,
  },
  {
    number: 5,
    title: "成品输出",
    description: "条漫/短视频双形态，即刻可发布",
    icon: Video,
  },
];

export default function Pipeline() {
  return (
    <section id="pipeline" className="section-padding bg-bg-primary">
      <div className="container-lg">
        {/* Brand Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex justify-center mb-6"
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-bg-secondary rounded-full text-brand-primary font-medium">
            <Sparkles className="w-4 h-4" />
            FrameSpark™
          </span>
        </motion.div>

        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-center mb-12 lg:mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            五阶段故事引擎
          </h2>
          <p className="text-text-tertiary max-w-2xl mx-auto">
            从一句话创意到可发布作品，全程自动化，无需专业技能
          </p>
        </motion.div>

        {/* Pipeline Stages */}
        <div className="relative">
          {/* Connection Line (Desktop) */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-bg-tertiary to-transparent -translate-y-1/2" />

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: { staggerChildren: 0.1 },
              },
            }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 lg:gap-6"
          >
            {stages.map((stage, index) => (
              <motion.div
                key={stage.number}
                variants={{
                  hidden: { opacity: 0, y: 30 },
                  visible: {
                    opacity: 1,
                    y: 0,
                    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
                  },
                }}
                className="relative"
              >
                {/* Stage Card */}
                <div className="relative bg-bg-secondary rounded-xl p-5 lg:p-6 border-l-3 border-brand-primary hover:bg-bg-tertiary transition-colors duration-fast">
                  {/* Stage Number */}
                  <div className="absolute -left-3 top-5 w-6 h-6 rounded-full bg-brand-primary flex items-center justify-center text-sm font-bold text-bg-primary">
                    {stage.number}
                  </div>

                  {/* Icon */}
                  <div className="w-10 h-10 rounded-lg bg-brand-primary/10 flex items-center justify-center mb-3 ml-3">
                    <stage.icon className="w-5 h-5 text-brand-primary" />
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-semibold text-text-primary mb-2 ml-3">
                    {stage.title}
                  </h3>
                  <p className="text-sm text-text-tertiary leading-relaxed ml-3">
                    {stage.description}
                  </p>
                </div>

                {/* Arrow (Desktop) */}
                {index < stages.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-6 -translate-y-1/2 z-10">
                    <div className="w-0 h-0 border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent border-l-[8px] border-l-brand-primary/50" />
                  </div>
                )}
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="text-center text-text-muted mt-10 font-serif italic"
        >
          &ldquo;专业能力平民化，让每个人都能做电影&rdquo;
        </motion.p>
      </div>
    </section>
  );
}
