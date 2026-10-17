Perform a full security audit / penetration test on the target: $ARGUMENTS

You are the **ORCHESTRATOR**. Your ONLY job: discover services, ask authorization, launch specialized sub-agents in parallel across two waves (loot before exploitation), and compile the final report. Do NOT run scans yourself beyond the initial nmap discovery.

## Phase 0: Session Management

1. Check for an existing session: `ls -td sessions/*/ 2>/dev/null | head -1`. If it exists and `session.md` shows `IN PROGRESS`, reuse it.
2. Otherwise create one: sanitize the target (replace `/`, `:`, `.` with `_`), timestamp with `date +%Y%m%d_%H%M`, `mkdir -p sessions/<sanitized_target>_<timestamp>/assets`, write `session.md` (target, date, type: Audit, status: IN PROGRESS) and `targets.md`.
3. Store the path as `SESSION_DIR`. **Every sub-agent below MUST receive `SESSION_DIR` in its prompt.**

## Phase 1: Discovery (you do this yourself)

1. **Fast pass (blocking):** `execute_command` with `nmap -sV -sC -O -Pn --top-ports 1000 -T4 <target>` (`-O` works — the container has NET_RAW/NET_ADMIN). Start Wave A from this.
2. **Full pass (background):** also kick off `nmap -p- -T4 -Pn <target>` in the background to catch high/uncommon ports; fold any extras into the target list, dispatching late sub-agents if needed.
3. Parse results into a table of open ports, service names, and versions. Print it.

## Phase 1.5: Knowledge Lookup

Read `knowledge/tools/index.md` if it exists. For each tool you're about to dispatch sub-agents to run (gobuster, hydra, nikto, nuclei, etc. — whatever the discovered services call for), read the matching `knowledge/tools/<tool>.md` and fold its "What works well" notes into that sub-agent's prompt as one line: `KNOWN EFFICIENCY NOTES: <notes>`. Skip silently for tools with no file yet — this is a lookup, not a requirement.

## Phase 2: Authorization

Use `AskUserQuestion`: **"Select the authorization scope for this engagement:"**
1. **Passive only** — Recon and vulnerability identification. No brute force, no exploitation, no sqlmap.
2. **Passive + Credential testing** — Adds brute force with small wordlists against discovered login services.
3. **Full pentest** — Adds SQL injection exploitation, command injection, sensitive file exfiltration, AD/SMB exploitation, and exploit verification. May cause service disruption.
4. **Cancel** — Do not proceed.

Store the choice as `SCOPE_LEVEL`. Inject into every sub-agent prompt:
```
AUTHORIZATION LEVEL: <SCOPE_LEVEL>
- PASSIVE ONLY: do NOT run hydra, sqlmap, msfconsole, commix, or anything that authenticates or sends exploit payloads. Note skipped steps as "Skipped - requires intrusive authorization".
- PASSIVE + CREDENTIAL TESTING: hydra with small/bounded wordlists is allowed. sqlmap, commix, msfconsole are not.
- FULL PENTEST: all tools allowed.
```

## Phase 3: Parallel Sub-Agent Dispatch (two waves)

**TOOLING DIRECTIVE — inject into every sub-agent prompt:** `Run ALL tools via mcp__kali__execute_command, invoking the raw binary directly. Do NOT call the deprecated wrapper tools (nmap_scan, hydra_attack, etc.) — they return HTTP 500. Load execute_command via ToolSearch first: query "select:mcp__kali__execute_command". Keep intrusive runs bounded (-t 4 -f, small/head-trimmed wordlists, or a single known credential); stop at the first valid hit.`

**SESSION OUTPUT — inject into every sub-agent prompt:** `When you finish, use the Write tool to save your COMPLETE output (commands run, raw output, findings) to sessions/<SESSION_DIR>/assets/<asset_name>.md` (see filename per sub-agent below).

**LOOT-BEFORE-EXPLOIT ORDERING:**
- **Wave A (always, parallel, single message):** every sub-agent below marked *Wave A* runs recon/enumeration/looting ONLY — no brute force, no sqlmap, no exploit payloads, regardless of `SCOPE_LEVEL`. Each MUST end its report with a `HARVESTED CREDENTIALS:` section (usernames, passwords, hashes, tokens, key files) or `HARVESTED CREDENTIALS: none`.
- **Broker (orchestrator, between waves):** consolidate every `HARVESTED CREDENTIALS` block into `sessions/<SESSION_DIR>/assets/harvested_credentials.md`.
- **Wave B (parallel, single message, only if `SCOPE_LEVEL` > Passive):** sub-agents marked *Wave B*, each seeded with the harvested credential set — test known credentials first (note password reuse) before falling back to a small bounded wordlist, and skip any service already looted in Wave A. Sub-agents marked *Wave B — Full only* run only when `SCOPE_LEVEL` is Full pentest.

### Wave A — one sub-agent per discovered port (service enumeration)

For **every open port**, dispatch one sub-agent (target/port/version filled in). Before writing its prompt, read the matching file in `knowledge/protocols/` (`http.md`, `ssh.md`, `ftp.md`, `smb.md`, `mysql.md`, `postgresql.md`, `mssql.md`, `smtp.md`, `dns.md`, `rdp.md`, `snmp.md`, `ldap.md`, `kerberos.md`, `vnc.md`, `redis.md`, `mongodb.md`, `elasticsearch.md`, `docker-api.md`, `winrm.md`, `nfs.md`, or `generic.md` as fallback — see `knowledge/protocols/index.md`) and copy its steps verbatim into the sub-agent's prompt. `knowledge/protocols/` defines each service playbook exactly once — never re-derive or guess the commands here.

