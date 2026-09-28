import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    if len(sys.argv) > 1:
        module = sys.argv[1]

        if module == "text-to-morse-video":
            runpy.run_path(str(ROOT / "text-to-morse-video" / "encrypt" / "encrypt.py"), run_name="__main__")
        elif module == "text-to-image":
            runpy.run_path(str(ROOT / "text-to-image" / "cli.py"), run_name="__main__")
        else:
            print(f"Something went wrong. No such module {module} found")
        return

    print("Available modules: text-to-morse-video, text-to-image")