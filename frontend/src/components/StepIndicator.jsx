export default function StepIndicator({ current, total }) {
  return (
    <div className="flex gap-1.5 justify-center mb-6">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`h-1 rounded-full transition-all ${i === current ? 'w-6 bg-tg-accent' : i < current ? 'w-3 bg-tg-accent/50' : 'w-3 bg-tg-muted/30'}`}
        />
      ))}
    </div>
  )
}
