import { Metadata } from "next";
import LoginContent from "./LoginContent";

export const metadata: Metadata = {
  title: "登录 - 序话Story",
  description: "输入邀请码开始创作",
};

export default function LoginPage() {
  return <LoginContent />;
}
