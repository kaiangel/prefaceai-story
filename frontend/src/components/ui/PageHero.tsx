"use client";

import { motion } from "framer-motion";

interface PageHeroProps {
  title: string;
  subtitle: string;
}

export default function PageHero({ title, subtitle }: PageHeroProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center py-12 lg:py-16"
    >
      <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">
        {title}
      </h1>
      <p className="text-text-tertiary text-lg max-w-2xl mx-auto">
        {subtitle}
      </p>
    </motion.div>
  );
}
