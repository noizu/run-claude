"use client";

import { useEffect, useRef } from "react";
import type { Model, Profile } from "@/lib/types";
import { fmtPrice, fmtTps } from "./Bits";

const SLOT_ORDER = ["fable", "opus", "sonnet", "haiku"] as const;

export default function ProfileModal({
  profile,
  models,
  onOpenModel,
  onClose,
}: {
  profile: Profile;
  models: Map<string, Model>;
  onOpenModel: (name: string) => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ref.current?.focus();
  }, []);

  const slotEntries = SLOT_ORDER.map((slot) => [slot, profile.slots[slot]] as const).filter(
    ([, m]) => Boolean(m),
  );
  const extended = profile.extended.filter((m) => !slotEntries.some(([, s]) => s === m));

  const ModelRef = ({ name }: { name: string }) => {
    const model = models.get(name);
    return (
      <button className="model-link" onClick={() => onOpenModel(name)} title={name}>
        {name}
        {model ? (
          <span className="faint" style={{ marginLeft: 6, fontFamily: "var(--mono)", fontSize: 11 }}>
            {fmtPrice(model.pricing?.text?.in)}/{fmtPrice(model.pricing?.text?.out)}
            {model.tokens_per_second ? ` · ${fmtTps(model.tokens_per_second)}` : ""}
          </span>
        ) : (
          <span className="faint" style={{ marginLeft: 6, fontSize: 11 }}>
            ⚠ not in model registry
          </span>
        )}
      </button>
    );
  };

  return (
    <div
      className="overlay"
      ref={ref}
      tabIndex={-1}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label={`Profile ${profile.display_name}`}
    >
      <div className="modal">
        <button className="close" onClick={onClose} aria-label="Close">
          ✕
        </button>
        <h2>{profile.display_name}</h2>
        <p className="faint" style={{ margin: "6px 0 0" }}>
          profile <code>{profile.name}</code> · resolved from {profile.source_file}
          {profile.shadowed_in.length > 0 && (
            <> · shadowed/disabled in: {profile.shadowed_in.join(", ")}</>
          )}
        </p>

        <section>
          <h3>Tier slots</h3>
          <table className="attrs">
            <tbody>
              {slotEntries.map(([slot, modelName]) => (
                <tr key={slot}>
                  <th>{slot}</th>
                  <td>
                    <ModelRef name={modelName as string} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {extended.length > 0 && (
          <section>
            <h3>Extended models ({extended.length})</h3>
            <table className="attrs">
              <tbody>
                {extended.map((name) => (
                  <tr key={name}>
                    <th />
                    <td>
                      <ModelRef name={name} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section>
          <h3>Always included</h3>
          <p className="muted" style={{ margin: 0 }}>
            {profile.always_include.join(", ")}{" "}
            <span className="faint">
              (added to every profile by resolve_profile_models; ultra/fast/cheap tier aliases)
            </span>
          </p>
        </section>
      </div>
    </div>
  );
}
