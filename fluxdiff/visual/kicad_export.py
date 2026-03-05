import subprocess
import os
import shutil


def export_pcb_png(pcb_file: str, output_png: str):
    """
    Export PCB as PNG using KiCad CLI.
    KiCad 8 does not support direct PNG export,
    so we export SVG and convert to PNG.
    """

    output_dir = os.path.dirname(output_png)
    os.makedirs(output_dir, exist_ok=True)

    svg_file = output_png.replace(".png", ".svg")

    try:
        # Export SVG from top copper layer
        subprocess.run(
            [
                "kicad-cli",
                "pcb",
                "export",
                "svg",
                pcb_file,
                "--layers",
                "F.Cu",
                "--output",
                svg_file,
            ],
            check=True,
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to export PCB as SVG: {e}")

    # Convert SVG → PNG using rsvg-convert (if installed)
    try:
        subprocess.run(
            ["rsvg-convert", svg_file, "-o", output_png],
            check=True,
        )
    except Exception:
        print("SVG exported but PNG conversion failed. Install librsvg if needed.")