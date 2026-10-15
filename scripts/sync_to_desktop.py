import os
import shutil
import zipfile
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent

# Potential destination paths on Windows
DESKTOP_DIRS = [
    Path("C:/Users/girik/OneDrive/Desktop"),
    Path("C:/Users/girik/Desktop"),
]

# Excluded folders and files when copying/zipping
EXCLUDE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    ".system_generated",
}

def copy_tree(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(src):
        # In-place modify dirs to skip excluded
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        rel_root = Path(root).relative_to(src)
        target_root = dst / rel_root
        target_root.mkdir(parents=True, exist_ok=True)

        for f in files:
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            src_file = Path(root) / f
            dst_file = target_root / f
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                print(f"Failed to copy {src_file}: {e}")

def create_zip(src: Path, zip_path: Path):
    if zip_path.exists():
        try:
            zip_path.unlink()
        except Exception:
            pass
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith(".pyc") or f == ".DS_Store":
                    continue
                file_path = Path(root) / f
                rel_path = file_path.relative_to(src)
                zf.write(file_path, arcname=str(rel_path))

def main():
    print(f"Source Directory: {SOURCE_DIR}")
    for desktop in DESKTOP_DIRS:
        if not desktop.exists():
            continue
        print(f"\nProcessing Desktop Target at: {desktop}")
        
        # 1. Update test 4 (Primary user target)
        test4_dir = desktop / "test 4"
        print(f" -> Syncing into '{test4_dir}' ...")
        copy_tree(SOURCE_DIR, test4_dir)
        print(f"    [OK] Synced {test4_dir}")

        test4_zip = desktop / "test 4.zip"
        print(f" -> Creating zip archive '{test4_zip}' ...")
        create_zip(SOURCE_DIR, test4_zip)
        print(f"    [OK] Created {test4_zip}")

        # Also create test4 (no space) alias for safety
        test4_nospace_dir = desktop / "test4"
        copy_tree(SOURCE_DIR, test4_nospace_dir)
        test4_nospace_zip = desktop / "test4.zip"
        create_zip(SOURCE_DIR, test4_nospace_zip)
        print(f"    [OK] Also mirrored to test4 and test4.zip")

    print("\nAll Desktop targets synced and zipped successfully!")

if __name__ == "__main__":
    main()
