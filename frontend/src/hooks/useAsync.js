import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Run an async function and track {data, error, loading}.
 * Pass `immediate: false` to only run when `run()` is called.
 */
export function useAsync(fn, deps = [], { immediate = true } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: immediate });
  const latest = useRef(0);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(async (...args) => {
    const id = ++latest.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fn(...args);
      if (id === latest.current) setState({ data, error: null, loading: false });
      return data;
    } catch (error) {
      if (id === latest.current) setState((s) => ({ ...s, error, loading: false }));
      return undefined;
    }
  }, deps);

  useEffect(() => { if (immediate) run(); }, [run, immediate]);

  return { ...state, run, setData: (data) => setState((s) => ({ ...s, data })) };
}
