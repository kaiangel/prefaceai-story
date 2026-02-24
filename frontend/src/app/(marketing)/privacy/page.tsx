import { Metadata } from "next";
import PrivacyContent from "./PrivacyContent";

export const metadata: Metadata = {
  title: "隐私政策 - 序话Story",
  description: "序话Story 隐私保护政策",
};

export default function PrivacyPage() {
  return <PrivacyContent />;
}
