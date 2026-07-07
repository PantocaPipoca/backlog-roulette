# Backlog Roulette

A terminal app that picks what you play, watch, or read next by chance, not by choice.

## The problem

Steam sales, Humble Bundles, secondhand bookshops, "just one more DLC," it's never one game, one movie, or one book. It's fifty. Life happens, and the backlog keeps growing while your free time doesn't. Eventually you're staring at a library so big that choosing anything feels like a chore, so you start three things, finish none, and buy five more during the next sale.

Backlog Roulette takes the decision out of your hands. You feed it your backlog, it spins a wheel, and whatever comes up is what you're doing next. No more scrolling your library for twenty minutes. No more "eh, maybe something else." The wheel decides, so just embrace the gambler inside you and let luck decide what's best for you :).

It works for games, movies, and books alike, and supports tiers, so the things you're genuinely hyped for get better odds without completely burying the smaller stuff you also want to get around to eventually.

## Features

- Smart roulette: weighted odds with customizable tiers, rerolls, and Top X candidate selection.
- Universal backlog types: support for games, movies, books, and any custom category you want to add.
- Focus system: the roulette really takes charge and only lets you have one active item (for example, one active game) before spinning again. So finish it first, then move on to the next pick. Of course, this is completely optional :)
- Progress tracking: complete history of spins, finishes, drops, ratings, and other activity.
- Fully customizable: adjust settings and behavior to match your preferred workflow.
- Terminal UI: colorful, fast, and built with a bit of personality.

## Requirements

* Python 3.10 or newer
* No external dependencies, everything runs on the standard library

## Installation

### Option A: Download the executable (no Python required)

Grab the latest build for your OS from the [Releases page](https://github.com/PantocaPipoca/backlog-roulette/releases), put it in its own folder, and run it. It'll create `roulettes/` and `data/` next to itself on first run.

### Option B: Run from source

```bash
git clone https://github.com/PantocaPipoca/backlog-roulette.git
cd backlog_roulette
python main.py
```

## Setting up your first wheel

Backlog Roulette reads lists from a `roulettes/` folder (created automatically on first run) as plain JSON files. Each file represents one wheel for one backlog type.

```json
{
  "type": "games",
  "tiers": { "S": 50, "A": 35, "B": 15 },
  "items": [
    {
      "name": "Elden Ring",
      "tier": "S",
      "estimated_hours": 60,
      "note": "Already 20h in, just finish it"
    },
    {
      "name": "Resident Evil 4 Remake",
      "tier": "S",
      "series": ["Resident Evil"],
      "completion_condition": "Beat on Standard"
    },
    {
      "name": "Stardew Valley",
      "tier": "B"
    }
  ]
}
```

Three example wheels ship in `roulettes/` (`example_games.json`, `example_movies.json`, `example_books.json`) so you have something to spin right away.

### Schema reference

| Field | Applies to | Notes |
|---|---|---|
| `type` | required, top level | `"games"`, `"movies"`, or `"books"` |
| `tiers` | optional, top level | Map of tier name to weight. Higher weight means more likely to be picked. If omitted, defaults to `{"S": 50, "A": 35, "B": 15}` |
| `items` | required, top level | Array of item objects |
| `name` | all items | required |
| `tier` | all items | optional, must match a key in `tiers` |
| `series` | all items | optional list, for example `["Resident Evil"]` |
| `note` | all items | optional free text |
| `status` | all items | `idle` (default), `done`, `dropped`, or `incomplete`, managed automatically by the app, you normally don't need to set this by hand |
| `estimated_hours` | games | optional |
| `completion_condition` | games | optional, for example `"Beat the campaign"` |
| `runtime_minutes` | movies | optional |
| `pages` | books | optional |

### Tiers, explained

Tiers don't gate anything, every item in a tier can still be picked. They just weight the odds. A tier weight of 50 versus 15 means items in the first tier are picked roughly 3.3 times more often, but a B tier game can still come up. It's meant to nudge the wheel toward the things you're most excited about without ever fully burying the rest of your backlog.

### Building a wheel fast with AI

Typing out hundreds of games by hand is nobody's idea of fun. The easiest way to build a wheel is to screenshot your library (Steam, Letterboxd, Goodreads, whatever) and hand it to an LLM with a prompt like this:

```
Here's a screenshot of my games/movies/books library.
Convert it into a JSON file following this exact schema:

{
  "type": "games",
  "tiers": { "S": 50, "A": 35, "B": 15 },
  "items": [
    { "name": "...", "tier": "S" or "A" or "B" }
  ]
}

Rules:
* Only include "name" and "tier" unless I tell you otherwise.
* Assign tiers based on how acclaimed the title is, or ask me
  which ones I'm most excited for if you're unsure.
* Return only the JSON, no extra commentary.
```

Drop the result into `roulettes/your_list.json` and you're ready to spin.

## License

MIT License.