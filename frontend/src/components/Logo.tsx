// Brand mark: a flat, ink suspension bridge connecting skill nodes — editorial,
// monochrome, with a single forest-green node accent. No gradients.

export default function Logo({ size = 34 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="SkillBridge"
      role="img"
    >
      <rect x="0.6" y="0.6" width="46.8" height="46.8" rx="7" fill="#1A1714" />
      {/* deck */}
      <path d="M9 32 H39" stroke="#F4F1EA" strokeWidth="2.4" strokeLinecap="round" />
      {/* arch */}
      <path
        d="M11 32 C 18 16.5, 30 16.5, 37 32"
        stroke="#F4F1EA"
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="round"
      />
      {/* cables */}
      <path
        d="M17 21.8 V32 M24 17.6 V32 M31 21.8 V32"
        stroke="#F4F1EA"
        strokeWidth="1.2"
        opacity="0.55"
        strokeLinecap="round"
      />
      {/* nodes */}
      <circle cx="11" cy="32" r="2.6" fill="#F4F1EA" />
      <circle cx="37" cy="32" r="2.6" fill="#F4F1EA" />
      <circle cx="24" cy="17.6" r="2.4" fill="#3E7A5E" />
    </svg>
  );
}
