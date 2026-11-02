// The sections of the GUI, one line each: `id` (router.js, GuiModule.sections) and the
// module whose default export is the section's component (plan D9). The rail shows them in
// the order of SECTION_ORDER; a section not listed here is not shown.

/** @type {Array<{id: string, load: () => Promise<{default: Function}>}>} */
export const SECTIONS = [
  { id: "polecenia", load: () => import("./polecenia/index.js") },
];
