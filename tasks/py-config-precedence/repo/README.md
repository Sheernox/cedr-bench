# notify-digest

Collects pending notifications and posts them to a chat channel as digests.

```
python3 -m notify.cli --config notify.toml < items.txt
python3 -m notify.cli --show-settings
```

## Settings

| Setting          | Type    | Default      | Meaning                                              |
|------------------|---------|--------------|------------------------------------------------------|
| `channel`        | string  | `#general`   | Where digests are posted                              |
| `batch_size`     | integer | `50`         | Items per message; `0` sends everything in one message |
| `retries`        | integer | `3`          | Delivery attempts after the first; `0` never retries |
| `timeout`        | number  | `10.0`       | Seconds to wait for the chat server; `0` waits forever |
| `quiet`          | boolean | `false`      | Print nothing on success                              |
| `dry_run`        | boolean | `false`      | Build the digest but do not send it                   |
| `subject_prefix` | string  | `[digest]`   | Put in front of every message; may be empty           |

Every setting can come from four places. The first one that sets it wins:

1. a command-line flag (`--batch-size 0`, `--quiet` / `--no-quiet`),
2. an environment variable (`NOTIFY_BATCH_SIZE=0`),
3. the config file (`batch_size = 0` under `[notify]`),
4. the default above.

A value that is set always counts, even when it is `0`, `false` or an empty
string. The only exception is an environment variable set to the empty string,
which counts as unset (shells make it too easy to export one by accident).

### Environment variables

Each setting has a variable named `NOTIFY_` plus the setting in capitals.
Integers and numbers are written as usual. Booleans accept `true`/`false`,
`yes`/`no`, `on`/`off` and `1`/`0`, in any case. Any other value is an error
that names the variable.

### Config file

The file is TOML. Settings go under a `[notify]` table; an unknown key or a
value of the wrong type is an error. The file comes from `--config`, then
`NOTIFY_CONFIG`, then the `config_path` a caller passes in. With none of
those, no file is read.

## Library use

```python
from notify.settings import load_settings

settings = load_settings(["--quiet"], {"NOTIFY_CHANNEL": "#ops"})
```

`load_settings(argv, environ=None, config_path=None)` reads the given
environment mapping; with `environ=None` it reads the process environment.

## Tests

```
python3 -m unittest discover -s tests
```
