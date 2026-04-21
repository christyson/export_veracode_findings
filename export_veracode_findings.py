#!/usr/bin/env python3

from veracode_api_py import ApplicationAPI, FlawAPI
from datetime import datetime, timezone
import argparse
import csv
import sys

PAGE_SIZE = 500
APP_PAGE_SIZE = 100


# -------------------------------------------------
# DATE HANDLING
# -------------------------------------------------
def parse_veracode_date(date_str):
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def parse_input_date(date_str, label):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        raise ValueError(f"{label} date must be in YYYY-MM-DD format")


def prompt_for_date(label):
    while True:
        try:
            return parse_input_date(
                input(f"Enter {label} date (YYYY-MM-DD): ").strip(),
                label
            )
        except ValueError as e:
            print(f"❌ {e}")


# -------------------------------------------------
# APPLICATION LOOKUP
# -------------------------------------------------
def prompt_for_selection(options):
    while True:
        try:
            choice = int(input("Select application number: ").strip())
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a number.")


def find_app_by_name(app_name):
    """
    Finds applications by partial, case-insensitive match.
    Prompts if multiple are found.
    """
    app_api = ApplicationAPI()
    matches = []
    page = 0

    while True:
        response = app_api.get_applications(page=page, size=APP_PAGE_SIZE)
        apps = response.get("_embedded", {}).get("applications", [])
        if not apps:
            break

        for app in apps:
            name = app.get("profile", {}).get("name", "")
            if app_name.lower() in name.lower():
                matches.append({
                    "name": name,
                    "guid": app.get("guid"),
                    "business_unit": app.get("profile", {}).get("business_unit", {}).get("name", "N/A")
                })

        page += 1

    if not matches:
        raise ValueError(f"No applications found matching '{app_name}'")

    if len(matches) == 1:
        print(f"✅ Using application: {matches[0]['name']}")
        return matches[0]["guid"]

    print("\n⚠️ Multiple applications matched:\n")
    for i, app in enumerate(matches, start=1):
        print(f"{i}. {app['name']} (Business Unit: {app['business_unit']})")

    return prompt_for_selection(matches)["guid"]


# -------------------------------------------------
# FLAW RETRIEVAL (ALL SCAN TYPES IN ONE RUN)
# -------------------------------------------------
def get_flaws_in_date_range(app_id, start_date, end_date):
    flaw_api = FlawAPI()
    all_flaws = []
    page = 0

    while True:
        response = flaw_api.get_flaws(
            app_id=app_id,
            page=page,
            size=PAGE_SIZE
        )

        flaws = response.get("_embedded", {}).get("flaws", [])
        if not flaws:
            break

        for flaw in flaws:
            opened_date = parse_veracode_date(flaw.get("finding_opened_date"))

            if opened_date and start_date <= opened_date <= end_date:
                all_flaws.append({
                    "issue_id": flaw.get("issue_id"),
                    "scan_type": flaw.get("scan_type"),
                    "severity": flaw.get("severity"),
                    "status": flaw.get("status"),
                    "finding_opened_date": opened_date.isoformat(),
                    "cwe": flaw.get("cwe"),
                    "title": flaw.get("title"),
                    "file_name": flaw.get("file_name"),
                    "line_number": flaw.get("line_number")
                })

        page += 1

    return all_flaws


# -------------------------------------------------
# REPORTING / EXPORT
# -------------------------------------------------
def print_scan_type_summary(flaws):
    summary = {}
    for flaw in flaws:
        scan_type = flaw.get("scan_type", "UNKNOWN")
        summary[scan_type] = summary.get(scan_type, 0) + 1

    print("\n📊 Findings by scan type:")
    for scan_type, count in summary.items():
        print(f"  {scan_type}: {count}")


def write_csv(records, filename):
    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def export_to_csv(flaws, filename, split_scan_type=False):
    if not flaws:
        print("⚠️ No findings to export.")
        return

    if split_scan_type:
        base = filename.replace(".csv", "")
        sca = [f for f in flaws if f.get("scan_type") == "SCA"]
        non_sca = [f for f in flaws if f.get("scan_type") != "SCA"]

        if sca:
            write_csv(sca, f"{base}_sca.csv")
            print(f"✅ Exported SCA findings: {base}_sca.csv")

        if non_sca:
            write_csv(non_sca, f"{base}_non_sca.csv")
            print(f"✅ Exported non-SCA findings: {base}_non_sca.csv")
    else:
        write_csv(flaws, filename)
        print(f"✅ Exported findings: {filename}")


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Export Veracode SCA and all other findings to CSV"
    )
    parser.add_argument("--app-name", help="Application name (partial match ok)")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--csv", dest="csv_file", help="Output CSV filename")
    parser.add_argument(
        "--split-scan-type",
        action="store_true",
        help="Export SCA and non-SCA findings into separate CSV files"
    )

    args = parser.parse_args()

    try:
        app_name = args.app_name or input(
            "Enter Veracode Application Name (partial ok): "
        ).strip()

        start_date = (
            parse_input_date(args.start_date, "START")
            if args.start_date
            else prompt_for_date("START")
        )

        end_date = (
            parse_input_date(args.end_date, "END")
            if args.end_date
            else prompt_for_date("END")
        )

        if start_date > end_date:
            raise ValueError("Start date must be before end date")

        csv_file = args.csv_file or input("Enter output CSV filename: ").strip()

        app_id = find_app_by_name(app_name)

        print(
            f"\n📅 Retrieving ALL findings (SCA + others) "
            f"from {start_date.date()} to {end_date.date()}...\n"
        )

        flaws = get_flaws_in_date_range(app_id, start_date, end_date)

        print(f"✅ Found {len(flaws)} total findings")
        print_scan_type_summary(flaws)

        export_to_csv(flaws, csv_file, args.split_scan_type)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()