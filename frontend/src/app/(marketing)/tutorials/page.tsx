import { Metadata } from "next";
import TutorialsContent from "./TutorialsContent";

export const metadata: Metadata = {
  title: "使用教程 - 序话Story",
  description: "3步开始你的创作之旅",
};

export default function TutorialsPage() {
  return <TutorialsContent />;
}
