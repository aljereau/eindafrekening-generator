#!/usr/bin/env python3
"""Compare user's address list with database to find missing houses."""

import sqlite3
import json
from dotenv import load_dotenv
import anthropic

load_dotenv()

DB_PATH = "database/ryanrent_mock.db"

USER_ADDRESSES = """
1e Verdeligsweg 6 - 537, Putte
1e Verdeligsweg 6 - 821, Putte 
1e Verdeligsweg 6 - 822, Putte
2e Maasbosstraat 2A Vlaardingen
2e Maasbosstraat 2B Vlaardingen
2e Maasbosstraat 2C Vlaardingen
2e van Leyden Gaelstraat 6, Vlaardingen
Acacialaan 9 Pijnacker
Algemeen woningen
Allard Piersonlaan 142 Den Haag
Amperestraat 36A, Schiedam
Archimedesstraat 6B, Schiedam
Broekweg 25 Vlaardingen
Broersveld 150B Schiedam
Broersvest 74c Schiedam
Buizerdstraat 210 Maassluis
Burchstraat 16A, Oostburg
Burgemeester Stulemeijerlaan 71, Schiedam
Chopinstraat 33c Vlaardingen
Chopinstraat 35A, Vlaardingen
Chopinstraat 39C Vlaardingen
Cloosterstraat 23A, Kloosterzande
Compierekade 15, Alphen a/d Rijn
Coornhertstraat 95 Vlaardingen
Cubalaan 25 Poeldijk
Curacaolaan 24 Vlaardingen
Curacaolaan 88 Vlaardingen
De Driesprong 17 Kwintsheul
de Lus 16 ap28, Schagen
Dorpstraat 27, Moordrecht
Dorpstraat 48 Lopik
Dorpstraat 48, Aarlanderveen
Engelsestraat 16L01 Rotterdam
Engelsestraat 16L3, Rotterdam
Europalaan 50, Sas van Gent
Fenacoliuslaan 56b, Maassluis
Franselaan 273-B
Franz Liszstraat 5, Terneuzen
G.A. Brederolaan 75B Maassluis
Galgeweg 48A, 's-Gravenzande
Genestestraat 32 Terneuzen
Gerberalaan 113
Goudestein 30 Rotterdam
Grimbergen 19
Groenelaan 30B Schiedam
Groeneweg 127 's Gravenzande
Groeneweg 71 's Granzande
Groeneweg 74 's Gravenzande
Haagkamp 11
Hagastraat 8 Schiedam
Herautpad 22 Schiedam
Herenpad 20A, Schiedam
Herenpad 20B, Schiedam
Hoge Noordweg 27B Naaldwijk
Hoge Noordweg 28 Naaldwijk
Hogenbanweg 331 Schiedam
Homeflex Park Honselersdijk
Hontenissestraat 124A Rotterdam
Hontenissestraat 162 Rotterdam
Hotel de Sluiskop
Hugo de Vriesstraat 54 Vlaardingen
Ida Gerhardtplein 10 Spijkenisse
J. van Lennepstraat 13A Schiedam
J. van Lennepstraat 13B Schiedam
J. van Lennepstraat 34 Schiedam
Jacob van Ruijsdaelstraat 28 Roosendaal
Jan van Arkelstraat 118 Vlaardingen
Kaapsebos 11 Maasdijk
Kapershoek 11 Rotterdam
Keesomstraat 22 Vlaardingen
Keesomstraat 50 Vlaardingen
Keesomstraat 54 Vlaardingen
Kerkdreef 42 Axel
Kerklaan 74, Nieuwerkerk aan den IJssel
Kerklaan 80 Nieuwerkerk aan de IJssel
Kerkwervesingel 127 Rotterdam
Kerstendijk 125 Rotterdam
Kethelweg 1B Vlaardingen
Kethelweg 1C Vlaardingen
Kethelweg 66A, Vlaardingen
Kethelweg 66B, Vlaardingen
Kethelweg 66C
Kethelweg 66D, Vlaardingen
Kethelweg 68A
Kimbrenoord 15 Rotterdam
Kimbrenoord 49, Rotterdam
Koperwerf 28
Korhaanstraat 6 Rotterdam
Kreekrug 1 De Lier
Kruiningenstraat 152 Rotterdam
Kruisweg 16, Wobrugge
Kwekerslaan 7, 's-Gravenzande
Kwikstaartweg 45
L.A. Kesperweg 31a Vlaardingen
Laan van Zuid 949
Lange Kruisweg 12 Maasdijk
Lauwersmeer 4, Barendrecht
Leidinglaan 64+66, Sluiskil
Lekdijk 14, Krimpen aan den IJsel
Liesveld 100 Vlaardingen
Lorentzstraat 73 Vlaardingen
Maasdijk 206 's Gravenzande
Maasdijk 69
Markt 5 Bovenwoning, Massluis
Mathenesserdijk 261-C03, Rotterdam
Mendelssohnplein 10C Vlaardingen
Mendelssohnplein 13D Vlaardingen
Mendelssohnplein 46A Vlaardingen
Messchaertplein 39, Vlaardingen
Messchaertplein 40, Vlaardingen
Middelrode 8 Rotterdam
Miltonstraat 55 Rotterdam
Molenstraat 10 Naaldwijk
Molenstraat 23 Naaldwijk
Monsterseweg 26A
Mr. Troelstrastraat 11 Vlaardingen
Mr. Troelstrastraat 37 Vlaardingen
Narcissenstraat 23 Rozenburg
Nic. Beetsstraat 29 Vlaardingen
Nijverheidstraat 26a, Studio 201, Vlaardingen
Noordstraat 26, Walsoorden
Ofwegen 1A, Woubrugge
Oostene 23
Oosterstraat 89 Vlaardingen 
Oostlaan 3 De Lier
Papsouwselaan 138, Delft
Papsouwselaan 178, Delft
Papsouwselaan 30, Delft
Papsouwselaan 32, Delft
Papsouwselaan 34, Delft
Papsouwselaan 44, Delft
Papsouwselaan 52, Delft
Papsouwselaan 58, Delft
Papsouwselaan 68, Delft
Papsouwselaan 86, Delft
Parallelweg 110A Vlaardingen 
Parallelweg 114C
Parallelweg 122a Vlaardingen
Parallelweg 134B
Parallelweg 98B Vlaardingen
Pasteursingel 61B Rotterdam
Plaats 10, Montfoort
Platostraat 80 Rotterdam
Ploegstraat 2a, Schiedam
Prinses Wilhelminastraat 9, Hekendorp
Professor Poelslaan 58c Rotterdam
Putsebocht 136 B01
Rembrandtstraat 20B Naaldwijk
Roerdompstraat 4B, Alblasserdam
Rotterdamsedijk 154b Schiedam
Rubensplein 3b Schiedam
Rubensplein 6B3 Schiedam
Schalkeroord 389 Rotterdam
Schere 238 Rotterdam
Schoonegge 110 Rotterdam
Schoonegge 84 Rotterdam
Singelweg 95, Axel
Sint Liduinastraat 76A Schiedam
Sint Liduinastraat 80 A B Schiedam
Socratesstraat 168 Rotterdam
Spoorsingel 154B, Vlaardingen
St. Annalandstraat 116 Rotterdam
Steenen Dijck 87, Maassluis
Stuifkenszand apart. 2c t/m 4e
Sweelinckstraat 32 Vlaardingen
Tholenstraat 114 Rotterdam
Tulpenstraat 45 Rozenburg
v.d. Waalstraat 16 Vlaardingen
Vaartweg 106C Vlaardingen
Van der Waalsstraat 70 Vlaardingen
Van der Werffstraat 166, Vlaardingen
Van der Werffstraat 240 Vlaardingen
Van der Werffstraat 370 Vlaardingen
Van Ruijsdaellaan 72A, Schiedam
Van Ruijsdaellaan 72B, Schiedam
Van Ruijsdaellaan 72C, Schiedam
van Scorelstraat 73 Maassluis
Voorstraat 25, Vlaardingen
W.M. Bakkerslaan 34, Maasluis
Wagenstraat 70, Wagenberg
Westlandse Langeweg 14
Woutersweg 20
Wouwsestraat 65
Zuidhoek 209D Rotterdam
Zwethkade Zuid 30A, Den Hoorn
Zwingel 8B
""".strip().split('\n')

