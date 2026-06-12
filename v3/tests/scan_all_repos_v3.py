# scan_all_repos_v3.py
# Full Multi-Domain Repository Scanner — CodeTruth Agent V3 Module 1
# Scans all domains, saves individual reports + full domain summary
# (JSON, CSV, Markdown) for documents and social posts
# Run: python v3/tests/scan_all_repos_v3.py

import sys
import os
import json
import csv
from datetime import datetime, timezone

sys.path.insert(0, r"C:\AI_Project\CodeTruthAgent")

from v3.repository_cognition import RepositoryCognitionEngine, ReportWriter

OUTPUT_DIR = r"C:\AI_Project\CodeTruthAgent\v3\outputs\real_scans"
os.makedirs(OUTPUT_DIR, exist_ok=True)

REPOS = [
    # ── Original 15 ────────────────────────────────────────────────
    ("CodeTruthAgent",   "CODE_GOVERNANCE",      r"C:\AI_Project\CodeTruthAgent"),
    ("Django",           "PYTHON_WEB",            r"C:\repos\v3\django"),
    ("Flask",            "PYTHON_WEB",            r"C:\repos\v3\flask"),
    ("FastAPI",          "PYTHON_WEB",            r"C:\repos\v3\fastapi"),
    ("Transformers",     "ML_PIPELINE",           r"C:\repos\v3\transformers"),
    ("Redis",            "DATABASE_SYSTEM",        r"C:\repos\v3\redis"),
    ("Nginx",            "WEB_SERVER",             r"C:\repos\v3\nginx"),
    ("SpringBoot",       "JAVA_WEB",               r"C:\repos\v3\spring-boot"),
    ("Elasticsearch",    "DATA_ENGINEERING",       r"C:\repos\v3\elasticsearch"),
    ("VSCode",           "FRONTEND",               r"C:\repos\v3\vscode"),
    ("React",            "FRONTEND",               r"C:\repos\v3\react"),
    ("Rust",             "COMPILER_TOOLCHAIN",     r"C:\repos\v3\rust"),
    ("Go",               "COMPILER_TOOLCHAIN",     r"C:\repos\v3\go"),
    ("Odoo",             "ERP_SYSTEM",             r"C:\repos\v3\odoo"),
    ("SAP_UI5",          "FRONTEND",               r"C:\repos\v3\ui5-webcomponents"),

    # ── CAD / Engineering Design ───────────────────────────────────
    ("FreeCAD",          "CAD_SYSTEM",             r"C:\repos\v3\FreeCAD"),
    ("LibreCAD",         "CAD_SYSTEM",             r"C:\repos\v3\LibreCAD"),

    # ── Aerospace / Simulation ─────────────────────────────────────
    ("OpenMDAO",         "SIMULATION_TOOL",        r"C:\repos\v3\OpenMDAO"),
    ("pyNastran",        "SIMULATION_TOOL",        r"C:\repos\v3\pyNastran"),

    # ── Blockchain / Web3 ──────────────────────────────────────────
    ("py-evm",           "BLOCKCHAIN_NODE",        r"C:\repos\v3\py-evm"),
    ("solana-py",        "BLOCKCHAIN_NODE",        r"C:\repos\v3\solana-py"),

    # ── Medical / Healthcare ───────────────────────────────────────
    ("pydicom",          "MEDICAL_SYSTEM",         r"C:\repos\v3\pydicom"),
    ("hl7apy",           "MEDICAL_SYSTEM",         r"C:\repos\v3\hl7apy"),

    # ── Quantum Computing ──────────────────────────────────────────
    ("Qiskit",           "QUANTUM_COMPUTING",      r"C:\repos\v3\qiskit"),
    ("PennyLane",        "QUANTUM_COMPUTING",      r"C:\repos\v3\pennylane"),

    # ── GIS / Geospatial ───────────────────────────────────────────
    ("GeoPandas",        "GIS_SYSTEM",             r"C:\repos\v3\geopandas"),
    ("Shapely",          "GIS_SYSTEM",             r"C:\repos\v3\shapely"),

    # ── Finance / Trading ──────────────────────────────────────────
    ("Zipline",          "FINANCE_SYSTEM",         r"C:\repos\v3\zipline"),
    ("CCXT",             "FINANCE_SYSTEM",         r"C:\repos\v3\ccxt"),

    # ── Robotics ───────────────────────────────────────────────────
    ("rclpy",            "ROBOTICS_SYSTEM",        r"C:\repos\v3\rclpy"),
    ("Drake",            "ROBOTICS_SYSTEM",        r"C:\repos\v3\drake"),

    # ── Scientific Computing ───────────────────────────────────────
    ("Astropy",          "SCIENTIFIC_COMPUTING",   r"C:\repos\v3\astropy"),
    ("BioPython",        "SCIENTIFIC_COMPUTING",   r"C:\repos\v3\biopython"),

    # ── Cybersecurity ──────────────────────────────────────────────
    ("Scapy",            "SECURITY_TOOL",          r"C:\repos\v3\scapy"),
    ("pwntools",         "SECURITY_TOOL",          r"C:\repos\v3\pwntools"),

    # ── NLP ────────────────────────────────────────────────────────
    ("spaCy",            "NLP_TOOL",               r"C:\repos\v3\spaCy"),
    ("NLTK",             "NLP_TOOL",               r"C:\repos\v3\nltk"),

    # ── Audio / Speech ─────────────────────────────────────────────
    ("librosa",          "AUDIO_PROCESSING",       r"C:\repos\v3\librosa"),
    ("Whisper",          "AUDIO_PROCESSING",       r"C:\repos\v3\whisper"),

    # ── Computer Vision ────────────────────────────────────────────
    ("opencv-python",    "COMPUTER_VISION",        r"C:\repos\v3\opencv-python"),
    ("Ultralytics",      "COMPUTER_VISION",        r"C:\repos\v3\ultralytics"),

    # ── Network / Telecom ──────────────────────────────────────────
    ("Netmiko",          "NETWORK_TOOL",           r"C:\repos\v3\netmiko"),
    ("NAPALM",           "NETWORK_TOOL",           r"C:\repos\v3\napalm"),

    # ── Energy / Power ─────────────────────────────────────────────
    ("pandapower",       "ENERGY_SYSTEM",          r"C:\repos\v3\pandapower"),
    ("PyPSA",            "ENERGY_SYSTEM",          r"C:\repos\v3\PyPSA"),

    # ── Optimization ───────────────────────────────────────────────
    ("PuLP",             "OPTIMIZATION_TOOL",      r"C:\repos\v3\pulp"),
    ("CVXPY",            "OPTIMIZATION_TOOL",      r"C:\repos\v3\cvxpy"),

    # ── Satellite / Space ──────────────────────────────────────────
    ("poliastro",        "SPACE_SYSTEM",           r"C:\repos\v3\poliastro"),
    ("python-sgp4",      "SPACE_SYSTEM",           r"C:\repos\v3\python-sgp4"),

    # ── Graph Analytics ────────────────────────────────────────────
    ("NetworkX",         "GRAPH_ANALYTICS",        r"C:\repos\v3\networkx"),
    ("python-igraph",    "GRAPH_ANALYTICS",        r"C:\repos\v3\python-igraph"),

    # ── Embedded / IoT ─────────────────────────────────────────────
    ("MicroPython",      "EMBEDDED_SYSTEM",        r"C:\repos\v3\micropython"),
    ("CircuitPython",    "EMBEDDED_SYSTEM",        r"C:\repos\v3\circuitpython"),

    # ── FPGA / Hardware Description ────────────────────────────────
    ("cocotb",           "FPGA_HARDWARE",          r"C:\repos\v3\cocotb"),
    ("amaranth",         "FPGA_HARDWARE",          r"C:\repos\v3\amaranth"),

    # ── Firmware / RTOS ─────────────────────────────────────────────
    ("zephyr",           "FIRMWARE",               r"C:\repos\v3\zephyr"),
    ("u-boot",           "FIRMWARE",               r"C:\repos\v3\u-boot"),

    # ── DSP / SDR ───────────────────────────────────────────────────
    ("gnuradio",         "DSP_TOOL",               r"C:\repos\v3\gnuradio"),

    # ── Mobile Application ──────────────────────────────────────────
    ("Kivy",             "MOBILE_APPLICATION",     r"C:\repos\v3\kivy"),
    ("Toga",             "MOBILE_APPLICATION",     r"C:\repos\v3\toga"),

    # ── Cloud Infrastructure / IaC ──────────────────────────────────
    ("Pulumi",           "CLOUD_INFRASTRUCTURE",   r"C:\repos\v3\pulumi"),

    # ── Container Orchestration ─────────────────────────────────────
    ("kubernetes-python","CONTAINER_ORCHESTRATION",r"C:\repos\v3\kubernetes-python"),

    # ── CI/CD Pipeline ───────────────────────────────────────────────
    ("python-jenkins",   "CI_CD_PIPELINE",         r"C:\repos\v3\python-jenkins"),

    # ── Media Streaming ──────────────────────────────────────────────
    ("ffmpeg-python",    "MEDIA_STREAMING",        r"C:\repos\v3\ffmpeg-python"),
    ("gst-python",       "MEDIA_STREAMING",        r"C:\repos\v3\gst-python"),

    # ── Drone / UAV ──────────────────────────────────────────────────
    ("dronekit-python",  "DRONE_UAV",              r"C:\repos\v3\dronekit-python"),
    ("ArduPilot",        "DRONE_UAV",              r"C:\repos\v3\ardupilot"),

    # ── Climate Science ──────────────────────────────────────────────
    ("xarray",           "CLIMATE_SCIENCE",        r"C:\repos\v3\xarray"),
    ("MetPy",            "CLIMATE_SCIENCE",        r"C:\repos\v3\MetPy"),
]


