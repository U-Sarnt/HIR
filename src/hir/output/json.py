import os
import json

def dump_json(data: dict, base_filename: str = None, directory: str = "results/json") -> str:
    """
    Serializa `data` a archivo JSON con nombre secuencial.
    Asegura permisos de lectura para todos (0o644).
    """
    os.makedirs(directory, exist_ok=True)
    existing = [f for f in os.listdir(directory) if f.endswith('.json')]
    idx = len(existing) + 1
    idx_str = f"{idx:02d}"
    filename = f"{base_filename + '_' if base_filename else ''}{idx_str}.json"
    out_path = os.path.join(directory, filename)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    try:
        os.chmod(out_path, 0o644)
        sudo_uid = os.environ.get("SUDO_UID")
        sudo_gid = os.environ.get("SUDO_GID")
        if sudo_uid and sudo_gid:
            os.chown(out_path, int(sudo_uid), int(sudo_gid))
    except PermissionError:
        pass
    
    return out_path
