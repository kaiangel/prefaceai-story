"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

const categories = [
  { id: "all", label: "全部" },
  { id: "urban", label: "都市情感" },
  { id: "cyberpunk", label: "科幻冒险" },
];

interface StoryGroup {
  id: string;
  title: string;
  category: string;
  description: string;
  images: string[];
}

const storyGroups: StoryGroup[] = [
  {
    id: "story-a",
    title: "最后一碗面",
    category: "urban",
    description: "父女亲情故事",
    images: [
      "/comics/story-a/shot_01.png",
      "/comics/story-a/shot_02.png",
      "/comics/story-a/shot_03.png",
      "/comics/story-a/shot_04.png",
    ],
  },
  {
    id: "story-b",
    title: "最后的记忆商人",
    category: "cyberpunk",
    description: "赛博朋克冒险",
    images: [
      "/comics/story-b/shot_01.png",
      "/comics/story-b/shot_02.png",
      "/comics/story-b/shot_03.png",
      "/comics/story-b/shot_04.png",
    ],
  },
];

// Flatten for grid display
const works = storyGroups.flatMap((group) =>
  group.images.map((image, index) => ({
    id: `${group.id}-${index}`,
    title: group.title,
    category: group.category,
    image,
    description: group.description,
    storyId: group.id,
    imageIndex: index,
  }))
);

export default function Showcase() {
  const [activeCategory, setActiveCategory] = useState("all");
  const [lightbox, setLightbox] = useState<{
    storyId: string;
    imageIndex: number;
  } | null>(null);

  const filteredWorks =
    activeCategory === "all"
      ? works
      : works.filter((work) => work.category === activeCategory);

  const currentStoryGroup = lightbox
    ? storyGroups.find((g) => g.id === lightbox.storyId)
    : null;

  const openLightbox = useCallback((storyId: string, imageIndex: number) => {
    setLightbox({ storyId, imageIndex });
  }, []);

  const closeLightbox = useCallback(() => {
    setLightbox(null);
  }, []);

  const goToPrev = useCallback(() => {
    if (!lightbox || !currentStoryGroup) return;
    setLightbox((prev) => {
      if (!prev) return null;
      const newIndex =
        prev.imageIndex === 0
          ? currentStoryGroup.images.length - 1
          : prev.imageIndex - 1;
      return { ...prev, imageIndex: newIndex };
    });
  }, [lightbox, currentStoryGroup]);

  const goToNext = useCallback(() => {
    if (!lightbox || !currentStoryGroup) return;
    setLightbox((prev) => {
      if (!prev) return null;
      const newIndex =
        prev.imageIndex === currentStoryGroup.images.length - 1
          ? 0
          : prev.imageIndex + 1;
      return { ...prev, imageIndex: newIndex };
    });
  }, [lightbox, currentStoryGroup]);

  // Keyboard navigation
  useEffect(() => {
    if (!lightbox) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowLeft") goToPrev();
      if (e.key === "ArrowRight") goToNext();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [lightbox, closeLightbox, goToPrev, goToNext]);

  // Lock body scroll when lightbox open
  useEffect(() => {
    if (lightbox) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [lightbox]);

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
            更多创作可能
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
                onClick={() => openLightbox(work.storyId, work.imageIndex)}
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

      {/* Lightbox Modal */}
      <AnimatePresence>
        {lightbox && currentStoryGroup && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-bg-primary/95 backdrop-blur-sm"
            onClick={closeLightbox}
          >
            {/* Close button */}
            <button
              onClick={closeLightbox}
              className="absolute top-4 right-4 z-50 w-11 h-11 sm:w-10 sm:h-10 flex items-center justify-center bg-bg-tertiary/80 hover:bg-bg-elevated rounded-full transition-colors duration-fast"
              aria-label="关闭"
            >
              <X className="w-5 h-5 text-text-secondary" />
            </button>

            {/* Story info */}
            <div className="absolute top-4 left-4 z-50">
              <h3 className="text-lg font-semibold text-text-primary">
                {currentStoryGroup.title}
              </h3>
              <p className="text-sm text-text-tertiary">
                {lightbox.imageIndex + 1} / {currentStoryGroup.images.length}
              </p>
            </div>

            {/* Prev button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToPrev();
              }}
              className="absolute left-2 sm:left-4 z-50 w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center bg-bg-tertiary/60 hover:bg-bg-elevated rounded-full transition-colors duration-fast"
              aria-label="上一张"
            >
              <ChevronLeft className="w-6 h-6 text-text-secondary" />
            </button>

            {/* Image */}
            <motion.div
              key={`${lightbox.storyId}-${lightbox.imageIndex}`}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="relative w-full max-w-lg mx-4 sm:mx-16 aspect-[3/4]"
              onClick={(e) => e.stopPropagation()}
            >
              <Image
                src={currentStoryGroup.images[lightbox.imageIndex]}
                alt={`${currentStoryGroup.title} - 第${lightbox.imageIndex + 1}页`}
                fill
                className="object-contain rounded-lg"
                sizes="(max-width: 768px) 100vw, 512px"
                priority
              />
            </motion.div>

            {/* Next button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToNext();
              }}
              className="absolute right-2 sm:right-4 z-50 w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center bg-bg-tertiary/60 hover:bg-bg-elevated rounded-full transition-colors duration-fast"
              aria-label="下一张"
            >
              <ChevronRight className="w-6 h-6 text-text-secondary" />
            </button>

            {/* Dots */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
              {currentStoryGroup.images.map((_, index) => (
                <button
                  key={index}
                  onClick={(e) => {
                    e.stopPropagation();
                    setLightbox((prev) =>
                      prev ? { ...prev, imageIndex: index } : null
                    );
                  }}
                  className={`w-3 h-3 sm:w-2.5 sm:h-2.5 rounded-full transition-all duration-fast ${
                    index === lightbox.imageIndex
                      ? "bg-brand-primary scale-110"
                      : "bg-text-muted hover:bg-text-tertiary"
                  }`}
                  aria-label={`跳转到第${index + 1}页`}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
