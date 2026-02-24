import {
  Header,
  Footer,
  HeroSection,
  ValueProposition,
  Pipeline,
  Showcase,
  Stats,
  CTASection,
} from "@/components";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <HeroSection />
        <ValueProposition />
        <Pipeline />
        <Showcase />
        <Stats />
        <CTASection />
      </main>
      <Footer openSubPagesInNewTab />
    </>
  );
}
