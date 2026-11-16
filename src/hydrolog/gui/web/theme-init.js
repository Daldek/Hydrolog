// Before the first paint: the stored theme (key "nogat-theme", shared with Nogat's other
// pages; "auto" or nothing follows the system) and the embedded flag "?nogat=1", which
// hides Hydrolog's own top bar and rail inside Nogat's shell (data-host="nogat").
try {
  var t = localStorage.getItem("nogat-theme");
  if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
} catch (e) {}
if (new URLSearchParams(window.location.search).get("nogat") === "1") {
  document.documentElement.dataset.host = "nogat";
}
