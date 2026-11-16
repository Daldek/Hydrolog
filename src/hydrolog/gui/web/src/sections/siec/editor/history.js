// The history of Sieć's edits (plan 2026-11-10-network-editor, D9): a pure module without
// Preact or the DOM. It holds the section's inputs before and after every step, in memory
// only, up to a limit of steps (the oldest go first). The inputs are immutable and share
// their unchanged nodes, so a step costs only what it changed. A step is one action: a
// push opens a new step, unless it names the same `merge` key as the open last step (and
// comes within `within` ms of it, when given), when it replaces that step's inputs: the
// keys of a field merge until the field commits (`seal`), moves of one node by keys
// within 1 s are one. Undo and redo seal the step they reach, so the next edit is a step
// of its own. What is part of opening a network, not an edit (Hydrolog's layout replacing
// provisional rows), rewrites every step instead of adding one.

/**
 * A history of steps.
 *
 * @param {{limit?: number}} [options] the most steps kept (100)
 * @returns {{reset: (inputs: object) => void, push: (inputs: object, options?: {merge?:
 *   string|null, within?: number|null, at?: number}) => boolean, seal: () => void, undo:
 *   () => object|null, redo: () => object|null, rewrite: (change: (inputs: object) =>
 *   object) => void, current: object|null, canUndo: boolean, canRedo: boolean, steps:
 *   number}} the history: `reset` starts it at some inputs (not a step), `push` records
 *   the inputs after an edit (false when they are the current ones), `undo` and `redo`
 *   return the inputs to show (null when there is nothing to do), `rewrite` changes the
 *   inputs of every step alike
 */
export function createHistory({ limit = 100 } = {}) {
  let past = [];
  let future = [];
  const last = () => (past.length ? past[past.length - 1] : null);
  return {
    reset(inputs) {
      past = [{ inputs, merge: null, at: 0, sealed: true }];
      future = [];
    },
    push(inputs, { merge = null, within = null, at = Date.now() } = {}) {
      const top = last();
      if (!top) {
        this.reset(inputs);
        return false;
      }
      if (top.inputs === inputs) return false;
      future = [];
      const joins = merge !== null && past.length > 1 && !top.sealed && top.merge === merge && (within === null || at - top.at <= within);
      if (joins) {
        top.inputs = inputs;
        top.at = at;
        return true;
      }
      past.push({ inputs, merge, at, sealed: false });
      if (past.length > limit + 1) past = past.slice(past.length - limit - 1);
      return true;
    },
    seal() {
      const top = last();
      if (top) top.sealed = true;
    },
    undo() {
      if (past.length < 2) return null;
      future.unshift(past.pop());
      const top = last();
      top.sealed = true;
      return top.inputs;
    },
    redo() {
      if (!future.length) return null;
      const step = future.shift();
      step.sealed = true;
      past.push(step);
      return step.inputs;
    },
    rewrite(change) {
      for (const step of [...past, ...future]) step.inputs = change(step.inputs);
    },
    get current() {
      const top = last();
      return top ? top.inputs : null;
    },
    get canUndo() {
      return past.length > 1;
    },
    get canRedo() {
      return future.length > 0;
    },
    get steps() {
      return past.length - 1;
    },
  };
}