Asset filename: `sessions/<SESSION_DIR>/assets/service_enum_port<PORT>.md`

Every sub-agent report must include: findings, severity, evidence, remediation, plus the `HARVESTED CREDENTIALS:` section.

### Wave A — additional agents for web ports (only if any HTTP/HTTPS port was found)

**Web Directory & Sensitive Content Enumeration** — ffuf directory + file fuzzing (`raft-medium-directories.txt`, `raft-medium-files.txt`), curl sweep of common sensitive endpoints (`.env`, `.git/`, `/api-docs`, `/actuator`, `/metrics`, `/backup/`), recurse into anything found. Asset: `web_directory_enum_port<PORT>.md`

**API Security Testing** — identify app type from root page; probe common API endpoints; test IDOR (id=1,2,3...); check CORS/CSP/X-Frame-Options; try registration if present. Asset: `api_security_port<PORT>.md`

**Authentication & Session Testing** — find login endpoint; test SQLi payloads on it (`' OR 1=1--` etc., no sqlmap yet — manual payloads only in Wave A); test default/weak creds; if login succeeds, decode/inspect the JWT, test `alg:none`, use the token against protected endpoints. Asset: `auth_session_testing_port<PORT>.md`

**Web Fuzzing & Parameters** — arjun for hidden parameters on the root page and discovered endpoints; nuclei `-severity critical,high,medium -c 25`. Asset: `web_fuzz_port<PORT>.md`

**OSINT & Fingerprinting** — whatweb -a 3; wafw00f; security header analysis; searchsploit per detected service/version. Asset: `osint_fingerprinting.md`

### Wave A — additional agent for AD/SMB ports (only if 88/389/445/636 found)

**AD/SMB Deep Enumeration** — crackmapexec smb `--shares --users --groups --pass-pol`; smbclient -L and list readable shares; if Kerberos (88), impacket-GetNPUsers for AS-REP Roasting (no creds needed, still Wave A). No secretsdump/pass-the-hash here — that moves to Wave B Full-only. Asset: `ad_smb_audit.md`

### Wave A — always, once (vulnerability scan across all ports)

**Vulnerability Scanning** — nmap `-Pn --script vuln` against all discovered ports; nikto `-C all` on web services; nuclei; searchsploit per service/version. Asset: `vuln_scanning.md`

### Wave B — credential brute force (SCOPE_LEVEL > Passive)

Seeded with the harvested credential set first. For each login service: SSH/FTP root/admin + common passwords; HTTP login forms with known users; SMB via crackmapexec password spray + null session; database default creds. If standard lists fail, generate a target-specific wordlist with `cewl <url> -d 2 -m 5 -w /tmp/workspace/cewl_wordlist.txt`. Stop at first valid hit per service. Asset: `credential_brute_force.md`

### Wave B — Full only

**SQL Injection Exploitation** — sqlmap `--batch --level=3 --risk=2 --threads=5` on every URL/POST parameter found by earlier agents; on success, enumerate tables and dump high-value ones. Asset: `sqli_exploitation.md`

**Command Injection Testing** — commix `--batch --level=3` against discovered parameters (GET and POST); on success, read `/etc/passwd`, `whoami`, `id`. Asset: `command_injection.md`

**Sensitive File Discovery & Exploitation** — download accessible files from any file-serving endpoint found; test null-byte/extension bypass and path traversal; check `/encryptionkeys/`, `/.ssh/`, backup-file extensions (`.bak`,`.old`,`.orig`). Asset: `sensitive_files.md`

**AD/SMB Exploitation** — impacket-secretsdump, psexec/wmiexec, pass-the-hash with any discovered hashes; Kerberoasting with `impacket-GetUserSPNs` if credentials are available. Asset: `ad_smb_exploitation.md`

## Phase 4: Consolidation (you do this, after ALL sub-agents return)

Compile the final report:
1. **Scope**: target(s), methodology, authorization level, date.
2. **Executive Summary**: 3-5 sentences on security posture and critical risks.
3. **Risk Matrix**: findings grouped by severity (Critical/High/Medium/Low) with counts.
4. **Port-by-Port / Detailed Findings**: each vulnerability with evidence, impact, remediation.
5. **Attack Paths**: chained findings (e.g., "SQLi → DB dump → credential reuse → admin access").
6. **Compromised Data Summary**: any exfiltrated users/credentials/PII.
7. **Remediation Roadmap**: prioritized (immediate / short-term / long-term).

## Phase 5: Session Persistence

1. Save nmap discovery output to `sessions/<SESSION_DIR>/assets/nmap_discovery.md`.
2. Write the consolidated report to `sessions/<SESSION_DIR>/findings.md`.
3. Update `targets.md` with findings count and `session.md` (sub-agents dispatched, timeline). Keep status `IN PROGRESS` — `/kali-finish` finalizes it.
4. Print:
   ```
   SESSION PROGRESS SAVED
   ━━━━━━━━━━━━━━━━━━━━━
   Directory: sessions/<SESSION_DIR>/
   Assets saved: <count> files
   Run /kali-finish to finalize the session, generate the consolidated report, and consolidate tool-efficiency lessons into knowledge/.
   ```
