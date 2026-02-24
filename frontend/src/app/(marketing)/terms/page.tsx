import { Metadata } from "next";
import TermsContent from "./TermsContent";

export const metadata: Metadata = {
  title: "使用条款 - 序话Story",
  description: "序话Story 服务使用条款",
};

export default function TermsPage() {
  return <TermsContent />;
}
