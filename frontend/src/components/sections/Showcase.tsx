"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";

const categories = [
  { id: "all", label: "全部" },
  { id: "urban", label: "都市情感" },
  { id: "cyberpunk", label: "科幻冒险" },
  { id: "wuxia", label: "古风武侠" },
];

const works = [
  {
    id: "1",
    title: "最后一碗面",
    category: "urban",
    image: "/comics/story-a/shot_01.png",
    description: "父女亲情故事",
  },
  {
    id: "2",
    title: "最后一碗面",
    category: "urban",
    image: "/comics/story-a/shot_02.png",
    description: "父女亲情故事",
  },
  {
    id: "3",
    title: "最后一碗面",
    category: "urban",
    image: "/comics/story-a/shot_03.png",
    description: "父女亲情故事",
  },
  {
    id: "4",
    title: "最后一碗面",
    category: "urban",
    image: "/comics/story-a/shot_04.png",
    description: "父女亲情故事",
  },
  {
    id: "5",
    title: "最后的记忆商人",
    category: "cyberpunk",
    image: "/comics/story-b/shot_01.png",
    description: "赛博朋克冒险",
  },
  {
    id: "6",
    title: "最后的记忆商人",
    category: "cyberpunk",
    image: "/comics/story-b/shot_02.png",
    description: "赛博朋克冒险",
  },
  {
    id: "7",
    title: "最后的记忆商人",
    category: "cyberpunk",
    image: "/comics/story-b/shot_03.png",
    description: "赛博朋克冒险",
  },
  {
    id: "8",
    title: "最后的记忆商人",
    category: "cyberpunk",
    image: "/comics/story-b/shot_04.png",
    description: "赛博朋克冒险",
  },
];

export default function Showcase() {
  const [activeCategory, setActiveCategory] = useState("all");

  const filteredWorks =
    activeCategory === "all"
      ? works
      : works.filter((work) => work.category === activeCategory);

  return (
    <section id="showcase" className="section-padding bg-bg-secondary">
      <div className="container-lg">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            用户故事展示
          </h2>
          <p className="text-text-tertiary max-w-2xl mx-auto">
            探索由序话Story创作的精彩作品
          </p>
        </motion.div>

        {/* Category Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="flex flex-wrap justify-center gap-3 mb-10"
        >
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all duration-fast ${
                activeCategory === category.id
                  ? "bg-brand-primary text-bg-primary"
                  : "bg-bg-tertiary text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
              }`}
            >
              {category.label}
            </button>
          ))}
        </motion.div>

        {/* Works Grid */}
        <motion.div
          layout
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          <AnimatePresence mode="popLayout">
            {filteredWorks.map((work) => (
              <motion.div
                key={work.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
                className="group relative aspect-[3/4] rounded-lg overflow-hidden cursor-pointer"
              >
                <Image
                  src={work.image}
                  alt={work.title}
                  fill
                  className="object-cover transition-transform duration-slow group-hover:scale-105"
                  sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
                />

                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-bg-primary/90 via-bg-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-fast">
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <h3 className="text-lg font-semibold text-text-primary mb-1">
                      {work.title}
                    </h3>
                    <p className="text-sm text-text-tertiary">
                      {work.description}
                    </p>
                  </div>
                </div>

                {/* Category Badge */}
                <div className="absolute top-3 left-3">
                  <span className="px-2 py-1 bg-bg-primary/70 backdrop-blur-sm text-xs text-text-secondary rounded">
                    {categories.find((c) => c.id === work.category)?.label}
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>

        {/* View More */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="text-center mt-10"
        >
          <button className="btn-secondary">
            查看更多作品
          </button>
        </motion.div>
      </div>
    </section>
  );
}
