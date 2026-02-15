#!/usr/bin/env python3
"""Check which Short's Marine dealer ID is in the EOS list"""
import csv

EOS_LIST_FILE = '/Users/michaelnseula/code/dealermargins/list-53ebba158ff57891258fef1e.csv'

def check_shorts_in_eos():
    """Check Short's Marine entries in EOS list"""
    print("\n" + "="*80)
    print("CHECKING SHORT'S MARINE IN EOS LIST 53ebba158ff57891258fef1e")
    print("="*80 + "\n")

    shorts_entries = []

    try:
        with open(EOS_LIST_FILE, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Search for Short's Marine
                if 'SHORT' in row['Dealership'].upper() and 'MARINE' in row['Dealership'].upper():
                    shorts_entries.append(row)

        if shorts_entries:
            print(f"Found {len(shorts_entries)} Short's Marine entries in EOS list:\n")

            for idx, entry in enumerate(shorts_entries, 1):
                print("="*80)
                print(f"ENTRY #{idx}")
                print("="*80)
                print(f"Dealer ID:   {entry['DealerID']}")
                print(f"Dealership:  {entry['Dealership']}")
                print()

                # Check Q series as example
                print("Q SERIES:")
                print(f"  Base Boat:       {entry['Q_BASE_BOAT']}%")
                print(f"  Engine:          {entry['Q_ENGINE']}%")
                print(f"  Options:         {entry['Q_OPTIONS']}%")
                print(f"  Volume Discount: {entry['Q_VOL_DISC']}%")
                print(f"  Freight:         ${float(entry['Q_FREIGHT']):,.2f}")
                print(f"  Prep:            ${float(entry['Q_PREP']):,.2f}")
                print()

                # Check QX series
                print("QX SERIES:")
                print(f"  Base Boat:       {entry['QX_BASE_BOAT']}%")
                print(f"  Engine:          {entry['QX_ENGINE']}%")
                print(f"  Options:         {entry['QX_OPTIONS']}%")
                print(f"  Volume Discount: {entry['QX_VOL_DISC']}%")
                print(f"  Freight:         ${float(entry['QX_FREIGHT']):,.2f}")
                print(f"  Prep:            ${float(entry['QX_PREP']):,.2f}")
                print()

                # Check R series
                print("R SERIES:")
                print(f"  Base Boat:       {entry['R_BASE_BOAT']}%")
                print(f"  Engine:          {entry['R_ENGINE']}%")
                print(f"  Options:         {entry['R_OPTIONS']}%")
                print(f"  Volume Discount: {entry['R_VOL_DISC']}%")
                print(f"  Freight:         ${float(entry['R_FREIGHT']):,.2f}")
                print(f"  Prep:            ${float(entry['R_PREP']):,.2f}")
                print()

                # Check S series
                print("S SERIES:")
                print(f"  Base Boat:       {entry['S_BASE_BOAT']}%")
                print(f"  Engine:          {entry['S_ENGINE']}%")
                print(f"  Options:         {entry['S_OPTIONS']}%")
                print(f"  Volume Discount: {entry['S_VOL_DISC']}%")
                print(f"  Freight:         ${float(entry['S_FREIGHT']):,.2f}")
                print(f"  Prep:            ${float(entry['S_PREP']):,.2f}")
                print()

                # Check M series
                print("M SERIES:")
                print(f"  Base Boat:       {entry['M_BASE_BOAT']}%")
                print(f"  Engine:          {entry['M_ENGINE']}%")
                print(f"  Options:         {entry['M_OPTIONS']}%")
                print(f"  Volume Discount: {entry['M_VOL_DISC']}%")
                print(f"  Freight:         ${float(entry['M_FREIGHT']):,.2f}")
                print(f"  Prep:            ${float(entry['M_PREP']):,.2f}")
                print()

                # Identify which one this is
                if entry['DealerID'] == '00457200':
                    print("⚠️  THIS IS THE ENTRY WITH LEADING ZEROS (00457200)")
                    print("    - Has 27% margins across all series")
                    print("    - Has $0 freight and prep")
                    print("    - ❌ LIKELY CAUSING THE UNDERSTATEMENT ISSUE")
                elif entry['DealerID'] == '457200':
                    print("✅ THIS IS THE ENTRY WITHOUT LEADING ZEROS (457200)")
                    print("    - Has 30% margins for most series (37% for M)")
                    print("    - Has freight charges: $1,450-$1,850")
                    print("    - Has prep charges: $2,350-$4,350")
                    print("    - ✓ THIS SHOULD BE THE ACTIVE DEALER")

                print()

            # Summary and recommendation
            print("="*80)
            print("SUMMARY & RECOMMENDATION")
            print("="*80)

            dealer_ids = [e['DealerID'] for e in shorts_entries]

            if '00457200' in dealer_ids and '457200' in dealer_ids:
                print("\n⚠️  PROBLEM IDENTIFIED: Both dealer IDs are in the EOS list!")
                print("\nThe system may be using the WRONG dealer ID (00457200)")
                print("which has:")
                print("  - Lower margins (27% vs 30%)")
                print("  - Missing freight ($0 vs $1,450-$1,850)")
                print("  - Missing prep ($0 vs $2,350-$4,350)")
                print("\nThis would cause the window sticker to be understated by $3,800-$6,200+")
                print("\n✅ RECOMMENDED FIX:")
                print("  1. Remove dealer 00457200 from the EOS list")
                print("  2. Keep only dealer 457200 (without leading zeros)")
                print("  3. Verify dealer lookup uses '457200' not '00457200'")
                print("  4. Regenerate window stickers")
            elif '00457200' in dealer_ids:
                print("\n❌ CRITICAL: Only the WRONG dealer ID (00457200) is in the list!")
                print("This is definitely causing the understatement issue.")
                print("\n✅ REQUIRED FIX:")
                print("  1. Add or update to dealer 457200 (without leading zeros)")
                print("  2. Remove dealer 00457200")
            elif '457200' in dealer_ids:
                print("\n✅ GOOD: The correct dealer ID (457200) is in the list")
                print("\nIf pricing is still wrong, check:")
                print("  1. Verify the dealer lookup is using '457200'")
                print("  2. Confirm freight/prep are being added to final price")
                print("  3. Check console logs for which dealer ID is being loaded")

        else:
            print("❌ No Short's Marine entries found in EOS list!")
            print("\nThis means the dealer is not configured in the system.")
            print("\n✅ REQUIRED FIX:")
            print("  1. Add dealer 457200 to the EOS list")
            print("  2. Sync from warrantyparts.DealerMargins table")

    except FileNotFoundError:
        print(f"❌ Error: EOS list file not found: {EOS_LIST_FILE}")
    except Exception as e:
        print(f"❌ Error reading EOS list: {e}")

if __name__ == "__main__":
    check_shorts_in_eos()
