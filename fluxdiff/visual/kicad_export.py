import subprocess
import os
import cairosvg  # Replacement for rsvg-convert

def export_pcb_png(pcb_file: str, output_png: str):
    """
    Export PCB as PNG using KiCad CLI and CairoSVG.
    """
    output_dir = os.path.dirname(output_png)
    os.makedirs(output_dir, exist_ok=True)

    svg_file = output_png.replace(".png", ".svg")

    try:
        # 1. Export SVG using KiCad CLI
        # Added --page-size-mode 2 to ensure 'before' and 'after' 
        # images have the exact same bounding box dimensions.
        subprocess.run(
            [
                "kicad-cli",
                "pcb",
                "export",
                "svg",
                pcb_file,
                "--layers", "F.Cu,F.SilkS,Edge.Cuts",
                "--page-size-mode", "2",
                "--theme", "kicad_default",
                "--output", svg_file,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to export PCB as SVG: {e}")

    # 2. Convert SVG → PNG using CairoSVG
    try:
        # Scale=4 provides high-res output for OpenCV diffing.
        # You can adjust scale based on your needs.
        cairosvg.svg2png(
            url=svg_file, 
            write_to=output_png,
            scale=4.0 
        )
        print(f"✅ Successfully rendered: {output_png}")
        
        # Cleanup: Optional, remove SVG after conversion to keep output/ clean
        # os.remove(svg_file)

    except Exception as e:
        print(f"❌ CairoSVG conversion failed: {e}")
        # Fallback check: if the file wasn't created, the rest of the pipeline will crash
        if not os.path.exists(output_png):
            raise RuntimeError("PNG was not generated. Check CairoSVG installation.")