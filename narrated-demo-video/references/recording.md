# Take: a Playwright recording paced to the voice

Record one continuous take with `@playwright/test`'s `chromium` and `recordVideo`. Keep the recorder script under
the app repository's `.context/demo/` and run it **from the app repository root**: the kit resolves Playwright
from the working directory, because the kit itself lives outside the app.

## The kit

[`scripts/recorder_kit.mjs`](../scripts/recorder_kit.mjs) exports `createTake()`:

```js
import { createTake } from "<skill-dir>/scripts/recorder_kit.mjs";

const take = await createTake({
  outDir: ".context/demo/take",
  durations: ".context/demo/vo/durations.json",
  storageState: ".context/demo/auth-state.json",      // optional: start signed in
  hide: ['button[aria-label="Open TanStack Router Devtools"]'], // dev-only chrome to hide
});
const { page, mark, waitForLine, pointAt, clickLike, smoothScroll, typeHuman, pause } = take;

await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });
let vo = mark("vo:1_arrive");               // the line "1_arrive" starts here
await clickLike(page.getByRole("link", { name: /get started/i }));
await waitForLine(vo, "1_arrive");          // hold the scene until the line has finished, plus a breath
// … more scenes …
mark("end");
await take.finish();                        // writes marks.json, closes the context so the video is finalised
```

`mark("vo:<key>")` names must match the keys in `durations.json`. Always finish with `mark("end")`. If a step
throws, call `take.fail(error)`: it screenshots, dumps the page text, and still closes the context, because an
unclosed context leaves a `.webm` with no duration that ffprobe cannot read.

## What makes it feel human

- **Pointer.** Playwright videos have no cursor. The kit injects a fixed `div` moved by a CSS `transform`
  transition and glides it to each target about 0.6 s before the click. Because it is positioned in page
  coordinates, it also works over third-party iframes.
- **Typing.** `typeHuman()` presses one character at a time: 85–190 ms between keys, 260–420 ms after every
  fourth character so card numbers and codes land in groups.
- **Scrolling.** `smoothScroll(y, ms)` uses `behavior: "smooth"`; give each move 1.5–2 s.
- **Pauses.** Let key states sit: 2–3 s on an error message or a success toast. `waitForLine()` does most of
  this for free.

## Pacing to the voice

Start each scene's narration at a `mark`, do the scene's actions, then `waitForLine(mark, key)`. To land a word
on an action, delay the action instead: `await pause(durations[key] * 1000 - 3200)` before the click puts the
click near the end of the line. Dead air of 3–5 s between lines is normal while pages load; the bed covers it.

## Sign in off camera

Never record a login form. Sign in with a separate, unrecorded context, wait for the app's first authenticated
API response (navigating away earlier can abandon the token exchange), then
`await context.storageState({ path })` and pass that file as `storageState`. The file holds tokens: keep it
under `.context/`, `chmod 600`, and delete it when the video is done.

## Third-party payment fields

Stripe's Payment Element lives in one of several `__privateStripeFrame*` iframes and renders as an accordion.
Find the frame by content rather than by index (the first frame is a hidden controller), click the "Card"
header, then fill the fields; several labels match more than once, so use `.first()`. Test cards: `4242 4242
4242 4242` succeeds, `4000 0000 0000 0002` declines.

## Refreshing app state without a reload

If the recorder changes server state behind the app's back, a page reload shows as a flash. For TanStack Query
apps, `window.dispatchEvent(new Event("offline"))` followed by `"online"` refetches stale queries in place.

## Staging, honestly

If a step in the journey is not built yet, drive it through the API at that moment so the story stays
continuous, then **disclose it** next to the published video. Confirm the real parts really happened: check the
API response and the database, not just the screen.

A continuous take exercises paths that separate clips never do. A decline-then-retry take once exposed a real
idempotency bug on the retry. Treat surprises in the take as findings, not as noise to edit around.

## After the take

Revert any temporary patches made to get the flow working locally, confirm the working tree is clean, and list
what was seeded or charged (test-mode payments, database rows) in the final report.
