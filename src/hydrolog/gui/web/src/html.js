// Preact with htm: the one place that binds the tagged template, re-exporting what the
// components use. Modules import the vendored files by relative paths (CSP script-src
// 'self' blocks import maps), so every module shares one Preact instance.

import htm from "../vendor/htm/htm.mjs";
import { h } from "../vendor/preact/preact.mjs";

export { Component, Fragment, createContext, createRef, h, render } from "../vendor/preact/preact.mjs";
export {
  useCallback,
  useContext,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "../vendor/preact/hooks.mjs";

/** Tagged template rendering Preact elements: html`<div class="x">${child}</div>`. */
export const html = htm.bind(h);
