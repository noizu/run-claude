// Mirror of run_claude/models.yaml `metadata:` extended shape (see
// run_claude/profiles.py ModelMetadata) plus loader provenance fields.

export type PricingSource =
  | "docs"
  | "inferred"
  | "estimate"
  | "subscription"
  | "free"
  | "na";

export interface ModalityPricing {
  in: number | null;
  out: number | null;
}

export interface Pricing {
  text?: { in: number | null; cached_in?: number | null; out: number | null };
  audio?: ModalityPricing;
  image?: ModalityPricing;
  source?: PricingSource;
}

export interface Limits {
  max_input_tokens?: number | null;
  max_output_tokens?: number | null;
  max_thinking_tokens?: number | null;
}

export interface Thinking {
  supported?: boolean;
  levels?: string[];
  default_level?: string | null;
}

export interface Modalities {
  input?: string[]; // subset of: text, image, audio, video
  output?: string[]; // subset of: text, image, audio
}

export interface Model {
  name: string;
  provider: string;
  description: string;
  strengths?: string;
  weaknesses?: string;
  pricing?: Pricing;
  limits?: Limits;
  thinking?: Thinking;
  modalities?: Modalities;
  supports_tools?: boolean | null;
  context_window?: number | null;
  tokens_per_second?: number | null;
  notes?: string;
  // Non-secret slice of litellm_params (api_key values are never shipped).
  litellm_model?: string;
  api_base?: string;
  reasoning_effort?: string;
  // Loader provenance (which file(s) defined this entry).
  sources: string[];
  overridden?: boolean; // a later file replaced an earlier definition
  synthesized?: boolean; // produced by family-clone synthesis
}

export interface ProfileSlots {
  fable?: string; // effective slot (fable || opus fallback), loader-resolved
  opus?: string;
  sonnet?: string;
  haiku?: string;
}

export interface Profile {
  name: string;
  display_name: string;
  slots: ProfileSlots;
  extended: string[];
  always_include: string[];
  source_file: string; // file the effective definition resolved from
  shadowed_in: string[]; // files holding a disabled/overridden entry for this name
}

export interface LoadedFile {
  kind: string; // "builtin-models" | "user-models" | "builtin-profiles" | ...
  label: string;
  path: string;
  entries: number; // model entries or profile names
}

export interface ExplorerData {
  models: Model[];
  profiles: Profile[];
  files: LoadedFile[];
  generated_at: string;
}
