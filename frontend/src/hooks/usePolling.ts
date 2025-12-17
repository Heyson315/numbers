import { useEffect, useRef, useState } from 'react';

export function usePolling<T>(fn: () => Promise<T>, intervalMs: number, enabled = true) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const result = await fn();
        if (!cancelled) setData(result);
      } catch (e: any) {
        if (!cancelled) setError(e);
      }
      timerRef.current = window.setTimeout(tick, intervalMs);
    };
    tick();
    return () => {
      cancelled = true;
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [fn, intervalMs, enabled]);

  return { data, error };
}
