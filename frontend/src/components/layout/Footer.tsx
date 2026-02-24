import { Sparkles } from "lucide-react";
import Link from "next/link";

const footerLinks = {
  product: {
    title: "产品",
    links: [
      { label: "功能介绍", href: "/#features" },
      { label: "作品展示", href: "/#showcase" },
      { label: "定价", href: "/pricing" },
    ],
  },
  support: {
    title: "支持",
    links: [
      { label: "帮助中心", href: "/help" },
      { label: "使用教程", href: "/tutorials" },
      { label: "常见问题", href: "/faq" },
    ],
  },
  company: {
    title: "关于",
    links: [
      { label: "关于我们", href: "/about" },
      { label: "联系我们", href: "/contact" },
      { label: "加入我们", href: "/careers" },
    ],
  },
  legal: {
    title: "法律",
    links: [
      { label: "使用条款", href: "/terms" },
      { label: "隐私政策", href: "/privacy" },
    ],
  },
};

interface FooterProps {
  openSubPagesInNewTab?: boolean;
}

export default function Footer({ openSubPagesInNewTab = false }: FooterProps) {
  const isAnchorLink = (href: string) => href.startsWith("/#");

  return (
    <footer className="bg-bg-primary border-t border-bg-tertiary">
      <div className="container-lg py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Logo & Description */}
          <div className="col-span-2 md:col-span-4 lg:col-span-1 mb-8 lg:mb-0">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <Sparkles className="w-6 h-6 text-brand-primary" />
              <span className="text-xl font-bold text-text-primary">
                序话<span className="text-brand-primary">Story</span>
              </span>
            </Link>
            <p className="text-text-tertiary text-sm leading-relaxed">
              AI驱动的条漫和短视频创作平台，让每个人都能轻松创作专业级作品。
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([key, section]) => (
            <div key={key}>
              <h3 className="text-text-primary font-semibold mb-4">
                {section.title}
              </h3>
              <ul className="space-y-3">
                {section.links.map((link) => {
                  const linkClass =
                    "text-text-tertiary hover:text-brand-primary transition-colors duration-fast text-sm";

                  if (isAnchorLink(link.href)) {
                    return (
                      <li key={link.label}>
                        <a href={link.href} className={linkClass}>
                          {link.label}
                        </a>
                      </li>
                    );
                  }

                  if (openSubPagesInNewTab) {
                    return (
                      <li key={link.label}>
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={linkClass}
                        >
                          {link.label}
                        </a>
                      </li>
                    );
                  }

                  return (
                    <li key={link.label}>
                      <Link href={link.href} className={linkClass}>
                        {link.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-bg-tertiary flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-text-muted text-sm">
            © 2026 序话Story. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-muted hover:text-brand-primary transition-colors"
              aria-label="Twitter"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
            <a
              href="https://weibo.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-text-muted hover:text-brand-primary transition-colors"
              aria-label="Weibo"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M10.098 20.323c-3.977.391-7.414-1.406-7.672-4.02-.259-2.609 2.759-5.047 6.74-5.441 3.979-.394 7.413 1.404 7.671 4.018.259 2.6-2.759 5.049-6.739 5.443zM9.05 17.219c-.384.616-1.208.884-1.829.602-.612-.279-.793-.991-.406-1.593.379-.595 1.176-.861 1.793-.601.622.263.82.972.442 1.592zm1.27-1.627c-.141.237-.449.353-.689.253-.236-.09-.313-.361-.177-.586.138-.227.436-.346.672-.24.239.09.315.36.194.573zm.176-2.719c-1.893-.493-4.033.45-4.857 2.118-.838 1.692-.145 3.56 1.608 4.163 1.822.625 4.063-.249 4.857-1.946.784-1.672.082-3.83-1.608-4.335z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
