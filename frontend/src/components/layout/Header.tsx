"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Menu, X } from "lucide-react";

export default function Header() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isMobileMenuOpen]);

  const navItems = [
    { label: "功能", href: "#features" },
    { label: "作品", href: "#showcase" },
    { label: "技术", href: "#pipeline" },
    { label: "联系", href: "#cta" },
  ];

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed top-0 left-0 right-0 z-50 h-16 transition-all duration-normal ${
        isScrolled
          ? "bg-bg-primary/95 backdrop-blur-md border-b border-bg-tertiary"
          : "bg-transparent"
      }`}
    >
      <div className="container-lg h-full flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2 group">
          <Sparkles className="w-6 h-6 text-brand-primary transition-transform duration-fast group-hover:rotate-12" />
          <span className="text-xl font-bold text-text-primary">
            序话<span className="text-brand-primary">Story</span>
          </span>
        </a>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="text-text-secondary hover:text-brand-primary transition-colors duration-fast"
            >
              {item.label}
            </a>
          ))}
        </nav>

        {/* CTA Button */}
        <div className="hidden md:block">
          <a
            href="#cta"
            className="btn-primary text-sm"
          >
            申请内测
          </a>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2 text-text-secondary hover:text-text-primary transition-colors"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="md:hidden absolute top-16 left-0 right-0 bg-bg-secondary border-b border-bg-tertiary"
        >
          <nav className="container-lg py-4 flex flex-col gap-4">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                className="text-text-secondary hover:text-brand-primary transition-colors duration-fast py-2"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <a
              href="#cta"
              className="btn-primary text-sm mt-2"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              申请内测
            </a>
          </nav>
        </motion.div>
      )}
    </motion.header>
  );
}
