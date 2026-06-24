export function CardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="aspect-[4/3] bg-tg-muted/10" />
      <div className="p-3 space-y-2">
        <div className="h-3 bg-tg-muted/10 rounded w-2/3" />
        <div className="h-2.5 bg-tg-muted/10 rounded w-1/2" />
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
    <div className="card flex items-center gap-3 p-3 animate-pulse">
      <div className="w-12 h-12 rounded-xl bg-tg-muted/10 shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3 bg-tg-muted/10 rounded w-3/4" />
        <div className="h-2.5 bg-tg-muted/10 rounded w-1/2" />
      </div>
    </div>
  )
}
