import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import yaml from "js-yaml";
import type {
  ExplorerData,
  LoadedFile,
  Model,
  Profile,
} from "./types";

// Mirrors run_claude/keys.py FAMILY_CLONES: [srcFamily, dstFamily, defaultEnv]
const FAMILY_CLONES: ReadonlyArray<readonly [string, string, string]> = [
  ["zai", "zai-alt", "ZAI_SUB_KEY_TYNA"],
  ["zai-oa", "zai-oa-alt", "ZAI_SUB_KEY_TYNA"],
];

// Mirrors run_claude/profiles.py ALWAYS_INCLUDE_MODELS
const ALWAYS_INCLUDE_MODELS = ["ultra", "fast", "cheap"];

/** Find the repo root (dir containing run_claude/models.yaml), mirroring get_builtin_dir(). */
function repoRoot(): string {
  const env = process.env.RUN_CLAUDE_REPO_ROOT;
  if (env) return env;
  let dir = process.cwd();
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(dir, "run_claude", "models.yaml"))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

/** User config dir, mirroring get_config_dir() (XDG_CONFIG_HOME respected). */
function configDir(): string {
  const env = process.env.RUN_CLAUDE_CONFIG_DIR;
  if (env) return env;
  const base = process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config");
  return path.join(base, "run-claude");
}

