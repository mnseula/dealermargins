#!/usr/bin/env python3
"""
Manual Window Sticker Generator for Display/Test Boats

For boats not in the database (like ETWTEST024), this script can generate
a window sticker from manual input.

Usage:
    python3 generate_manual_window_sticker.py
"""

import mysql.connector
from typing import Dict, Optional

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def get_dealer_info(dealer_name_search: str) -> Optional[Dict]:
    """Get dealer information from DealerMargins table"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Search for dealer in DealerMargins
    cursor.execute("""
        SELECT DISTINCT
            dealer_id,
            dealer_name
        FROM DealerMargins
        WHERE dealer_name LIKE %s
        LIMIT 1
    """, (f'%{dealer_name_search}%',))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return {
            'dealer_id': result[0],
            'dealer_name': result[1]
        }
    return None

def generate_window_sticker_manual():
    """Generate window sticker for ETWTEST024"""

    print("=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - WINDOW STICKER".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    # Dealer Information
    print("\n" + "=" * 80)
    print("DEALER INFORMATION")
    print("=" * 80)
    print("PONTOON BOAT, LLC")
    print("2805 DECIO DRIVE")
    print("ELKHART, IN 46517")
    print("www.benningtonmarine.com")
    print("888-906-2628")

    # Boat Information
    print("\n" + "=" * 80)
    print("📋 BOAT INFORMATION")
    print("=" * 80)
    print(f"   Model:                 2024 20SF-SPS")
    print(f"   Hull Serial (HIN):     ETWTEST024")
    print(f"   Stock #:               (Display Model)")
    print(f"   Series:                S Series")

    # Specifications
    print("\n" + "=" * 80)
    print("📐 SPEC/CAPACITY US")
    print("=" * 80)
    print(f"   LOA:                   22' 4\"")
    print(f"   Pontoon Length:        20' 4\"")
    print(f"   Deck Length:           20' 6\"")
    print(f"   Beam:                  8' 6\"")
    print(f"   Pontoon Diameter:      25\"")
    print(f"   Engine Configuration:  Single Outboard")
    print(f"   Fuel Capacity:         22.4 gal (usable)")

    # Performance Package
    print("\n" + "=" * 80)
    print("🚤 PERFORMANCE PACKAGE SPECS")
    print("=" * 80)
    print("   Package 2: With 25\" Tubes")
    print(f"   Person Capacity:       10 People")
    print(f"   Hull Weight:           1,819 lbs")
    print(f"   Max HP:                150 HP")
    print(f"   Pontoon Gauge:         0.08")

    # Standard Features - Interior
    print("\n" + "=" * 80)
    print("✨ STANDARD FEATURES - INTERIOR")
    print("=" * 80)
    print("   Seating & Furniture:")
    print("      • 1 Chaise Lounge")
    print("      • 4 Fishing Seats")
    print("      • Sun Pad Lounge with Storage Compartment")
    print("      • Air Recliner Reclining Helm Chair with Integrated Headrest")
    print("      • Duraframe Seat Bases")
    print("      • Powder Coated Seat Hinges")
    print("      • Kidney-Shaped Table")

    print("\n   Storage & Convenience:")
    print("      • Stern Cupholder Box")
    print("      • Bow Storage Box with Starboard Lid (Starboard Corner)")
    print("      • Stern Storage Closet")
    print("      • Stainless Steel Black Rimmed Cupholders")

    print("\n   Fishing Features:")
    print("      • 4 Pole Rod Holder")
    print("      • Bow Livewell with Starboard Lid (Port Corner Box)")
    print("      • Center Mounted Aft Livewell with Rod and Cup Holders")

    print("\n   Entertainment & Comfort:")
    print("      • Bennington Deluxe Flush Mount Speakers")
    print("      • Serene Soft Touch Base Vinyl with Simtex Accent")

    print("\n   Fuel & Safety:")
    print("      • 26 Gallon Fuel Tank, 22.4 Gallon Usable Capacity")
    print("      • Fire Extinguisher")
    print("      • Lighted Gate Glides")

    # Standard Features - Exterior
    print("\n" + "=" * 80)
    print("✨ STANDARD FEATURES - EXTERIOR")
    print("=" * 80)
    print("   Pontoons & Structure:")
    print("      • 25\" Pontoons")
    print("      • Rounded Solid Keels")
    print("      • .250 in. Thick Bow and Stern Cross Channels")
    print("      • Underdeck Spray Deflectors")
    print("      • Extruded Splash Guards")

    print("\n   Rails & Panels:")
    print("      • Anodized Raised Rails")
    print("      • S Series Anodized Streamline Rail System with Full Height Panels")

    print("\n   Hardware & Fittings:")
    print("      • 6 in. Stainless Steel Cleats")
    print("      • Stainless Steel Corner Castings")
    print("      • Stainless Steel Deck Bolts (Fanged Elevator Bolts)")

    print("\n   Boarding & Deck:")
    print("      • Deep-Step Stern Boarding Ladder")
    print("      • Stern Deck")

    print("\n   Cover & Protection:")
    print("      • Quick Release 10 ft. Bimini Top with Surlast Embroidered Boot")
    print("      • Surlast Mooring Cover")
    print("      • Mooring Cover Quick Clips")

    print("\n   Lighting & Branding:")
    print("      • Integrated Docking and Nav Lights")
    print("      • Crystal Cap Series Logos")
    print("      • Raised Bennington Logos")

    # Standard Features - Console
    print("\n" + "=" * 80)
    print("✨ STANDARD FEATURES - CONSOLE")
    print("=" * 80)
    print("   Console Design:")
    print("      • S Series Versa Helm")
    print("      • Locking Side Access Console Door")
    print("      • Ironwood Dash Accents")

    print("\n   Instrumentation:")
    print("      • Custom Sterling Gauge Package: Fuel, Tachometer and Trim")
    print("      • Hour Meter")
    print("      • Polished Steering Wheel")

    print("\n   Electronics & Controls:")
    print("      • All in One Kicker Stereo System (KMC45)")
    print("      • 12 Volt Receptacle USB A/C")
    print("      • Rocker Switches with Dash Mount Breakers")
    print("      • Sealed Deutsch Connectors")

    print("\n   Lighting:")
    print("      • Console Courtesy Light")

    # Warranty
    print("\n" + "=" * 80)
    print("🛡️  WARRANTY")
    print("=" * 80)
    print("   • Industry Leading Factory Backed Lifetime Structural")
    print("     and Deck Warranty")
    print("   • 10-Year Bow-to-Stern Warranty*")

    # Included Options
    print("\n" + "=" * 80)
    print("📦 INCLUDED OPTIONS")
    print("=" * 80)
    print(f"   {'Item Description':<50s} {'Item #':<20s} {'Qty':>5s}")
    print(f"   {'-'*50} {'-'*20} {'-'*5}")
    print(f"   {'DISPLAY VIV 7 LXS':<50s} {'DISPLAY_LXS_VIV':<20s} {'1':>5s}")

    # Footer
    print("\n" + "=" * 80)
    print("💰 PRICING")
    print("=" * 80)
    print("   NO PRICES - DISPLAY MODEL")
    print("\n   *All prices found on this boat builder and website are based on")
    print("   standard MSRP in US Dollars. Prices DO NOT include destination fees,")
    print("   prep, registration fees, taxes, dealer installed options, or any")
    print("   other applicable discounts or charges.")

    print("\n" + "=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - www.benningtonmarine.com".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    print("\n✅ Window sticker generated successfully!")
    print(f"   Model: 2024 20SF-SPS")
    print(f"   Hull: ETWTEST024")
    print(f"   Dealer: PONTOON BOAT, LLC")

if __name__ == '__main__':
    try:
        generate_window_sticker_manual()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
