#!/usr/bin/env python3
"""
Update build_excel_template.py to:
1. Change dropdown from "5_uur,7_uur" to "Basis Schoonmaak,Intensief Schoonmaak"
2. Remove ALL sheet protection code
"""

with open('build_excel_template.py', 'r') as f:
    lines = f.readlines()

# Changes to make
changes_made = []

for i in range(len(lines)):
    # Change dropdown options
    if '5_uur,7_uur' in lines[i]:
        lines[i] = lines[i].replace('5_uur,7_uur', 'Basis Schoonmaak,Intensief Schoonmaak')
        lines[i] = lines[i].replace('Kies 5_uur of 7_uur', 'Kies Basis Schoonmaak of Intensief Schoonmaak')
        changes_made.append(f'Line {i+1}: Changed dropdown options')
    
    # Change formula references
    if '=\"5_uur\"' in lines[i] or '=\"7_uur\"' in lines[i]:
        lines[i] = lines[i].replace('=\"5_uur\"', '=\"Basis Schoonmaak\"')
        lines[i] = lines[i].replace('=\"7_uur\"', '=\"Intensief Schoonmaak\"')
        changes_made.append(f'Line {i+1}: Updated formula reference')
    
    # Remove Protection(locked=True)
    if '.protection = Protection(locked=True)' in lines[i]:
        lines[i] = ''  # Remove the line entirely
        changes_made.append(f'Line {i+1}: Removed Protection(locked=True)')
    
    # Comment out ws.protection.sheet = True
    if 'ws.protection.sheet = True' in lines[i] and not lines[i].strip().startswith('#'):
        lines[i] = lines[i].replace('ws.protection.sheet = True', '# ws.protection.sheet = True  # DISABLED - All cells unlocked')
        changes_made.append(f'Line {i+1}: Disabled sheet protection')

# Remove protection loops - just comment them out
# Find and comment blocks that start with "Enable sheet protection" comments
in_protection_block = False
for i in range(len(lines)):
    if 'Enable sheet protection' in lines[i] and lines[i].strip().startswith('#'):
        in_protection_block = True
    
    if in_protection_block:
        if 'for row_cells in ws.iter_rows()' in lines[i]:
            # Comment out this line and next ~10 lines until we hit a blank line or new section
            j = i
            while j < len(lines) and j < i +15:
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    if 'def ' in lines[j] or (lines[j].strip() == ''):
                        break
                    if not lines[j].strip().startswith('#'):
                        lines[j] = '    # ' + lines[j].lstrip()
                j += 1
            in_protection_block = False

# Write back
with open('build_excel_template.py', 'w') as f:
    f.writelines(lines)

print('✅ Updated build_excel_template.py')
for change in changes_made[:10]:
    print(f'  • {change}')
if len(changes_made) > 10:
    print(f'  • ... and {len(changes_made) - 10} more changes')
