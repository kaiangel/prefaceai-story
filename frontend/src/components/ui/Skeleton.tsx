"use client";

export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`bg-bg-tertiary rounded-lg animate-pulse ${className}`} />;
}

export function StoryCardSkeleton() {
  return (
    <div className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden">
      <SkeletonBlock className="aspect-[3/4]" />
      <div className="p-3 space-y-2">
        <SkeletonBlock className="h-4 w-3/4" />
        <SkeletonBlock className="h-3 w-1/2" />
      </div>
    </div>
  );
}

export function StoryGridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <StoryCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function StoryDetailSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-4">
        <SkeletonBlock className="aspect-[2/3] max-w-sm mx-auto rounded-xl" />
        <div className="flex gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonBlock key={i} className="w-14 h-20 rounded-md flex-shrink-0" />
          ))}
        </div>
      </div>
      <div className="space-y-4">
        <SkeletonBlock className="h-6 w-3/4" />
        <SkeletonBlock className="h-4 w-full" />
        <SkeletonBlock className="h-4 w-2/3" />
        <SkeletonBlock className="h-20 w-full rounded-lg" />
        <SkeletonBlock className="h-20 w-full rounded-lg" />
      </div>
    </div>
  );
}

export function SettingsSkeleton() {
  return (
    <div className="max-w-lg mx-auto space-y-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="bg-bg-secondary rounded-xl border border-white/5 p-6 space-y-3">
          <SkeletonBlock className="h-4 w-1/4" />
          <SkeletonBlock className="h-10 w-full" />
          <SkeletonBlock className="h-10 w-full" />
        </div>
      ))}
    </div>
  );
}

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-bg-secondary rounded-xl border border-white/5 p-4 space-y-2">
          <SkeletonBlock className="h-3 w-1/2" />
          <SkeletonBlock className="h-7 w-1/3" />
        </div>
      ))}
    </div>
  );
}
