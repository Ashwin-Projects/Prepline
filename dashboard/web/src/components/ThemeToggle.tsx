import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

// Light/dark theme on <html>, remembered per browser (index.html applies it before first paint).
export function useTheme() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("prepline-theme", dark ? "dark" : "light");
    } catch {
      // storage unavailable: theme still applies for this session
    }
  }, [dark]);
  return [dark, setDark] as const;
}

// Shared by the sidebar (labelled) and the story header (compact, icon only).
export function ThemeToggle({ compact = false, className = "" }: { compact?: boolean; className?: string }) {
  const [dark, setDark] = useTheme();
  return (
    <button
      type="button"
      onClick={() => setDark(!dark)}
      className={`press flex cursor-pointer items-center gap-2 rounded-md text-[13px] text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink ${
        compact ? "size-10 justify-center" : "px-2.5 py-2"
      } ${className}`}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      data-testid="theme-toggle"
    >
      {dark ? <Sun size={15} aria-hidden="true" /> : <Moon size={15} aria-hidden="true" />}
      {!compact && (dark ? "Light theme" : "Dark theme")}
    </button>
  );
}
