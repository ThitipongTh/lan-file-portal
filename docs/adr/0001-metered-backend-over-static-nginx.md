---
status: accepted
---

# Metered FastAPI backend replaces the static read-only Nginx server

## Context

The original AIMsLab File Sharing was a deliberately minimal static site: Nginx serving a **read-only** bind-mounted folder with autoindex, no backend, no accounts, a read-only container root filesystem, and `no-new-privileges`. The product now requires an Admin page with **live per-transfer download/upload speed metrics**, **file management** (upload, create folder, rename, delete), and a **permission split** (Admin edits; everyone else downloads).

## Decision

Replace the static-Nginx model with a **single FastAPI (Uvicorn) service in one container** that serves the UI, the browse/download API, the upload/manage API, and the metrics. Downloads and uploads are **streamed through the application** so bytes can be metered in real time. The Share is mounted **read-write**, a single Admin authenticates by password (from `.env`) over the trusted LAN, and sessions use a signed cookie.

## Considered options

- **Keep Nginx and bolt on a sidecar for metrics/management.** Rejected: Nginx serving files directly cannot be metered per transfer, and splitting download-serving from upload-handling across two processes complicates byte accounting and the shared read-write mount for no real gain over one small app.
- **Static Nginx (status quo).** Rejected: cannot satisfy auth, uploads, or live metering at all.

## Consequences

- Three protections from the original hardened build are **deliberately given up for trusted-LAN use only**: TLS (admin password now travels over plain HTTP), the read-only Share mount (now read-write), and "no sessions." These are documented loudly in `AGENTS.md` and `README.md`, which previously forbade exactly these features and must be rewritten.
- Retained where still possible: `no-new-privileges`, a non-root process, path-traversal/dot-file rejection, LAN-only exposure with no router forwarding.
- Metrics are in-memory and reset on restart; there is no database.
