import sys
import json
import os
from datetime import datetime, timezone


def load_entries(path):
    entries = []
    is_jsonl = True  # tracks which format we loaded, so we know how to write back

    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        print("⚠️ Log file is empty.")
        return entries, is_jsonl

    try:
        for line in content.splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        return entries, is_jsonl
    except json.JSONDecodeError:
        pass

    entries = []
    is_jsonl = False
    try:
        data = json.loads(content)
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = [data]
    except json.JSONDecodeError as e:
        print(f"❌ Couldn't parse {path} as JSONL or JSON: {e}")
        sys.exit(1)

    return entries, is_jsonl


def write_sorted_jsonl(path, entries):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    os.replace(tmp_path, path)


def get_field(entry, *keys, default="?"):
    """Return the first matching key found in the entry (handles varying schemas)."""
    for key in keys:
        if key in entry and entry[key] not in (None, ""):
            return entry[key]
    return default


TIMESTAMP_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%I:%M %p %d/%m/%Y",
)


def parse_timestamp(raw_ts):
    if raw_ts in (None, "?", ""):
        return None

    if isinstance(raw_ts, (int, float)):
        try:
            return datetime.fromtimestamp(raw_ts, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    if isinstance(raw_ts, str):
        # fromisoformat robustly handles all 4 ISO variants above in one shot
        try:
            dt = datetime.fromisoformat(raw_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            pass

        # Fallback for any non-ISO legacy formats (e.g. already-pretty-printed strings)
        for fmt in TIMESTAMP_FORMATS:
            try:
                dt = datetime.strptime(raw_ts, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except ValueError:
                continue

    return None


CANONICAL_FORMAT_EXAMPLE = "2026-08-17T20:55:37.832689+00:00"  # microseconds + UTC offset


def canonical_timestamp_str(dt):
    """The current MessageStore format: UTC-aware isoformat, e.g.
    '2026-08-17T20:55:37.832689+00:00'."""
    return dt.astimezone(timezone.utc).isoformat()


def format_timestamp(raw_ts):
    dt = parse_timestamp(raw_ts)
    if dt:
        return dt.strftime("%I:%M %p on %d/%m/%Y")
    if raw_ts in (None, "?", ""):
        return "??:?? on ??/??/????"
    return str(raw_ts)  # give up, show as-is


def normalize_timestamps(entries):
    changed = 0
    for entry in entries:
        raw_ts = entry.get("timestamp")
        if raw_ts is None:
            continue
        dt = parse_timestamp(raw_ts)
        if dt is None:
            continue  # can't parse it — leave as-is rather than guess
        canonical = canonical_timestamp_str(dt)
        if raw_ts != canonical:
            entry["timestamp"] = canonical
            changed += 1
    return changed


def format_table_str(rows):
    if not rows:
        return ""

    MAX_MSG_WIDTH = 60

    cleaned_rows = []
    for idx, username, text, ts in rows:
        flat_text = " ".join(text.split())  # collapse newlines/multi-space
        if len(flat_text) > MAX_MSG_WIDTH:
            flat_text = flat_text[:MAX_MSG_WIDTH - 1] + "…"
        cleaned_rows.append((idx, username, flat_text, ts))

    idx_width = max(len(r[0]) for r in cleaned_rows)
    user_width = max(len(r[1]) for r in cleaned_rows)
    msg_width = max(len(r[2]) for r in cleaned_rows)

    lines = [
        f"{idx:<{idx_width}}  {username:<{user_width}}  {text:<{msg_width}}  {ts}"
        for idx, username, text, ts in cleaned_rows
    ]
    return "\n".join(lines)


def print_table(rows):
    table = format_table_str(rows)
    if table:
        print(table)


MILESTONE_NUMBERS = [1, 69, 100, 500, 1000, 6969]
MILESTONE_STEP = 5000


def compute_milestones(total):
    milestones = list(MILESTONE_NUMBERS)
    next_step = MILESTONE_STEP
    while next_step <= total:
        milestones.append(next_step)
        next_step += MILESTONE_STEP
    return sorted(m for m in milestones if m <= total)


def get_milestone_rows(entries):
    rows = []
    for m in compute_milestones(len(entries)):
        entry = entries[m - 1]
        username = get_field(entry, "username", "user", "name",
                              "user_id", default="Unknown")
        text = get_field(entry, "text", "message", "content", default="")
        raw_ts = get_field(entry, "timestamp", "time", "date", default=None)
        pretty_ts = format_timestamp(raw_ts)
        rows.append((f"Msg no.{m}", username, text, pretty_ts))
    return rows


def main():
    count = 50
    path = "message_log.jsonl"

    args = sys.argv[1:]
    if len(args) >= 1:
        try:
            count = int(args[0])
        except ValueError:
            path = args[0]
            args = args[1:]
    if len(args) >= 2:
        path = args[1]

    entries, is_jsonl = load_entries(path)
    if not entries:
        return

    # --- Step 1: confirm/reformat every entry to the current timestamp format ---
    if is_jsonl:
        reformatted_count = normalize_timestamps(entries)
        if reformatted_count:
            print(f"🔧 {reformatted_count} of {len(entries)} entries were in an old "
                  f"timestamp format — reformatted to match the current format "
                  f"({CANONICAL_FORMAT_EXAMPLE}).\n")
        else:
            print(f"✅ All {len(entries)} entries already match the current format.\n")

    # --- Step 2: sort chronologically ---
    # Entries with an unparseable/missing timestamp are treated as "oldest"
    # (pushed to the front) rather than crashing the sort, and original
    # relative order is preserved among ties via stable sort.
    def sort_key(entry):
        raw_ts = get_field(entry, "timestamp", "time", "date", default=None)
        dt = parse_timestamp(raw_ts)
        return dt if dt else datetime.min.replace(tzinfo=timezone.utc)

    unparsed_count = sum(
        1 for e in entries
        if parse_timestamp(get_field(e, "timestamp", "time", "date", default=None)) is None
    )
    if unparsed_count:
        print(f"⚠️ {unparsed_count} entr{'y' if unparsed_count == 1 else 'ies'} "
              f"had no valid timestamp — sorted as oldest.\n")

    entries.sort(key=sort_key)

    # Persist to disk if anything changed (reformatted timestamps and/or new
    # sort order) so the on-disk file stays clean, not just this run's
    # in-memory view. Only safe for JSONL sources.
    if is_jsonl:
        write_sorted_jsonl(path, entries)
        print(f"💾 Saved {len(entries)} entries to {path} (sorted, normalized)\n")

    total = len(entries)
    last_n = entries[-count:]

    print("=" * 60)
    print(f"📜 Last {len(last_n)} messages from {path}")
    print("=" * 60)

    last_n_rows = []
    for i, entry in enumerate(last_n, start=1):
        username = get_field(entry, "username", "user", "name",
                              "user_id", default="Unknown")
        text = get_field(entry, "text", "message", "content", default="")
        raw_ts = get_field(entry, "timestamp", "time", "date", default=None)
        pretty_ts = format_timestamp(raw_ts)
        last_n_rows.append((str(i), username, text, pretty_ts))

    print_table(last_n_rows)
    print("=" * 60)

    # --- Milestone messages: #1, 100, 500, 1000, then every 5000 after ---
    milestone_rows = get_milestone_rows(entries)

    if milestone_rows:
        print(f"\n🏁 Milestone messages ")
        print("=" * 60)
        print_table(milestone_rows)
        print("=" * 60)


if __name__ == "__main__":
    main()