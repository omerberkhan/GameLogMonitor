#!/usr/bin/env python3
"""
Weapon IDs Updater
Fetches the latest weapon data from finder.cstone.space and generates weapon_ids.json
"""

import json
import requests
import re
from datetime import datetime
from pathlib import Path


def fetch_weapon_data(url="https://finder.cstone.space/GetFPSWeapons"):
    """
    Fetch weapon data from the API

    Args:
        url: API endpoint URL

    Returns:
        List of weapon dictionaries
    """
    print("Fetching weapon data from API...")

    try:
        # Add timestamp parameter to avoid caching
        timestamp = int(datetime.now().timestamp() * 1000)
        response = requests.get(f"{url}?_={timestamp}", timeout=10)
        response.raise_for_status()

        data = response.json()
        print(f"[OK] Successfully fetched {len(data)} weapons")
        return data

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching weapon data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error parsing JSON response: {e}")
        return None


def clean_weapon_name(name):
    """
    Clean up weapon name for better readability

    Args:
        name: Raw weapon name

    Returns:
        Cleaned weapon name
    """
    # Remove excessive whitespace
    name = ' '.join(name.split())

    # Remove common suffixes that don't add value
    name = re.sub(r'\s*\(.*?\)\s*$', '', name)  # Remove parenthetical suffixes

    return name.strip()


def generate_weapon_mapping(weapons):
    """
    Generate weapon ID to name mapping

    Args:
        weapons: List of weapon dictionaries from API

    Returns:
        Dictionary mapping weapon codes to friendly names
    """
    if not weapons:
        return {}

    weapon_mapping = {}

    for weapon in weapons:
        # Extract relevant fields
        code_name = weapon.get('ItemCodeName', '')
        friendly_name = weapon.get('Name', '')
        manufacturer = weapon.get('Manu', '')
        weapon_type = weapon.get('ItemClass', '')

        if not code_name:
            continue

        # Use the friendly name, or fall back to code name
        display_name = clean_weapon_name(friendly_name) if friendly_name else code_name

        # Store the mapping - use code name as key
        weapon_mapping[code_name] = display_name

        # Also store lowercase version for case-insensitive matching
        weapon_mapping[code_name.lower()] = display_name

        # Extract base name without variant suffixes for matching log entries
        # Example: KLWE_LaserRepeater_S3_Banu -> KLWE_LaserRepeater_S3
        base_name = re.sub(r'_[A-Z][a-z]+\d*$', '', code_name)
        if base_name != code_name and base_name:
            weapon_mapping[base_name] = display_name
            weapon_mapping[base_name.lower()] = display_name

    print(f"[OK] Generated {len(weapon_mapping)} weapon ID mappings")
    return weapon_mapping


def save_weapon_ids(weapon_mapping, output_file="weapon_ids.json"):
    """
    Save weapon ID mapping to JSON file

    Args:
        weapon_mapping: Dictionary of weapon ID mappings
        output_file: Output file path
    """
    output_path = Path(output_file)

    try:
        # Sort alphabetically for easier reading
        sorted_mapping = dict(sorted(weapon_mapping.items()))

        # Write to file with nice formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_mapping, f, indent=2, ensure_ascii=False)

        print(f"[OK] Weapon IDs saved to {output_path}")
        print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB")

    except Exception as e:
        print(f"[ERROR] Error saving weapon IDs: {e}")


def create_backup(file_path):
    """
    Create a backup of existing weapon_ids.json if it exists

    Args:
        file_path: Path to the file to backup
    """
    path = Path(file_path)

    if path.exists():
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.parent / f"{path.stem}_backup_{timestamp}{path.suffix}"

        try:
            import shutil
            shutil.copy2(path, backup_path)
            print(f"[OK] Created backup: {backup_path.name}")
        except Exception as e:
            print(f"[WARN] Could not create backup: {e}")


def print_statistics(weapons, weapon_mapping):
    """
    Print statistics about the fetched weapons

    Args:
        weapons: List of weapon dictionaries
        weapon_mapping: Generated weapon mapping
    """
    print("\n" + "="*60)
    print("Weapon Statistics")
    print("="*60)

    if not weapons:
        print("No weapon data available")
        return

    # Count by type
    types = {}
    manufacturers = {}

    for weapon in weapons:
        weapon_type = weapon.get('ItemClass', 'Unknown')
        manufacturer = weapon.get('Manu', 'Unknown')

        types[weapon_type] = types.get(weapon_type, 0) + 1
        manufacturers[manufacturer] = manufacturers.get(manufacturer, 0) + 1

    print(f"\nTotal weapons fetched: {len(weapons)}")
    print(f"Total mappings created: {len(weapon_mapping)}")

    print("\nWeapons by type:")
    for weapon_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {weapon_type}: {count}")

    print("\nTop manufacturers:")
    for manufacturer, count in sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {manufacturer}: {count}")

    print("="*60 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("Star Citizen Weapon IDs Updater")
    print("="*60 + "\n")

    # Create backup of existing file
    create_backup("weapon_ids.json")

    # Fetch weapon data
    weapons = fetch_weapon_data()

    if not weapons:
        print("\n[ERROR] Failed to fetch weapon data. Exiting.")
        return 1

    # Generate weapon mapping
    weapon_mapping = generate_weapon_mapping(weapons)

    if not weapon_mapping:
        print("\n[ERROR] Failed to generate weapon mapping. Exiting.")
        return 1

    # Save to file
    save_weapon_ids(weapon_mapping)

    # Print statistics
    print_statistics(weapons, weapon_mapping)

    print("[OK] Update complete!\n")
    return 0


if __name__ == "__main__":
    exit(main())
