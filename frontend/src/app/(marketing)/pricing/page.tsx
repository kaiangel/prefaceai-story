import { Metadata } from "next";
import PricingContent from "./PricingContent";

export const metadata: Metadata = {
  title: "定价 - 序话Story",
  description: "选择适合你的方案，Free/Pro/Max 三档定价",
};

export default function PricingPage() {
  return <PricingContent />;
}
