#!/usr/bin/env python3
"""
Compare MSRP calculation methods: Legacy vs CPQ

Tests both methods to show the difference
"""

print("=" * 120)
print("MSRP CALCULATION METHODS COMPARISON")
print("=" * 120)
print()

# Example numbers from CPQTEST26 / PDF
dealer_cost = 69056.00
freight = 0.00
prep = 0.00

# Margins (example values)
base_boat_margin = 0.73  # 27% margin = 73% of MSRP
msrp_margin = 0.73  # Typically same as base boat
vol_disc = 1.0  # No volume discount

# CPQ provided MSRP (from PDF)
cpq_msrp = 97664.00

print("INPUT VALUES:")
print("-" * 120)
print(f"  Dealer Cost:         ${dealer_cost:,.2f}")
print(f"  Freight:             ${freight:,.2f}")
print(f"  Prep:                ${prep:,.2f}")
print(f"  Base Boat Margin:    {(1-base_boat_margin)*100:.0f}% ({base_boat_margin:.2f})")
print(f"  CPQ-Provided MSRP:   ${cpq_msrp:,.2f}")
print()

print("=" * 120)
print("METHOD 1: CURRENT (Use Real CPQ MSRP)")
print("=" * 120)
print()

# Calculate sale price
sale_price_current = (dealer_cost * vol_disc) / base_boat_margin + freight + prep
msrp_current = cpq_msrp  # Use real CPQ MSRP

print("CALCULATION:")
print(f"  Sale Price = (${dealer_cost:,.2f} × {vol_disc}) / {base_boat_margin} + ${freight:,.2f} + ${prep:,.2f}")
print(f"  Sale Price = ${sale_price_current:,.2f}")
print()
print(f"  MSRP = ${msrp_current:,.2f} (from CPQ system)")
print()

print("RESULTS:")
print(f"  Dealer Cost:    ${dealer_cost:,.2f}")
print(f"  Sale Price:     ${sale_price_current:,.2f}")
print(f"  MSRP:           ${msrp_current:,.2f}")
print(f"  Markup:         ${sale_price_current - dealer_cost:,.2f} ({((sale_price_current - dealer_cost) / dealer_cost * 100):.1f}%)")
print(f"  MSRP Premium:   ${msrp_current - sale_price_current:,.2f} ({((msrp_current - sale_price_current) / sale_price_current * 100):.1f}%)")
print()

print("CUSTOMER SEES:")
print(f"  ✓ MSRP:           ${msrp_current:,.2f}")
print(f"  ✓ Sale Price:     ${sale_price_current:,.2f}")
print(f"  ✓ Savings:        ${msrp_current - sale_price_current:,.2f}")
print()

print("=" * 120)
print("METHOD 2: LEGACY SV SERIES (MSRP = Sale Price)")
print("=" * 120)
print()

# Calculate sale price (same as Method 1)
sale_price_legacy = (dealer_cost * vol_disc) / base_boat_margin + freight + prep
msrp_legacy = sale_price_legacy  # MSRP = Sale Price (SV method)

print("CALCULATION:")
print(f"  Sale Price = (${dealer_cost:,.2f} × {vol_disc}) / {base_boat_margin} + ${freight:,.2f} + ${prep:,.2f}")
print(f"  Sale Price = ${sale_price_legacy:,.2f}")
print()
print(f"  MSRP = Sale Price = ${msrp_legacy:,.2f}  ← MSRP equals sale price")
print()

print("RESULTS:")
print(f"  Dealer Cost:    ${dealer_cost:,.2f}")
print(f"  Sale Price:     ${sale_price_legacy:,.2f}")
print(f"  MSRP:           ${msrp_legacy:,.2f}")
print(f"  Markup:         ${sale_price_legacy - dealer_cost:,.2f} ({((sale_price_legacy - dealer_cost) / dealer_cost * 100):.1f}%)")
print(f"  MSRP Premium:   ${msrp_legacy - sale_price_legacy:,.2f} (0.0%)")
print()

print("CUSTOMER SEES:")
print(f"  ✓ MSRP:           ${msrp_legacy:,.2f}")
print(f"  ✓ Sale Price:     ${sale_price_legacy:,.2f}")
print(f"  ✓ Savings:        $0.00 (no discount from MSRP)")
print()

print("=" * 120)
print("COMPARISON SUMMARY")
print("=" * 120)
print()

print("| Metric | Method 1 (CPQ MSRP) | Method 2 (SV Legacy) | Difference |")
print("|--------|--------------------:|---------------------:|-----------:|")
print(f"| Dealer Cost | ${dealer_cost:,.2f} | ${dealer_cost:,.2f} | $0.00 |")
print(f"| Sale Price | ${sale_price_current:,.2f} | ${sale_price_legacy:,.2f} | ${sale_price_current - sale_price_legacy:,.2f} |")
print(f"| MSRP | ${msrp_current:,.2f} | ${msrp_legacy:,.2f} | ${msrp_current - msrp_legacy:,.2f} |")
print(f"| Customer Savings | ${msrp_current - sale_price_current:,.2f} | $0.00 | ${(msrp_current - sale_price_current):,.2f} |")
print()

print("=" * 120)
print("BUSINESS IMPLICATIONS")
print("=" * 120)
print()

print("METHOD 1 (Current - Use Real CPQ MSRP):")
print("  ✅ Pros:")
print("    - Shows customer a 'discount' from MSRP")
print("    - Uses official CPQ-provided MSRP values")
print("    - More transparent pricing structure")
print("    - Competitive advantage (appears to offer savings)")
print()
print("  ❌ Cons:")
print("    - Different from SV series legacy behavior")
print("    - MSRP may seem inflated if not market-competitive")
print()

print("METHOD 2 (SV Legacy - MSRP = Sale Price):")
print("  ✅ Pros:")
print("    - Simpler pricing (one price point)")
print("    - Matches SV series legacy behavior")
print("    - No confusing 'discounts' - straightforward pricing")
print("    - Customer knows this IS the price")
print()
print("  ❌ Cons:")
print("    - No perceived 'savings' for customer")
print("    - Ignores CPQ-provided MSRP values")
print("    - May seem more expensive vs competitors showing MSRP discounts")
print()

print("=" * 120)
print("RECOMMENDATION")
print("=" * 120)
print()

print("Option A: Keep Current Method (Use CPQ MSRP)")
print("  - Best for competitive positioning")
print("  - Shows value/savings to customer")
print("  - Honors CPQ system's MSRP values")
print()

print("Option B: Switch to SV Legacy Method (MSRP = Sale Price)")
print("  - Best for consistency with SV series")
print("  - Simpler pricing presentation")
print("  - 'What you see is what you pay'")
print()

print("Option C: Make it Configurable by Series")
print("  - SV series: MSRP = Sale Price (legacy)")
print("  - All others: Use CPQ MSRP (current)")
print("  - Best of both worlds")
print()

print("=" * 120)
print("QUESTIONS FOR BOSS")
print("=" * 120)
print()

print("1. Which series should use 'MSRP = Sale Price' method?")
print("   - Only SV series (like legacy)?")
print("   - All CPQ boats?")
print("   - Configurable by series?")
print()

print("2. Should we override CPQ-provided MSRP values?")
print("   - CPQ system has official MSRP values")
print("   - Should we calculate from sale price instead?")
print()

print("3. What's the business goal?")
print("   - Pricing simplification?")
print("   - Match legacy behavior?")
print("   - Competitive positioning?")
print()

print("=" * 120)
