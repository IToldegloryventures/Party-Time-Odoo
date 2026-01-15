"""Debug why QBO names aren't matching."""
from openpyxl import load_workbook
import sys
sys.path.insert(0, r'C:\Users\ashpt\Party-Time-Odoo\scripts')
from merge_vendor_data import VendorMerger

merger = VendorMerger(
    rippling_path=r'C:\Users\ashpt\Downloads\Copy of Vendors Rippling.xlsx',
    qbo_path=r'C:\Users\ashpt\Downloads\Copy of Vendors QBO.xlsx',
    master_path=r'C:\Users\ashpt\Downloads\Master Vendors List (1).xlsx'
)

rippling_vendors = merger.load_rippling_vendors()
qbo_vendors = merger.load_qbo_vendors()
master_vendors = merger.load_master_vendors()

print(f"Rippling vendors loaded: {len(rippling_vendors)}")
print(f"QBO vendors loaded: {len(qbo_vendors)}")
print(f"Master vendors loaded: {len(master_vendors)}")
print()

# Check first 10 Rippling names
print("First 10 Rippling vendor names:")
for i, v in enumerate(rippling_vendors[:10]):
    print(f"  {i+1}. '{v.name}' (company: '{v.company_name}')")

print("\nFirst 10 QBO vendor names:")
for i, v in enumerate(qbo_vendors[:10]):
    print(f"  {i+1}. '{v.name}' (phone: '{v.phone}')")

print("\nFirst 10 Master vendor names:")
for i, v in enumerate(master_vendors[:10]):
    notes_preview = v.vendor_notes[:50] if v.vendor_notes else "(none)"
    print(f"  {i+1}. '{v.name}' (notes: '{notes_preview}')")

# Try matching
print("\n\nTrying to match first 5 Rippling vendors:")
for r_vendor in rippling_vendors[:5]:
    r_name = r_vendor.name.strip().lower()
    print(f"\nRippling: '{r_vendor.name}'")
    
    # Check QBO
    qbo_match = None
    for q_vendor in qbo_vendors:
        q_name = q_vendor.name.strip().lower()
        if r_name == q_name:
            qbo_match = q_vendor
            break
    if qbo_match:
        print(f"  -> QBO match: '{qbo_match.name}' (phone: '{qbo_match.phone}')")
    else:
        print(f"  -> No QBO match found")
        # Show closest QBO names
        print(f"     Closest QBO names:")
        for q_vendor in qbo_vendors[:5]:
            print(f"       '{q_vendor.name}'")
    
    # Check Master
    master_match = None
    for m_vendor in master_vendors:
        m_name = m_vendor.name.strip().lower()
        if r_name == m_name:
            master_match = m_vendor
            break
    if master_match:
        notes_preview = master_match.vendor_notes[:50] if master_match.vendor_notes else "(none)"
        print(f"  -> Master match: '{master_match.name}' (notes: '{notes_preview}')")
    else:
        print(f"  -> No Master match found")
