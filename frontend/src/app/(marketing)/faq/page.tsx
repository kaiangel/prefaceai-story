import { Metadata } from "next";
import FAQContent from "./FAQContent";

export const metadata: Metadata = {
  title: "常见问题 - 序话Story",
  description: "关于序话Story，你想知道的都在这里",
};

export default function FAQPage() {
  return <FAQContent />;
}
