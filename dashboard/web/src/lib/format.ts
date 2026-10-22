export const DOMAIN_NAMES: Record<string, string> = {
  dsa: "Data structures & algorithms",
  os: "Operating systems",
  dbms: "Databases",
  cn: "Computer networks",
  system_design: "System design",
  none: "No taxonomy topic",
};

export const DOMAIN_SHORT: Record<string, string> = {
  dsa: "DSA",
  os: "OS",
  dbms: "DBMS",
  cn: "Networks",
  system_design: "System design",
};

export const domainName = (d: string) => DOMAIN_NAMES[d] ?? d;
export const domainShort = (d: string) => DOMAIN_SHORT[d] ?? d;

export const pct = (x: number | null | undefined, digits = 0) =>
  x === null || x === undefined ? "—" : `${(x * 100).toFixed(digits)}%`;

export const num = (x: number | null | undefined, digits = 3) =>
  x === null || x === undefined ? "—" : x.toFixed(digits);

export const date = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "—";

// Coverage at depth D: (1 - e^(-gamma*D)) / (1 - e^(-5*gamma)). At the fallback depth D = 1 with gamma = 0.5 this is ~0.43.
export const coverageAtDepth = (depth: number, gamma: number) =>
  (1 - Math.exp(-gamma * depth)) / (1 - Math.exp(-5 * gamma));
