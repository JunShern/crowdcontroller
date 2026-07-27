# Crowd Controller

Let a room full of people play one video game together from their phones.

Everyone opens a link, gets an on-screen game controller, and presses buttons.
Every second, the votes are tallied and the single most popular button press is
sent to the game as a real keystroke. A projector-friendly dashboard shows the
live vote counts and a countdown to the next move.

This was originally built to run a game of *Stardew Valley* at a wedding
reception: one character stood still while a crowd of guests voted to steer a
second character across the map to find them. The code is not tied to that,
though — everything the crowd does is just a keypress, so it works with any game
that takes keyboard and mouse input.

> **A note on this documentation.** It was written by
> [Claude](https://claude.ai), an AI assistant, based on a read-through of the
> code in this repo.
>
> If you'd like to run this and get stuck, the setup assumes a fair amount of
> technical background (see the next section). Two good ways to get unstuck:
> ask a friend who does software development, or paste the errors you're
> hitting into an AI assistant such as [Claude](https://claude.ai) or ChatGPT
> and work through it with them.

---

## Please read this first

**This is a working prototype, not a product.** It was written to be run once,
by a developer, who could fix things live if they broke. It is shared because
people asked how it worked, and it might save you a weekend if you want to build
something similar.

There is no installer, no setup wizard, and no hosted version you can just sign
up for. To run it you will need to be comfortable with all of the following:

- Running commands in a terminal
- Installing Python packages
- Deploying a small web service to a host like Railway, Render, or Fly.io
  (free tiers are fine) and getting a public HTTPS URL back
- Editing a couple of config values in Python files
- Debugging it yourself if something misbehaves on the day

If several of those are unfamiliar, this will likely be a frustrating project
rather than a fun one — that's a completely reasonable place to be, and it's
worth knowing now rather than the night before your event.

You will also need, physically:

- **A dedicated computer to run the game.** The crowd controls its keyboard and
  mouse, so nobody can use it for anything else while the game is running.
- **A second computer and a second copy of the game**, if you want the
  two-player setup described above. Two players means two accounts and two
  licenses.
- **A projector or big screen**, so the crowd can see what they're doing.
- **Decent internet for your guests.** Everyone's phone needs to reach your
  backend. Venue wifi or good cell service — test this in the actual room.

Budget an afternoon for setup, and **do a rehearsal with a few friends before
the real event.**

---

## How it works

```
Audience phones (web UI) → Backend server → Controller → Game
        └───────────────────────────┴──────────────────→ Visualizer
```

1. **Audience votes.** Guests open the link on their phones and tap buttons. Each
   tap sends a command over a WebSocket.
2. **Backend relays.** A small FastAPI server receives commands and broadcasts
   them to connected clients. It holds no state and makes no decisions.
3. **Controller aggregates.** A script on the gaming computer connects to the
   backend as a client and counts every command it sees in a one-second window.
4. **Controller executes.** When the window closes, the most-voted command wins
   and is sent to the game as a keystroke via PyAutoGUI.
5. **Visualizer displays.** A local dashboard shows live vote bars, the
   countdown, and a history of executed commands — put this on the projector.

The backend has to be publicly reachable because guests' phones are on mobile
networks, but the controller only makes an outbound connection, so the gaming
computer can sit behind any normal home or venue network.

### The components

| Path | What it does |
| --- | --- |
| `backend/main.py` | FastAPI + WebSocket relay. This is the part you deploy. |
| `backend/static/index.html` | The phone controller UI (NES.css styled). |
| `controller/crowd_aggregator.py` | Main script: tallies votes, executes the winner, serves the dashboard. |
| `controller/controller.py` | Maps command names to actual key/mouse presses. |
| `controller/visualizer.html` | The projector dashboard. |
| `controller/direct_control.py` | Debug mode: executes every command immediately, no voting. Useful for testing that keystrokes reach the game. |

---

## Setup

### 1. Deploy the backend

The backend is a standard FastAPI app. A `Procfile` and `railway.toml` are
included, so on Railway you can point it at this repo and it should build
without changes. Any host that runs Python and supports WebSockets works too.

You need to end up with a public URL, e.g. `https://your-app.up.railway.app`.
Open it in a browser — you should see the controller UI with a green
"Connected" indicator in the corner.

To run it locally instead (for testing on your own network):

```bash
pip install -r requirements.txt
python backend/main.py     # serves on http://localhost:8000
```

### 2. Set up the gaming computer

Install the controller dependencies:

```bash
pip install -r controller/requirements.txt
```

**On macOS you must grant Accessibility permission**, or PyAutoGUI will silently
do nothing. Go to *System Settings → Privacy & Security → Accessibility* and
enable whichever app you launch the script from (Terminal, iTerm, VS Code…).
This is the single most common reason for "nothing happens."

Verify that keystrokes actually reach the game before going further:

```bash
python controller/controller.py
```

This gives you five seconds to click into the game window, then fires a few test
inputs. If your character doesn't move, fix that before continuing.

### 3. Run the controller

Point the controller at your backend and start it:

```bash
export CROWD_BACKEND_URL="wss://your-app.up.railway.app/ws"
export JOIN_URL="your-short-link.example"   # optional, shown on the dashboard
python controller/crowd_aggregator.py
```

Note the `wss://` scheme (not `https://`) and the `/ws` path on the end.

Then open <http://localhost:8080> for the dashboard and put it on the projector.

### 4. Share the link

Give guests the backend URL. A short link or a QR code is much easier to read
off a projector than a long hosting URL.

Click into the game window and leave it focused — keystrokes go to whatever
window is in front.

---

## Configuration

Set as environment variables before starting:

| Variable | Default | Meaning |
| --- | --- | --- |
| `CROWD_BACKEND_URL` | `ws://localhost:8000/ws` | WebSocket address of your backend |
| `JOIN_URL` | *(unset)* | Link shown on the dashboard banner; hidden if unset |
| `VISUALIZER_PORT` | `8080` | Port for the local dashboard |
| `PORT` | `8000` | Port the backend listens on when run directly |

In `controller/crowd_aggregator.py`:

- `AGGREGATION_WINDOW` — voting window in seconds. `1` feels responsive; longer
  windows (3–5s) give a bigger crowd time to coordinate and make the vote bars
  more fun to watch. Worth experimenting with during your rehearsal.

## Commands

The default action set is tuned for *Stardew Valley*:

| Button | Input sent |
| --- | --- |
| MOVE_UP / DOWN / LEFT / RIGHT | `W` / `S` / `A` / `D` |
| PICKAXE | `1`, then left-click |
| WATER | `2`, then left-click |
| PROPOSE | `3`, then right-click |
| YES | `Y` |

To adapt this to another game you'll need to edit three places consistently:

1. `controller/controller.py` — the `Action` enum and the key sequences in
   `Controller.execute()`
2. `backend/static/index.html` — the `data-action` buttons
3. `backend/static/index.html` — the `commandFeedback` map (the emoji that pop
   up when a button is pressed)

The names must match exactly across all three.

---

## Known limitations

Things to know before you rely on this in front of an audience:

- **There is no authentication.** Anyone with the link can vote. An unguessable
  short link is your only access control. Don't post it publicly during an
  event.
- **There is no moderation.** You cannot mute or kick anyone, and a determined
  person can spam commands to skew the vote. At a private event, social pressure
  handles this fine. At an open one, it won't.
- **The backend broadcasts every command to every connected client**, so traffic
  grows quickly with crowd size. It was tested at wedding-reception scale, not
  with hundreds of simultaneous users.
- **The game window must stay focused.** Anything that steals focus — a
  notification, a screensaver, someone alt-tabbing — sends the crowd's
  keystrokes into the wrong place.
- **PyAutoGUI's failsafe is enabled.** Moving the mouse into a screen corner
  aborts the running action by design. Keep the mouse away from the edges.
- **Only tested on macOS.** It should work anywhere PyAutoGUI does, but Windows
  and Linux are untested.
- **No reconnect guarantees.** The controller retries the backend every five
  seconds, but if your host sleeps a free-tier instance, expect a gap.

---

## License

MIT — see [LICENSE](LICENSE). Do what you like with it; no warranty.

Built with FastAPI, WebSockets, PyAutoGUI, and
[NES.css](https://nostalgic-css.github.io/NES.css/).
