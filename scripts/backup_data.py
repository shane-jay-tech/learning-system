"""数据备份工具：把 progress.db（含 WAL）打包成时间戳 zip。

用法：
    python scripts/backup_data.py                 # 创建备份到 data/backups/
    python scripts/backup_data.py --list          # 列出已有备份
    python scripts/backup_data.py --restore data/backups/progress-xxx.zip   # 恢复（覆盖现有库）

零依赖（标准库 zipfile/shutil）；恢复前会自动 checkpoint WAL 并保留旧库为 .bak。
"""
import argparse
import shutil
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "progress.db"
BACKUP_DIR = ROOT / "data" / "backups"

# 直接 `python scripts/backup_data.py`（含 launcher 子进程钩子）时 sys.path[0] 是
# scripts/ 而非仓库根，core 包不可见——先引导根目录再延迟导入。
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _checkpoint():
    """WAL 里的未合并数据先落盘，保证备份完整。"""
    if not DB.exists():
        return
    from core.progress import ProgressDAO
    dao = ProgressDAO(str(DB))
    try:
        dao.checkpoint_wal()
    finally:
        dao.close()


def create_backup() -> str:
    _checkpoint()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = BACKUP_DIR / f"progress-{stamp}.zip"
    with zipfile.ZipFile(str(out_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(DB) + suffix)
            if p.exists():
                zf.write(str(p), arcname=f"progress.db{suffix}")
    return str(out_path)


def list_backups():
    if not BACKUP_DIR.is_dir():
        return []
    return sorted(BACKUP_DIR.glob("progress-*.zip"), reverse=True)


def restore_backup(zip_path: str) -> None:
    src = Path(zip_path)
    if not src.exists():
        raise FileNotFoundError(f"备份不存在: {src}")
    # 恢复前把现有库保留为 .bak，防止误操作丢数据
    if DB.exists():
        shutil.copy2(str(DB), str(DB) + ".bak")
    with zipfile.ZipFile(str(src)) as zf:
        names = {n: n for n in zf.namelist() if n.startswith("progress.db")}
        for arcname in ("progress.db", "progress.db-wal", "progress.db-shm"):
            # zip 里的名字可能是 progress.db / progress.db-wal / progress.db-shm
            if arcname in names:
                with zf.open(arcname) as f_in, open(DB.parent / arcname, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        # 若备份里有 shm/wal 拼写变体也处理
        for name in names:
            if name not in ("progress.db", "progress.db-wal"):
                with zf.open(name) as f_in, open(DB.parent / name, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)


def prune_backups(keep: int = 5) -> int:
    """只保留最近 keep 份备份，返回删除数量。"""
    backups = list_backups()
    removed = 0
    for old_zip in backups[keep:]:
        try:
            old_zip.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def main():
    parser = argparse.ArgumentParser(description="Backup/restore progress.db")
    parser.add_argument("--list", action="store_true", help="列出已有备份")
    parser.add_argument("--restore", metavar="ZIP", help="从备份恢复（覆盖现有库，旧库保留为 .bak）")
    parser.add_argument("--keep", type=int, default=5, help="保留最近 N 份备份（默认 5，0 表示不轮换）")
    args = parser.parse_args()

    if args.list:
        backups = list_backups()
        if not backups:
            print("暂无备份。")
        for b in backups:
            print(f"  {b.name}  ({b.stat().st_size / 1024:.1f} KB)")
        return 0

    if args.restore:
        try:
            restore_backup(args.restore)
            print(f"已恢复: {args.restore}")
            print(f"旧库保留为: {DB}.bak")
            return 0
        except Exception as e:
            print(f"恢复失败: {e}", file=sys.stderr)
            return 1

    out = create_backup()
    print(f"备份完成: {out}")
    if args.keep > 0:
        removed = prune_backups(args.keep)
        if removed:
            print(f"轮换: 已删除最旧 {removed} 份（保留 {args.keep} 份）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
