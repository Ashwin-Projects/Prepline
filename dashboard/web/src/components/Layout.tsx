import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { BarChart3, BookOpen, Columns3, FlaskConical, Gauge, Moon, ShieldCheck, Sun, Table2 } from "lucide-react";

const NAV = [
  { to: "/", label: "Overview", icon: Gauge },
  { to: "/compare", label: "Compare", icon: Columns3 },
  { to: "/topics", label: "Topic explorer", icon: Table2 },
  { to: "/confidence", label: "Confidence", icon: ShieldCheck },
  { to: "/benchmark", label: "Benchmark", icon: FlaskConical },
  { to: "/methodology", label: "Methodology", icon: BookOpen },
];

function useTheme() {
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

export function Layout() {
  const [dark, setDark] = useTheme();
  const location = useLocation();
  return (
    <div className="grid min-h-screen grid-cols-[13rem_minmax(0,1fr)] max-[900px]:grid-cols-1">
      <aside className="sticky top-0 flex h-screen flex-col border-r border-line bg-surface px-3 py-4 max-[900px]:static max-[900px]:h-auto max-[900px]:border-r-0 max-[900px]:border-b">
        <div className="mb-5 flex items-center gap-2 px-2">
          <BarChart3 size={20} className="text-primary" aria-hidden="true" />
          <div>
            <p className="text-[15px] font-bold tracking-tight text-ink">PREPLINE</p>
            <p className="text-[11px] leading-tight text-ink-3">Curriculum ↔ interview alignment</p>
          </div>
        </div>
        <nav aria-label="Pages" className="flex flex-col gap-0.5 max-[900px]:flex-row max-[900px]:flex-wrap">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[14px] transition-colors duration-150 ${
                  isActive ? "bg-primary-soft font-medium text-primary" : "text-ink-2 hover:bg-surface-2 hover:text-ink"
                }`
              }
            >
              <Icon size={16} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          onClick={() => setDark(!dark)}
          className="press mt-auto flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-2 text-[13px] text-ink-2 hover:bg-surface-2 hover:text-ink max-[900px]:mt-3"
          aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
          data-testid="theme-toggle"
        >
          {dark ? <Sun size={15} aria-hidden="true" /> : <Moon size={15} aria-hidden="true" />}
          {dark ? "Light theme" : "Dark theme"}
        </button>
      </aside>
      <div className="flex min-w-0 flex-col">
        <main key={location.pathname} className="page-enter flex-1 px-7 py-6 max-[900px]:px-4">
          <Outlet />
        </main>
        <footer className="border-t border-line px-7 py-3 text-[12px] text-ink-3" data-testid="disclaimer">
          Topic alignment is diagnostic, not a hiring guarantee: it compares syllabus topics with topics reported in public
          interview write-ups. Results v1.2 · taxonomy v1.0 · scoring config v1.2.
        </footer>
      </div>
    </div>
  );
}
