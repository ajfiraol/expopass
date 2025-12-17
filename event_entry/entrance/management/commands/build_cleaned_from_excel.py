import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Rebuild cleaned.csv from file.xlsx. "
        "Computes 1 VIP and N-1 staff per booth when only a staff count is present."
    )

    def handle(self, *args, **options):
        """
        Expected Excel (file.xlsx):
          - Columns (case-insensitive):
              Name, Booth ID, Staff no, Phone no, Location
          - 'Staff no' is the total number of people for that booth.

        This command generates cleaned.csv with columns:
          Name, Booth ID, Staff Code, Phone no, Location, Staff Type

        For each booth:
          - 1 row with Staff Type = VIP
          - (N-1) rows with Staff Type = Sales
          - Staff Code pattern similar to existing CSV, e.g. 1PV01, 1PS02, 2PV01...

        If file.xlsx already has a 'Staff Code' column, we simply
        copy it through to cleaned.csv without recomputing.
        """
        try:
            import pandas as pd
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    "pandas is required for this command. Install it with 'pip install pandas'."
                )
            )
            return

        base_dir = settings.BASE_DIR
        excel_path = Path(base_dir) / "file.xlsx"
        csv_path = Path(base_dir) / "cleaned.csv"

        if not excel_path.exists():
            self.stderr.write(self.style.ERROR(f"Excel file not found: {excel_path}"))
            return

        df = pd.read_excel(excel_path)

        # Normalize column names
        df.columns = [str(c).strip() for c in df.columns]

        # If Excel already has Staff Code, assume it's already expanded like cleaned.csv
        if "Staff Code" in df.columns:
            # Ensure Sold column (if present) is carried through; if not present, nothing to do
            df.to_csv(csv_path, index=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Detected existing 'Staff Code' column. Copied data to {csv_path}."
                )
            )
            return

        # Otherwise, compute expanded rows from a staff count column
        # Try common variants for the staff count column
        staff_no_col = None
        for candidate in ["Staff no", "Staff No", "Staff_no", "Staff count", "Staff Count"]:
            if candidate in df.columns:
                staff_no_col = candidate
                break

        if staff_no_col is None:
            self.stderr.write(
                self.style.ERROR(
                    "Could not find a 'Staff no' or 'Staff count' column in file.xlsx. "
                    "Add one or include an explicit 'Staff Code' column."
                )
            )
            return

        required_cols = ["Name", "Booth ID", staff_no_col, "Phone no", "Location"]
        for col in required_cols:
            if col not in df.columns:
                self.stderr.write(
                    self.style.ERROR(f"Missing required column in Excel: '{col}'")
                )
                return

        # Per-location sequence counters so codes look like 1PV01, 1PS02, 2PV01...
        from collections import defaultdict

        counters = defaultdict(int)  # key: location (e.g. '1p', '2p', 'O') -> sequence int

        rows_out = []

        def location_prefix(loc: str) -> str:
            loc = (loc or "").strip()
            if not loc:
                return "X"  # fallback
            # '1p' -> '1P', '2p' -> '2P', 'O' -> 'O'
            if len(loc) == 2 and loc[1].lower() == "p":
                return f"{loc[0]}P"
            return loc.upper()

        # Optional Sold column (case-insensitive match)
        sold_col = None
        for c in df.columns:
            if str(c).strip().lower() == "sold":
                sold_col = c
                break

        for _, row in df.iterrows():
            name = str(row["Name"]).strip() or "Unknown"
            booth_id = str(row["Booth ID"]).strip() or ""
            phone_no = str(row["Phone no"]).strip() if not pd.isna(row["Phone no"]) else ""
            loc = str(row["Location"]).strip() or "1p"
            sold_val = ""
            if sold_col is not None and not pd.isna(row[sold_col]):
                sold_val = str(row[sold_col]).strip()

            try:
                total_staff = int(row[staff_no_col]) if not pd.isna(row[staff_no_col]) else 0
            except (ValueError, TypeError):
                total_staff = 0

            if total_staff <= 0:
                # No staff for this booth
                continue

            prefix = location_prefix(loc)

            for i in range(total_staff):
                counters[loc] += 1
                seq = counters[loc]

                if i == 0:
                    staff_type = "VIP"
                    type_letter = "V"
                else:
                    staff_type = "Sales"
                    type_letter = "S"

                # Staff Code like 1PV01, 1PS02, 2PV01
                staff_code = f"{prefix}{type_letter}{seq:02d}"

                row_out = {
                    "Name": name,
                    "Booth ID": booth_id,
                    "Staff Code": staff_code,
                    "Phone no": phone_no,
                    "Location": loc,
                    "Staff Type": staff_type,
                }
                if sold_col is not None:
                    row_out["Sold"] = sold_val
                rows_out.append(row_out)

        if not rows_out:
            self.stderr.write(
                self.style.WARNING(
                    "No rows generated from file.xlsx (no positive staff counts found)."
                )
            )
        else:
            out_df = pd.DataFrame(rows_out)
            out_df.to_csv(csv_path, index=False)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated {len(rows_out)} rows into {csv_path} from {excel_path}."
                )
            )



