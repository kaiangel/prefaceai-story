import { Metadata } from "next";
import ContactContent from "./ContactContent";

export const metadata: Metadata = {
  title: "联系我们 - 序话Story",
  description: "有任何问题或建议，我们随时倾听",
};

export default function ContactPage() {
  return <ContactContent />;
}
