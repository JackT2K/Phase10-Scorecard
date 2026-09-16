# P10 Family Scorekeeper

P10 is a self-hosted, mobile-first Phase 10 scorekeeper built for families who want to digitize notebook records, track long-term statistics, and run synchronized live games from their phones.

The application includes historical game entry, player and notebook management, live score submission with host approval, an installable Progressive Web App, and a full-screen TV dashboard.

> P10 is an independent family project. It is not affiliated with, endorsed by, or sponsored by Mattel.

## Features

### Historical score tracking

- Add historical games from paper notebooks
- Store exact, approximate, month-only, year-only, or unknown dates
- Preserve notebook name, page, and sequence order
- Record final scores only, per-round scores, or mixed records
- Edit and delete existing games
- Duplicate games with the same participants
- Automatically suggest the next notebook sequence number
- Export game data to CSV

### Player management

- Add and edit players
- Assign each player a custom color
- Activate or deactivate players without losing history
- View individual player statistics and score trends

### Notebook management

- Add and edit notebooks
- Store notebook descriptions
- Delete a notebook without deleting its games
- Preserve games under “No notebook” after notebook deletion

### Statistics

- Lowest average score
- Most wins
- Lowest and highest recorded scores
- Completed games and DNFs
- Player score trends
- Player phase statistics
- Head-to-head statistics
- Recent game history

DNF players remain visible in game history but are excluded from completed-game averages and win calculations.

### Live gameplay

- Create a live game with a four-character join code
- Select participating players and the host
- Join directly from the home screen
- Mobile player identity selection
- Shared Phase 10 round card
- Colored player initials displayed beside each player’s current phase
- Current player phase highlighting
- Support for several players occupying the same phase
- Explicit Playing, Scoring, Review, and Next Round states
- Score entry opens only after the host ends the round
- Private score submissions
- Phase-completion submission
- Automatic player-screen updates
- Host score entry from the host screen
- Host approval, correction, or rejection of submitted scores
- Approve all submissions and start the next round
- Prevent advancement until every active player submits
- Mark a player as having left the game
- Preserve departed players as DNF
- Automatically end the game when Phase 10 is completed
- Archive completed live games into normal game history

### TV dashboard

The full-screen TV dashboard is available at:

```text
/tv
```

Idle mode rotates through:

- Lowest average leaderboard
- Most wins leaderboard
- Head-to-head statistics
- Historical score trends
- Recent games

When a live game exists, the dashboard switches to live-game presentation mode and displays:

- Current cumulative standings
- Phase progress
- Player score-submission status
- Host-review status
- Approved per-round score trends
- Players who left the game

The TV dashboard is designed for a Smart TV browser, Chromecast tab casting, or a small computer connected to a television.

### Installable app

P10 is an installable Progressive Web App.

Included PWA support:

- Web app manifest
- Service worker
- Offline fallback screen
- Android and Chromium install prompt
- Apple Add to Home Screen metadata
- App icons and favicons
- Standalone app display
- Shortcuts for Live Game, Add Game, and TV Dashboard

PWA installation requires HTTPS, except when testing from localhost.

## Screens and routes

```text
/                         Home dashboard
/games/new                Add a historical game
/history                  Game history
/players                  Player management
/notebooks                Notebook management
/stats                    Statistics dashboard
/live                     Create or manage a live game
/live/join                Join a live game
/tv                       Full-screen TV dashboard
/export.csv               Export historical data
```

## Technology

- Python
- Flask
- Gunicorn
- SQLite
- Jinja templates
- Chart.js
- Docker Compose
- Progressive Web App manifest and service worker

## Requirements

- Ubuntu Server or another Docker-capable Linux distribution
- Docker Engine
- Docker Compose plugin
- A reverse proxy for HTTPS is strongly recommended

The included installer can install Docker and its prerequisites on a base Ubuntu Server installation.

## Installation on Ubuntu Server

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd p10-v1
```

Make the scripts executable:

```bash
chmod +x install.sh backup.sh
```

Run the installer:

```bash
sudo ./install.sh
```

The installer:

1. Installs prerequisite packages.
2. Adds Docker’s Ubuntu package repository.
3. Installs Docker Engine and Docker Compose.
4. Enables Docker at startup.
5. Creates the `.env` file if one does not exist.
6. Generates an application secret and household PIN.
7. Builds and starts the P10 container.

## Manual configuration

Copy the environment template if needed:

```bash
cp .env.example .env
```

Example configuration:

```dotenv
SECRET_KEY=replace-with-a-long-random-value
HOUSEHOLD_PIN=change-me
HOUSEHOLD_NAME=My Family
DATABASE_PATH=/data/p10.db
P10_BIND_IP=127.0.0.1
P10_PORT=8080
SESSION_COOKIE_SECURE=false
```

After enabling HTTPS, set:

```dotenv
SESSION_COOKIE_SECURE=true
```

Apply configuration changes:

```bash
docker compose up -d --build
```

## Direct LAN access

The default deployment binds to localhost for use behind a reverse proxy:

```dotenv
P10_BIND_IP=127.0.0.1
```

For direct LAN access, change it to:

```dotenv
P10_BIND_IP=0.0.0.0
```

Then restart:

```bash
docker compose up -d
```

Do not expose the application directly to the public internet without HTTPS and an appropriate access-control layer.

## Reverse proxy

The application is intended to run under one hostname, for example:

```text
p10.example.com
```

All statistics, live gameplay, history, and TV functionality use paths under the same hostname.

## Common commands

Start or rebuild:

```bash
docker compose up -d --build
```

View container status:

```bash
docker compose ps
```

Follow application logs:

```bash
docker compose logs -f
```

Restart the application:

```bash
docker compose restart
```

Stop the application:

```bash
docker compose down
```

## Backups

Run the included backup script:

```bash
./backup.sh
```

Backups are stored under:

```text
./backups/
```

The primary application database is stored in the Docker volume at:

```text
/data/p10.db
```

Keep periodic copies of the SQLite database outside the VM or host running P10.

## Updating

For a Git-based deployment:

```bash
git pull
docker compose up -d --build
```

## PWA installation

### Android or Chromium desktop

1. Open P10 over HTTPS.
2. Refresh the page once after deployment.
3. Use the browser’s Install App option.

### iPhone or iPad

1. Open P10 in Safari.
2. Open the Share menu.
3. Select Add to Home Screen.

Live scoring, statistics, and game synchronization require connectivity to the P10 server. The service worker only provides the application shell and offline fallback page.

The original patch-era stylesheets are removed by the CSS consolidation installer after validation.

## Data behavior

- A player who leaves a live game is preserved as DNF.
- DNF players retain recorded scores and rounds.
- DNF results do not count as completed-game averages or wins.
- A completed Phase 10 live game is archived into normal history.
- Notebook sequence remains independent from game date.
- Deactivating a player does not remove historical records.
- Deleting a notebook does not delete its games.

## Security notes

The household PIN is intended for a private family application. For stronger protection, place P10 behind one or more of the following:

- A private VPN
- NetBird or another overlay network
- An identity-aware reverse proxy
- An authenticated access gateway

Use HTTPS for all remote access, especially for PWA installation and session-cookie security.

## Disclaimer

Phase 10 is a trademark of its respective owner. This repository is an independent scorekeeping and family game companion project and does not include official artwork, card assets, or game software.
