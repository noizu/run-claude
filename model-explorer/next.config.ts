import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Don't generate an AGENTS.md inside the app dir on dev runs.
  agentRules: false,
  // Server components read the YAML files at request time (force-dynamic in the
  // page), so user-override edits show up on refresh without a rebuild.
};

export default nextConfig;
