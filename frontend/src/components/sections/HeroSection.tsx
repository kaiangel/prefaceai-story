"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { ChevronLeft, ChevronRight, Play } from "lucide-react";

const stories = [
  {
    id: "story-a",
    title: "都市亲情",
    description: "《最后一碗面》",
    images: [
      "/comics/story-a/shot_01.png",
      "/comics/story-a/shot_02.png",
      "/comics/story-a/shot_03.png",
      "/comics/story-a/shot_04.png",
    ],
  },
  {
    id: "story-b",
    title: "赛博朋克",
    description: "《最后的记忆商人》",
    images: [
      "/comics/story-b/shot_01.png",
      "/comics/story-b/shot_02.png",
      "/comics/story-b/shot_03.png",
      "/comics/story-b/shot_04.png",
    ],
  },
];

export default function HeroSection() {
  const [currentStoryIndex, setCurrentStoryIndex] = useState(0);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const resumeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const currentStory = stories[currentStoryIndex];

  // Clear pending resume timer
  const clearResumeTimer = useCallback(() => {
    if (resumeTimerRef.current) {
      clearTimeout(resumeTimerRef.current);
      resumeTimerRef.current = null;
    }
  }, []);

  // Pause autoplay and schedule resume after 5s
  const pauseAndResume = useCallback(() => {
    setIsAutoPlaying(false);
    clearResumeTimer();
    resumeTimerRef.current = setTimeout(() => setIsAutoPlaying(true), 5000);
  }, [clearResumeTimer]);

  // Cleanup resume timer on unmount
  useEffect(() => {
    return () => clearResumeTimer();
  }, [clearResumeTimer]);

  // Auto advance images
  useEffect(() => {
    if (!isAutoPlaying) return;

    const timer = setInterval(() => {
      setCurrentImageIndex((prev) => {
        if (prev >= currentStory.images.length - 1) {
          // Switch to next story
          setCurrentStoryIndex((storyIdx) => (storyIdx + 1) % stories.length);
          return 0;
        }
        return prev + 1;
      });
    }, 3500);

    return () => clearInterval(timer);
  }, [isAutoPlaying, currentStory.images.length]);

  const handleStorySwitch = useCallback((index: number) => {
    setCurrentStoryIndex(index);
    setCurrentImageIndex(0);
    pauseAndResume();
  }, [pauseAndResume]);

  const handlePrevImage = useCallback(() => {
    setCurrentImageIndex((prev) =>
      prev === 0 ? currentStory.images.length - 1 : prev - 1
    );
    pauseAndResume();
  }, [currentStory.images.length, pauseAndResume]);

  const handleNextImage = useCallback(() => {
    setCurrentImageIndex((prev) =>
      prev === currentStory.images.length - 1 ? 0 : prev + 1
    );
    pauseAndResume();
  }, [currentStory.images.length, pauseAndResume]);

  return (
    <section className="relative min-h-[100dvh] flex flex-col justify-center pt-16 overflow-hidden">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-bg-primary via-bg-primary/95 to-bg-secondary" />

      <div className="relative z-10 container-lg">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex justify-center mb-6"
        >
          <span className="inline-flex items-center gap-2 px-4 py-2 bg-bg-tertiary rounded-full text-sm text-text-secondary">
            <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
            内测申请开放中
          </span>
        </motion.div>

        {/* Main Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-4xl md:text-5xl lg:text-6xl font-bold text-center mb-3"
        >
          一句话，一个<span className="text-gradient">完整故事</span>
        </motion.h1>

        {/* English subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="text-base md:text-lg text-text-muted text-center mb-2"
        >
          Turn one sentence into a complete AI-generated story
        </motion.p>

        {/* Slogan */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-xl md:text-2xl text-text-tertiary text-center mb-8 font-serif"
        >
          FrameSpark™ AI Story Engine
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
        >
          <a href="#cta" className="btn-primary animate-glow-pulse">
            开始你的故事
          </a>
          <a href="#showcase" className="btn-secondary flex items-center gap-2">
            <Play className="w-4 h-4" />
            看看效果
          </a>
        </motion.div>

        {/* Comic Carousel */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.7 }}
          className="relative"
        >
          {/* Current Story Title */}
          <div className="text-center mb-4">
            <span className="text-text-tertiary text-sm">
              {currentStory.title}
            </span>
            <span className="mx-2 text-text-muted">|</span>
            <span className="text-text-secondary font-serif">
              {currentStory.description}
            </span>
          </div>

          {/* Image Container */}
          <div className="relative flex items-center justify-center gap-4">
            {/* Prev Button */}
            <button
              onClick={handlePrevImage}
              className="hidden md:flex absolute left-0 z-20 w-10 h-10 items-center justify-center bg-bg-tertiary/80 hover:bg-bg-elevated rounded-full transition-all duration-fast"
              aria-label="Previous image"
            >
              <ChevronLeft className="w-5 h-5 text-text-secondary" />
            </button>

            {/* Images Row - slide in from right */}
            <div className="flex gap-3 md:gap-4 overflow-hidden px-4 md:px-12 justify-center">
              <AnimatePresence mode="popLayout">
                {currentStory.images.slice(0, currentImageIndex + 1).map((src, index) => (
                  <motion.div
                    key={`${currentStory.id}-${index}`}
                    layout
                    initial={{ opacity: 0, x: 300, scale: 0.8 }}
                    animate={{
                      opacity: 1,
                      x: 0,
                      scale: index === currentImageIndex ? 1.02 : 0.95,
                    }}
                    exit={{ opacity: 0, x: -100, scale: 0.8 }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    className={`relative flex-shrink-0 w-40 md:w-56 lg:w-64 aspect-[3/4] rounded-lg overflow-hidden cursor-pointer transition-shadow duration-story ${
                      index === currentImageIndex
                        ? "ring-2 ring-brand-primary shadow-glow-md"
                        : "opacity-60"
                    }`}
                    onClick={() => {
                      setCurrentImageIndex(index);
                      pauseAndResume();
                    }}
                  >
                    <Image
                      src={src}
                      alt={`${currentStory.title} - 第${index + 1}页`}
                      fill
                      className="object-cover"
                      sizes="(max-width: 768px) 160px, (max-width: 1024px) 224px, 256px"
                      priority={index < 2}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* Next Button */}
            <button
              onClick={handleNextImage}
              className="hidden md:flex absolute right-0 z-20 w-10 h-10 items-center justify-center bg-bg-tertiary/80 hover:bg-bg-elevated rounded-full transition-all duration-fast"
              aria-label="Next image"
            >
              <ChevronRight className="w-5 h-5 text-text-secondary" />
            </button>
          </div>

          {/* Story Switcher */}
          <div className="flex justify-center gap-3 mt-6">
            {stories.map((story, index) => (
              <button
                key={story.id}
                onClick={() => handleStorySwitch(index)}
                className={`w-3 h-3 rounded-full transition-all duration-fast ${
                  index === currentStoryIndex
                    ? "bg-brand-primary scale-110"
                    : "bg-text-muted hover:bg-text-tertiary"
                }`}
                aria-label={`切换到${story.title}`}
              />
            ))}
          </div>

          {/* Progress Indicator */}
          <div className="flex justify-center gap-2 mt-4">
            {currentStory.images.map((_, index) => (
              <div
                key={index}
                className={`h-1 rounded-full transition-all duration-fast ${
                  index === currentImageIndex
                    ? "w-8 bg-brand-primary"
                    : "w-2 bg-text-muted"
                }`}
              />
            ))}
          </div>
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <div className="w-6 h-10 border-2 border-text-muted rounded-full flex justify-center">
          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-3 bg-text-muted rounded-full mt-2"
          />
        </div>
      </motion.div>
    </section>
  );
}
