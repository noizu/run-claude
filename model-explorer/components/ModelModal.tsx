"use client";

import { useEffect, useRef } from "react";
import type { Model } from "@/lib/types";
import { fmtPrice, fmtTokens, fmtTps, ProviderBadge, SourceBadge } from "./Bits";

export default function ModelModal({ model, onClose }: { model: Model; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ref.current?.focus();
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const p = model.pricing;
  const l = model.limits;
  const t = model.thinking;

  return (
    <div
      className="overlay"
      ref={ref}
      tabIndex={-1}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label={`Model ${model.name}`}
    >
      <div className="modal">
        <button className="close" onClick={onClose} aria-label="Close">
          ✕
        </button>
        <h2>{model.name}</h2>
        <div className="row" style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
          <ProviderBadge model={model} />
          <SourceBadge model={model} />
          {t?.supported && (
            <span className="badge think">
              thinking{t.default_level ? ` · ${t.default_level}` : ""}
            </span>
          )}
          {model.overridden && (
            <span className="badge override" title="Defined in the installation file and overridden by ~/.config/run-claude/models.yaml">
              user override
            </span>
          )}
          {model.synthesized && (
            <span className="badge synth" title="Synthesized by family-clone logic (profiles.py _synthesize_family_clones)">
              synthesized clone
            </span>
          )}
        </div>

        {model.description && (
          <section>
            <p className="muted" style={{ margin: 0 }}>
              {model.description}
            </p>
          </section>
        )}

        <section>
          <h3>Pricing · USD per 1M tokens</h3>
          <table className="attrs">
            <tbody>
              <tr>
                <th>Text input</th>
                <td className="num">{fmtPrice(p?.text?.in)}</td>
              </tr>
              <tr>
                <th>Text input (cached)</th>
                <td className="num">{fmtPrice(p?.text?.cached_in)}</td>
              </tr>
              <tr>
                <th>Text output</th>
                <td className="num">{fmtPrice(p?.text?.out)}</td>
              </tr>
              <tr>
                <th>Audio input</th>
                <td className="num">{fmtPrice(p?.audio?.in)}</td>
              </tr>
              <tr>
                <th>Audio output</th>
                <td className="num">{fmtPrice(p?.audio?.out)}</td>
              </tr>
              <tr>
                <th>Image input</th>
                <td className="num">{fmtPrice(p?.image?.in)}</td>
              </tr>
              <tr>
                <th>Image output</th>
                <td className="num">{fmtPrice(p?.image?.out)}</td>
              </tr>
            </tbody>
          </table>
          {model.notes && <p className="faint" style={{ marginBottom: 0 }}>{model.notes}</p>}
        </section>

        <section>
          <h3>Limits & throughput</h3>
          <table className="attrs">
            <tbody>
              <tr>
                <th>Context window</th>
                <td className="num">{fmtTokens(model.context_window)}</td>
              </tr>
              <tr>
                <th>Max input tokens</th>
                <td className="num">{fmtTokens(l?.max_input_tokens)}</td>
              </tr>
              <tr>
                <th>Max output tokens</th>
                <td className="num">{fmtTokens(l?.max_output_tokens)}</td>
              </tr>
              <tr>
                <th>Max thinking tokens</th>
                <td className="num">{fmtTokens(l?.max_thinking_tokens)}</td>
              </tr>
              <tr>
                <th>Throughput (estimated)</th>
                <td className="num">{fmtTps(model.tokens_per_second)}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section>
          <h3>Capabilities</h3>
          <table className="attrs">
            <tbody>
              <tr>
                <th>Thinking supported</th>
                <td>{t ? (t.supported ? "yes" : "no") : "—"}</td>
              </tr>
              <tr>
                <th>Thinking levels</th>
                <td>{t?.levels?.length ? t.levels.join(", ") : "—"}</td>
              </tr>
              <tr>
                <th>Default thinking level</th>
                <td>{t?.default_level ?? "—"}</td>
              </tr>
              <tr>
                <th>Tool / function calling</th>
                <td>
                  {model.supports_tools === true
                    ? "supported"
                    : model.supports_tools === false
                      ? "not supported"
                      : "—"}
                </td>
              </tr>
              <tr>
                <th>Input modalities</th>
                <td>{model.modalities?.input?.length ? model.modalities.input.join(", ") : "—"}</td>
              </tr>
              <tr>
                <th>Output modalities</th>
                <td>{model.modalities?.output?.length ? model.modalities.output.join(", ") : "—"}</td>
              </tr>
            </tbody>
          </table>
        </section>

        {(model.strengths || model.weaknesses) && (
          <section>
            <h3>Notes</h3>
            <table className="attrs">
              <tbody>
                {model.strengths && (
                  <tr>
                    <th>Strengths</th>
                    <td>{model.strengths}</td>
                  </tr>
                )}
                {model.weaknesses && (
                  <tr>
                    <th>Weaknesses</th>
                    <td>{model.weaknesses}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        )}

        <section>
          <h3>Routing</h3>
          <table className="attrs">
            <tbody>
              <tr>
                <th>LiteLLM model</th>
                <td className="num">{model.litellm_model ?? "—"}</td>
              </tr>
              {model.api_base && (
                <tr>
                  <th>API base</th>
                  <td className="num">{model.api_base}</td>
                </tr>
              )}
              {model.reasoning_effort && (
                <tr>
                  <th>reasoning_effort</th>
                  <td className="num">{model.reasoning_effort}</td>
                </tr>
              )}
              <tr>
                <th>Defined in</th>
                <td>{model.sources.join(" → ")}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
