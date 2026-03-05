import type { Metadata } from "next";
import StoryDetailContent from "./StoryDetailContent";

export const metadata: Metadata = {
  title: "故事详情 - 序话Story",
  description: "查看故事详情和画面",
};

export default function StoryDetailPage() {
  return <StoryDetailContent />;
}
