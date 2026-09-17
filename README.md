# P10 Family Scorekeeper

P10 is a self-hosted companion app for families who love playing Phase 10 and want more than a simple score sheet. It combines historical score tracking, statistics, live game management, TV dashboards, and an installable mobile experience into a single application.

P10 was designed around a real-world family use case: years of handwritten notebook scores, ongoing friendly competition, and the desire to see long-term trends without losing the simplicity of sitting around a table and playing cards.

---

# What P10 Does

## Historical Game Archive

P10 can store years of historical game records.

Features include:

- Notebook organization
- Notebook page tracking
- Notebook sequence tracking
- Exact or approximate dates
- Final score entry
- Per-round score entry
- Mixed entry methods
- Editing previously entered games
- Duplicate game creation for repeated groups

This makes it possible to digitize old scorebooks while preserving the original order of games.

---

## Player Profiles

Each player has a profile that includes:

- Name
- Custom color
- Active or inactive status
- Historical participation records
- Statistics
- Phase progress history

Players can be disabled without losing history.

---

## Statistics & Trends

P10 automatically calculates statistics from completed games.

Examples include:

- Lowest average score
- Most wins
- Highest score
- Lowest score
- Completed games
- DNF counts
- Player score trends
- Head-to-head comparisons
- Recent game history

The goal is to make long-term family competition fun and easy to follow.

---

## Live Gameplay

Live gameplay allows players to participate using phones or tablets.

Features include:

- Live game creation
- Join code support
- Player identity selection
- Host controls
- Shared phase tracking
- Round review workflow
- Score submission
- Manual score entry
- Pause and resume support
- Automatic game completion

---

## Host Review Workflow

P10 intentionally separates playing from scoring.

Typical flow:

1. Players play the round.
2. Host ends the round.
3. Score entry opens.
4. Players submit scores.
5. Host reviews scores.
6. Host advances the game.

This helps prevent accidental score entry mistakes.

---

## Manual Score Entry

Not every player has a device available.

Hosts can enable:

"Host Enters Score"

for individual players.

When enabled:

- Player devices cannot submit scores.
- Host enters scores manually.
- Manual scores are approved immediately.

This is useful for younger players, guests, or anyone without a phone.

---

## Pause & Resume Games

Some Phase 10 games take a long time.

P10 supports:

- Pausing a live game
- Resuming another day
- Starting a different game while one is paused
- Preserving rounds, phases, and scores

Paused games do not appear in TV dashboard live mode.

---

## Phase Tracking

P10 includes a visual Phase 10 card that displays:

- Current player phases
- Colored player markers
- Shared table progress
- Personal phase highlighting

Multiple players can occupy the same phase and the display automatically adjusts.

---

## Automatic Completion

When a player completes Phase 10:

- The live game ends
- Historical records are generated automatically
- Rounds are preserved
- Statistics update automatically

This eliminates duplicate entry work.

---

## TV Dashboard

The TV dashboard is designed for wall displays, smart TVs, Chromecast sessions, or small computers connected to a television.

When no live game is active it displays:

- Rankings
- Trends
- Wins
- Head-to-head statistics
- Recent games

When a live game is active it displays:

- Current standings
- Score status
- Phase progress
- Live trends
- Participation status

---

## Installable App

P10 is a Progressive Web App (PWA).

Supported features:

- Install on phones
- Install on tablets
- Add to Home Screen
- Standalone app mode
- App icon support
- Offline shell support

Users can interact with P10 like a native application without downloading from an app store.

---

# Setup

## Install Prerequisites

```bash
sudo ./install-prereqs.sh
```

## Configure and Start P10

```bash
./install.sh
```

The installer creates:

- Required folders
- Database location
- Application secrets
- Household PIN

Then it starts the application automatically.

---

# Backups

Create a backup using:

```bash
./backup.sh
```

Backups include:

- Database
- Environment configuration

Regular backups are strongly recommended.

---

# Designed For Families

P10 was created to make family game history fun, accessible, and easy to preserve.

Whether you're adding years of notebook records or tracking a live game in progress, P10 is focused on making Phase 10 more enjoyable without getting in the way of playing the game.


# Disclaimer

## Trademark Notice

Phase 10® is a registered trademark of Mattel, Inc.

P10 Family Scorekeeper is an independent community-created scorekeeping and companion application designed for tracking scores, statistics, and gameplay history for personal use.

This project is not affiliated with, endorsed by, sponsored by, authorized by, or connected to Mattel, Inc. in any way.

No official Phase 10 game assets, card artwork, card images, logos, packaging artwork, proprietary game content, or copyrighted materials are included with this project.

All trademarks, product names, and registered trademarks remain the property of their respective owners and are used solely for identification and compatibility purposes.

If you are the owner of any intellectual property referenced by this project and believe content should be modified or removed, please contact the project maintainer.

## Fan Project Disclaimer

P10 Family Scorekeeper is a fan-created utility intended to help families and friends record scores, track statistics, and manage game history.

This software does not provide the Phase 10 game itself and is not intended to replace or reproduce the original card game. Ownership of a legitimate copy of the game may be required depending on how the software is used.

This project exists solely as a companion tool for game tracking and record keeping.