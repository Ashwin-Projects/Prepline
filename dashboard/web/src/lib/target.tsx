import { createContext, useContext, useState, type ReactNode } from "react";

const DEFAULT_TARGET = "amazon_sde1";
const KEY = "prepline-target";

interface TargetState {
  target: string;
  setTarget: (id: string) => void;
}

const TargetContext = createContext<TargetState>({ target: DEFAULT_TARGET, setTarget: () => {} });

// The selected company/role is shared by Overview, Topic explorer and Confidence, and remembered per browser.
export function TargetProvider({ children }: { children: ReactNode }) {
  const [target, setTargetState] = useState<string>(() => {
    try {
      return localStorage.getItem(KEY) ?? DEFAULT_TARGET;
    } catch {
      return DEFAULT_TARGET;
    }
  });
  const setTarget = (id: string) => {
    setTargetState(id);
    try {
      localStorage.setItem(KEY, id);
    } catch {
      // storage unavailable: the selection still works for this session
    }
  };
  return <TargetContext.Provider value={{ target, setTarget }}>{children}</TargetContext.Provider>;
}

export const useTarget = () => useContext(TargetContext);
