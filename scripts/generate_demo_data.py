"""Generate the ThreatIQ deterministic demo event dataset.

Creates backend/demo_data/demo_events.json with exactly 50 events:
  - Category 1 (25): routine normal events, business hours, known internal IPs
  - Category 2 (15): suspicious but isolated events, no attack chain
  - Category 3 (10): "Operation Shadow DB" coordinated attack chain (T+00:00..T+00:25)

Output is fully deterministic (no randomness) so demo runs and judging
sessions always see identical data.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "backend" / "demo_data" / "demo_events.json"

# "Operation Shadow DB" anchor: attack chain begins 2026-08-28 22:00.
ATTACK_BASE = datetime(2026, 8, 28, 22, 0, 0)

# (ip, asset, criticality) tuples for recurring infrastructure.
WEB_PROXY = ("10.0.0.1", "web-proxy-01", "medium")
DNS_SERVER = ("10.0.0.53", "dns-server-01", "medium")
JUMP_HOST = ("10.0.0.20", "jump-host-01", "medium")
VPN_GATEWAY = ("10.0.0.2", "vpn-gateway-01", "medium")
PROD_DB = ("10.0.0.5", "prod-db-01", "critical")
DEV_SERVER = ("10.0.0.15", "dev-server-02", "medium")
EXTERNAL_EXFIL = ("45.33.12.199", "external-host", "high")
EXTERNAL_C2 = ("45.33.12.200", "external-host", "high")

_sequence = 0


def make_event(timestamp, source_ip, destination_ip, destination_asset,
               asset_criticality, event_type, protocol, port,
               failed_attempts, bytes_transferred, raw_severity, details):
    global _sequence
    _sequence += 1
    return {
        "event_id": f"evt-{_sequence:04d}",
        "timestamp": timestamp.isoformat(),
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "destination_asset": destination_asset,
        "asset_criticality": asset_criticality,
        "event_type": event_type,
        "protocol": protocol,
        "port": port,
        "failed_attempts": failed_attempts,
        "bytes_transferred": bytes_transferred,
        "raw_severity": raw_severity,
        "details": details,
    }


def ts(day: str, clock: str) -> datetime:
    return datetime.fromisoformat(f"{day}T{clock}")


def build_category_1():
    """25 routine events on business days 2026-08-24..26, 09:00-17:00."""
    users = ["jchen", "mrodriguez", "apatel", "slee", "dkim",
             "tnguyen", "rsharma", "jwilson", "agarcia", "kpetrov"]
    workstations = [(f"workstation-{i:02d}", f"10.0.0.{100 + i}")
                    for i in range(1, 11)]

    https_slots = [
        ("2026-08-24", "09:12:00"), ("2026-08-24", "11:23:00"),
        ("2026-08-24", "14:05:00"), ("2026-08-25", "09:47:00"),
        ("2026-08-25", "10:58:00"), ("2026-08-25", "13:45:00"),
        ("2026-08-25", "15:52:00"), ("2026-08-26", "10:23:00"),
        ("2026-08-26", "14:21:00"), ("2026-08-26", "16:38:00"),
    ]
    https_bytes = [52400, 812000, 2340000, 156000, 3200000,
                   98000, 1450000, 2760000, 210000, 610000]

    dns_slots = [
        ("2026-08-24", "09:03:00"), ("2026-08-24", "12:08:00"),
        ("2026-08-25", "10:15:00"), ("2026-08-25", "14:33:00"),
        ("2026-08-25", "16:47:00"), ("2026-08-26", "11:42:00"),
        ("2026-08-26", "15:19:00"), ("2026-08-26", "16:02:00"),
    ]
    dns_bytes = [180, 240, 320, 150, 410, 200, 260, 190]

    ssh_slots = [
        ("2026-08-24", "09:30:00"), ("2026-08-24", "13:12:00"),
        ("2026-08-25", "10:44:00"), ("2026-08-25", "15:40:00"),
        ("2026-08-26", "11:51:00"), ("2026-08-26", "14:56:00"),
        ("2026-08-26", "16:15:00"),
    ]
    ssh_bytes = [42000, 65000, 38000, 71000, 45000, 52000, 39000]

    events = []
    for idx, (day, clock) in enumerate(https_slots):
        _, ip = workstations[idx]
        events.append(make_event(
            ts(day, clock), ip, *WEB_PROXY,
            "https_session", "TCP", 443, 1, https_bytes[idx], "low",
            f"Routine HTTPS browsing session to approved corporate SaaS application (user {users[idx]})",
        ))
    for idx, (day, clock) in enumerate(dns_slots):
        asset, ip = workstations[idx]
        events.append(make_event(
            ts(day, clock), ip, *DNS_SERVER,
            "dns_query", "UDP", 53, 1, dns_bytes[idx], "low",
            f"Routine DNS resolution of allow-listed corporate and external domains from {asset}",
        ))
    for idx, (day, clock) in enumerate(ssh_slots):
        _, ip = workstations[idx]
        events.append(make_event(
            ts(day, clock), ip, *JUMP_HOST,
            "ssh_session", "SSH", 22, 1, ssh_bytes[idx], "low",
            f"Scheduled SSH administration session to bastion host (user {users[idx]})",
        ))
    return events


def build_category_2():
    """15 suspicious but isolated events (no chain, no follow-up traffic)."""
    rows = [
        ("2026-08-25", "23:41:00", "198.51.100.77", "10.0.0.30", "app-server-01", "medium",
         "port_probe", "TCP", 8080, 0, 1840, "medium",
         "Single TCP probe of HTTP alternate port 8080 from external address 198.51.100.77; connection closed with no payload"),
        ("2026-08-26", "01:52:00", "203.0.113.200", "10.0.0.40", "mail-relay-01", "medium",
         "port_probe", "TCP", 25, 0, 960, "medium",
         "Isolated SMTP port probe of mail-relay-01 from external IP 203.0.113.200 during off-hours; no message transfer attempted"),
        ("2026-08-26", "03:15:00", "198.51.100.88", "10.0.0.31", "app-server-02", "medium",
         "port_probe", "TCP", 3389, 0, 1240, "medium",
         "Single RDP port probe against app-server-02 from external address 198.51.100.88; no authentication attempted"),
        ("2026-08-27", "20:30:00", "192.168.1.150", "10.0.0.15", "dev-server-02", "medium",
         "port_probe", "TCP", 22, 0, 840, "low",
         "After-hours SSH port probe of dev-server-02 from printer-segment address 192.168.1.150; single SYN, no retry"),
        ("2026-08-26", "02:00:00", "10.0.0.105", "10.0.0.20", "jump-host-01", "medium",
         "off_hour_login", "SSH", 22, 1, 12400, "medium",
         "Successful SSH login at 02:00 outside the approved change window for account 'contractor-tmp' from workstation-05"),
        ("2026-08-25", "14:47:00", "10.0.0.107", "10.0.0.53", "dns-server-01", "medium",
         "dns_spike", "UDP", 53, 0, 204800, "medium",
         "Single DNS query burst from workstation-07: 3,200 lookups in 60 seconds for randomized subdomains of update-check-cdn.net"),
        ("2026-08-27", "10:12:00", "10.0.0.103", "10.0.0.53", "dns-server-01", "medium",
         "dns_query", "UDP", 53, 0, 312, "medium",
         "DNS query from workstation-03 for newly registered domain 'cloud-storage-updates.top' (domain age 3 days)"),
        ("2026-08-26", "04:20:00", "198.51.100.120", "10.0.0.2", "vpn-gateway-01", "medium",
         "failed_vpn_login", "TLS", 443, 2, 3600, "medium",
         "2 failed VPN authentication attempts for privileged account 'admin' from external IP 198.51.100.120"),
        ("2026-08-27", "06:02:00", "203.0.113.55", "10.0.0.2", "vpn-gateway-01", "medium",
         "failed_vpn_login", "TLS", 443, 1, 1800, "low",
         "Single failed VPN login for employee account 'jdoe' from unrecognized external IP 203.0.113.55"),
        ("2026-08-25", "13:22:00", "10.0.0.105", "10.0.0.105", "workstation-05", "low",
         "usb_device_insertion", "LOCAL", 0, 0, 0, "medium",
         "Unregistered USB mass-storage device inserted on workstation-05 (device ID 090C:1000); no DLP policy violation recorded yet"),
        ("2026-08-26", "15:08:00", "10.0.0.102", "10.0.0.102", "workstation-02", "low",
         "privilege_escalation_attempt", "LOCAL", 0, 1, 0, "medium",
         "Denied attempt to add intern account 'intern-kwu' to local Administrators group on workstation-02; blocked by group policy"),
        ("2026-08-27", "18:47:00", "10.0.0.109", "10.0.0.60", "fileserver-02", "medium",
         "after_hours_file_access", "SMB", 445, 0, 125829120, "medium",
         "After-hours bulk read of 120 MB from the finance share by workstation-09; logged-in user is not a member of the finance group"),
        ("2026-08-26", "09:05:00", "198.51.100.90", "10.0.0.2", "vpn-gateway-01", "medium",
         "impossible_travel_login", "TLS", 443, 0, 9800, "medium",
         "VPN login for 'mrodriguez' from 198.51.100.90 (Toronto) 30 minutes after a login from 203.0.113.10 (Singapore); impossible travel"),
        ("2026-08-27", "11:36:00", "10.0.0.104", "10.0.0.104", "workstation-04", "low",
         "malware_quarantined", "LOCAL", 0, 0, 0, "medium",
         "EDR quarantined 'invoice_scan.exe' (PUA.Win32.Bundler) downloaded from personal cloud storage on workstation-04"),
        ("2026-08-26", "12:30:00", "10.0.0.30", "10.0.0.30", "app-server-01", "medium",
         "service_account_anomaly", "LOCAL", 0, 1, 0, "medium",
         "Service account 'svc_reporting' performed an interactive console login on app-server-01; service accounts must not log in interactively"),
    ]
    return [make_event(ts(day, clock), src, dest, asset, crit, etype, proto,
                       port, failed, size, severity, details)
            for (day, clock, src, dest, asset, crit, etype, proto,
                 port, failed, size, severity, details) in rows]


def build_category_3():
    """10 "Operation Shadow DB" attack-chain events (T+00:00 .. T+00:25).

    Correlation design (see DEMO_SCENARIO.md): the pre-compromise events
    (T+00..T+09) are sourced from the attack host 192.168.1.201 and
    correlate into Incident #1 (Reconnaissance + Brute Force). Once the
    attacker is logged in, the on-host actions (T+12..T+25) originate from
    prod-db-01 itself (10.0.0.5) and correlate into Incident #2
    (Exfiltration + Persistence). Both groups chain within the
    correlator's 15-minute source-IP window.
    """
    chain = [
        # (T+ minutes, source_ip, (dest_ip, asset, criticality), event_type,
        #  protocol, port, failed_attempts, bytes, severity, details)
        (0, "192.168.1.201", PROD_DB, "port_scan", "TCP", 3306, 0, 124000, "critical",
         "Port scan detected: 1,024 ports probed on prod-db-01 from host 192.168.1.201; threat-intelligence hit flags the source as known-malicious scanner infrastructure (Operation Shadow DB reconnaissance)"),
        (3, "192.168.1.201", DEV_SERVER, "ssh_failed_login", "SSH", 22, 3, 2340, "medium",
         "3 failed SSH authentication attempts against dev-server-02 from 192.168.1.201 within 40 seconds"),
        (7, "192.168.1.201", PROD_DB, "auth_brute_force", "MySQL", 3306, 47, 41300, "critical",
         "47 failed authentication attempts for username 'admin' against MySQL service on prod-db-01 from 192.168.1.201; pattern consistent with credential stuffing from a leaked password list"),
        (9, "192.168.1.201", PROD_DB, "login_success", "MySQL", 3306, 1, 5600, "high",
         "Successful database login for account 'dbuser_bak' from 192.168.1.201; account not previously used from this source (lateral movement)"),
        (12, "10.0.0.5", PROD_DB, "process_execution", "LOCAL", 0, 0, 0, "critical",
         "Unexpected PowerShell process launched on prod-db-01 under 'dbuser_bak' session: powershell.exe -nop -w hidden -enc SQBFAFgAKABOAGUAdwAtAE8AYgBqAGUAYwB0AA=="),
        (15, "10.0.0.5", EXTERNAL_EXFIL, "data_exfiltration", "TCP", 443, 0, 2469606195, "critical",
         "2.3 GB outbound data transfer from prod-db-01 to external IP 45.33.12.199 over TLS; volume is 40x the daily baseline"),
        (17, "10.0.0.5", DNS_SERVER, "dns_query", "UDP", 53, 0, 96, "critical",
         "DNS query from prod-db-01 for known-malicious C2 domain 'malicious-c2-domain.xyz'; threat-intelligence hit for AsyncRAT infrastructure"),
        (20, "10.0.0.5", PROD_DB, "account_creation", "LOCAL", 0, 0, 0, "critical",
         "Hidden local account 'svc_hidden' created on prod-db-01 and added to the local Administrators group; hidden via registry SpecialAccounts\\UserList"),
        (22, "10.0.0.5", EXTERNAL_C2, "c2_reverse_shell", "TCP", 4444, 0, 84500, "critical",
         "Reverse TCP connection established from prod-db-01 to 45.33.12.200:4444; matches Metasploit meterpreter default handler signature"),
        (25, "10.0.0.5", PROD_DB, "certificate_modification", "LOCAL", 0, 0, 0, "high",
         "Unauthorized TLS certificate replacement on prod-db-01; self-signed certificate installed and bound to a service endpoint to enable an encrypted C2 channel"),
    ]
    events = []
    for offset, source, (dest_ip, asset, crit), etype, proto, port, failed, size, severity, details in chain:
        events.append(make_event(
            ATTACK_BASE + timedelta(minutes=offset), source, dest_ip, asset, crit,
            etype, proto, port, failed, size, severity, details,
        ))
    return events


def main():
    events = build_category_1() + build_category_2() + build_category_3()
    if len(events) != 50:
        raise RuntimeError(f"Expected 50 events, generated {len(events)}")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(events)} events -> {OUTPUT_FILE}")
    print("  Category 1 (normal):     25 events, evt-0001..evt-0025")
    print("  Category 2 (suspicious): 15 events, evt-0026..evt-0040")
    print("  Category 3 (attack):     10 events, evt-0041..evt-0050")


if __name__ == "__main__":
    main()
