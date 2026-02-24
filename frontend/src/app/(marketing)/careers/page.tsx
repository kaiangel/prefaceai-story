import { Metadata } from "next";
import CareersContent from "./CareersContent";

export const metadata: Metadata = {
  title: "加入我们 - 序话Story",
  description: "和我们一起，用AI重新定义故事创作",
};

export default function CareersPage() {
  return <CareersContent />;
}
