import sqlite3
import sys
import os

# Add Shared to path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(root_dir, 'Shared'))

from database import Database

# Facturatie data from user
facturatie_data = """0388	Factuur
0022	Factuur
0148	DS
0149	DS
0150	DS
0003	Factuur
0190	Factuur
0007	DS
0341	Factuur
0372	Factuur
0293	Factuur
0294	Factuur
0373	Factuur
0383	Factuur
0297	Factuur
0350	Factuur
0356	Factuur
0299	Factuur
0300	Factuur
0301	Factuur
0302	Factuur
0303	Factuur
0304	Factuur
0305	Factuur
0384	Factuur
0327	Factuur
0307	Factuur
0002	DS
0043	DS
0135	Factuur
0353	Factuur
0055	DS
0012	DS
0013	DS
0040	DS
0152	Factuur
0322	Factuur
0346	Factuur
0047	DS
0048	DS
0049	DS
0280	DS
0281	DS
0004	Factuur
0027	Factuur
0097	DS
0160	Factuur
0131	Factuur
0026	Factuur
0370	Factuur
0051	Factuur
0052	Factuur
0375	Factuur
0053	Factuur
0151	Factuur
0165	Factuur
0056	DS
0371	Factuur
0153	Factuur
0023	DS
0024	DS
0058	DS
0059	DS
0354	Factuur
0066	Factuur
0061	Factuur
0136	DS
0063	Factuur
0095	Factuur
0064	DS
0006	Factuur
0065	DS
0331	DS
0067	Factuur
0017	Factuur
0109	DS
0070	DS
0170	Factuur
0025	Factuur
0071	DS
0072	DS
0073	DS
0325	Factuur
0176	Factuur
0133	Factuur
0107	DS
0031	DS
0181	Factuur
0075	Factuur
0078	DS
0147	Factuur
0391	Factuur
0039	DS
0187	Factuur
0188	Factuur
0087	Factuur
0146	DS
0082	Factuur
0193	Factuur
0159	Factuur
0084	Factuur
0308	Factuur
0309	Factuur
0310	Factuur
0311	Factuur
0312	Factuur
0313	Factuur
0314	Factuur
0332	Factuur
0315	Factuur
0316	Factuur
0317	Factuur
0338	Factuur
0318	Factuur
0319	Factuur
0339	Factuur
0320	Factuur
0321	Factuur
0225	Factuur
0199	Factuur
0010	Factuur
0011	Factuur
0088	Factuur
0122	Factuur
0033	Factuur
0333	Factuur
0034	Factuur
0085	DS
0202	DS
0359	Factuur
0086	DS
0119	DS
0126	Factuur
0125	Factuur
0206	Factuur
0360	Factuur
0337	Factuur
0382	Factuur
0207	DS
0365	Factuur
0090	DS
0185	DS
0091	DS
0092	Factuur
0028	DS
0385	Factuur
0210	DS
0029	DS
0118	DS
0323	DS
0184	Factuur
0018	DS
0098	DS
0035	Factuur
0036	Factuur
0252	Factuur
0253	Factuur
0254	Factuur
0255	Factuur
0256	Factuur
0257	Factuur
0258	Factuur
0259	Factuur
0217	Factuur
0221	DS
0222	DS
0076	Factuur
0100	Factuur
0101	Factuur
0020	Factuur
0103	Factuur
0104	DS
0102	Factuur
0046	Factuur
0166	DS
0328	Factuur
0329	Factuur
0330	Factuur
A-0076	Factuur
0001	Factuur
0336	Factuur
0227	Factuur
0110	Factuur
0369	DS
0112	DS
0042	DS
0380	Factuur
0381	Factuur
0230	Factuur
0344	DS
0081	Factuur
0260	Factuur
0261	Factuur
0262	Factuur
0263	Factuur
0264	Factuur
0265	Factuur
0266	Factuur
0267	Factuur
0349	Factuur
0268	Factuur
0113	DS
0114	DS
0120	DS
0231	Factuur
0044	Factuur
0045	Factuur
0079	Factuur
0386	DS
0115	Factuur
0269	DS
0270	DS
0271	DS
0272	DS
0340	Factuur
0117	DS
0204	Factuur
0233	DS
0005	Factuur
0226	Factuur
0121	Factuur
0179	Factuur
0154	Factuur
0362	Factuur
0236	Factuur
0144	DS
0197	DS
0239	Factuur
0164	Factuur
0050	Factuur
0243	Factuur
0123	DS
0124	DS
0200	DS
0099	Factuur
0127	Factuur
0128	DS
0249	Factuur
0129	DS
0021	Factuur
0241	Factuur
0130	Factuur
0089	Factuur
0347	Factuur
0351	Factuur
0352	Factuur
0016	Factuur
0324	DS
0387	Factuur
0374	Factuur
0158	DS
0167	DS
0077	Factuur
0080	Factuur
A-0121	Factuur
0368	Factuur
A-0108	Factuur
0138	DS
0139	Factuur
0037	Factuur
0105	Factuur
0171	Factuur
0212	Factuur
0140	DS
0142	DS
0141	DS
0143	DS
0145	DS
0232	Factuur
0376	Factuur"""

def add_facturatie_column():
    """Add facturatie_type column to huizen table"""
    db = Database()
    conn = db.get_connection()
    
    try:
        # Add column if it doesn't exist
        conn.execute("""
            ALTER TABLE huizen 
            ADD COLUMN facturatie_type TEXT DEFAULT 'Factuur'
        """)
        print("✅ Added facturatie_type column to huizen table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Column facturatie_type already exists")
        else:
            raise
    
    conn.commit()
    conn.close()

def import_facturatie_data():
    """Import facturatie data from user's list"""
    db = Database()
    conn = db.get_connection()
    
    lines = facturatie_data.strip().split('\n')
    updated = 0
    not_found = []
    
    for line in lines:
        parts = line.split('\t')
        if len(parts) != 2:
            continue
            
        object_id = parts[0].strip()
        facturatie_type = parts[1].strip()
        
        if not object_id or not facturatie_type:
            continue
        
        # Update the record
        cursor = conn.execute("""
            UPDATE huizen 
            SET facturatie_type = ?
            WHERE object_id = ?
        """, (facturatie_type, object_id))
        
        if cursor.rowcount > 0:
            updated += 1
        else:
            not_found.append(object_id)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {updated} houses with facturatie_type")
    if not_found:
        print(f"⚠️  {len(not_found)} object_ids not found in database:")
        print(f"   {', '.join(not_found[:10])}" + (" ..." if len(not_found) > 10 else ""))

if __name__ == "__main__":
    print("🔧 Adding facturatie_type column...")
    add_facturatie_column()
    
    print("\n📥 Importing facturatie data...")
    import_facturatie_data()
    
    print("\n✅ Done!")
