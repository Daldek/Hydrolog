// The depth of PMAXTP (ADR-0018) for the point, p, duration and method of step 2, for
// whichever section shows the step (plan 2026-11-10-network-wizard, D4): Hydrogram zlewni
// on its channel "hydrogram-pmaxtp", Sieć for its network's rainfall on "siec-pmaxtp". The
// depth remembered with the inputs (`pmaxtp_fetched`) is used while it was fetched for the
// same options; otherwise, once they are given and valid, `precip pmaxtp` fetches it on the
// host's channel (debounced as a run, a newer fetch superseding an older one, never a run)
// and the host keeps the record it is handed. A point outside the atlas stands on its
// field, any other failure (IMGW-PIB unreachable, an answer without a depth) on the row of
// the depth, with „Pobierz ponownie”.

import { api } from "../../api.js";
import { withReason } from "../../forms/model.js";
import { useEffect, useMemo, useRef, useState } from "../../html.js";
import { describeError } from "../../labels/errors.js";
import { describeNotice } from "../../labels/notices.js";
import { createChannel } from "../../recompute.js";
import { PMAXTP_COMMAND, PMAXTP_FIELDS, pmaxtpDepth, pmaxtpKey, pmaxtpOptions, pmaxtpRecord } from "./state.js";

/**
 * Word an error of a PMAXTP fetch: on the field of the point it names (a point outside the
 * atlas), else on the row of the depth (IMGW-PIB unreachable, an answer it cannot read).
 *
 * @param {object} doc the hydrolog-error/1 document
 * @returns {{fields: Object<string, string>, text: string}} the messages
 */
function wordPmaxtpError(doc) {
  const described = describeError(doc);
  const field = described.option && Object.hasOwn(PMAXTP_FIELDS, described.option) ? PMAXTP_FIELDS[described.option] : "pmaxtp_depth";
  return { fields: { [field]: withReason(described.text, described.reason || (doc && doc.code) || "") }, text: described.text };
}

/**
 * PMAXTP's depth for the inputs of step 2: remembered, or fetched on the host's channel.
 *
 * @param {object} inputs the inputs with the fields of step 2 (`rain_source`, the point,
 *   p, the duration, the method and `pmaxtp_fetched`)
 * @param {{channel: string, valid: boolean, onDepth: (record: object) => void}} options the
 *   host's channel; whether the fields of PMAXTP passed their checks (nothing is fetched
 *   before); and what keeps a fetched depth: the record of pmaxtpRecord, the options it was
 *   fetched for with `depth_mm`, for the host's `pmaxtp_fetched`
 * @returns {{depth: number|null, busy: boolean, failed: {key: string, fields: Object<string,
 *   string>, text: string}|null, onRetry: (() => void)|null, reset: () => void}} the depth
 *   [mm] (null while it is to be fetched or the rainfall is not PMAXTP), whether it is being
 *   fetched, the failure of the fetch of these options with its messages by field, „Pobierz
 *   ponownie” after a failure of the source, and what drops a fetch and its failure
 *   („Wyczyść”)
 */
export function usePmaxtp(inputs, { channel, valid, onDepth }) {
  const [failure, setFailure] = useState(null);
  const [busy, setBusy] = useState(false);
  const outcome = useRef(null);
  const fetches = useMemo(
    () =>
      createChannel({
        onBusy: setBusy,
        onOutcome: (next) => outcome.current(next),
      }),
    [],
  );
  useEffect(() => () => fetches.dispose(), [fetches]);

  const depth = pmaxtpDepth(inputs);
  const wanted = valid ? pmaxtpOptions(inputs) : null;
  const key = wanted && depth === null ? pmaxtpKey(wanted) : null;
  const failed = failure && failure.key === key ? failure : null;
  const latest = useRef(key);
  latest.current = key;
  const keep = useRef(onDepth);
  keep.current = onDepth;

  outcome.current = (next) => {
    // The task returns its errors; a rejection would be a fault of the GUI itself
    const value = next.ok ? next.value : { key: latest.current, error: { code: "internal_error", message: String(next.error) } };
    if (value.error) {
      setFailure({ key: value.key, ...wordPmaxtpError(value.error) });
      return;
    }
    const envelope = value.envelope;
    const result = envelope.status === "ok" ? envelope.result : null;
    if (!result || typeof result.depth_mm !== "number") {
      const words = (envelope.notices || []).map((notice) => describeNotice(notice).text).join(" ");
      setFailure({ key: value.key, fields: { pmaxtp_depth: words }, text: words });
      return;
    }
    setFailure(null);
    keep.current(pmaxtpRecord(value.options, result.depth_mm));
  };

  useEffect(() => {
    if (!key || failed) {
      fetches.cancel();
      return;
    }
    const sent = { key, options: wanted };
    fetches.request(async (signal) => {
      try {
        const envelope = await api.run(PMAXTP_COMMAND, sent.options, { channel, signal });
        return { ...sent, envelope };
      } catch (error) {
        if (error && error.name === "AbortError") throw error;
        return { ...sent, error: error && error.doc ? error.doc : { code: "internal_error", message: String(error) } };
      }
    });
  }, [key, Boolean(failed)]);

  return {
    depth,
    busy,
    failed,
    // A failure of the source itself (not of the point) may pass: „Pobierz ponownie”
    onRetry: failed && failed.fields.pmaxtp_depth ? () => setFailure(null) : null,
    reset: () => {
      fetches.cancel();
      setFailure(null);
    },
  };
}
