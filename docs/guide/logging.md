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
any handler you added yourself. It takes `level`, `sink` (anything
`logger.add` accepts: a stream, a file path, a function) and `format`
(`tesserae.log.DEFAULT_FORMAT` by default), and returns the handler id.

## What Tesserae logs

| Level | Message |
|---|---|
| `DEBUG` | a screen loaded (`app.load`), a screen shown (`app.show`), the traceback of a failed hot reload |
| `INFO` | hot reload started, and what it watches; each view reloaded; each theme or stylesheet file applied |
| `WARNING` | Python warnings such as `FontFallbackWarning`, when `configure_logging` captures them (below) |
| `ERROR` | a hot reload that failed, naming the file and the error |

Each message carries the Tesserae module it came from (`tesserae.app`,
`tesserae.spec.watch`), which loguru shows as `{name}`.

## Failed hot reloads

When a background reload fails, from a YAML error, an unknown component,
or a spec or stylesheet `tre` rejects, Tesserae logs one `ERROR` line
naming the file. The traceback is logged at `DEBUG`, so a typo doesn't
print a stack trace unless you ask for one. The screen stays as it was,
and the app and the watcher keep running. `ViewWatcher.poll()`, which
your own loop calls, still raises instead.

## Warnings

`FontFallbackWarning` is a real Python warning, so
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
