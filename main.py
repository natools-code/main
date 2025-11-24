from nicegui import ui, app
import asyncio
import socket
import re
from typing import List
from fastapi import Request

try:
    import dns.resolver
except Exception:
    dns = None


# (favicon link will be added per-page to avoid mixing global UI with @ui.page)

HOSTNAME_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$")


def is_valid_host(host: str) -> bool:
    host = host.strip()
    if not host:
        return False
    if len(host) > 253:
        return False
    # allow simple hostnames / domain names
    if HOSTNAME_RE.match(host):
        return True
    # allow IPv4
    try:
        socket.inet_aton(host)
        return True
    except Exception:
        pass
    # allow IPv6
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except Exception:
        return False


async def stream_subprocess(cmd: List[str], log, timeout: int = 60) -> None:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            # read stdout
            while True:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
                if not line:
                    break
                log.push(line.decode(errors='ignore').rstrip())
        except asyncio.TimeoutError:
            proc.kill()
            log.push('[timeout] command exceeded timeout')

        # capture any remaining stderr
        stderr = await proc.stderr.read()
        if stderr:
            for l in stderr.decode(errors='ignore').splitlines():
                log.push(l)

    except FileNotFoundError:
        log.push(f'Command not found: {cmd[0]}')
    except Exception as e:
        log.push(f'Error running command: {e}')


@ui.page('/')
def index(request: Request):
    # add favicon/head tag for this page
    ui.add_head_html('<link rel="icon" type="image/png" href="https://n-a.ir/img/na_128.png" />')
    # Determine client IP: prefer X-Forwarded-For header, fall back to socket client
    xff = request.headers.get('x-forwarded-for') or request.headers.get('X-Forwarded-For')
    if xff:
        client_ip = xff.split(',')[0].strip()
    else:
        client_ip = request.client.host if request.client is not None else ''

    with ui.row().classes('justify-center'):
        ui.image("https://n-a.ir/img/logo.png").classes('h-12')

    with ui.tabs().classes('justify-start') as tabs:
        ping_tab = ui.tab('Ping')
        traceroute_tab = ui.tab('Traceroute')
        dns_tab = ui.tab('DNS Lookup')

    with ui.tab_panels(tabs, value=ping_tab).classes('w-1/2') as panels:
        with ui.tab_panel(ping_tab).classes('w-full'):
            with ui.column().classes('w-full'):
                # Set the host input default to the detected client IP
                host_input = ui.input('Host or IP', placeholder='example.com', value=client_ip).classes('w-full')
                # NiceGUI's ui.input does not accept a `type` kwarg; keep as text and parse as int
                count_input = ui.input('Count', value='4').classes('w-full')
                ping_log = ui.log(max_lines=500).classes('w-full h-64')

                def on_ping_click():
                    host = host_input.value or ''
                    try:
                        count = int(count_input.value or 4)
                    except Exception:
                        count = 4

                    if not is_valid_host(host):
                        ping_log.push('Invalid host')
                        return

                    async def _run():
                        ping_log.push(f'PING {host} (count={count})')
                        cmd = ['ping', '-c', str(max(1, min(count, 20))), host]
                        await stream_subprocess(cmd, ping_log, timeout=30 + count * 5)

                    asyncio.create_task(_run())

                ui.button('Ping', on_click=on_ping_click)

        with ui.tab_panel(traceroute_tab).classes('w-full'):
            with ui.column().classes('w-full'):
                tr_host = ui.input('Host or IP', placeholder='example.com', value=client_ip).classes('w-full')
                tr_log = ui.log(max_lines=1000).classes('w-full h-64')

                def on_tr_click():
                    host = tr_host.value or ''
                    if not is_valid_host(host):
                        tr_log.push('Invalid host')
                        return

                    async def _run():
                        tr_log.push(f'Traceroute {host}')
                        # prefer system traceroute
                        cmd = ['traceroute', host]
                        await stream_subprocess(cmd, tr_log, timeout=120)

                    asyncio.create_task(_run())

                ui.button('Traceroute', on_click=on_tr_click)

        with ui.tab_panel(dns_tab).classes('w-full'):
            with ui.column().classes('w-full'):
                dns_host = ui.input('Domain', placeholder='example.com').classes('w-full')
                dns_log = ui.log(max_lines=500).classes('w-full h-64')

                def on_dns_click():
                    host = (dns_host.value or '').strip()
                    if not host:
                        dns_log.push('No domain provided')
                        return

                    async def _run():
                        dns_log.push(f'DNS Lookup for {host}')
                        if dns is None:
                            dns_log.push('dnspython not installed; see requirements.txt')
                            return

                        resolver = dns.resolver.Resolver()
                        qtypes = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']
                        for q in qtypes:
                            try:
                                answers = resolver.resolve(host, q, lifetime=5)
                                for r in answers:
                                    dns_log.push(f'{q}: {r.to_text()}')
                            except Exception as e:
                                dns_log.push(f'{q}: {e}')

                    asyncio.create_task(_run())

                ui.button('DNS Lookup', on_click=on_dns_click)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Network Assistant', port=8080)
