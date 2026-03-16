"use client";

import { motion } from "framer-motion";
import { Sparkles, Zap, Users, Github } from "lucide-react";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const values = [
  {
    icon: Sparkles,
    title: "你的画面，任何风格",
    description:
      "都市黄昏、古镇晨雾、星际远航——你脑子里的画面是什么风格，它就是什么风格。80+ 种视觉风格，从写实摄影到中国水墨。",
  },
  {
    icon: Zap,
    title: "说出来就够了",
    description:
      "你不需要学剪辑，不需要画分镜。说出你看见的画面，剩下的——故事构思、角色设计、分镜编排、画面生成——系统全部完成。",
  },
  {
    icon: Users,
    title: "每个人天生会讲故事",
    description:
      "三岁的孩子就会讲故事。你需要的不是美术基础或专业软件，是一个让脑海里的画面走出来的出口。",
  },
];

const team = [
  {
    name: "Kai Sun",
    nameCn: "",
    role: "Founder & CEO",
    roleCn: "创始人 & CEO",
    photo: "/team/kai.jpg",
    bio: [
      "连续创业者（Simple Fresh 创始人、商灯创始人、小羊医生 CPO）",
      "2022年底开始深度使用 ChatGPT，并交叉使用 Claude、Gemini、Perplexity 等主流 AI 工具，对 Prompt Engineering 有行业内领先的深刻理解",
      "擅长从0到1构建产品，具备出色的用户增长、市场营销及产品战略规划能力",
    ],
    github: "https://github.com/kaiangel",
  },
  {
    name: "Ben Li",
    nameCn: "",
    role: "Co-founder & CTO",
    roleCn: "联合创始人 & CTO",
    photo: "/team/ben.jpg",
    bio: [
      "58安居客 3年资深架构师",
      "车轮互联 7~8年 AI 智能路考项目产品技术负责人，项目从0到上亿级年收入",
      "曾技术参与创业 2年，拿过 2 轮机构投资",
      "擅长构建稳定、高效且可扩展的技术架构，具备丰富的 AI 和 NLP 领域经验",
    ],
    github: "",
  },
  {
    name: "Amy Wu",
    nameCn: "",
    role: "Co-founder & Head of Marketing",
    roleCn: "联合创始人 & 市场运营负责人",
    photo: "/team/amy.jpg",
    bio: [
      "前 FanBook 运营负责人",
      "擅长挖掘创意、勇于开拓创新，凭借丰富的市场运营经验推动产品在市场中脱颖而出",
    ],
    github: "",
  },
];

export default function AboutContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero title="关于序话Story" subtitle="致每一个脑子里装满画面的人" />

      {/* Mission — V2 Brand Manifesto */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-2xl mx-auto mb-16"
      >
        <h2 className="text-2xl font-bold mb-1">我们的使命</h2>
        <p className="text-sm text-text-muted mb-8">Our Mission</p>
        <div className="text-text-secondary leading-relaxed space-y-8">
          <div className="space-y-3">
            <p>你脑海里有一个画面。</p>
            <p>也许是很久以前的一个下午。也许是你编出来的一个故事。也许只是一个模糊的感觉——一种光线，一个表情，一句没说出口的话。</p>
            <p className="text-text-primary font-medium">你看得见它。</p>
            <p className="text-text-primary font-medium">很清楚。</p>
            <p>但你没办法让别人也看见。</p>
          </div>

          <div className="space-y-3">
            <p>你试过。</p>
            <p>你试过用文字描述它——但文字太慢了，等你写完，那个画面已经凉了。</p>
            <p>你试过画出来——但手跟不上脑子。</p>
            <p>你试过拍出来——但现实里找不到那个光线、那个角度、那个恰到好处的表情。</p>
            <p>于是那个画面，就留在了你脑子里。</p>
            <p>和你之前的一千个画面一样。</p>
          </div>

          <div className="space-y-3">
            <p>我们脑子里装满了没人看过的电影。</p>
            <p>不是因为它们不够好。</p>
            <p>是因为它们没有出口。</p>
          </div>

          <div className="space-y-3">
            <p>序话Story 做的事情很简单。</p>
            <p>你说出来。</p>
            <p>它让所有人看见。</p>
          </div>
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
          想象力，不该被困住
        </h2>
        <div className="text-text-secondary leading-relaxed space-y-4">
          <p>
            从想象到可见，中间隔着一道鸿沟。
          </p>
          <p>
            画家用画笔跨越它，导演用摄影机跨越它，作家用文字跨越它——但这些跨越方式，都需要几年到几十年的训练。
          </p>
          <p>
            序话Story 做的，是第一次让这个跨越不需要任何训练。
          </p>
          <p>
            你只需要会讲故事。而你天生就会。
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

      {/* Team */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.42 }}
        className="max-w-4xl mx-auto mb-16"
      >
        <h2 className="text-2xl font-bold mb-1">核心团队</h2>
        <p className="text-sm text-text-muted mb-2">Our Team</p>
        <p className="text-text-tertiary text-sm mb-8">
          一支兼具 AI 技术深度和产品商业化经验的创始团队
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {team.map((member, i) => (
            <motion.div
              key={member.name}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 + i * 0.1 }}
              className="bg-bg-secondary rounded-xl p-6 border border-white/5"
            >
              <img
                src={member.photo}
                alt={member.name}
                className="w-20 h-20 rounded-full object-cover mb-4 border-2 border-white/10"
              />
              <div className="mb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold">{member.name}</h3>
                  {member.github && (
                    <a
                      href={member.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-text-muted hover:text-brand-primary transition-colors"
                      aria-label={`${member.name} GitHub`}
                    >
                      <Github className="w-4 h-4" />
                    </a>
                  )}
                </div>
                {member.nameCn && (
                  <p className="text-sm text-text-muted">{member.nameCn}</p>
                )}
                <p className="text-sm text-brand-primary mt-1">{member.roleCn}</p>
              </div>
              <ul className="space-y-2">
                {member.bio.map((line, j) => (
                  <li
                    key={j}
                    className="text-sm text-text-secondary leading-relaxed flex gap-2"
                  >
                    <span className="text-text-muted mt-1.5 flex-shrink-0">·</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Tech Foundation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="text-center mb-16"
      >
        <h2 className="text-xl font-bold mb-1">技术基座</h2>
        <p className="text-sm text-text-muted mb-6">Powered By</p>
        <p className="text-text-tertiary text-sm mb-6">
          基于前沿 AI 技术，让想象力真正落地
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {["Powered by Google Gemini", "LLM Narrative Generation", "AI Image Synthesis", "Multi-modal AI Pipeline"].map((tag) => (
            <span
              key={tag}
              className="px-3 py-1.5 rounded-full text-xs border border-white/10 text-text-muted bg-white/[0.03]"
            >
              {tag}
            </span>
          ))}
        </div>
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
