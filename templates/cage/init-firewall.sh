#!/bin/bash
# Aura Cage: Default-Deny Firewall Configuration Script
# Blocks 100% of outbound network traffic except DNS, loopback, and explicitly allowed domains.
set -e

echo "[AURA CAGE] Initializing Default-Deny Network Firewall..."

# 1. Ensure required network tools exist
if ! command -v iptables &> /dev/null || ! command -v ipset &> /dev/null; then
    echo "[AURA CAGE ERROR] iptables or ipset not available. Ensure NET_ADMIN and NET_RAW capabilities are granted."
    exit 1
fi

# 2. Allow Loopback and Established Connections
iptables -F OUTPUT 2>/dev/null || true
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 3. Allow DNS resolution (UDP & TCP 53)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# 4. Create ipset for allowed domains
ipset destroy allowed-domains 2>/dev/null || true
ipset create allowed-domains hash:ip timeout 86400

DOMAINS_FILE="$(dirname "$0")/allowed-domains.txt"
if [ ! -f "$DOMAINS_FILE" ]; then
    DOMAINS_FILE="/workspaces/.devcontainer/allowed-domains.txt"
fi

if [ -f "$DOMAINS_FILE" ]; then
    echo "[AURA CAGE] Populating allowed IP set from $DOMAINS_FILE..."
    while IFS= read -r domain || [ -n "$domain" ]; do
        # Ignore comments and empty lines
        [[ "$domain" =~ ^#.*$ ]] && continue
        [ -z "$domain" ] && continue
        
        # Resolve domain IPs
        for ip in $(dig +short "$domain" 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'); do
            ipset add allowed-domains "$ip" 2>/dev/null || true
        done
    done < "$DOMAINS_FILE"
fi

# 5. Allow outbound HTTP/HTTPS ONLY to allowed domains ipset
iptables -A OUTPUT -p tcp -m set --match-set allowed-domains dst -m multiport --dports 80,443 -j ACCEPT

# 6. Default-Deny: Drop all other outbound traffic
iptables -A OUTPUT -j DROP

echo "[AURA CAGE OK] Firewall locked in Default-Deny mode. All unauthorized outbound traffic will be dropped."
