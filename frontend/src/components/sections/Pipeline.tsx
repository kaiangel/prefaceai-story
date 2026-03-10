"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export default function Pipeline() {
  return (
    <section id="pipeline" className="section-padding bg-bg-primary relative overflow-hidden">
      {/* Ambient glow effects */}
      <div className="absolute inset-0 pointer-events-none">
        <motion.div
          animate={{
            opacity: [0.15, 0.3, 0.15],
            scale: [1, 1.1, 1],
          }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(var(--brand-primary-rgb),0.12) 0%, rgba(var(--brand-primary-rgb),0.03) 50%, transparent 70%)",
          }}
        />
        <motion.div
          animate={{
            opacity: [0.08, 0.18, 0.08],
            scale: [1.1, 1, 1.1],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute top-1/3 left-1/4 w-[400px] h-[400px] rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(var(--brand-gradient-end-rgb),0.1) 0%, transparent 60%)",
          }}
        />
        <motion.div
          animate={{
            opacity: [0.06, 0.14, 0.06],
            scale: [1, 1.15, 1],
          }}
          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 4 }}
          className="absolute bottom-1/3 right-1/4 w-[350px] h-[350px] rounded-full"
          style={{
            background: "radial-gradient(circle, rgba(var(--brand-cta-rgb),0.08) 0%, transparent 60%)",
          }}
        />
      </div>

      <div className="container-lg relative z-10">
        {/* Brand Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex justify-center mb-8"
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-bg-secondary rounded-full text-brand-primary font-medium">
            <Sparkles className="w-4 h-4" />
            AI Story Engine
          </span>
        </motion.div>

        {/* Brand Name - Large Display */}
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-5xl md:text-7xl lg:text-8xl font-bold text-center mb-6 tracking-tight"
        >
          <span className="text-gradient">FrameSpark</span>
          <span className="text-text-tertiary font-light">™</span>
        </motion.h2>

        {/* Slogan */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-xl md:text-2xl lg:text-3xl text-text-secondary text-center mb-10 font-serif"
        >
          每个人都有自己的故事
        </motion.p>

        {/* Horizontal light sweep line */}
        <motion.div
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto max-w-md h-px mb-10"
          style={{
            background: "linear-gradient(90deg, transparent, rgba(var(--brand-primary-rgb),0.5), transparent)",
          }}
        />

        {/* Core message */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.7 }}
          className="text-center text-text-tertiary max-w-lg mx-auto text-lg leading-relaxed mb-6"
        >
          一句话变成完整故事，不需要任何技术技能
        </motion.p>

        {/* Tech Stack Tags */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.9 }}
          className="flex flex-wrap justify-center gap-3 mb-10"
        >
          {["Powered by Google Gemini", "LLM Narrative Generation", "AI Image Synthesis", "Multi-modal AI"].map((tag) => (
            <span
              key={tag}
              className="px-3 py-1.5 rounded-full text-xs border border-white/10 text-text-muted bg-white/[0.03]"
            >
              {tag}
            </span>
          ))}
        </motion.div>

        {/* Demo Video */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 1.0 }}
          className="max-w-3xl mx-auto mb-10"
        >
          <video
            src="/demo.mp4"
            controls
            playsInline
            preload="metadata"
            poster=""
            className="w-full rounded-xl border border-white/10 shadow-lg"
          >
            Your browser does not support the video tag.
          </video>
          <p className="text-center text-text-muted text-xs mt-3">Product Demo — From idea to finished story in minutes</p>
        </motion.div>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 1.2 }}
          className="text-center text-text-muted font-serif italic"
        >
          &ldquo;专业能力平民化，让每个人都能做电影&rdquo;
        </motion.p>
      </div>
    </section>
  );
}
