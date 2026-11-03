# Instructions for the deploying agent

You are the agent deploying and maintaining AIMSLAB LAN File Sharing. Treat this file as your authoritative repository operating guide. Read `README.md`, `compose.yaml`, and `nginx.conf` before you make deployment changes.

## Deploy

- Before each deployment, you must explicitly ask the operator which host folder to share: the default `./shared` folder or a custom folder configured through `SHARE_PATH` in `.env`. Explain that `SHARE_PATH` also configures the default folder; these are two folder choices, not different deployment systems.
- You must wait for the operator's answer before you change deployment configuration or start/recreate the service. Do not silently select the default or reuse an existing `.env` value. If the operator has already explicitly specified the folder for this deployment, treat that as the answer and do not ask again.
- If the operator chooses a custom folder without providing its path, you must ask for the full host path. Check the target operating system when it is unknown and needed to interpret the path. You may inspect files and prepare changes while waiting, but must not deploy.

- You must use Docker Engine with Docker Compose v2 or later, or Docker Desktop with Linux containers on Windows/macOS.
- You must choose a host folder containing only the files the operator intends to distribute. Create it before startup; do not mount a home directory, drive root, or repository containing credentials.
- You should copy `.env.example` to `.env` and set `SHARE_PATH` and `PORT` for the target host. Use the cross-platform examples in the README; prefer an absolute path and quote spaces. Keep `.env` and shared contents out of commits.
- You must preserve `/srv/shared` as the container destination and its read-only mount. Preserve the read-only root filesystem, temporary filesystem mounts, and `no-new-privileges` setting.
- You must run `docker compose config --quiet` before `docker compose up -d`. A missing source directory must fail rather than create an unintended empty share.
- You should give the operator the trusted LAN address and configured port. You must not claim successful deployment until you have verified the running service.

## Security

- You must deploy only on a trusted LAN. This service has no authentication or TLS; anyone who can reach its published port can read the shared files.
- You must restrict the host firewall to the intended trusted network. Compose publishes on all host interfaces by default. Do not enable router port forwarding, public tunnels, or public hosting for this configuration.
- You must never put credentials, personal data, or confidential material in the share. Check nested directories and symbolic links for unintended content; do not rely on hidden-file filtering as a security boundary.
- You must retain read-only downloads and must not add uploads, deletion, or write permissions without an explicit requirement and security review.
- You must give Docker access only to the intended host directory. Resolve permission or SELinux issues with the least necessary access; never disable host protections or use broad write permissions as a shortcut.

## Verify

- You must validate the resolved Compose configuration locally, including the chosen source, `/srv/shared` target, read-only flag, and host port. Do not publish output containing private paths.
- You must run `docker compose exec portal nginx -t`, inspect `docker compose ps`, and review `docker compose logs --tail=100 portal` for startup errors.
- You must check the browser title and visible heading are `AIMSLAB LAN File Sharing`.
- You must verify listing, nested-folder navigation, filename search, sorting, and a sample download against the original contents. Repeat access from a second device on the trusted LAN.
- You must verify writes fail with a read-only-filesystem error using `docker compose exec portal sh -c 'touch /srv/shared/.write-check'`. If a marker is created, remove it and fix the mount before serving files.
- You must remove verification samples and report which checks passed, failed, or could not run. Never report configuration-only checks as a live deployment test.

## Maintain and recover

- You should review access/error logs and available disk space periodically, while treating logs as potentially sensitive. Configure host-appropriate log rotation for long-running deployments.
- You must back up shared files and local configuration before changes. Docker does not back up a bind-mounted folder, and a read-only container mount does not prevent host-side deletion.
- You should record the current image ID/digest and configuration before updates. Run `docker compose pull` and `docker compose up -d` during an appropriate maintenance window, then repeat verification. The `nginx:stable-alpine` tag can change.
- You must recreate the container with `docker compose up -d` after changing `SHARE_PATH` or `PORT`. Files added or removed inside the selected share appear without a restart.
- You should stop service with `docker compose down` when needed; preserve the host share and `.env`. To recover, restore the known-good configuration and image, recreate the service, and repeat verification. Do not delete operator data as part of cleanup.
