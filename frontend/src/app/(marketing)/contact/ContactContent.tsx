"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, MessageCircle, MapPin, CheckCircle } from "lucide-react";
import Link from "next/link";
import PageHero from "@/components/ui/PageHero";

const contactInfo = [
  {
    icon: Mail,
    title: "邮箱",
    content: "kai@prefaceai.mov",
    sub: "工作日 24 小时内回复",
  },
  {
    icon: MessageCircle,
    title: "微信客服",
    content: "Andrea@PrefaceAI",
    sub: "微信号：xingxiwh016",
  },
  {
    icon: MapPin,
    title: "地址",
    content: "中国 · 上海",
    sub: "黄浦区黄陂南路838号中海国际",
  },
];

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

export default function ContactContent() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!form.name.trim()) {
      newErrors.name = "请输入你的名字";
    }
    if (!form.email.trim()) {
      newErrors.email = "请输入邮箱地址";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = "请输入有效的邮箱地址";
    }
    if (!form.message.trim()) {
      newErrors.message = "请输入消息内容";
    } else if (form.message.trim().length < 10) {
      newErrors.message = "消息内容至少需要10个字";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setSubmitting(false);
    setSubmitted(true);
  };

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="container-lg section-padding">
      <PageHero
        title="联系我们"
        subtitle="有任何问题或建议，我们随时倾听"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="max-w-4xl mx-auto mb-16"
      >
        <div className="text-center mb-8">
          <Link
            href="/faq"
            className="text-brand-primary hover:underline text-sm"
          >
            很多问题可能已有解答 →
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          <div className="lg:col-span-2 space-y-6">
            {contactInfo.map((info) => (
              <div key={info.title} className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-brand-primary/10 flex items-center justify-center flex-shrink-0">
                  <info.icon className="w-5 h-5 text-brand-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">{info.title}</h3>
                  <p className="text-text-secondary">{info.content}</p>
                  <p className="text-text-tertiary text-sm">{info.sub}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="lg:col-span-3">
            {submitted ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-bg-secondary rounded-xl p-8 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-success" />
                </div>
                <h3 className="text-xl font-semibold mb-2">消息已发送！</h3>
                <p className="text-text-secondary">我们会尽快回复你。</p>
              </motion.div>
            ) : (
              <form
                onSubmit={handleSubmit}
                className="bg-bg-secondary rounded-xl p-6 lg:p-8 space-y-5"
              >
                <div>
                  <input
                    type="text"
                    placeholder="你的名字"
                    value={form.name}
                    onChange={(e) => handleChange("name", e.target.value)}
                    className={`w-full bg-bg-tertiary rounded-lg px-4 py-3 text-text-primary placeholder:text-text-muted outline-none transition-colors ${
                      errors.name
                        ? "ring-2 ring-error"
                        : "focus:ring-2 focus:ring-brand-primary/50"
                    }`}
                  />
                  {errors.name && (
                    <p className="text-error text-sm mt-1">{errors.name}</p>
                  )}
                </div>

                <div>
                  <input
                    type="email"
                    placeholder="your@email.com"
                    value={form.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    className={`w-full bg-bg-tertiary rounded-lg px-4 py-3 text-text-primary placeholder:text-text-muted outline-none transition-colors ${
                      errors.email
                        ? "ring-2 ring-error"
                        : "focus:ring-2 focus:ring-brand-primary/50"
                    }`}
                  />
                  {errors.email && (
                    <p className="text-error text-sm mt-1">{errors.email}</p>
                  )}
                </div>

                <div>
                  <input
                    type="text"
                    placeholder="简要描述你的问题"
                    value={form.subject}
                    onChange={(e) => handleChange("subject", e.target.value)}
                    className="w-full bg-bg-tertiary rounded-lg px-4 py-3 text-text-primary placeholder:text-text-muted outline-none focus:ring-2 focus:ring-brand-primary/50 transition-colors"
                  />
                </div>

                <div>
                  <textarea
                    placeholder="详细描述你的问题或建议..."
                    rows={5}
                    value={form.message}
                    onChange={(e) => handleChange("message", e.target.value)}
                    className={`w-full bg-bg-tertiary rounded-lg px-4 py-3 text-text-primary placeholder:text-text-muted outline-none resize-none transition-colors ${
                      errors.message
                        ? "ring-2 ring-error"
                        : "focus:ring-2 focus:ring-brand-primary/50"
                    }`}
                  />
                  {errors.message && (
                    <p className="text-error text-sm mt-1">{errors.message}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary w-full disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {submitting ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      发送中...
                    </>
                  ) : (
                    "发送消息"
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
