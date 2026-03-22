import os
import click

from fluxdiff.parser.pcb_parser import parse_pcb
from fluxdiff.diff.diff_engine import compare_pcbs
from fluxdiff.visual.kicad_export import export_pcb_png
from fluxdiff.visual.image_diff import generate_visual_diff
from fluxdiff.visual.component_diff import generate_component_visual_diff

@click.command()
@click.argument("before_file", type=click.Path(exists=True))
@click.argument("after_file", type=click.Path(exists=True))
@click.option("--viewer", is_flag=True, default=False, help="Open PCB diff viewer after diffing")
def main(before_file, after_file, viewer):
    """
    Compare two KiCad PCB files and generate a semantic+visual diff.

    Example: python main.py before.kicad_pcb after.kicad_pcb
    """

    # 1. Parse both PCBs
    before_pcb = parse_pcb(before_file)
    after_pcb = parse_pcb(after_file)
    print("Before components:", len(before_pcb.components))
    print("After components:", len(after_pcb.components))

    # 2. Compute differences
    diff_report = compare_pcbs(before_pcb, after_pcb)

    # 3. Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # 4. Export both PCBs as images
    before_png = os.path.join(output_dir, "before.png")
    after_png = os.path.join(output_dir, "after.png")
    diff_png = os.path.join(output_dir, "diff_overlay.png")
    component_diff_png = os.path.join(output_dir, "component_diff.png")
    try:
        export_pcb_png(before_file, before_png)
        export_pcb_png(after_file, after_png)

        generate_visual_diff(before_png, after_png, diff_png)
        print("\nVisual diff generated:", diff_png)

        generate_component_visual_diff(
            before_png,
            after_png,
            before_pcb.components,
            after_pcb.components,
            component_diff_png
        )

        print("Component diff generated:", component_diff_png)

    except Exception as e:
        print("\n[INFO] Visual diff skipped:", e)

    # 6. Print semantic diff report
    print("\nPCB DIFF REPORT")

    print("\n=== COMPONENT CHANGES ===")
    for change in diff_report.component_changes:
        print("-", change)

    print("\n=== NET CHANGES ===")
    for change in diff_report.net_changes:
        print("-", change)

    print("\n=== ROUTING CHANGES ===")
    for change in diff_report.routing_changes:
        print("-", change)

    # Write PCB diff report to file
    diff_report_path = os.path.join(output_dir, "diff_report.txt")
    with open(diff_report_path, "w", encoding="utf-8") as f:
        f.write("PCB DIFF REPORT\n\n")

        f.write("=== COMPONENT CHANGES ===\n")
        for change in diff_report.component_changes:
            f.write(f"- {change}\n")
        f.write("\n")

        f.write("=== NET CHANGES ===\n")
        for change in diff_report.net_changes:
            f.write(f"- {change}\n")
        f.write("\n")

        f.write("=== ROUTING CHANGES ===\n")
        for change in diff_report.routing_changes:
            f.write(f"- {change}\n")
        f.write("\n")

        f.write("=== SUMMARY ===\n")
        f.write(f"Component changes: {len(diff_report.component_changes)}\n")
        f.write(f"Net changes: {len(diff_report.net_changes)}\n")
        f.write(f"Routing changes: {len(diff_report.routing_changes)}\n")

    print(f"\nDiff report written to: {diff_report_path}")

    # -- Viewer Option --
    if viewer:
        try:
            from fluxdiff.viewer.server import run_viewer_server
            print("Opening PCB diff viewer at http://localhost:5000")
            run_viewer_server()
        except Exception as e:
            print("[ERROR] Could not launch viewer:", e)

if __name__ == "__main__":
    main()