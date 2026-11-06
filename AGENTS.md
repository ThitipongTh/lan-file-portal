# Instructions for the deploying agent

You are the agent deploying and maintaining **AIMsLab File Sharing**. Treat this
file as your authoritative repository operating guide. Read `README.md`,
`compose.yaml`, `Dockerfile`, and `docs/adr/0001-metered-backend-over-static-nginx.md`
before you make deployment changes.

## What this is

A FastAPI application (one container) that serves a public browse/download UI, a
password-protected admin page for managing the shared files, and a live
download/upload speed dashboard. Transfers stream through the app so they can be
metered. The **Share** is the host folder the operator chooses; it is mounted
**read-write** at `/srv/shared` so the admin can manage it. See `GLOSSARY.md`
for the domain terms (Admin, Share, Manage, Download-only, Active transfer).

This replaced an earlier read-only static-Nginx server; ADR 0001 records why.

## Deploy

- Before each deployment, you must explicitly ask the operator which host folder
  to share: the default `./shared` folder or a custom folder configured through
  `SHARE_PATH` in `.env`. Explain that `SHARE_PATH` also configures the default
  folder; these are two folder choices, not different deployment systems.
- You must wait for the operator's answer before you change deployment
  configuration or start/recreate the service. Do not silently select the
  default or reuse an existing `.env` value. If the operator has already
  explicitly specified the folder for this deployment, treat that as the answer.
- If the operator chooses a custom folder without a path, ask for the full host
  path. Check the target OS when needed to interpret the path. You may inspect
  files and prepare changes while waiting, but must not deploy.
- You must use Docker Engine with Docker Compose v2+, or Docker Desktop with
  Linux containers on Windows/macOS.
- You must choose a host folder containing only the files the operator intends
  to distribute. Create it before startup; do not mount a home directory, drive
  root, or repository containing credentials. The admin can **delete** anything
  in this folder, so never point it at data you cannot afford to lose.
- You should copy `.env.example` to `.env` and set, for the target host:
  `SHARE_PATH`, `PORT`, `ADMIN_PASSWORD`, and `PUID`/`PGID`. Prefer an absolute
  `SHARE_PATH` and quote spaces. Keep `.env` and shared contents out of commits.
- You must set `PUID`/`PGID` to the owner of `SHARE_PATH` (find with `id -u` /
  `id -g`). A mismatch makes uploads and deletes fail with permission errors.
- To enable the admin page you must set a non-empty `ADMIN_PASSWORD`. A blank
  password is a valid download-only deployment; confirm which the operator
  wants. Set `SESSION_SECRET` to a long random value if admin sessions should
  survive restarts.
- You must preserve `/srv/shared` as the container destination, the read-only
  root filesystem, the `/tmp` tmpfs, the non-root `user:` mapping, and
  `no-new-privileges`. The Share mount is intentionally **read-write**; do not
  re-add `read_only: true` to it.
- You must run `docker compose config --quiet`, then `docker compose up -d
  --build`. A missing source directory must fail rather than create an empty
  share.
- You should give the operator the trusted LAN address and configured port. You
  must not claim successful deployment until you have verified the running
  service.

## Security

- You must deploy only on a trusted LAN. There is no TLS: the admin password and
  session cookie travel in clear text, readable by anyone sniffing the network.
- You must restrict the host firewall to the intended trusted network. Compose
  publishes on all host interfaces by default. Do not enable router port
  forwarding, public tunnels, or public hosting.
- You must never put credentials, personal data, or confidential material in the
  Share. Everyone who can reach the port can download everything in it. Check
  nested directories and symlinks; do not rely on hidden-file filtering as a
  security boundary.
- The Share is read-write and the admin can delete recursively. Treat the admin
  password as a real secret; do not commit it, log it, or reuse it.
- You must keep the retained hardening: non-root process, read-only root
  filesystem, `no-new-privileges`, path-traversal and dot-name rejection. Grant
  Docker only the intended host directory. Resolve permission/SELinux issues
  with least access; never disable host protections or use broad write perms as
  a shortcut.
- Adding features beyond the current set (per-user accounts, TLS, write access
  for non-admins, etc.) requires an explicit requirement and a security review;
  record material decisions as an ADR.

## Verify

- You must validate the resolved Compose config locally, including the chosen
  source, the `/srv/shared` target, the read-write Share mount, the `user:`
  mapping, and the host port. Do not publish output containing private paths.
- You must inspect `docker compose ps` and review `docker compose logs
  --tail=100 portal` for `Application startup complete` and any errors.
- You must check the browser title and visible heading are `AIMsLab File
  Sharing`, and that `/admin` loads.
- You must verify listing, nested-folder navigation, filename search, sorting,
  and a sample download against the original contents. Repeat from a second
  device on the trusted LAN.
- When admin is enabled, you must verify: wrong password is rejected; correct
  password signs in; the dashboard updates during a download; and upload, new
  folder, rename, and delete work and are reflected in the public listing.
- You must verify the app filesystem is read-only except the Share:
  `docker compose exec portal sh -c 'touch /app/.write-check'` must fail, and
  `docker compose exec portal sh -c 'touch /srv/shared/.write-check && rm
  /srv/shared/.write-check'` must succeed. If the app-dir write succeeds, fix
  the mount before serving.
- You must remove verification samples and report which checks passed, failed,
  or could not run. Never report configuration-only checks as a live test.

## Maintain and recover

- You should review logs and disk space periodically, treating logs as
  potentially sensitive. Configure host-appropriate log rotation for
  long-running deployments. Metrics are in-memory and reset on restart.
- You must back up the Share and local configuration before changes. Docker does
  not back up a bind-mounted folder, and the admin can delete host-side files.
- You should record the current image ID/digest and configuration before
  updates. Rebuild with `docker compose build --pull` and `docker compose up -d`
  during a maintenance window, then repeat verification. The `python:3.12-slim`
  base image can change; pinned app dependencies are in `requirements.txt`.
- You must recreate the container with `docker compose up -d` after changing
  `SHARE_PATH`, `PORT`, `ADMIN_PASSWORD`, `SESSION_SECRET`, or `PUID`/`PGID`.
  Files added or removed inside the Share appear without a restart.
- You should stop service with `docker compose down` when needed; preserve the
  host Share and `.env`. To recover, restore the known-good configuration and
  image, recreate the service, and repeat verification. Do not delete operator
  data as part of cleanup.
