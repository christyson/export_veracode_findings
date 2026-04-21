# export_veracode_findings

````markdown
# Veracode Findings Export Script

This script exports **Veracode Application Security findings** to CSV using the official
https://github.com/veracode/veracode-api-py SDK.

In a **single run**, it retrieves:

- **SCA (Software Composition Analysis) findings**
- **All other findings** (SAST / DAST / etc.)

Findings are filtered by a user-defined date range and can be exported into:
- One combined CSV file **or**
- Separate CSV files for **SCA** and **non-SCA** findings

The script supports both **interactive prompts** and **CLI flags**, making it suitable for:
- Manual execution
- Scheduled jobs
- CI/CD pipelines

---

## Features

-  Single API traversal (efficient & scalable)
-  Retrieves **SCA + all other scan types together**
-  Partial, case-insensitive application name matching
-  Interactive selection when multiple apps match
-  Optional split CSV export by scan type
-  CLI and interactive modes supported
-  Zero non-standard Python dependencies beyond Veracode SDK

---

## Requirements

- Python **3.8+**
- Veracode API credentials
- Python dependency:

```text
veracode-api-py
````

Install dependencies:

```bash
pip install -r requirements.txt
```

***

## Veracode API Credentials

Configure credentials using environment variables (recommended by Veracode).

### Linux / macOS

```bash
export VERACODE_API_KEY_ID="YOUR_API_KEY_ID"
export VERACODE_API_KEY_SECRET="YOUR_API_KEY_SECRET"
```

### Windows (PowerShell)

```powershell
setx VERACODE_API_KEY_ID "YOUR_API_KEY_ID"
setx VERACODE_API_KEY_SECRET "YOUR_API_KEY_SECRET"
```

The SDK automatically picks these up.

***

## Usage

### Interactive Mode

Run the script without arguments:

```bash
python export_veracode_findings.py
```

You will be prompted for:

*   Application name (partial match supported)
*   Start date (`YYYY-MM-DD`)
*   End date (`YYYY-MM-DD`)
*   Output CSV filename

If multiple applications match, an interactive selection menu is shown.

***

### CLI / Automation Mode

Provide input with flags (recommended for CI/CD):

```bash
python export_veracode_findings.py \
  --app-name "Customer Portal" \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --csv customer_portal_findings.csv
```

Any missing arguments will fall back to interactive prompts.

***

### Optional Flags

#### `--split-scan-type`

Exports findings into **two CSV files** instead of one:

*   `*_sca.csv` — SCA findings only
*   `*_non_sca.csv` — all other findings

Example:

```bash
python export_veracode_findings.py \
  --app-name portal \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --csv portal_findings.csv \
  --split-scan-type
```

***

## Output

Each CSV row represents a single finding and includes (where available):

*   `issue_id`
*   `scan_type` (SCA, STATIC, DYNAMIC, etc.)
*   `severity`
*   `status`
*   `finding_opened_date`
*   `cwe`
*   `title`
*   `file_name`
*   `line_number`

A console summary is printed showing counts by scan type.

Example:

```text
 Findings by scan type:
  SCA: 42
  STATIC: 118
  DYNAMIC: 9
```

***

## Exit Codes

| Code | Meaning                                    |
| ---: | ------------------------------------------ |
|    0 | Success                                    |
|    1 | Invalid input, app not found, or API error |

***

## Common Use Cases

*   Security & audit reporting
*   Monthly / quarterly vulnerability exports
*   CI/CD security gates
*   SCA vs SAST trend analysis
*   Import into SIEM or vulnerability management tools

***

## Disclaimer

This script is provided **as-is** and is not an official Veracode product.
Modify and use it in accordance with your organization’s security policies.

***
