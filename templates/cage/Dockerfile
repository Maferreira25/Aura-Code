# Aura Cage: Hardened Sandboxed Container for AI Agents
FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Install security and network containment tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    ipset \
    dnsutils \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Setup non-root developer user
USER vscode
WORKDIR /workspace

ENV AURA_CAGE=1
