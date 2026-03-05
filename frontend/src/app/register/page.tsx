import type { Metadata } from "next";
import RegisterContent from "./RegisterContent";

export const metadata: Metadata = {
  title: "注册 - 序话Story",
  description: "创建你的序话Story账户，开始AI创作之旅",
};

export default function RegisterPage() {
  return <RegisterContent />;
}
