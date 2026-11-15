"""Ảnh minh họa cho tài sản mẫu; không ghi đè ảnh người dùng đã tải lên."""

import json
from pathlib import Path
from shutil import copyfile
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from .models import Asset

IMAGE_DIR = Path(__file__).resolve().parents[1] / "demo_images"


def apply_demo_images(db, config):
    manifest = IMAGE_DIR / "sources.json"
    if not manifest.is_file():
        return 0
    changed = 0
    config.storage_dir.mkdir(parents=True, exist_ok=True)
    for item in json.loads(manifest.read_text(encoding="utf-8")):
        source = IMAGE_DIR / item["file"]
        if not source.is_file():
            continue
        for asset in db.scalars(select(Asset).where(Asset.name == item["asset_name"])).unique():
            if asset.image_path:
                continue
            filename = (
                f"{asset.custodian_id}-{uuid5(NAMESPACE_URL, item['image_url']).hex}{source.suffix}"
            )
            destination = config.storage_dir / filename
            if not destination.is_file():
                copyfile(source, destination)
            asset.image_path = filename
            changed += 1
    db.flush()
    return changed
