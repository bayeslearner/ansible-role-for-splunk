# Build stage for ttyd
# Base image pinned by tag and digest (checked 2026-11-18). To move it: `docker buildx imagetools inspect <image>:<tag>`.
FROM ubuntu:22.04@sha256:9abcaffc92a5279fff3a6a41635c0800ea33e528425fb389658806476e7defde AS builder

# Install build dependencies
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      build-essential cmake git ca-certificates libjson-c-dev libwebsockets-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone and build ttyd from source
ARG TTYD_VERSION=1.7.7
RUN git clone --branch ${TTYD_VERSION} --depth 1 https://github.com/tsl0922/ttyd.git /tmp/ttyd && \
    cd /tmp/ttyd && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make

# Final stage
FROM localhost/splunk-base-ubuntu2204:latest

# Install runtime dependencies and tools
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg iproute2 net-tools nginx apache2-utils git \
      libjson-c5 libwebsockets16 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy ttyd binary from builder stage
COPY --from=builder /tmp/ttyd/build/ttyd /usr/local/bin/

# Ansible on the controller matches the molecule-runner image exactly (ansible-core and
# collections), so a playbook behaves the same from either place. Ubuntu 22.04's Python
# is too old for this ansible-core, so uv supplies Python 3.12 in its own virtualenv.
# Change a version here and in docker-images/molecule-runner/Dockerfile together.
COPY --from=ghcr.io/astral-sh/uv:0.8.22@sha256:9874eb7afe5ca16c363fe80b294fe700e460df29a55532bbfea234a0f12eddb1 /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN uv venv --python 3.12.11 /opt/ansible && \
    uv pip install --python /opt/ansible/bin/python --no-cache ansible-core==2.21.6 && \
    ln -s /opt/ansible/bin/ansible /opt/ansible/bin/ansible-playbook /opt/ansible/bin/ansible-galaxy \
          /opt/ansible/bin/ansible-inventory /opt/ansible/bin/ansible-vault /opt/ansible/bin/ansible-config \
          /opt/ansible/bin/ansible-doc /usr/local/bin/ && \
    chmod -R a+rX /opt/uv-python /opt/ansible && \
    ansible-galaxy collection install -p /usr/share/ansible/collections \
        ansible.posix:2.2.2 \
        community.crypto:3.5.1 \
        community.general:14.0.1 \
        community.docker:5.4.0

# Create systemd directory (service will be configured in prepare.yml)
RUN mkdir -p /etc/systemd/system

# Systemd adjustments: enable nginx
RUN systemctl enable nginx || true

# Create nginx configuration for ttyd
RUN mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled && \
    echo 'server {\n\
    listen 3000;\n\
    listen [::]:3000;\n\
    server_name _;\n\
\n\
    location /ttyd/ {\n\
        proxy_pass http://127.0.0.1:7681/;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_read_timeout 1800s;\n\
    }\n\
\n\
    location / {\n\
        return 301 /ttyd/;\n\
    }\n\
}' > /etc/nginx/sites-available/ttyd && \
    ln -sf /etc/nginx/sites-available/ttyd /etc/nginx/sites-enabled/

EXPOSE 22 3000
STOPSIGNAL SIGRTMIN+3
CMD ["/usr/sbin/init"]
