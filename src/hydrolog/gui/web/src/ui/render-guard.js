// A boundary around the drawing of a result: an error while its children render or draw (a
// chart's effect included) shows as an error in their place, never as the previous result
// still on the screen, and the section hears of it (`onError`) to mark its status. A new
// `resetKey` (the next result, or none after „Wyczyść”) draws the children again.

import { Component, html } from "../html.js";
import { common, t } from "../labels/common.js";

export class RenderGuard extends Component {
  /**
   * @param {{resetKey: unknown, onError?: (error: unknown) => void, name: string, children:
   *   object}} props the key whose change clears the error, the handler that hears of one,
   *   the name of the place for tests, and what is drawn
   */
  constructor(props) {
    super(props);
    this.state = { error: null, key: props.resetKey };
  }

  static getDerivedStateFromProps(props, state) {
    return props.resetKey === state.key ? null : { error: null, key: props.resetKey };
  }

  componentDidCatch(error) {
    this.setState({ error });
    if (this.props.onError) this.props.onError(error);
  }

  render({ name, children }, { error }) {
    if (!error) return children;
    const message = error instanceof Error ? error.message : String(error);
    return html`<div class="form-errors" role="alert" data-render-error=${name}>
      <strong>${common.render.title}</strong>
      <div>${t(common.render.text, { message })}</div>
    </div>`;
  }
}
