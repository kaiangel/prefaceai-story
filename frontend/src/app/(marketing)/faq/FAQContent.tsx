"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";
import FAQAccordion from "@/components/ui/FAQAccordion";

const faqData = [
  {
    category: "产品相关",
    items: [
      {
        question: "序话Story 是什么？",
        answer:
          "序话Story 是一个 AI 驱动的条漫和短视频创作平台。你只需要输入一句话创意，系统会自动生成完整的故事——包括角色设计、分镜编排和画面渲染，最终输出可直接发布的作品。",
      },
      {
        question: "支持哪些类型的故事？",
        answer:
          "几乎所有类型！都市情感、古装武侠、科幻冒险、童话寓言、悬疑推理、家庭生活……系统支持80+种画风和任意角色类型（人类、动物、奇幻生物等）。",
      },
      {
        question: "生成一个故事需要多长时间？",
        answer:
          "通常3-5分钟即可完成一个完整的条漫故事（6-15张图）。复杂的多章节故事可能需要更长时间。",
      },
      {
        question: "我可以自定义角色外观吗？",
        answer:
          "可以。Pro 及以上套餐支持自定义角色设定，包括外貌特征、服装风格等。系统会确保角色在所有画面中保持一致。",
      },
    ],
  },
  {
    category: "账号相关",
    items: [
      {
        question: "如何注册账号？",
        answer:
          "目前序话Story 处于内测阶段，需要邀请码才能注册。你可以在首页申请内测资格，我们会在24小时内审核并发送邀请码。",
      },
      {
        question: "忘记密码怎么办？",
        answer:
          "内测期间使用邀请码登录，无需密码。正式版将支持邮箱/手机号注册和密码找回。",
      },
      {
        question: "可以同时在多个设备使用吗？",
        answer: "可以。你的账号可以在电脑和手机上同时登录使用。",
      },
    ],
  },
  {
    category: "创作相关",
    items: [
      {
        question: "如何提升生成质量？",
        answer:
          "在输入创意时，尽量描述具体的场景、人物和情绪。比如把\"一个爱情故事\"改为\"咖啡店里，一个戴眼镜的程序员和一个画家的偶遇\"。加上画风偏好（如\"日系温暖插画风\"）效果更好。",
      },
      {
        question: "生成的内容可以商用吗？",
        answer:
          "Pro 及以上套餐生成的内容可用于商业用途，包括社交媒体发布、内容营销等。具体条款请查看使用条款。",
      },
      {
        question: "不满意的画面可以重新生成吗？",
        answer:
          "可以。在预览阶段，你可以对任意单张画面点击\"重新生成\"，系统会保持角色一致性的同时重新创作该画面。",
      },
      {
        question: "支持导出哪些格式？",
        answer:
          "条漫支持 PNG/JPG 图片序列导出，可选择适配抖音（2:3）、小红书（3:4）等平台的尺寸。视频模式支持 MP4 格式导出。",
      },
    ],
  },
  {
    category: "付费相关",
    items: [
      {
        question: "Free 套餐有什么限制？",
        answer:
          "Free 套餐每月可创作2个故事，支持3种基础画风，单章节（≤6张图），标准分辨率。适合体验产品功能。",
      },
      {
        question: "如何升级套餐？",
        answer:
          "在账号设置中选择目标套餐，支持微信支付和支付宝。升级立即生效，按剩余天数折算差价。",
      },
      {
        question: "年付方案可以退款吗？",
        answer:
          "购买后7天内且未使用额度的情况下，可申请全额退款。超过7天按已使用月份折算退款。",
      },
      {
        question: "发票可以开具吗？",
        answer:
          "可以。支持开具增值税普通发票和专用发票，在账号设置中提交开票信息即可。",
      },
    ],
  },
];

export default function FAQContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero
        title="常见问题"
        subtitle="关于序话Story，你想知道的都在这里"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-3xl mx-auto space-y-10 mb-16"
      >
        {faqData.map((section) => (
          <FAQAccordion
            key={section.category}
            category={section.category}
            items={section.items}
          />
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="flex flex-col sm:flex-row items-center justify-center gap-4"
      >
        <Link href="/contact" className="btn-primary">
          没找到答案？联系我们
        </Link>
        <Link href="/pricing" className="btn-secondary">
          查看定价方案
        </Link>
      </motion.div>
    </div>
  );
}
