// The form of one catalog command, generated from its commands-1 entry (plan D11):
//   html`<${CommandForm} command=${doc} values=${values} onChange=${set} errors=${errors} hide=${[]} />`
// A message of `errors` stands under its field; one without a shown field (key "#form",
// an option the form does not show) stands above the form.

import { html, useMemo, useState } from "../html.js";
import { ChoiceField, CheckField } from "../controls/choice-field.js";
import { FileField } from "../controls/file-field.js";
import { JsonField } from "../controls/json-field.js";
import { NumberField } from "../controls/number-field.js";
import { ChipsField, SeriesField } from "../controls/series-field.js";
import { TextField } from "../controls/text-field.js";
import { richText, splitReason } from "../controls/field.js";
import { t } from "../labels/common.js";
import { errors as errorTexts } from "../labels/errors.js";
import { formTexts } from "../labels/options.js";
import { Seg } from "../ui/seg.js";
import { fieldModel, isActive, isRequired, ONE_OF_KEY, oneOfKeyText } from "./model.js";

/** The key of `errors` for a message that belongs to no field. */
export const FORM_ERROR = "#form";

const CONTROLS = {
  number: NumberField,
  integer: NumberField,
  choice: ChoiceField,
  boolean: CheckField,
  series: SeriesField,
  chips: ChipsField,
  json: JsonField,
  objects: JsonField,
  "file-in": FileField,
  "file-out": FileField,
  text: TextField,
};

/**
 * The head of a command's form: its name, Polish summary and effects.
 *
 * @param {{entry: object}} props the command entry
 * @returns {object} the head
 */
function CommandHead({ entry }) {
  const polish = (entry.i18n && entry.i18n.pl) || {};
  const effects = entry.effects || {};
  return html`
    <div class="cmd-head">
      <h3><code>${entry.name}</code></h3>
      <p>${richText(polish.summary || entry.summary)}</p>
      <div class="chips">
        <span class="chip">${effects.read_only === false ? formTexts.effects.writes : formTexts.effects.readOnly}</span>
        <span class="chip">${effects.network ? formTexts.effects.network : formTexts.effects.offline}</span>
        <span class="chip">${t(formTexts.effects.mcp, { id: entry.operation_id })}</span>
      </div>
    </div>
  `;
}

/**
 * The messages that stand above the form: those of no shown field.
 *
 * @param {{messages: Array<string|{title?: string, text: string}>}} props the messages
 * @returns {object|null} the box
 */
function FormErrors({ messages }) {
  if (!messages.length) return null;
  const titled = messages.find((message) => typeof message === "object" && message.title);
  return html`
    <div class="form-errors" role="alert">
      <strong>${titled ? titled.title : errorTexts.aboveForm}</strong>
      <ul>
        ${messages.map((message) => {
          const { text, reason } = splitReason(typeof message === "object" ? message.text : message);
          return html`<li>${richText(text)}${reason ? html` <span class="reason">· ${reason}</span>` : null}</li>`;
        })}
      </ul>
    </div>
  `;
}

/**
 * The form of one catalog command.
 *
 * @param {{command: object, values?: object, onChange: (values: object) => void,
 *   errors?: Object<string, string|{title: string, text: string}>, hide?: string[],
 *   labels?: Object<string, string>, head?: boolean, idPrefix?: string,
 *   formId?: string, onSubmit?: () => void}} props the hydrolog-commands/1 document (or its
 *   entry), the values, the change handler (all values), messages by option name, options
 *   the caller supplies itself, label overrides, whether to show the head, the prefix of
 *   control ids, the form's id (for a submit button outside it) and the submit handler
 * @returns {object} the form
 */
export function CommandForm({
  command,
  values = {},
  onChange,
  errors = {},
  hide = [],
  labels,
  head = true,
  idPrefix,
  formId,
  onSubmit,
}) {
  const model = useMemo(() => fieldModel(command, { labels, hide, values }), [command, values, labels, hide.join("|")]);
  const entry = model.command;
  const prefix = idPrefix || `cf-${entry.operation_id || entry.name.replace(/\W+/g, "-")}`;
  const [moreOpen, setMoreOpen] = useState(null);
  const byName = new Map(model.fields.map((field) => [field.name, field]));
  const shown = new Set(model.fields.filter((field) => isActive(model, field)).map((field) => field.name));
  const loose = Object.entries(errors)
    .filter(([name, message]) => message && (name === FORM_ERROR || !shown.has(name)))
    .map(([, message]) => message);

  const set = (name, value) => onChange({ ...values, [name]: value });
  const renderField = (field) => {
    const Control = CONTROLS[field.kind] || TextField;
    return html`<${Control}
      key=${field.name}
      field=${field}
      id=${`${prefix}-${field.name}`}
      value=${values[field.name]}
      error=${typeof errors[field.name] === "object" ? errors[field.name].text : errors[field.name]}
      required=${isRequired(model, field, values)}
      disabled=${Boolean(field.disabledBy)}
      onInput=${(value) => set(field.name, value)}
    />`;
  };
  const renderName = (name) => {
    if (name === ONE_OF_KEY) return renderOneOf();
    const field = byName.get(name);
    return field && isActive(model, field) ? renderField(field) : null;
  };
  const renderOneOf = () => {
    const choice = model.oneOf;
    const group = choice.groups[choice.chosen];
    const legendId = `${prefix}-one-of`;
    return html`
      <fieldset class="one-of" key=${ONE_OF_KEY}>
        <legend id=${legendId}>${choice.title} <span class="key">${oneOfKeyText(choice.count)}</span></legend>
        <${Seg}
          items=${choice.groups.map((item) => ({ value: item.index, label: item.label, title: item.members.join(" + ") }))}
          value=${choice.chosen}
          onChange=${(index) => set(ONE_OF_KEY, index)}
          labelledBy=${legendId}
          full=${true}
        />
        <div class="pane" data-pane=${String(choice.chosen)}>
          ${group.names.map((name) => renderField(byName.get(name)))}
        </div>
      </fieldset>
    `;
  };
  const errorInMore = (section) => section.names.some((name) => errors[name]);
  const rules = (entry.i18n && entry.i18n.pl && entry.i18n.pl.rules) || [];

  return html`
    <form
      class="cmd-form"
      id=${formId}
      novalidate
      onSubmit=${(event) => {
        event.preventDefault();
        if (onSubmit) onSubmit();
      }}
    >
      ${head ? html`<${CommandHead} entry=${entry} />` : null}
      <${FormErrors} messages=${loose} />
      ${model.groups.map((section) => {
        if (section.id === "main") return section.names.map(renderName);
        if (section.id === "more") {
          const open = errorInMore(section) || (moreOpen === null ? section.open : moreOpen);
          return html`
            <details class="more" key="more" open=${open} onToggle=${(event) => setMoreOpen(event.currentTarget.open)}>
              <summary>${section.title} <span class="meta">${section.names.length}</span></summary>
              ${open ? section.names.map(renderName) : null}
            </details>
          `;
        }
        return html`
          <fieldset class="form-section" key=${section.id}>
            <legend>${section.title}</legend>
            ${section.names.map(renderName)}
          </fieldset>
        `;
      })}
      ${rules.length
        ? html`<p class="note">${formTexts.rules}: ${richText(rules.join(" "))}</p>`
        : null}
    </form>
  `;
}
