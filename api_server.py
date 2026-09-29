from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = PROJECT_ROOT / "generated_outputs"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# this is where I have to add the module that will come in
# it is not auto-fetch from tree, but rather, we put the entry point and stuff
ALLOWED_MODULES = {
    "morse": {
        "label": "Morse Audio",
        "backend": "text-to-morse-video",
        "entrypoint": "text-to-morse-video/encrypt/encrypt.py",
    },
    "pixels": {
        "label": "Pixel Cipher",
        "backend": "text-to-image",
        "entrypoint": "text-to-image/cli.py",
    },
}

app = FastAPI(title="CryptCross API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "cryptcross-api"}


@app.get("/api/modules")
def modules() -> list[dict]:
    return [
        {
            "slug": slug,
            "name": info["label"],
            "description": "Secure processing via the connected Python pipeline.",
            "backend": info["backend"],
        }
        for slug, info in ALLOWED_MODULES.items()
    ]


def make_output_dir(module_slug: str, mode: str, original_name: str, custom_output_dir: str | None = None) -> Path:
    if custom_output_dir:
        target_dir = Path(custom_output_dir).expanduser()
        if not target_dir.is_absolute():
            target_dir = PROJECT_ROOT / target_dir
    else:
        safe_name = Path(original_name).stem.replace(" ", "_") or "output"
        target_dir = OUTPUT_ROOT / module_slug / mode / safe_name

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def build_command(module_slug: str, input_path: Path, output_dir: Path, mode: Literal["encrypt", "decrypt"], source_type: str) -> list[str]:
    module = ALLOWED_MODULES[module_slug]
    entry = PROJECT_ROOT / module["entrypoint"]

    if module_slug == "morse":
        if mode == "decrypt":
            script = PROJECT_ROOT / "text-to-morse-video" / "decrypt" / "decrypt.py"
            cmd = [
                sys.executable,
                str(script),
                "--input",
                str(input_path),
                "--mode",
                "0",
                "--output-dir",
                str(output_dir),
            ]
            return cmd

        cmd = [
            sys.executable,
            str(entry),
            "--input",
            str(input_path),
            "--mode",
            "1" if source_type == "file" else "0",
            "--output-dir",
            str(output_dir),
            "--format",
            "wav",
        ]
        return cmd

    if module_slug == "pixels":
        command_name = "decrypt" if mode == "decrypt" else "encrypt"
        cmd = [
            sys.executable,
            str(entry),
            command_name,
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--mode",
            "1" if source_type == "file" else "0",
        ]
        return cmd

    raise ValueError(f"Unsupported module slug: {module_slug}")


@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    module: str = Form(...),
    mode: str = Form("encrypt"),
    source_type: str = Form("file"),
    output_dir: str | None = Form(default=None),
):
    if module not in ALLOWED_MODULES:
        raise HTTPException(status_code=400, detail=f"Unsupported module: {module}")

    if mode not in {"encrypt", "decrypt"}:
        raise HTTPException(status_code=400, detail="Mode must be 'encrypt' or 'decrypt'.")

    filename = (file.filename or "input.bin").replace("..", "")
    safe_name = Path(filename).name

    with TemporaryDirectory(prefix="cryptcross-") as tmpdir:
        tmp_path = Path(tmpdir)
        input_path = tmp_path / safe_name
        output_dir_path = make_output_dir(module, mode, safe_name, output_dir)

        contents = await file.read()
        input_path.write_bytes(contents)

        try:
            cmd = build_command(module, input_path, output_dir_path, mode, source_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "module": module,
                    "mode": mode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "message": "Processing failed in the Python pipeline.",
                },
            )

        generated = []
        if output_dir_path.exists():
            for path in sorted(output_dir_path.rglob("*")):
                if path.is_file():
                    generated.append(str(path.relative_to(output_dir_path)))

        return {
            "status": "ok",
            "module": module,
            "mode": mode,
            "sourceType": source_type,
            "outputDir": str(output_dir_path.resolve()),
            "files": generated,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "message": f"{module} pipeline completed successfully. Saved to {output_dir_path.resolve()}.",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
