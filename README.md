# LAN File Portal

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

## Project layout

- `compose.yaml`: Docker configuration
- `nginx.conf`: read-only file server and directory listing API
- `web/index.html`: browser interface
- `shared/`: files to distribute (contents are excluded from Git)
- `.env.example`: optional port configuration

## Troubleshooting

- Server and client must have network connectivity. Guest Wi-Fi / wireless client isolation can block transfers.
- Check that TCP 8080 is permitted by the host firewall **only on your trusted LAN**.
- Ensure files exist in `shared/` and are readable.
- If port 8080 is occupied, set a different `PORT` in `.env`.
- Docker Compose v2 is required.

## Security

**Trusted local network only.** No authentication and no HTTPS. Anyone able to reach the port can browse and download the shared files. Never put private files there, never forward this port on your router, and never expose it publicly. Docker publishes the port on all host interfaces unless you restrict the binding or host firewall. The shared directory is mounted read-only.

This is a classroom utility, not an authenticated document management system.
