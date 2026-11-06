# AIMsLab File Sharing

A LAN-only web application for sharing files from a host folder. The public can browse and download; a single administrator manages the files and watches live transfer speeds.

## Language

**AIMsLab File Sharing**:
The product. The canonical name, used verbatim in the page title, header, and docs.
_Avoid_: AIMSLAB LAN File Sharing, AIMSLAB, LAN File Portal

**Admin**:
The single person who authenticates with the admin password to manage files and view metrics. The only identity on the system; everyone else is anonymous.
_Avoid_: owner, operator (operator is the person deploying the stack, a separate concept), superuser

**Edit**:
The permission to manage the share. Held only by the Admin.
_Avoid_: write, manage-access

**Download-only**:
The permission to browse and download the Share without authenticating. Held by every non-Admin device on the LAN.
_Avoid_: guest, viewer, public user

**Share**:
The single host folder whose contents are offered for download, configured by the operator. Its path is the one thing the operator sets per host.
_Avoid_: shared directory, repository, library

**Manage**:
The set of Admin actions on the Share: upload a file, create a folder, rename, and delete.
_Avoid_: edit files, CRUD

**Download speed**:
The live rate at which the server is sending Share files to downloading devices.
_Avoid_: egress, bandwidth

**Upload speed**:
The live rate at which the server is receiving a file from the Admin during an upload.
_Avoid_: ingress

**Active transfer**:
One download or upload currently in progress, metered individually and shown on the admin dashboard.
_Avoid_: session, connection
