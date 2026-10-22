import { useEffect, useState } from "react";
import { getJson } from "./api";

export interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

// One request per path; aborted when the path changes or the page unmounts.
export function useApi<T>(path: string | null): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({ data: null, error: null, loading: path !== null });
  useEffect(() => {
    if (path === null) return;
    const controller = new AbortController();
    setState((s) => ({ data: s.data, error: null, loading: true }));
    getJson<T>(path, controller.signal)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setState({ data: null, error: err instanceof Error ? err.message : String(err), loading: false });
      });
    return () => controller.abort();
  }, [path]);
  return state;
}
