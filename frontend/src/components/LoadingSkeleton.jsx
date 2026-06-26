export function CardSkeleton() {
  return (
    <div className="card">
      <div className="aspect-[4/3] skeleton" />
      <div className="p-3 space-y-2">
        <div className="h-4 skeleton w-2/3" />
        <div className="h-3 skeleton w-1/2" />
        <div className="h-3 skeleton w-1/3" />
      </div>
    </div>
  )
}

export function ListSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {Array.from({ length: count }, (_, i) => <CardSkeleton key={i} />)}
    </div>
  )
}

export function ShopSkeleton() {
  return (
    <div className="card flex items-center gap-3 p-3">
      <div className="w-12 h-12 rounded-xl skeleton shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3.5 skeleton w-3/4" />
        <div className="h-3 skeleton w-1/2" />
      </div>
    </div>
  )
}

export function DetailSkeleton() {
  return (
    <div>
      <div className="aspect-square skeleton" />
      <div className="p-4 space-y-3">
        <div className="h-6 skeleton w-1/2" />
        <div className="h-4 skeleton w-3/4" />
        <div className="h-4 skeleton w-full" />
        <div className="h-12 skeleton" />
      </div>
    </div>
  )
}
