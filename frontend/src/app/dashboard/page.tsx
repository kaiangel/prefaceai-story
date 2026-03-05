import type { Metadata } from "next";
import DashboardContent from "./DashboardContent";

export const metadata: Metadata = {
  title: "工作台 - 序话Story",
  description: "管理你的故事创作，查看历史作品",
};

export default function DashboardPage() {
  return <DashboardContent />;
}
