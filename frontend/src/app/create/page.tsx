import { Metadata } from "next";
import { CreateProvider } from "@/contexts/CreateContext";
import CreateContent from "./CreateContent";

export const metadata: Metadata = {
  title: "开始创作 - 序话Story",
  description: "输入你的故事创意，选择风格和篇幅，AI帮你生成完整条漫",
};

export default function CreatePage() {
  return (
    <CreateProvider>
      <CreateContent />
    </CreateProvider>
  );
}
