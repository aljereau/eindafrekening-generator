import sqlite3
from pathlib import Path

# DB Path
DB_PATH = Path("database/ryanrent_mock.db")

def fix_and_update():
    print(f"🔧 Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # ---------------------------------------------------------
        # 0. DROP VIEW (Dependencies)
        # ---------------------------------------------------------
        print("🔻 Dropping view 'v_house_costs' to allow schema changes...")
        cursor.execute("DROP VIEW IF EXISTS v_house_costs")

        # ---------------------------------------------------------
        # 1. FIX INHUUR_CONTRACTEN (Remove unnecessary columns)
        # ---------------------------------------------------------
        print("🧹 Cleaning 'inhuur_contracten' (removing service breakdown)...")
        # List of columns to drop
        cols_to_drop = [
            "internet", "meubilering", "eindschoonmaak", 
            "tuinonderhoud", "stoffering", "aanschaf_inventaris",
            "internet_kosten", "inventaris_kosten", "schoonmaak_kosten"
        ]
        
        cursor.execute("PRAGMA table_info(inhuur_contracten)")
        existing_cols = [row[1] for row in cursor.fetchall()]

        for col in cols_to_drop:
            if col in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE inhuur_contracten DROP COLUMN {col}")
                    print(f"   - Dropped column: '{col}'")
                except sqlite3.OperationalError:
                     # Fallback for old SQLite if needed, but usually works
                     pass

        # ---------------------------------------------------------
        # 2. UPDATE HUIZEN SCHEMA (Rename/Add cols)
        # ---------------------------------------------------------
        print("🏗️  Updating 'huizen' schema to match business terms...")
        
        cursor.execute("PRAGMA table_info(huizen)")
        huizen_cols = [row[1] for row in cursor.fetchall()]
        
        # Renames
        renames = {
            "kosten_internet_standaard": "internet",
            "kosten_inventaris_standaard": "meubilering",
            "kosten_onderhoud_standaard": "tuinonderhoud",
            "kosten_aanschaf_standaard": "aanschaf_inventaris",
        }
        
        for old_c, new_c in renames.items():
            if old_c in huizen_cols and new_c not in huizen_cols:
                cursor.execute(f"ALTER TABLE huizen RENAME COLUMN {old_c} TO {new_c}")
                print(f"   - Renamed '{old_c}' -> '{new_c}'")
        
        # Drop obsolete
        if "kosten_afval_standaard" in huizen_cols:
             cursor.execute("ALTER TABLE huizen DROP COLUMN kosten_afval_standaard")
             print("   - Dropped 'kosten_afval_standaard'")
             
        # Add missing
        cursor.execute("PRAGMA table_info(huizen)")
        current_huizen_cols = [row[1] for row in cursor.fetchall()]
        
        new_cols = ["stoffering", "eindschoonmaak"]
        for col in new_cols:
            if col not in current_huizen_cols:
                cursor.execute(f"ALTER TABLE huizen ADD COLUMN {col} REAL DEFAULT 0")
                print(f"   - Added column '{col}'")

        # ---------------------------------------------------------
        # 3. RECREATE VIEW (Updated Definition)
        # ---------------------------------------------------------
        print("🔄 Recreating view 'v_house_costs'...")
        view_sql = """
        CREATE VIEW v_house_costs AS
            SELECT 
                h.id as house_id,
                h.adres,
                h.object_id,
                h.aantal_pers as capacity,
                
                -- Base Cost (Latest Inhuur) - Default to 0 if no contract
                COALESCE(
                    (SELECT inhuur_prijs_excl_btw 
                     FROM inhuur_contracten ic 
                     WHERE ic.property_id = h.id 
                     ORDER BY ic.start_date DESC LIMIT 1), 
                    0
                ) as base_cost,
                
                -- Fixed Overhead (Sum of mandatory standard costs)
                COALESCE(h.meubilering, 0) + 
                COALESCE(h.tuinonderhoud, 0) + 
                COALESCE(h.aanschaf_inventaris, 0) + 
                COALESCE(h.stoffering, 0) + 
                COALESCE(h.kosten_gem_heffingen_standaard, 0) + 
                COALESCE(h.kosten_operationeel_standaard, 0) 
                as fixed_overhead,
                
                -- Optional/Variable Components
                COALESCE(h.internet, 0) as cost_internet,
                COALESCE(h.voorschot_gwe, 0) as cost_gwe,
                COALESCE(h.eindschoonmaak, 0) as cost_cleaning
                
            FROM huizen h
            WHERE h.status = 'active';
        """
        cursor.execute(view_sql)
        print("   - View recreated successfully.")

        # ---------------------------------------------------------
        # 4. RECALCULATE HUIZEN COSTS
        # ---------------------------------------------------------
        print("🧮 Recalculating standard costs for properties...")
        
        # Get Parameters
        cursor.execute("SELECT naam, prijs_pp_pw FROM parameters")
        params = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"   - Loaded parameters: {params}")
        
        # Map Parameter Name -> Huizen Column
        param_col_map = {
            "Internet": "internet",
            "Meubilering": "meubilering",
            "Tuinonderhoud": "tuinonderhoud",
            "Aanschaf inventaris": "aanschaf_inventaris",
            "Stoffering": "stoffering"
        }
        
        # Get Houses
        cursor.execute("SELECT id, aantal_pers FROM huizen WHERE status='active' AND aantal_pers > 0")
        houses = cursor.fetchall()
        
        update_count = 0
        for house in houses:
            h_id, people = house
            if not people: continue
            
            # Factor: (52 weeks / 12 months) = 4.333
            monthly_factor = (52 / 12)
            
            updates = []
            values = []
            
            for p_name, col_name in param_col_map.items():
                if p_name in params:
                    price = params[p_name]
                    # Cost = Price (pppw) * People * 4.333
                    cost = round(price * people * monthly_factor, 2)
                    updates.append(f"{col_name} = ?")
                    values.append(cost)
            
            if updates:
                sql = f"UPDATE huizen SET {', '.join(updates)} WHERE id = ?"
                values.append(h_id)
                cursor.execute(sql, values)
                update_count += 1
                
        print(f"   - Updated costs for {update_count} houses.")

        conn.commit()
        print("\n✅ Schema Fix & Cost Update completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Operation failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_and_update()