def scan_repo(name, category, path):
    print(f"\n{'=' * 60}")
    print(f"  Scanning: {name}  [{category}]")
    print(f"{'=' * 60}")

    if not os.path.exists(path):
        print(f"  SKIPPED — path not found. Clone first:")
        print(f"  git clone --depth=1 <url> {path}")
        return None

    try:
        engine = RepositoryCognitionEngine(path)
        report = engine.scan()
        writer = ReportWriter(report)
        writer.print_console()

        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        txt_path = os.path.join(OUTPUT_DIR, f"scan_{safe_name}.txt")
        md_path  = os.path.join(OUTPUT_DIR, f"scan_{safe_name}.md")
        writer.save_txt(txt_path)
        writer.save_markdown(md_path)
        print(f"\n  Saved: {txt_path}")
        return report

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def print_summary(results):
    print(f"\n{'=' * 75}")
    print(f"  FULL DOMAIN SCAN SUMMARY")
    print(f"{'=' * 75}")
    print(f"  {'Repo':<22} {'Category':<22} {'Type':<22} {'Files':<8} {'Disc'}")
    print(f"  {'-'*22} {'-'*22} {'-'*22} {'-'*8} {'-'*6}")

    scanned = 0
    skipped = 0
    perfect = 0

    for name, category, report in results:
        if report is None:
            print(f"  {name:<22} {category:<22} {'SKIPPED':<22} {'-':<8} {'-'}")
            skipped += 1
        else:
            disc = f"{report.discovery_score*100:.0f}%"
            print(f"  {name:<22} {category:<22} {report.application_type:<22} "
                  f"{report.total_files_scanned:<8} {disc}")
            scanned += 1
            if report.discovery_score == 1.0:
                perfect += 1

    print(f"{'=' * 75}")
    print(f"\n  Scanned:  {scanned}")
    print(f"  Skipped:  {skipped}")
    print(f"  100% Discovery: {perfect}/{scanned}")
    print(f"\n  Reports saved to: {OUTPUT_DIR}")


