# Net Tools (Ping / Traceroute / DNS Lookup)

A small NiceGUI + FastAPI app that provides network troubleshooting tools similar to ping.eu:

- Ping
- Traceroute
- DNS Lookup (A/AAAA/MX/NS/TXT/SOA)

Requirements

Install with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run

```bash
python main.py
# open http://localhost:8080
```

Notes

- The UI is implemented with NiceGUI (which uses FastAPI under the hood).
- Ping and traceroute use the system `ping` and `traceroute` binaries — make sure they are available on your host.
- DNS lookup uses `dnspython`.
- For security the app validates hostnames and limits counts/timeouts; do not expose this publicly without additional hardening.

Files

- `main.py`: main application with UI and backend logic
- `requirements.txt`: Python dependencies

If you want, I can:

- add Dockerfile and a small docker-compose service
- add server-side streaming or WebSocket progress
- add tests or CI config
