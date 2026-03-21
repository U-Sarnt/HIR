import os
from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape


def _create_template_environment() -> Environment:
    return Environment(
        loader=PackageLoader("hir.output", "templates"),
        autoescape=select_autoescape(["html"]),
    )


def _select_template_name(data: dict) -> str:
    if "hops" in data:
        return "traceroute_report.html.j2"
    return "arp_report.html.j2"


def render_html(data: dict, base_filename: str = None, directory: str = "results/html") -> str:
    os.makedirs(directory, exist_ok=True)
    existing = [f for f in os.listdir(directory) if f.endswith('.html')]
    idx = len(existing) + 1
    filename = f"{base_filename}_{idx:02d}.html" if base_filename else f"report_{idx:02d}.html"
    out_path = os.path.join(directory, filename)

    env = _create_template_environment()

    # Selección de plantilla
    template = env.get_template(_select_template_name(data))
    if "hops" in data:
        rendered = template.render(host=data["host"], hops=data["hops"], timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    else:
        rendered = template.render(subnet=data["subnet"], devices=data["devices"], timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(rendered)

    # Ajustar permisos y ownership si procede…
    os.chmod(out_path, 0o644)
    sudo_uid = os.environ.get("SUDO_UID")
    sudo_gid = os.environ.get("SUDO_GID")
    if sudo_uid and sudo_gid:
        try:
            os.chown(out_path, int(sudo_uid), int(sudo_gid))
        except PermissionError:
            pass

    return out_path
