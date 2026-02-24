"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const sections = [
  { id: "collection", title: "1. 信息收集", content: "我们可能收集以下类型的信息：\n\n1.1 账号信息：邮箱地址、用户名（注册时提供）。\n\n1.2 创作内容：你输入的创意文本、生成的故事内容和图片。\n\n1.3 使用数据：访问时间、使用功能、设备信息、浏览器类型。\n\n1.4 支付信息：支付方式（我们不直接存储银行卡号或支付密码，由第三方支付平台处理）。" },
  { id: "usage", title: "2. 信息使用", content: "我们收集的信息用于：\n\n2.1 提供和改进服务功能。\n\n2.2 处理你的订单和支付。\n\n2.3 发送产品更新和服务通知（你可随时取消订阅）。\n\n2.4 分析产品使用情况，优化用户体验。\n\n2.5 防范安全风险，保护用户权益。" },
  { id: "storage", title: "3. 信息存储与安全", content: "3.1 你的数据存储在位于中国境内的安全服务器上。\n\n3.2 我们采用行业标准的加密技术（SSL/TLS）保护数据传输安全。\n\n3.3 我们定期进行安全审计，确保数据安全措施的有效性。\n\n3.4 你的创作内容默认仅你本人可见，不会未经授权对外公开。" },
  { id: "sharing", title: "4. 信息共享", content: "我们不会出售你的个人信息。以下情况除外：\n\n4.1 经你明确同意的情况。\n\n4.2 法律法规要求或政府部门依法要求的情况。\n\n4.3 与合作的第三方服务提供商共享必要信息（如支付处理），且要求其遵守同等的隐私保护标准。" },
  { id: "cookies", title: "5. Cookie 使用", content: "5.1 我们使用 Cookie 来记住你的登录状态和偏好设置。\n\n5.2 你可以通过浏览器设置管理 Cookie，但禁用 Cookie 可能影响部分功能使用。" },
  { id: "rights", title: "6. 用户权利", content: "你有权：\n\n6.1 访问和导出你的个人数据。\n\n6.2 更正不准确的个人信息。\n\n6.3 删除你的账号和相关数据（注销后30天内数据将被永久删除）。\n\n6.4 撤回授权同意（可能影响部分服务使用）。" },
  { id: "minors", title: "7. 未成年人保护", content: "7.1 本平台不面向14周岁以下的未成年人提供服务。\n\n7.2 如我们发现收集了未成年人的信息，将立即删除相关数据。" },
  { id: "updates", title: "8. 政策更新", content: "我们可能不时更新本隐私政策。重大更新会通过邮件或站内通知告知你。继续使用本平台即表示你接受更新后的隐私政策。" },
  { id: "contact", title: "9. 联系方式", content: "如对本隐私政策有任何疑问，请联系：privacy@xuhuastory.com" },
];

export default function PrivacyContent() {
  return (
    <div className="container-lg section-padding">
      <PageHero title="隐私政策" subtitle="最后更新：2026年2月14日" />

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
          <Link href="/terms" className="btn-secondary">
            查看使用条款
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
