# tmux cheat sheet

tmux keeps terminals running when you close the window, and lets one screen hold
several of them. That is the whole idea.

Every key below is stock tmux, so it works on any machine — including the remote
VMs `agent-run` starts agents on.

## The one thing to internalise

**Every tmux command starts with the prefix: `Ctrl-b`.** Press and release it,
then press the next key. `Ctrl-b` then `c` is written `prefix c` here.

If nothing happens, you probably held `Ctrl` while pressing the second key.

## Getting in and out

| Do this | Key |
| --- | --- |
| Start a session | `tmux` |
| Start a *named* session | `tmux new -s work` |
| Leave it running and come back to your shell | `prefix d` (detach) |
| Reattach to the last session | `tmux attach` |
| Reattach to a named one | `tmux attach -t work` |
| List what is running | `tmux ls` |
| Kill a session from outside | `tmux kill-session -t work` |

Detaching is the point: the programs inside keep running. Closing the terminal
window does the same thing — nothing is lost.

## Windows — like browser tabs

| Do this | Key |
| --- | --- |
| New window | `prefix c` |
| Next / previous | `prefix n` / `prefix p` |
| Jump to window 3 | `prefix 3` |
| Pick from a list | `prefix w` |
| Rename the current one | `prefix ,` |
| Close it | `exit`, or `prefix &` |

## Panes — splitting one window

| Do this | Key |
| --- | --- |
| Split left/right | `prefix %`  (or `prefix |`) |
| Split top/bottom | `prefix "`  (or `prefix -`) |
| Move between panes | `prefix ←↑↓→` |
| Resize | `prefix H J K L`, repeatable |
| Zoom one pane to fullscreen, and back | `prefix z` |
| Close it | `exit`, or `prefix x` |

`prefix z` is the one people miss. When a pane gets busy, zoom it, read, unzoom.

The `|` and `-` splits are additions here, and they open in the current
directory. `%` and `"` are the real defaults and still work.

## Scrolling back

Mouse scroll works. For the keyboard:

| Do this | Key |
| --- | --- |
| Enter scroll/copy mode | `prefix [` |
| Move | arrows, `PgUp`/`PgDn`, `/` to search |
| Start selecting | `v` |
| Copy and leave | `y` (goes to the macOS clipboard) |
| Leave without copying | `q` |

Selecting with the mouse also copies to the clipboard.

## Additions in this config

Everything else above is stock. These are keys tmux leaves unbound:

| Key | Does |
| --- | --- |
| `prefix r` | Reload `tmux.conf` |
| `prefix \|` / `prefix -` | Split, keeping the current directory |
| `prefix H J K L` | Resize, repeatable without re-pressing the prefix |

The status bar shows `PREFIX` when tmux is waiting for your second key — useful
while the habit forms.

## Watching remote agents

`agent-run monitor` builds a session called `agent-run` with one window per live
run, each streaming that run's output.

```bash
agent-run monitor        # build or refresh it
tmux attach -t agent-run # watch
# prefix n / prefix p to move between agents, prefix d to leave it running
```

Re-running `monitor` adds windows for new runs and prunes finished ones without
disturbing the window you are watching.

To drive one agent rather than watch it, `agent-run attach <name>` puts you
inside the tmux session on that VM. `prefix d` detaches and leaves it working.

## When something looks wrong

| Symptom | Cause | Fix |
| --- | --- | --- |
| Keys do nothing | You are in copy mode | `q` |
| A pane is stuck full-screen | It is zoomed | `prefix z` |
| Colours look flat | Terminal not advertising true colour | Check `echo $TERM` outside tmux |
| Config change had no effect | Not reloaded | `prefix r` |
| `duplicate session` on create | It already exists | `tmux attach -t <name>` |
