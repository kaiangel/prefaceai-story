import { Metadata } from "next";
import AboutContent from "./AboutContent";

export const metadata: Metadata = {
  title: "关于我们 - 序话Story",
  description: "AI时代，每个人都会讲故事",
};

export default function AboutPage() {
  return <AboutContent />;
}
