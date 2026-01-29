# 🚤 Window Sticker System - Quick Start Guide
## One-Page Reference

---

## 🎯 What It Does

Generate window stickers with complete pricing and dealer cost for any Bennington boat.

---

## ⚡ Quick Start

```bash
python3 generate_complete_window_sticker.py <HULL_NUMBER>

# Example:
python3 generate_complete_window_sticker.py ETWP6278J324
```

That's it! ✅

---

## 📊 How It Works (Simple Version)

```
1. You provide: Hull Serial Number (e.g., ETWP6278J324)
                         ↓
2. System gets boat info from: SerialNumberMaster table
                         ↓
3. System determines: Model Year 24 → Search BoatOptions24
                         ↓
4. System gets pricing: Line items with MSRP
                         ↓
5. System calculates: Dealer Cost (if margins available)
                         ↓
6. Output: Complete Window Sticker
```

---

## 🔑 The Three Tables

### 1. **SerialNumberMaster** (warrantyparts)
- **What:** Boat header info (model, dealer, colors)
- **Key Field:** `SN_MY` = Model Year (24, 25, 26)
- **Use:** Starting point - tells us which table to search

### 2. **BoatOptions24/25/26** (warrantyparts)
- **What:** Line items with MSRP pricing
- **Key Field:** `ItemMasterProdCat` = Category (BS1, EN7, ACC)
- **Use:** Get complete pricing breakdown

### 3. **DealerMargins** (warrantyparts_test)
- **What:** Margin percentages per dealer per series
- **Key Field:** `dealer_id` + `series_id`
- **Use:** Calculate dealer cost

---

## 💰 Dealer Cost Formula

```
Dealer Cost = MSRP × (1 - Margin%)

Example:
  MSRP:         $100,000
  Margin:       27%
  Dealer Cost:  $100,000 × 0.73 = $73,000
  Savings:      $27,000
```

---

## 📋 Product Categories

```
BS1 / BOA  → Base Boat
EN7 / ENG  → Engine
ACC / ACY  → Accessories
PPR / PPY  → Prep & Rigging
H1* / H3*  → Colors & Options
L0 / L12   → Seating & Furniture
C1L / C2   → Discounts (negative)
```

---

## 🔍 Common Tasks

### Find a boat:
```sql
SELECT * FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWP6278J324';
```

### Get line items:
```sql
SELECT * FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324';
```

### Check dealer margins:
```sql
SELECT * FROM warrantyparts_test.DealerMargins
WHERE dealer_id = '333836' AND series_id = 'SV';
```

---

## ⚠️ Important Notes

### ✅ DO:
- Always start with SerialNumberMaster
- Use `ItemMasterProdCat` for categorization
- Use `SN_MY` to determine table

### ❌ DON'T:
- Filter by item numbers starting with "90" (old system)
- Search all BoatOptions tables (inefficient)
- Start with BoatOptions directly

---

## 🎓 Key Insight

**The Magic Field: `SN_MY`**

This field in SerialNumberMaster tells you which BoatOptions table to search:
- `SN_MY = 24` → Search `BoatOptions24`
- `SN_MY = 25` → Search `BoatOptions25`
- `SN_MY = 26` → Search `BoatOptions26`

**This makes lookups 10x faster!**

---

## 📞 Need Help?

See **WINDOW_STICKER_SYSTEM_COMPLETE_GUIDE.md** for:
- Detailed explanations
- Troubleshooting
- SQL examples
- Architecture diagrams

---

## 📈 Examples

| Hull | Model | MSRP | Type |
|------|-------|------|------|
| ETWP6278J324 | 2024 20SVFSR | $31,386 | Small Fishing |
| ETWS0235L526 | 2026 22SSRSF | $60,938 | Mid-Size Sport |
| ETWC6109F526 | 2025 30QXSBAX2SE | $257,363 | Luxury QX |

---

**System Status:** ✅ Production Ready
**Last Updated:** January 29, 2026
