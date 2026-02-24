import { Metadata } from "next";
import HelpContent from "./HelpContent";

export const metadata: Metadata = {
  title: "帮助中心 - 序话Story",
  description: "快速找到你需要的答案",
};

export default function HelpPage() {
  return <HelpContent />;
}
