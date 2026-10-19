# Logging

Tesserae logs with [loguru](https://loguru.readthedocs.io/). It uses
loguru's shared `logger` and adds no output of its own, so its messages
go wherever your app's loguru setup sends them. With no setup at all,
that's loguru's default output on stderr, so you see them straight away.

## Setting up the console

`configure_logging()` is a one-call setup for `app.py`:

```python
from loguru import logger

from tesserae import App, configure_logging

configure_logging()          # INFO and above, Tesserae's format
# configure_logging("DEBUG") # also shows loads, screen switches, tracebacks

logger.info("starting")      # your own messages use the same logger
```

The output looks like:

```
12:48:27.553 | INFO     | tesserae.spec.watch - reloaded /path/to/Home_View.yaml
```

`configure_logging` replaces loguru's default stderr handler and leaves
any handler you added yourself. Call it once: each call adds a handler, so a second call prints every message twice (`logger.remove(handler_id)` removes one). It takes `level`, `sink` (anything
`logger.add` accepts: a stream, a file path, a function) and `format`
(`tesserae.log.DEFAULT_FORMAT` by default), and returns the handler id.

## What Tesserae logs

| Level | Message |
|---|---|
| `DEBUG` | a screen loaded (`app.load`), a screen shown (`app.show`), the traceback of a failed hot reload |
| `INFO` | hot reload started (`hot reload on: watching N screen(s) and M theme/stylesheet file(s)`), and what it watches; hot reload off in a built app (there are no source files); a screen it does not watch; each view reloaded; each theme or stylesheet file applied; the app switching between light and dark or between standard and high contrast |
| `WARNING` | a view file in the older syntax, once per file (it still loads: `tesserae migrate-yaml` moves it); a `Link` whose `href` is refused (only `http`, `https`, `mailto` and `tel` are opened); a property the user edits given one bare name that cannot be written back (`Main_View.yaml:5:42: Checkbox checked is given 'flag', which is a ViewModel attribute that is not a Signal: the user's edit is not written back (one-way)`), once for each place in a file; Python warnings such as `FontFallbackWarning`, when `configure_logging` captures them (below) |
| `ERROR` | a hot reload that failed, naming the file and the error; a hot-reload watcher that stopped |

Each message carries the Tesserae module it came from (`tesserae.app`,
`tesserae.spec.watch`), which loguru shows as `{name}`. A mistake in a view, such as an unknown property or a name
no ViewModel has, is an exception that names the file, line and column; the one mistake that is logged instead is the one-way property above.

## Failed hot reloads

When a background reload fails, from a YAML error, an unknown widget,
or a spec or stylesheet `tre` rejects, Tesserae logs one `ERROR` line
naming the file. The traceback is logged at `DEBUG`, so a typo doesn't
print a stack trace unless you ask for one. The screen stays as it was,
and the app and the watcher keep running. `ViewWatcher.poll()`, which
your own loop calls, still raises instead.

## Warnings

`FontFallbackWarning` (`from tesserae.fonts import FontFallbackWarning`) is a real Python warning, so
`warnings.filterwarnings("error", category=FontFallbackWarning)` still
turns it into an exception. By default, `configure_logging` also shows
warnings through loguru, so they appear in the same format as
everything else. Pass `capture_warnings=False` to leave Python's own
warning output alone.

## Turning Tesserae's messages off

```python
from loguru import logger

logger.disable("tesserae")                 # everything from Tesserae
logger.disable("tesserae.spec.watch")      # just hot reload
```

`logger.enable("tesserae")` turns them back on.
