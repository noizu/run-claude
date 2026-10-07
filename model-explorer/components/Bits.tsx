import type { Model, PricingSource } from "@/lib/types";

export function fmtPrice(v: number | null | undefined): string {
  if (v === undefined || v === null) return "—";
  if (v === 0) return "free";
  return `$${v < 1 ? v.toFixed(v < 0.01 ? 4 : 3).replace(/0+$/, "").replace(/\.$/, "") : v % 1 === 0 ? v.toFixed(0) : v.toFixed(2)}`;
}

export function fmtTokens(v: number | null | undefined): string {
  if (v === undefined || v === null) return "—";
  if (v >= 1_000_000 && v % 1_000_000 === 0) return `${v / 1_000_000}M`;
  if (v >= 1_000) return `${Math.round(v / 1000)}K`;
  return String(v);
}

export function fmtTps(v: number | null | undefined): string {
  if (v === undefined || v === null) return "—";
  return `~${v} t/s`;
}

const SOURCE_LABEL: Record<PricingSource, string> = {
  docs: "documented pricing",
  inferred: "inferred",
  estimate: "estimated",
  subscription: "subscription/plan",
  free: "free",
  na: "n/a",
};

export function SourceBadge({ model }: { model: Model }) {
  const src = model.pricing?.source;
  if (!src) return null;
  return (
    <span className={`badge ${src}`} title={`Pricing provenance: ${SOURCE_LABEL[src]}`}>
      {SOURCE_LABEL[src]}
    </span>
  );
}

export function ProviderBadge({ model }: { model: Model }) {
  return (
    <span className="badge provider" style={{ background: providerColor(model.provider) }}>
      {model.provider || "?"}
    </span>
  );
}

const PALETTE = [
  "rgba(88,166,255,0.18)",
  "rgba(63,185,80,0.16)",
  "rgba(210,153,34,0.16)",
  "rgba(188,140,255,0.16)",
  "rgba(248,81,73,0.14)",
  "rgba(219,171,122,0.16)",
];

export function providerColor(provider: string): string {
  let h = 0;
  for (const ch of provider) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}
