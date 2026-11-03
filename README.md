# AIMSLAB LAN File Sharing

A read-only file download website for your classroom or lab, powered by Docker Compose and Nginx.

## Start in three commands

```bash
git clone https://github.com/syanyong/lan-file-portal.git
cd lan-file-portal
docker compose up -d
```

Put the files you wish to share into the `shared/` directory. They appear immediately, without restarting Docker.

On the server, open http://localhost:8080 . On another device on the same network, open `http://SERVER-IP:8080`. Users can browse folders, search filenames within the current folder, and download files. Clients need only a browser.

Find the server IP:
- macOS: `ipconfig getifaddr en0` (verify the Wi-Fi device)
- Linux: `hostname -I`
- Windows: `ipconfig`

## Commands

```bash
docker compose up -d       # Start in the background
docker compose logs -f      # See logs
docker compose down         # Stop the server
```

To change the host port, copy `.env.example` to `.env`, edit `PORT=8080`, then run `docker compose up -d` again.

## Choose the shared host folder

The default is `./shared`, relative to `compose.yaml`. To share another folder:

1. Create the folder and place only files intended for LAN users inside it.
2. Copy `.env.example` to `.env` (`cp .env.example .env` on macOS/Linux; `Copy-Item .env.example .env` in PowerShell).
3. Set `SHARE_PATH` in `.env`, using one of these examples:

   | Host | Example |
   | --- | --- |
   | macOS | `SHARE_PATH='/Users/yourname/AIMSLAB Shared'` |
   | Linux | `SHARE_PATH=/srv/aimslab/shared` |
   | Windows Docker Desktop | `SHARE_PATH='C:/AIMSLAB Shared'` |
   | Docker from WSL | `SHARE_PATH=/mnt/c/AIMSLAB-Shared` |

4. Run `docker compose config --quiet`, then `docker compose up -d`.

Use an absolute path for clarity; use forward slashes on Windows and quote paths containing spaces. Do not use `~` as a home-directory shortcut. Docker Desktop must have permission to access the folder (check its file-sharing settings if the mount is denied). On Linux, grant directory traversal and file read permissions to the container without making files world-writable. SELinux hosts may need an administrator-approved bind-mount label; do not disable SELinux.

Compose mounts your chosen host folder at `/srv/shared` **read-only**. Keep this container path unchanged. A missing host folder causes startup to fail instead of silently creating an empty folder. Changing `SHARE_PATH` requires `docker compose up -d` to recreate the container; changing files within the chosen folder does not. `.env` is excluded from Git. Do not commit shared files or private host paths.

## Verify deployment

- Run `docker compose config --quiet` and inspect `docker compose config` locally to confirm the source folder and read-only mount. Its output contains your host path; avoid posting it publicly.
- Run `docker compose exec portal nginx -t` and `docker compose ps`.
- Open `http://localhost:8080` (or your configured port) and check the page title and header say **AIMSLAB LAN File Sharing**.
- Add a harmless sample file and nested folder to your chosen host folder. Browse, search, sort, and download them; compare the downloaded contents with the original. Remove the samples afterward.
- Repeat from a second device on the trusted LAN using `http://SERVER-IP:8080`.
- Confirm `docker compose exec portal sh -c 'touch /srv/shared/.write-check'` fails with a read-only-filesystem error. If it unexpectedly succeeds, remove the marker and correct the mount before serving files.

## Project layout

- `compose.yaml`: Docker configuration
- `nginx.conf`: read-only file server and directory listing API
- `web/index.html`: browser interface
- `shared/`: files to distribute (contents are excluded from Git)
- `.env.example`: host port and shared-folder configuration
- `AGENTS.md`: authoritative deployment, security, maintenance, and verification instructions for agents
- `CLAUDE.md`: directs Claude to `AGENTS.md`

## Troubleshooting

- Server and client must have network connectivity. Guest Wi-Fi / wireless client isolation can block transfers.
- Check that TCP 8080 is permitted by the host firewall **only on your trusted LAN**.
- Ensure files exist in your configured `SHARE_PATH` (default `shared/`) and are readable.
- If port 8080 is occupied, set a different `PORT` in `.env`.
- Docker Compose v2 is required.

## Security

**Trusted local network only.** No authentication and no HTTPS. Anyone able to reach the port can browse and download the shared files. Never put private files there, never forward this port on your router, and never expose it publicly. Docker publishes the port on all host interfaces unless you restrict the binding or host firewall. The shared directory is mounted read-only.

This is a classroom utility, not an authenticated document management system.
