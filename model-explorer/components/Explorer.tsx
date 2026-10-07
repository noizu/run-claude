"use client";

import { useMemo, useState } from "react";
import type { ExplorerData, Model, Profile } from "@/lib/types";
import { fmtPrice, fmtTps, ProviderBadge, SourceBadge } from "./Bits";
import ModelModal from "./ModelModal";
import ProfileModal from "./ProfileModal";

type ModalState =
  | { kind: "model"; name: string }
  | { kind: "profile"; name: string };

export default function Explorer({ data }: { data: ExplorerData }) {
  const [tab, setTab] = useState<"models" | "profiles">("models");
  const [query, setQuery] = useState("");
  const [providers, setProviders] = useState<Set<string>>(new Set());
  // Modal stack enables dig-down: profile → model → (nothing deeper today).
  const [stack, setStack] = useState<ModalState[]>([]);

  const modelIndex = useMemo(
    () => new Map(data.models.map((m) => [m.name, m])),
    [data.models],
  );

  const providerList = useMemo(() => {
    const counts = new Map<string, number>();
    for (const m of data.models) counts.set(m.provider, (counts.get(m.provider) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [data.models]);

  const q = query.trim().toLowerCase();
  const matchesModel = (m: Model) =>
    !q ||
    m.name.toLowerCase().includes(q) ||
    m.provider.toLowerCase().includes(q) ||
    m.description.toLowerCase().includes(q) ||
    (m.strengths ?? "").toLowerCase().includes(q) ||
    (m.litellm_model ?? "").toLowerCase().includes(q);

  const filteredModels = useMemo(
    () =>
      data.models.filter(
        (m) =>
          (providers.size === 0 || providers.has(m.provider)) && matchesModel(m),
      ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data.models, providers, q],
  );

  const filteredProfiles = useMemo(() => {
    if (!q) return data.profiles;
    const modelHit = (name?: string) =>
      name ? modelIndex.get(name) && matchesModel(modelIndex.get(name)!) : false;
    return data.profiles.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.display_name.toLowerCase().includes(q) ||
        Object.values(p.slots).some((s) => s?.toLowerCase().includes(q) || modelHit(s)) ||
        p.extended.some((m) => m.toLowerCase().includes(q) || modelHit(m)),
    );
  }, [data.profiles, q, modelIndex]);

  const toggleProvider = (p: string) =>
    setProviders((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });

  const open = (m: ModalState) => setStack((s) => [...s, m]);
  const closeTop = () => setStack((s) => s.slice(0, -1));

  const top = stack[stack.length - 1];
  const topModel = top?.kind === "model" ? modelIndex.get(top.name) : undefined;
  const topProfile = top?.kind === "profile" ? data.profiles.find((p) => p.name === top.name) : undefined;

  return (
    <div className="wrap">
      <header className="top">
        <div className="brand">
          <h1>run-claude · model explorer</h1>
          <span className="sub">
            {data.models.length} models · {data.profiles.length} profiles ·{" "}
            {new Date(data.generated_at).toLocaleTimeString()}
          </span>
        </div>
        <div className="filebar">
          {data.files.map((f) => (
            <span key={f.path} className="filechip" title={f.path}>
              {f.label}: <b>{f.entries}</b>
            </span>
          ))}
        </div>
      </header>

      <div className="controls">
        <div className="search">
          <input
            type="search"
            placeholder="Search models, providers, profiles…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>
        <div className="tabs">
          <button className={tab === "models" ? "active" : ""} onClick={() => setTab("models")}>
            Models
          </button>
          <button className={tab === "profiles" ? "active" : ""} onClick={() => setTab("profiles")}>
            Profiles
          </button>
        </div>
        <span className="count">
          {tab === "models" ? filteredModels.length : filteredProfiles.length} shown
        </span>
      </div>

      {tab === "models" && (
        <div className="chips">
          {providerList.map(([p, n]) => (
            <button
              key={p}
              className={`chip ${providers.has(p) ? "on" : ""}`}
              onClick={() => toggleProvider(p)}
            >
              {p} · {n}
            </button>
          ))}
        </div>
      )}

      {tab === "models" ? (
        <div className="grid">
          {filteredModels.map((m) => (
            <button className="card" key={m.name} onClick={() => open({ kind: "model", name: m.name })}>
              <div className="name">{m.name}</div>
              <div className="row">
                <ProviderBadge model={m} />
                <SourceBadge model={m} />
                {m.thinking?.supported && <span className="badge think">thinking</span>}
                {m.synthesized && <span className="badge synth">clone</span>}
                {m.overridden && <span className="badge override">override</span>}
              </div>
              <div className="row">
                <span className="price">
                  in {fmtPrice(m.pricing?.text?.in)} · cached {fmtPrice(m.pricing?.text?.cached_in)} ·
                  out {fmtPrice(m.pricing?.text?.out)}
                </span>
                <span className="price">· {fmtTps(m.tokens_per_second)}</span>
              </div>
              {m.description && <div className="desc">{m.description}</div>}
            </button>
          ))}
          {filteredModels.length === 0 && (
            <div className="empty">No models match “{query}”.</div>
          )}
        </div>
      ) : (
        <div className="grid">
          {filteredProfiles.map((p) => (
            <ProfileCard key={p.name} profile={p} onOpen={() => open({ kind: "profile", name: p.name })} />
          ))}
          {filteredProfiles.length === 0 && (
            <div className="empty">No profiles match “{query}”.</div>
          )}
        </div>
      )}

      {topProfile && (
        <ProfileModal
          profile={topProfile}
          models={modelIndex}
          onOpenModel={(name) => open({ kind: "model", name })}
          onClose={closeTop}
        />
      )}
      {topModel && <ModelModal model={topModel} onClose={closeTop} />}
    </div>
  );
}

function ProfileCard({ profile, onOpen }: { profile: Profile; onOpen: () => void }) {
  const slotLabels: Array<[string, string | undefined]> = [
    ["fable", profile.slots.fable],
    ["opus", profile.slots.opus],
    ["sonnet", profile.slots.sonnet],
    ["haiku", profile.slots.haiku],
  ];
  return (
    <button className="card profile-card" onClick={onOpen}>
      <div className="name">{profile.display_name}</div>
      <div className="row">
        <span className="badge">{profile.name}</span>
        <span className="price">{profile.extended.length} extended</span>
      </div>
      <div className="slots">
        {slotLabels
          .filter(([, m]) => Boolean(m))
          .map(([tier, m]) => (
            <span className="slot" key={tier}>
              <span className="tier">{tier}</span>
              <span className="m">{m}</span>
            </span>
          ))}
      </div>
    </button>
  );
}
