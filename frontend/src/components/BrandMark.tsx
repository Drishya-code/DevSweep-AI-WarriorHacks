/** Compact mascot crop shared by the app header and navigation. */
export function BrandMark({ size = 32 }: { size?: number }) {
  const imageSize = size * 1.7

  return <span aria-hidden="true" className="relative inline-block shrink-0 overflow-hidden rounded-lg bg-[#050816]" style={{ width: size, height: size }}>
    <img
      src="/devsweep-neon-logo.png"
      alt=""
      className="absolute max-w-none"
      style={{ width: imageSize, height: imageSize, left: -size * 0.35, top: -size * 0.12 }}
    />
  </span>
}
