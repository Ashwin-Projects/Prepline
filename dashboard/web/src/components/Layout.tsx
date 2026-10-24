import { NavLink, Outlet, useLocation } from "react-router-dom";
import { BookOpen, Columns3, FlaskConical, Gauge, ShieldCheck, Table2, Waypoints } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

const STORY = { to: "/how-it-works", label: "How it works", icon: Waypoints };

const NAV = [
  { to: "/", label: "Overview", icon: Gauge },
  { to: "/compare", label: "Compare", icon: Columns3 },
  { to: "/topics", label: "Topic explorer", icon: Table2 },
  { to: "/confidence", label: "Confidence", icon: ShieldCheck },
  { to: "/benchmark", label: "Benchmark", icon: FlaskConical },
  { to: "/methodology", label: "Methodology", icon: BookOpen },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `relative flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[14px] transition-colors duration-150 before:absolute before:inset-y-1.5 before:left-0 before:w-[2px] before:rounded-full before:transition-colors before:duration-150 max-[900px]:before:hidden ${
    isActive
      ? "bg-surface-2 font-medium text-ink before:bg-primary max-[900px]:bg-primary-soft max-[900px]:text-primary"
      : "text-ink-2 before:bg-transparent hover:bg-surface-2 hover:text-ink"
  }`;

export function Layout() {
  const location = useLocation();
  return (
    <div className="grid min-h-screen grid-cols-[14rem_minmax(0,1fr)] max-[900px]:grid-cols-1">
      <aside className="sticky top-0 flex h-screen flex-col border-r border-line bg-surface px-3 py-5 max-[900px]:static max-[900px]:h-auto max-[900px]:border-r-0 max-[900px]:border-b">
        <div className="mb-6 px-2.5">
          <p className="font-display text-[24px] leading-none font-semibold tracking-[-0.015em] text-ink">Prepline</p>
          <p className="mt-1.5 text-[12px] leading-snug text-ink-3">Curriculum ↔ interview alignment</p>
        </div>
        <nav aria-label="Pages" className="flex flex-col gap-0.5 max-[900px]:flex-row max-[900px]:flex-wrap">
          <NavLink to={STORY.to} className={linkClass}>
            <STORY.icon size={16} aria-hidden="true" />
            {STORY.label}
          </NavLink>
          <span className="mx-2.5 my-2 h-px bg-line max-[900px]:hidden" aria-hidden="true" />
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"} className={linkClass}>
              <Icon size={16} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <ThemeToggle className="mt-auto max-[900px]:mt-3" />
      </aside>
      <div className="flex min-w-0 flex-col">
        <main key={location.pathname} className="page-enter flex-1 px-8 py-7 max-[900px]:px-4 max-[900px]:py-5">
          <Outlet />
        </main>
        <footer className="border-t border-line px-8 py-3 text-[12px] text-ink-3 max-[900px]:px-4" data-testid="disclaimer">
          Topic alignment is diagnostic, not a hiring guarantee: it compares syllabus topics with topics reported in public
          interview write-ups. Results v1.2 · taxonomy v1.0 · scoring config v1.2.
        </footer>
      </div>
    </div>
  );
}
