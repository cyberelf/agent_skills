#!/bin/bash
# Firewall initialization script for agent worker containers
# This script sets up basic network security rules

set -e

echo "Initializing firewall rules..."

# Check if running with sufficient privileges
if [ "$EUID" -ne 0 ]; then 
   echo "This script must be run as root or with sudo"
   exit 1
fi

# Load iptables modules if needed
modprobe -a iptable_filter iptable_nat ip_conntrack ip_conntrack_ftp 2>/dev/null || true

# Create ipset for allowed IPs (if needed)
if command -v ipset >/dev/null 2>&1; then
    ipset create -exist allowed_ips hash:ip
    echo "Created ipset for allowed IPs"
fi

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow outbound connections (agent needs to access APIs)
iptables -A OUTPUT -j ACCEPT

# Allow inbound SSH (if needed for debugging)
# iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Log dropped packets (optional, for debugging)
# iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: " --log-level 4

echo "Firewall rules initialized successfully"
exit 0