interface RawEntry {
  model_name?: string;
  litellm_params?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

function readYaml(file: string): Record<string, unknown> {
  try {
    const doc = yaml.load(fs.readFileSync(file, "utf-8"));
    if (doc && typeof doc === "object") return doc as Record<string, unknown>;
  } catch {
    // A malformed user file must not take the explorer down.
  }
  return {};
}

function toModel(
  raw: RawEntry,
  sources: string[],
  overridden: boolean,
  synthesized: boolean,
): Model | null {
  if (!raw.model_name) return null;
  const meta = (raw.metadata ?? {}) as Record<string, unknown>;
  const lp = (raw.litellm_params ?? {}) as Record<string, unknown>;
  return {
    name: raw.model_name,
    provider: typeof meta.provider === "string" ? meta.provider : "",
    description: typeof meta.description === "string" ? meta.description : "",
    strengths: typeof meta.strengths === "string" ? meta.strengths : undefined,
    weaknesses: typeof meta.weaknesses === "string" ? meta.weaknesses : undefined,
    pricing: (meta.pricing as Model["pricing"]) ?? undefined,
    limits: (meta.limits as Model["limits"]) ?? undefined,
    thinking: (meta.thinking as Model["thinking"]) ?? undefined,
    modalities: (meta.modalities as Model["modalities"]) ?? undefined,
    supports_tools:
      typeof meta.supports_tools === "boolean" ? meta.supports_tools : undefined,
    context_window: (meta.context_window as number | null) ?? undefined,
    tokens_per_second: (meta.tokens_per_second as number | null) ?? undefined,
    notes: typeof meta.notes === "string" ? meta.notes : undefined,
    // api_key / api_key_name deliberately excluded — never shipped to the client.
    litellm_model: typeof lp.model === "string" ? lp.model : undefined,
    api_base: typeof lp.api_base === "string" ? lp.api_base : undefined,
    reasoning_effort:
      typeof lp.reasoning_effort === "string" ? lp.reasoning_effort : undefined,
    sources,
    overridden,
    synthesized,
  };
}

/**
 * Load model definitions with base + user override logic, mirroring
 * run_claude/profiles.py load_model_definitions(): later files override by
 * model_name; an overriding entry without a description inherits the previous
 * metadata; then family clones are synthesized for missing dest entries.
 */
function loadModels(builtinFile: string, userFile: string) {
  const files: Array<{ label: string; path: string }> = [
    { label: "installation", path: builtinFile },
    { label: "user override", path: userFile },
  ];

  const byName = new Map<string, { model: Model; meta: Record<string, unknown> }>();
  const fileCounts: number[] = [];

  for (const source of files) {
    let count = 0;
    if (!fs.existsSync(source.path)) {
      fileCounts.push(0);
      continue;
    }
    const doc = readYaml(source.path);
    for (const raw of (doc.model_list as RawEntry[] | undefined) ?? []) {
      if (!raw.model_name) continue;
      const prev = byName.get(raw.model_name);
      const meta = { ...(prev?.meta ?? {}) };
      // Metadata inheritance: an override without its own description keeps
      // the prior entry's metadata (profiles.py:451-452).
      if (raw.metadata && typeof raw.metadata.description === "string" && raw.metadata.description) {
        Object.assign(meta, raw.metadata);
      }
      const model = toModel(
        { ...raw, metadata: meta },
        prev ? ["installation", "user override"] : [source.label],
        Boolean(prev),
        false,
      );
      if (model) {
        byName.set(raw.model_name, { model, meta });
        count += 1;
      }
    }
    fileCounts.push(count);
  }

  // Family-clone synthesis, mirroring _synthesize_family_clones().
  for (const [srcFam, dstFam, defaultEnv] of FAMILY_CLONES) {
    const srcPrefix = `${srcFam}/`;
    const dstPrefix = `${dstFam}/`;
    for (const [name, entry] of [...byName.entries()]) {
      if (!name.startsWith(srcPrefix)) continue;
      const altName = dstPrefix + name.slice(srcPrefix.length);
      if (byName.has(altName)) continue;
      const cloned: Model = {
        ...entry.model,
        name: altName,
        description: entry.model.description
          ? `${entry.model.description} (${dstFam} family)`
          : entry.model.description,
        sources: ["synthesized"],
        synthesized: true,
      };
      void defaultEnv; // dest key swap (os.environ/<defaultEnv>) is not shown in the UI
      byName.set(altName, { model: cloned, meta: entry.meta });
    }
  }

  return {
    models: [...byName.values()].map((e) => e.model),
    fileCounts,
  };
}

interface RawProfile {
  name?: string;
  opus_model?: string | null;
  sonnet_model?: string | null;
  haiku_model?: string | null;
  fable_model?: string | null;
  extended?: string[] | null;
  model?: unknown; // `model: null|false` disables (fall-through)
  meta?: Record<string, unknown>;
}

function isDisabled(data: unknown): boolean {
  // Mirrors _is_profile_disabled(): null/false/empty entries are disabled.
  if (!data || typeof data !== "object") return true;
  const obj = data as Record<string, unknown>;
  if (Object.keys(obj).length === 0) return true;
  if ("model" in obj) {
    const v = obj.model;
    if (v === null || v === false) return true;
  }
  return false;
}

function profileFromRaw(name: string, raw: RawProfile): {
  display_name: string;
  slots: Profile["slots"];
  extended: string[];
} {
  const meta = (raw.meta ?? raw) as Record<string, unknown>;
  const str = (v: unknown) => (typeof v === "string" && v ? v : undefined);
  const ext = Array.isArray(meta.extended) ? (meta.extended as string[]) : [];
  const opus = str(meta.opus_model);
  return {
    display_name: str(meta.name) ?? name,
    slots: {
      fable: str(meta.fable_model) ?? opus, // effective_fable_model(): falls back to opus
      opus,
      sonnet: str(meta.sonnet_model),
      haiku: str(meta.haiku_model),
    },
    extended: ext.filter((m) => typeof m === "string"),
  };
}

/**
 * Load profiles with 4-tier fall-through, mirroring load_profile():
 * first file where the profile exists AND is not disabled wins; `model: null`
 * in a higher-priority file falls through to the next.
 */
function loadProfiles(builtinDir: string, cfgDir: string) {
  const tiers: Array<{ label: string; path: string }> = [
    { label: "user.profiles.yaml (user override)", path: path.join(cfgDir, "user.profiles.yaml") },
    { label: "profiles.yaml (user config)", path: path.join(cfgDir, "profiles.yaml") },
    { label: "user.profiles.yaml (builtin override)", path: path.join(builtinDir, "user.profiles.yaml") },
    { label: "profiles.yaml (builtin)", path: path.join(builtinDir, "profiles.yaml") },
  ];

  const docs = tiers.map((t) =>
    fs.existsSync(t.path) ? (readYaml(t.path) as Record<string, RawProfile>) : null,
  );

  const profiles: Profile[] = [];
  // Union of names, preserving first-seen order (highest-priority file first).
  const seen = new Set<string>();
  const order: string[] = [];
  for (const doc of docs) {
    if (!doc) continue;
    for (const name of Object.keys(doc)) {
      if (name === "meta" || seen.has(name)) continue;
      seen.add(name);
      order.push(name);
    }
  }

  for (const name of order) {
    let resolved: { label: string; path: string; raw: RawProfile } | null = null;
    const shadowedIn: string[] = [];
    for (let i = 0; i < tiers.length; i++) {
      const doc = docs[i];
      if (!doc || !(name in doc)) continue;
      const raw = doc[name];
      if (isDisabled(raw)) {
        shadowedIn.push(tiers[i].label);
        continue; // disabled here → fall through to next file
      }
      if (!resolved) {
        resolved = { label: tiers[i].label, path: tiers[i].path, raw: raw as RawProfile };
      } else {
        shadowedIn.push(tiers[i].label); // shadowed by a higher-priority file
      }
    }
    if (!resolved) continue;
    const built = profileFromRaw(name, resolved.raw);
    profiles.push({
      name,
      display_name: built.display_name,
      slots: built.slots,
      extended: built.extended,
      always_include: ALWAYS_INCLUDE_MODELS,
      source_file: resolved.label,
      shadowed_in: shadowedIn,
    });
  }

  return { profiles, tiers: tiers.map((t, i) => ({ ...t, entries: docs[i] ? Object.keys(docs[i]!).filter((k) => k !== "meta").length : 0 })) };
}

export function loadExplorerData(): ExplorerData {
  const root = repoRoot();
  const cfg = configDir();
  const builtinModels = path.join(root, "run_claude", "models.yaml");
  const userModels = path.join(cfg, "models.yaml");

  const { models, fileCounts } = loadModels(builtinModels, userModels);
  const { profiles, tiers } = loadProfiles(root, cfg);

  const files: LoadedFile[] = [];
  const push = (kind: string, label: string, file: string, entries: number) => {
    if (fs.existsSync(file)) files.push({ kind, label, path: file, entries });
  };
  push("builtin-models", "installation models.yaml", builtinModels, fileCounts[0]);
  push("user-models", "user override models.yaml", userModels, fileCounts[1]);
  tiers.forEach((t, i) => {
    const kind = i < 2 ? "user-profiles" : "builtin-profiles";
    if (fs.existsSync(t.path)) files.push({ kind, label: t.label, path: t.path, entries: t.entries });
  });

  models.sort((a, b) =>
    a.provider.localeCompare(b.provider) || a.name.localeCompare(b.name),
  );

  return {
    models,
    profiles,
    files,
    generated_at: new Date().toISOString(),
  };
}