def save_full_summary(results):
    """Save full domain summary as JSON, CSV, and Markdown for
    documents, papers, and social posts."""

    rows = []
    for name, category, report in results:
        if report is None:
            rows.append({
                "repo": name,
                "category": category,
                "application_type": "SKIPPED",
                "primary_framework": "-",
                "total_files": "-",
                "python_files": "-",
                "discovery_score": "-",
                "classification_score": "-",
                "governance_gate": "-",
            })
        else:
            python_files = getattr(report, "python_file_count", None)
            if python_files is None:
                python_files = sum(1 for lang in [report.detected_languages]
                                    if "Python" in lang) if report.detected_languages else "-"
            rows.append({
                "repo": name,
                "category": category,
                "application_type": report.application_type,
                "primary_framework": report.primary_framework or "None",
                "total_files": report.total_files_scanned,
                "python_files": python_files,
                "discovery_score": f"{report.discovery_score*100:.0f}%",
                "classification_score": f"{report.classification_score*100:.0f}%",
                "governance_gate": "APPROVED" if report.cognition_status == "COMPLETE" else report.cognition_status,
            })

    scanned_rows = [r for r in rows if r["application_type"] != "SKIPPED"]
    perfect = [r for r in scanned_rows if r["discovery_score"] == "100%"]
    total_files = sum(r["total_files"] for r in scanned_rows if isinstance(r["total_files"], int))

    summary_meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "module": "CodeTruth Agent V3 — Module 1 — Repository Cognition Engine",
        "total_repos": len(rows),
        "scanned": len(scanned_rows),
        "skipped": len(rows) - len(scanned_rows),
        "discovery_100pct": len(perfect),
        "total_files_scanned": total_files,
        "domains_covered": len(set(r["category"] for r in scanned_rows)),
    }

    # ---- JSON ----
    json_path = os.path.join(OUTPUT_DIR, "FULL_DOMAIN_SUMMARY.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary_meta, "repositories": rows}, f, indent=2)

    # ---- CSV ----
    csv_path = os.path.join(OUTPUT_DIR, "FULL_DOMAIN_SUMMARY.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # ---- Markdown ----
    cls100 = sum(1 for r in scanned_rows if r["classification_score"] == "100%")
    n_types = len(set(r["application_type"] for r in scanned_rows))

    md_path = os.path.join(OUTPUT_DIR, "FULL_DOMAIN_SUMMARY.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# CodeTruth Agent V3 — Module 1\n")
        f.write("# Full Domain Scan Summary\n\n")
        f.write(f"**Generated:** {summary_meta['generated_at']}\n\n")
        f.write(
            f"**{summary_meta['total_repos']} repositories | "
            f"{n_types} application types | "
            f"{summary_meta['total_files_scanned']:,} files scanned**  \n"
        )
        f.write(
            f"**{summary_meta['discovery_100pct']}/{summary_meta['scanned']} discovery = 100% | "
            f"{cls100}/{summary_meta['scanned']} classification = 100% | "
            f"{summary_meta['skipped']} skipped**\n\n"
        )
        f.write("---\n\n")

        # Group rows by application_type (Type), sorted alphabetically.
        # Within each group, sort repos alphabetically by name.
        groups: dict[str, list[dict]] = {}
        for r in scanned_rows:
            groups.setdefault(r["application_type"], []).append(r)

        for app_type in sorted(groups.keys()):
            group_rows = sorted(groups[app_type], key=lambda r: r["repo"])
            n = len(group_rows)
            f.write(f"### {app_type}  ({n} repo{'s' if n != 1 else ''})\n\n")
            f.write("| Repo | Framework | Files | Discovery | Classification |\n")
            f.write("|---|---|---:|---:|---:|\n")
            for r in group_rows:
                files = r["total_files"]
                files_str = f"{files:,}" if isinstance(files, int) else str(files)
                fw = r["primary_framework"]
                if fw == "None":
                    fw = "No Framework Detected"
                f.write(
                    f"| {r['repo']} | {fw} | {files_str} | "
                    f"{r['discovery_score']} | {r['classification_score']} |\n"
                )
            f.write("\n")

        skipped_rows = [r for r in rows if r["application_type"] == "SKIPPED"]
        if skipped_rows:
            f.write(f"### SKIPPED  ({len(skipped_rows)} repos)\n\n")
            f.write("| Repo | Reason |\n")
            f.write("|---|---|\n")
            for r in skipped_rows:
                f.write(f"| {r['repo']} | Path not found |\n")
            f.write("\n")

    print(f"\n  Full domain summary saved:")
    print(f"    {json_path}")
    print(f"    {csv_path}")
    print(f"    {md_path}")

    return summary_meta


if __name__ == "__main__":
    results = []
    for name, category, path in REPOS:
        report = scan_repo(name, category, path)
        results.append((name, category, report))
    print_summary(results)
    save_full_summary(results)
    save_full_summary(results)