// Live recompute of „Hydrogram zlewni” (plan D13), a pure module without Preact: a change
// of valid data schedules a run 250 ms later and every further change restarts the delay;
// a newer request aborts the older one still in flight, and only the outcome of the newest
// is reported (a sequence number). „Liczenie…” starts 150 ms after a request that has not
// finished; invalid data cancel what is scheduled or running and keep the last result.

/** The delay of a run after the last change [ms]. */
export const RUN_DELAY_MS = 250;

/** How long a request waits before it is shown as busy [ms]. */
export const BUSY_AFTER_MS = 150;

/**
 * A channel of live runs.
 *
 * @param {{delay?: number, busyAfter?: number,
 *   onBusy: (busy: boolean) => void,
 *   onOutcome: (outcome: {ok: true, value: any}|{ok: false, error: any}, sequence: number) => void}} how
 *   the delays, and the handlers of the busy state and of the newest request's outcome
 * @returns {{request: (task: (signal: AbortSignal) => Promise<any>) => number,
 *   cancel: () => void, dispose: () => void, latest: () => number}} the channel:
 *   `request` schedules a task (an async function of an abort signal) and returns its
 *   sequence number; `cancel` drops what is scheduled or running; `dispose` stops it for good
 */
export function createChannel({ delay = RUN_DELAY_MS, busyAfter = BUSY_AFTER_MS, onBusy, onOutcome }) {
  let sequence = 0;
  let timer = null;
  let busyTimer = null;
  let controller = null;
  let busy = false;
  let disposed = false;

  const setBusy = (next) => {
    if (busy === next) return;
    busy = next;
    onBusy(next);
  };
  const stop = () => {
    clearTimeout(timer);
    clearTimeout(busyTimer);
    timer = null;
    busyTimer = null;
    if (controller) controller.abort();
    controller = null;
  };

  return {
    request(task) {
      if (disposed) return sequence;
      sequence += 1;
      const mine = sequence;
      stop();
      busyTimer = setTimeout(() => {
        if (mine === sequence) setBusy(true);
      }, busyAfter);
      timer = setTimeout(async () => {
        timer = null;
        const own = new AbortController();
        controller = own;
        let outcome;
        try {
          outcome = { ok: true, value: await task(own.signal) };
        } catch (error) {
          if (own.signal.aborted || (error && error.name === "AbortError")) return;
          outcome = { ok: false, error };
        }
        if (mine !== sequence || disposed) return;
        controller = null;
        clearTimeout(busyTimer);
        busyTimer = null;
        setBusy(false);
        onOutcome(outcome, mine);
      }, delay);
      return mine;
    },
    cancel() {
      sequence += 1;
      stop();
      setBusy(false);
    },
    dispose() {
      disposed = true;
      sequence += 1;
      stop();
    },
    latest() {
      return sequence;
    },
  };
}
