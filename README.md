# AIMsLab File Sharing

A LAN file-sharing website, powered by Docker Compose. Anyone on your local
network can browse and download files from a folder on this PC. A single
**admin** signs in to manage those files (upload, new folder, rename, delete)
and to watch **live download/upload speed** on a dashboard.

> **Trusted local network only.** There is no HTTPS and the admin password
> travels in the clear. See [Security](#security).

## Start in three steps

```bash
git clone https://github.com/syanyong/lan-file-portal.git
cd lan-file-portal
cp .env.example .env        # then set ADMIN_PASSWORD (see below)
docker compose up -d --build
```

Put the files you wish to share into the `shared/` directory (or point
`SHARE_PATH` at another folder — see [below](#choose-the-shared-host-folder)).
They appear immediately, no restart needed.

On the server, open <http://localhost:8080>. On another device on the same
network, open `http://SERVER-IP:8080`. Clients need only a browser.

Find the server IP:
- macOS: `ipconfig getifaddr en0` (verify the Wi-Fi device)
- Linux: `hostname -I`
- Windows: `ipconfig`

## The admin page

Visit `/admin` (e.g. <http://localhost:8080/admin>) and sign in with
`ADMIN_PASSWORD`. You get:

- **Live dashboard** — current download & upload throughput, a 60-second
  download/upload speed graph, totals since start, and a list of active
  transfers. Metrics live in memory and reset when the container restarts.
- **File management** — upload files, create folders, rename, and delete, all
  acting on the shared folder.

If `ADMIN_PASSWORD` is blank, the admin page is **disabled** and the site is
download-only. Set it in `.env` and run `docker compose up -d` to enable it.

## Configuration (`.env`)

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | Host port to publish on the LAN | `8080` |
| `SHARE_PATH` | Host folder to share (mounted read-write) | `./shared` |
| `ADMIN_PASSWORD` | Enables the admin page; blank = download-only | _(blank)_ |
| `SESSION_SECRET` | Keeps admins logged in across restarts | _(random each start)_ |
| `MAX_UPLOAD_BYTES` | Upload size cap; `0` disables | `2147483648` (2 GiB) |
| `PUID` / `PGID` | User/group the container runs as | `1000` / `1000` |

## Choose the shared host folder

The default is `./shared`, relative to `compose.yaml`. To share another folder:

1. Create the folder and place only files intended for LAN users inside it.
2. Set `SHARE_PATH` in `.env`, using one of these examples:

   | Host | Example |
   | --- | --- |
   | macOS | `SHARE_PATH='/Users/yourname/AIMSLAB Shared'` |
   | Linux | `SHARE_PATH=/srv/aimslab/shared` |
   | Windows Docker Desktop | `SHARE_PATH='C:/AIMSLAB Shared'` |
   | Docker from WSL | `SHARE_PATH=/mnt/c/AIMSLAB-Shared` |

3. Run `docker compose up -d` to recreate the container.

Use an absolute path for clarity; use forward slashes on Windows and quote
paths containing spaces. Do not use `~`.

**Ownership matters because uploads/deletes write to this folder.** The
container runs as `PUID:PGID` (default `1000:1000`). These must match the owner
of `SHARE_PATH`, or management will fail with permission errors. Find your IDs
with `id -u` and `id -g` (Linux/macOS) and set `PUID`/`PGID` in `.env`
accordingly. On Docker Desktop (macOS/Windows) the default usually works; grant
Docker access to the folder in its file-sharing settings if the mount is denied.

## Commands

```bash
docker compose up -d --build   # Build and start in the background
docker compose logs -f         # See logs
docker compose down            # Stop the server
```

Changing `SHARE_PATH`, `PORT`, `ADMIN_PASSWORD`, or `PUID`/`PGID` requires
`docker compose up -d` to recreate the container. Adding or removing files
inside the shared folder does not.

## Verify deployment

- `docker compose config --quiet` then `docker compose up -d --build`.
- `docker compose ps` shows the container `Up`; `docker compose logs portal`
  shows `Application startup complete`.
- Open `http://localhost:8080` — the title and header read **AIMsLab File
  Sharing**. Browse, search, and download a sample file; confirm the download
  matches the original.
- Open `/admin`, sign in, and confirm the dashboard updates while a download is
  in progress. Upload a file and confirm it appears for public download.
- Confirm the app filesystem is read-only except the share:
  `docker compose exec portal sh -c 'touch /app/x'` must fail;
  `docker compose exec portal sh -c 'touch /srv/shared/.x && rm /srv/shared/.x'`
  must succeed.
- Repeat from a second device on the trusted LAN using `http://SERVER-IP:8080`.

## Project layout

- `compose.yaml`: Docker Compose service definition
- `Dockerfile`: builds the application image
- `app/`: the FastAPI application
  - `main.py`: routes (UI, browse/download, admin manage, metrics WebSocket)
  - `security.py`: path-safety boundary and session tokens
  - `metrics.py`: in-memory live transfer metering
  - `config.py`: environment-driven configuration
  - `static/index.html`: public browse/download page
  - `static/admin.html`: admin dashboard + file manager
- `shared/`: default share folder (contents excluded from Git)
- `.env.example`: configuration template
- `GLOSSARY.md`, `docs/adr/`: domain model and architecture decisions
- `AGENTS.md`: authoritative guide for the deploying/maintaining agent

## Troubleshooting

- **Admin page says it's disabled**: set `ADMIN_PASSWORD` in `.env` and
  `docker compose up -d`.
- **Uploads/deletes fail with a permission error**: `PUID`/`PGID` don't match
  the owner of `SHARE_PATH`. Fix them in `.env` and recreate.
- **"source directory does not exist"**: create your `SHARE_PATH` folder first;
  the mount will not auto-create it.
- **Port busy**: set a different `PORT` in `.env`.
- Guest Wi-Fi / wireless client isolation can block LAN transfers.

## Security

**Trusted local network only.** This is a classroom/lab utility, not an
authenticated document-management system.

- **No HTTPS.** The admin password and session cookie travel in the clear over
  the LAN. Anyone sniffing the network can capture them. Never reuse a password
  you use elsewhere.
- **No public exposure.** Never forward this port on your router, and never put
  it behind a public tunnel or host. Docker publishes the port on all host
  interfaces unless you restrict the binding or host firewall — restrict it to
  your trusted LAN.
- **The share is read-write.** The admin can delete files, and a read-only
  container mount is *not* used (management needs to write). Back up anything
  important; deletes are permanent.
- **No per-user accounts.** There is one admin and an anonymous public. Everyone
  who can reach the port can download every file in the share. Never put
  credentials, personal data, or confidential material there.
- Retained hardening: the container runs **non-root** with `no-new-privileges`,
  a **read-only root filesystem** (only the share and `/tmp` are writable), and
  rejects path traversal and hidden (`.`-prefixed) names.
