# Base image pinned by tag and digest (checked 2026-11-18). To move it: `docker buildx imagetools inspect <image>:<tag>`.
FROM gitea/gitea:28.4.0@sha256:aa90e8f00b755b0d665214ab9c14447ea44d3190dbe6b6d0cb46cd9c4f55d309

# Set basic configuration
ENV GITEA__database__DB_TYPE=sqlite3
ENV GITEA__security__INSTALL_LOCK=true
ENV USER_UID=1000
ENV USER_GID=1000

# Create initial admin user
ENV GITEA__admin__DISABLE_REGISTRATION=false
# The lab's SSH key is RSA 2048 (testing/.secrets/id_rsa, never rotated). Gitea refuses RSA keys
# under 3071 bits unless this check is off; the server is reachable only on the lab network.
ENV GITEA__ssh__MINIMUM_KEY_SIZE_CHECK=false
ENV GITEA__ssh.minimum_key_sizes__RSA=2047
ENV GITEA__server__DOMAIN=git-server
ENV GITEA__server__HTTP_PORT=8929
ENV GITEA__server__ROOT_URL=http://git-server:8929/

EXPOSE 8929 22
