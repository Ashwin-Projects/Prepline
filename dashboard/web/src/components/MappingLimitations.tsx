import { ExternalLink } from "lucide-react";
import { Card } from "./ui";

const BACKLOG_URL = "https://github.com/Ashwin-Projects/Prepline/blob/main/docs/BACKLOG.md#known-mapping-limitations";

const ITEMS: { title: string; detail: string }[] = [
  {
    title: "Description-only matching",
    detail: "Taxonomy nodes are matched by their description, never their name, so a module titled “Dynamic Programming” can miss the DP node.",
  },
  {
    title: "DP false negatives",
    detail: "DAA’s DP module scores 0.45 against dsa.dp (τ = 0.50); DP coverage instead comes from Computer Architecture and Compiler Design units.",
  },
  {
    title: "Java I/O → messaging false positive",
    detail: "Java “IO Streams and Files” matches message queues, so messaging and pub/sub look covered when they are not.",
  },
  {
    title: "React routing → network layer false positive",
    detail: "Web Programming’s “Hooks and Routing” matches the network layer, while its WWW/IP/DNS module matches nothing.",
  },
  {
    title: "Missing taxonomy nodes",
    detail: "No node for hashing, greedy algorithms, interval problems, string matching or object-oriented design; those questions never enter a score.",
  },
];

export function MappingLimitations({ className = "" }: { className?: string }) {
  return (
    <Card
      className={className}
      title="Known mapping limitations"
      subtitle="Matcher, τ and taxonomy are frozen in config v1.2; these errors are in every score shown here."
      testId="mapping-limitations"
    >
      <ul className="grid grid-cols-2 gap-x-6 gap-y-2 text-[13px] max-[900px]:grid-cols-1">
        {ITEMS.map((item) => (
          <li key={item.title}>
            <span className="font-medium text-ink">{item.title}.</span>{" "}
            <span className="text-ink-2">{item.detail}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[13px] text-ink-3">
        Details and impact: <code className="font-mono text-[12px]">docs/BACKLOG.md</code> → Known mapping limitations (
        <a
          href={BACKLOG_URL}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-0.5 text-primary underline underline-offset-2 hover:no-underline"
        >
          on GitHub <ExternalLink size={12} aria-hidden="true" />
        </a>
        ).
      </p>
    </Card>
  );
}