def normalize_address(addr):
    """Simple normalization for comparison"""
    import re
    addr = addr.lower().strip()
    # Remove city suffixes for matching
    addr = re.sub(r',?\s*(vlaardingen|rotterdam|schiedam|naaldwijk|maassluis|den haag|delft|putte)$', '', addr, flags=re.IGNORECASE)
    addr = addr.strip().rstrip(',')
    return addr

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all DB addresses
    cursor.execute("SELECT object_id, adres FROM huizen")
    db_houses = {row[0]: row[1] for row in cursor.fetchall()}
    db_addresses_normalized = {normalize_address(addr): obj_id for obj_id, addr in db_houses.items()}
    
    print(f"📊 User list: {len(USER_ADDRESSES)} addresses")
    print(f"📦 Database: {len(db_houses)} houses")
    
    # Skip non-house entries
    skip_entries = ['algemeen woningen', 'hotel de sluiskop', 'stuifkenszand apart']
    
    # Find missing addresses
    missing = []
    found = []
    
    for addr in USER_ADDRESSES:
        addr = addr.strip()
        if not addr:
            continue
        if any(skip in addr.lower() for skip in skip_entries):
            continue
            
        normalized = normalize_address(addr)
        
        # Check if exists in DB
        match_found = False
        for db_norm, obj_id in db_addresses_normalized.items():
            # Check for partial match (street name + number)
            if normalized in db_norm or db_norm in normalized:
                match_found = True
                found.append((addr, obj_id))
                break
            # Check if first 15 chars match
            if len(normalized) > 10 and len(db_norm) > 10:
                if normalized[:15] == db_norm[:15]:
                    match_found = True
                    found.append((addr, obj_id))
                    break
        
        if not match_found:
            missing.append(addr)
    
    conn.close()
    
    print(f"\n✅ Found in DB: {len(found)}")
    print(f"❌ Missing: {len(missing)}")
    
    if missing:
        print("\n📋 Missing addresses:")
        for i, addr in enumerate(missing, 1):
            print(f"   {i}. {addr}")


if __name__ == "__main__":
    main()
