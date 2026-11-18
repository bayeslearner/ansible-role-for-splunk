# Ephemeral Molecule Runner for Cross-Platform Testing
# Runs molecule commands to provision containers via Docker socket
# Base image pinned by tag and digest (checked 2026-11-18). To move it: `docker buildx imagetools inspect <image>:<tag>`.
FROM python:3.12.16-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        curl \
        git \
        openssh-client \
        docker.io \
        build-essential \
        ethtool && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
# Exact versions: the ansible-controller image installs the same ansible-core and
# collections, so a playbook behaves the same from the runner and from the controller.
# Change a version here and in docker-images/ansible-controller/Dockerfile together.
RUN pip3 install --no-cache-dir \
        ansible-core==2.21.6 \
        ansible-dev-tools==26.1.0 \
        molecule==25.12.0 \
        molecule-plugins==26.11.0 \
        ansible-lint==26.11.0 \
        requests==2.34.2

# Install go-task
RUN sh -c "$(curl -fsSL https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin v3.54.0

# Install required Ansible collections
RUN ansible-galaxy collection install \
        ansible.posix:2.2.2 \
        community.crypto:3.5.1 \
        community.general:14.0.1 \
        community.docker:5.4.0

WORKDIR /workspace
CMD ["molecule", "--help"]
