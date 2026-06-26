export default function StepIndicator({ current, total }) {
  const percent = ((current + 1) / total) * 100

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-tg-muted">{current + 1}/{total} qadam</span>
        <span className="text-xs text-tg-accent font-medium">{Math.round(percent)}%</span>
      </div>
      <div className="h-1 bg-tg-border rounded-full overflow-hidden">
        <div
          className="h-full bg-tg-accent rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}
