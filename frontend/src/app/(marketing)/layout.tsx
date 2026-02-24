import SubPageHeader from "@/components/layout/SubPageHeader";
import Footer from "@/components/layout/Footer";

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SubPageHeader />
      <main className="min-h-screen bg-bg-primary">{children}</main>
      <Footer />
    </>
  );
}
