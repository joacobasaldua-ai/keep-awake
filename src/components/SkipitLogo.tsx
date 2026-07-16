export default function SkipitLogo({ className }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className ?? ""}`}>
      <svg viewBox="0 0 300 200" className="h-8 w-auto" aria-hidden="true">
        <path
          fill="#34D399"
          d="M35,138 C33,148 42,153 53,148 C90,132 150,92 200,58 C210,51 216,47 220,44 L220,32 C205,32 190,38 175,47 C130,74 80,108 48,133 C43,137 38,138 35,138 Z"
        />
        <path
          fill="#ffffff"
          d="M55,140 C52,145 58,148 66,144 C100,128 150,94 195,64 C202,59 207,56 211,53 L211,44 C200,44 190,49 180,56 C138,83 92,113 62,135 C59,137 57,138 55,140 Z"
        />
        <path
          fill="#34D399"
          d="M78,145 C74,152 82,156 92,151 C112,141 138,122 162,104 C178,92 192,81 202,73 L202,58 C190,58 178,64 168,72 C138,95 105,120 84,138 C82,140 80,143 78,145 Z"
        />
        <path
          fill="#34D399"
          d="M168,46 C172,30 192,19 217,19 C246,19 270,32 274,51 C277,66 266,78 248,79 C237,80 228,75 223,67 C217,78 202,84 188,80 C170,75 160,62 168,46 Z"
        />
        <circle cx="246" cy="43" r="8" fill="#ffffff" />
        <path
          fill="#34D399"
          d="M206,79 C221,84 230,97 228,111 C226,125 213,133 197,132 C187,132 179,127 177,119 C175,112 179,104 187,97 C195,90 201,84 206,79 Z"
        />
      </svg>
      <span className="text-2xl font-extrabold tracking-tight text-[#0c2622]">
        skipit
      </span>
    </span>
  );
}
