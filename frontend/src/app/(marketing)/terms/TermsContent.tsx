"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const sections = [
  { id: "service", title: "1. 服务说明", content: `序话Story（以下简称\u201c本平台\u201d）是由序话科技提供的AI驱动条漫和短视频创作服务。使用本平台即表示你同意遵守以下条款。` },
  { id: "account", title: "2. 账号注册与使用", content: "2.1 你需要通过邀请码注册账号才能使用本平台的完整功能。\n\n2.2 你有责任保管好自己的账号信息，因账号泄露导致的损失由你自行承担。\n\n2.3 每个邀请码仅限注册一个账号，不得转让或出售。" },
  { id: "ip", title: "3. 内容创作与知识产权", content: "3.1 你通过本平台创作的内容，其知识产权归属如下：\n• Free 套餐：创作内容可用于个人非商业用途\n• Pro/Max 套餐：创作内容可用于商业用途，你拥有完整的使用权\n\n3.2 你输入的创意文本、角色设定等原始素材的知识产权归你所有。\n\n3.3 你不得使用本平台创作违反法律法规的内容，包括但不限于：涉及暴力、色情、歧视、侵权的内容。\n\n3.4 本平台保留对违规内容进行删除和对违规账号进行封禁的权利。" },
  { id: "payment", title: "4. 付费服务", content: "4.1 本平台提供 Free、Pro、Max 三个套餐等级，具体权益以定价页面展示为准。\n\n4.2 付费套餐以自然月为计费周期，到期后自动续费，你可随时取消自动续费。\n\n4.3 退款政策：购买后7天内且未使用额度的情况下，可申请全额退款。\n\n4.4 平台保留调整价格的权利，价格变更会提前30天通知现有付费用户。" },
  { id: "conduct", title: "5. 用户行为规范", content: "5.1 不得利用技术手段绕过系统限制（如额度限制、生成频率限制）。\n\n5.2 不得对平台进行反向工程、爬虫抓取或其他未授权的技术操作。\n\n5.3 不得使用本平台生成侵犯他人知识产权、肖像权或隐私权的内容。" },
  { id: "disclaimer", title: "6. 免责声明", content: "6.1 AI 生成的内容可能存在不准确或不适当的情况，本平台不对生成内容的准确性承担责任。\n\n6.2 因不可抗力（包括但不限于网络故障、系统维护、自然灾害）导致的服务中断，本平台不承担责任。\n\n6.3 本平台不对因使用生成内容所产生的任何直接或间接损失承担责任。" },
  { id: "changes", title: "7. 条款修改", content: "本平台保留随时修改本条款的权利。修改后的条款将在本页面公布，继续使用本平台即表示你同意修改后的条款。重大变更会通过邮件或站内通知的方式告知。" },
  { id: "contact", title: "8. 联系方式", content: "如对本条款有任何疑问，请联系：kai@prefaceai.mov" },
];

export default function TermsContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero title="使用条款" subtitle="最后更新：2026年2月14日" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-3xl mx-auto"
      >
        <nav className="mb-10 p-6 bg-bg-secondary rounded-xl">
          <h2 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider mb-3">目录</h2>
          <ul className="space-y-2">
            {sections.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`} className="text-text-secondary hover:text-brand-primary transition-colors text-sm">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="space-y-10">
          {sections.map((s) => (
            <section key={s.id} id={s.id}>
              <h2 className="text-xl font-bold mb-4">{s.title}</h2>
              <div className="text-text-secondary leading-relaxed whitespace-pre-line">
                {s.content}
              </div>
            </section>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link href="/privacy" className="btn-secondary">
            查看隐私政策
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
