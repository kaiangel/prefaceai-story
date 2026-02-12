"use client";

import { motion } from "framer-motion";
import { Zap, Users, Film } from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "即发即用",
    description: "标题+文案+图片+BGM，完成即可发布到抖音/小红书/视频号",
    highlight: "完成即发布",
  },
  {
    icon: Users,
    title: "角色如一",
    description: "至多可保持6人在不同场景中的一致性",
    highlight: "6人一致",
  },
  {
    icon: Film,
    title: "双输出形式",
    description: "条漫素材包或完整视频，任你选择下载",
    highlight: "任你选择",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export default function ValueProposition() {
  return (
    <section id="features" className="section-padding bg-bg-secondary">
      <div className="container-lg">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            为什么选择<span className="text-gradient">序话Story</span>
          </h2>
          <p className="text-text-tertiary max-w-2xl mx-auto">
            我们重新定义了AI创作的标准，让每个人都能轻松创作专业级作品
          </p>
        </motion.div>

        {/* Feature Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              className="group relative bg-bg-tertiary rounded-xl p-6 lg:p-8 transition-all duration-fast hover:-translate-y-1 hover:shadow-lg"
            >
              {/* Icon */}
              <div className="w-12 h-12 rounded-lg bg-brand-primary/10 flex items-center justify-center mb-4 group-hover:bg-brand-primary/20 transition-colors duration-fast">
                <feature.icon className="w-6 h-6 text-brand-primary" />
              </div>

              {/* Title */}
              <h3 className="text-xl font-semibold text-text-primary mb-3">
                {feature.title}
              </h3>

              {/* Description */}
              <p className="text-text-secondary leading-relaxed">
                {feature.description}
              </p>

              {/* Highlight Badge */}
              <div className="mt-4">
                <span className="inline-block px-3 py-1 bg-brand-primary/10 text-brand-primary text-sm rounded-full">
                  {feature.highlight}
                </span>
              </div>

              {/* Decorative corner */}
              <div className="absolute top-0 right-0 w-16 h-16 overflow-hidden rounded-tr-xl">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-brand-primary/5 to-transparent -translate-y-16 translate-x-16 group-hover:translate-y-0 group-hover:translate-x-0 transition-transform duration-slow" />
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
