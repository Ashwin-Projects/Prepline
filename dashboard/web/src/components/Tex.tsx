import katex from "katex";

// KaTeX rendering of a trusted, static formula string (no user input reaches it).
export function Tex({ children, block = false }: { children: string; block?: boolean }) {
  const html = katex.renderToString(children, { displayMode: block, throwOnError: false, output: "html" });
  return block ? (
    <div className="overflow-x-auto py-1 text-ink" dangerouslySetInnerHTML={{ __html: html }} />
  ) : (
    <span className="text-ink" dangerouslySetInnerHTML={{ __html: html }} />
  );
}
