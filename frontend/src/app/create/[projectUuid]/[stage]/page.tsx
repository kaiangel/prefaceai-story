import { Metadata } from "next";
import { notFound } from "next/navigation";
import { CreateProvider } from "@/contexts/CreateContext";
import CreateContent from "../../CreateContent";
import { isUrlStage } from "@/lib/createUrl";

export const metadata: Metadata = {
  title: "继续创作 - 序话Story",
  description: "继续编辑你的故事 — 大纲 / 角色 / 场景 / 预览 / 交付",
};

interface PageProps {
  // Next.js 14 App Router: params is a Promise in newer versions; we destructure
  // and stay compatible with both shapes by typing it as `any` boundary.
  params: Promise<{ projectUuid: string; stage: string }>;
}

export default async function CreateStagePage({ params }: PageProps) {
  const { projectUuid, stage } = await params;

  // UX-16: Hard 404 for unknown stage segments — prevents URL fuzzing from rendering an empty page.
  if (!isUrlStage(stage)) {
    notFound();
  }

  return (
    <CreateProvider>
      <CreateContent urlProjectUuid={projectUuid} urlStage={stage} />
    </CreateProvider>
  );
}
