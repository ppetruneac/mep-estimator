/** Official Riser mark from getriser.co.uk / github.com/ppetruneac/getriser */
export function RiserMark({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      className={className}
      role="img"
      aria-label="Riser"
    >
      <title>Riser</title>
      <rect x="8" y="10" width="32" height="3" fill="currentColor" opacity="0.55" />
      <rect x="8" y="22.5" width="32" height="3" fill="currentColor" opacity="0.55" />
      <rect x="8" y="35" width="32" height="3" fill="currentColor" opacity="0.55" />
      <rect x="22.5" y="5" width="3" height="38" fill="currentColor" />
    </svg>
  );
}
