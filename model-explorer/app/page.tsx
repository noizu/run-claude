import Explorer from "@/components/Explorer";
import { loadExplorerData } from "@/lib/load";

// Re-read the YAML files on every request so edits to the installation or
// user-override files show up on refresh without a rebuild.
export const dynamic = "force-dynamic";

export default function Page() {
  const data = loadExplorerData();
  return <Explorer data={data} />;
}
