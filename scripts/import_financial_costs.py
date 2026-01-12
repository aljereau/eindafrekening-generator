#!/usr/bin/env python3
"""
Import costs (Rent, GWE, Internet, VVE) from text dump.
Updates 'huizen' and 'inhuur_contracten'.
"""

import sqlite3
import re
import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "database/ryanrent_mock.db"

RAW_DATA = """
Grootboekrekening	Huur (belast) woningen	
		
Omschrijving	Per.	Max. of Debet
1e Verdeligsweg 6 - 537, Putte		€ 475,00
1e Verdeligsweg 6 - 821, Putte 		€ 475,00
1e Verdeligsweg 6 - 822, Putte		€ 475,00
2e Maasbosstraat 2A Vlaardingen		€ 1.570,24
2e Maasbosstraat 2B Vlaardingen		€ 1.570,24
2e Maasbosstraat 2C Vlaardingen		€ 1.475,31
2e van Leyden Gaelstraat 6, Vlaardingen		€ 2.930,56
Acacialaan 9 Pijnacker		€ 6.753,42
Algemeen woningen		€ 13.043,23
Allard Piersonlaan 142 Den Haag		€ 1.416,85
Amperestraat 36A, Schiedam		€ 1.691,63
Archimedesstraat 6B, Schiedam		€ 1.623,96
Broekweg 25 Vlaardingen		€ 1.708,41
Broersveld 150B Schiedam		€ 990,46
Broersvest 74c Schiedam		€ 2.051,51
Buizerdstraat 210 Maassluis		€ 1.677,89
Burchstraat 16A, Oostburg		€ 3.550,00
Burgemeester Stulemeijerlaan 71, Schiedam		€ 1.019,00
Chopinstraat 33c Vlaardingen		€ 1.300,00
Chopinstraat 35A, Vlaardingen		€ 2.165,26
Chopinstraat 39C Vlaardingen		€ 1.952,46
Cloosterstraat 23A, Kloosterzande		€ 2.850,00
Compierekade 15, Alphen a/d Rijn		€ 6.250,00
Coornhertstraat 95 Vlaardingen		€ 1.557,73
Cubalaan 25 Poeldijk		€ 4.850,00
Curacaolaan 24 Vlaardingen		€ 3.269,00
Curacaolaan 88 Vlaardingen		€ 895,00
De Driesprong 17 Kwintsheul		€ 4.140,00
de Lus 16 ap28, Schagen		€ 59,85
Dorpstraat 27, Moordrecht		€ 1.409,40
Dorpstraat 48 Lopik		€ 11.100,00
Dorpstraat 48, Aarlanderveen		€ 8.640,30
Engelsestraat 16L01 Rotterdam		€ 1.993,32
Engelsestraat 16L3, Rotterdam		€ 3.435,06
Europalaan 50, Sas van Gent		€ 3.484,49
Fenacoliuslaan 56b, Maassluis		€ 1.003,21
Franselaan 273-B		€ 1.641,12
Franz Liszstraat 5, Terneuzen		€ 3.643,50
G.A. Brederolaan 75B Maassluis		€ 1.677,89
Galgeweg 48A, 's-Gravenzande		€ 3.643,50
Genestestraat 32 Terneuzen		€ 2.602,50
Gerberalaan 113		€ 111,47
Goudestein 30 Rotterdam		€ 1.327,00
Grimbergen 19		€ 2.916,00
Groenelaan 30B Schiedam		€ 1.625,00
Groeneweg 127 's Gravenzande		€ 2.650,00
Groeneweg 71 's Granzande		€ 1.850,00
Groeneweg 74 's Gravenzande		€ 1.916,00
Haagkamp 11		€ 2.006,42
Hagastraat 8 Schiedam		€ 1.451,23
Herautpad 22 Schiedam		€ 1.125,00
Herenpad 20A, Schiedam		€ 2.075,05
Herenpad 20B, Schiedam		€ 992,34
Hoge Noordweg 27B Naaldwijk		€ 2.700,00
Hoge Noordweg 28 Naaldwijk		€ 2.800,00
Hogenbanweg 331 Schiedam		€ 1.568,43
Homeflex Park Honselersdijk		€ 600,00
Hontenissestraat 124A Rotterdam		€ 1.574,00
Hontenissestraat 162 Rotterdam		€ 3.347,25
Hotel de Sluiskop		€ 16.986,67
Hugo de Vriesstraat 54 Vlaardingen		€ 895,00
Ida Gerhardtplein 10 Spijkenisse		€ 757,44
J. van Lennepstraat 13A Schiedam		€ 989,88
J. van Lennepstraat 13B Schiedam		€ 989,88
J. van Lennepstraat 34 Schiedam		€ 2.989,54
Jacob van Ruijsdaelstraat 28 Roosendaal		€ 1.560,00
Jan van Arkelstraat 118 Vlaardingen		€ 895,00
Kaapsebos 11 Maasdijk		€ 8.370,00
Kapershoek 11 Rotterdam		€ 1.400,53
Keesomstraat 22 Vlaardingen		€ 2.336,00
Keesomstraat 50 Vlaardingen		€ 895,00
Keesomstraat 54 Vlaardingen		€ 1.405,00
Kerkdreef 42 Axel		€ 2.250,00
Kerklaan 74, Nieuwerkerk aan den IJssel		€ 647,10
Kerklaan 80 Nieuwerkerk aan de IJssel		€ 764,26
Kerkwervesingel 127 Rotterdam		€ 3.226,47
Kerstendijk 125 Rotterdam		€ 1.200,00
Kethelweg 1B Vlaardingen		€ 1.708,41
Kethelweg 1C Vlaardingen		€ 1.708,41
Kethelweg 66A, Vlaardingen		€ 2.593,81
Kethelweg 66B, Vlaardingen		€ 2.593,81
Kethelweg 66C		€ 2.082,00
Kethelweg 66D, Vlaardingen		€ 4.293,83
Kethelweg 68A		€ 2.269,38
Kimbrenoord 15 Rotterdam		€ 1.993,32
Kimbrenoord 49, Rotterdam		€ 2.386,52
Koperwerf 28		€ 3.009,63
Korhaanstraat 6 Rotterdam		€ 914,99
Kreekrug 1 De Lier		€ 4.800,00
Kruiningenstraat 152 Rotterdam		€ 1.552,05
Kruisweg 16, Wobrugge		€ 4.750,00
Kwekerslaan 7, 's-Gravenzande		€ 4.506,00
Kwikstaartweg 45		€ 1.970,00
L.A. Kesperweg 31a Vlaardingen		€ 895,00
Laan van Zuid 949		€ 1.993,32
Lange Kruisweg 12 Maasdijk		€ 2.928,69
Lauwersmeer 4, Barendrecht		€ 2.550,00
Leidinglaan 64+66, Sluiskil		€ 1.927,05
Lekdijk 14, Krimpen aan den IJsel		€ 6.500,00
Liesveld 100 Vlaardingen		€ 1.270,97
Lorentzstraat 73 Vlaardingen		€ 1.865,50
Maasdijk 206 's Gravenzande		€ 3.400,00
Maasdijk 69		€ 3.400,00
Markt 5 Bovenwoning, Massluis		€ 1.715,60
Mathenesserdijk 261-C03, Rotterdam		€ 1.545,73
Mendelssohnplein 10C Vlaardingen		€ 2.801,00
Mendelssohnplein 13D Vlaardingen		€ 2.801,00
Mendelssohnplein 46A Vlaardingen		€ 1.561,50
Messchaertplein 39, Vlaardingen		€ 1.784,67
Messchaertplein 40, Vlaardingen		€ 2.810,70
Middelrode 8 Rotterdam		€ 1.400,53
Miltonstraat 55 Rotterdam		€ 1.345,37
Molenstraat 10 Naaldwijk		€ 2.088,66
Molenstraat 23 Naaldwijk		€ 1.282,51
Monsterseweg 26A		€ 8.450,00
Mr. Troelstrastraat 11 Vlaardingen		€ 895,00
Mr. Troelstrastraat 37 Vlaardingen		€ 1.723,44
Narcissenstraat 23 Rozenburg		€ 1.700,00
Nic. Beetsstraat 29 Vlaardingen		€ 895,00
Nijverheidstraat 26a, Studio 201, Vlaardingen		€ 59,85
Noordstraat 26, Walsoorden		€ 5.608,13
Ofwegen 1A, Woubrugge		€ 2.900,00
Oostene 23		€ 972,00
Oosterstraat 89 Vlaardingen 		€ 1.569,30
Oostlaan 3 De Lier		€ 2.561,50
Papsouwselaan 138, Delft		€ 435,00
Papsouwselaan 178, Delft		€ 560,00
Papsouwselaan 30, Delft		€ 435,00
Papsouwselaan 32, Delft		€ 435,00
Papsouwselaan 34, Delft		€ 435,00
Papsouwselaan 44, Delft		€ 435,00
Papsouwselaan 52, Delft		€ 435,00
Papsouwselaan 58, Delft		€ 435,00
Papsouwselaan 68, Delft		€ 435,00
Papsouwselaan 86, Delft		€ 435,00
Parallelweg 110A Vlaardingen 		€ 2.082,00
Parallelweg 114C		€ 2.100,00
Parallelweg 122a Vlaardingen		€ 895,00
Parallelweg 134B		€ 2.100,00
Parallelweg 98B Vlaardingen		€ 1.397,00
Pasteursingel 61B Rotterdam		€ 1.776,00
Plaats 10, Montfoort		€ 2.300,00
Platostraat 80 Rotterdam		€ 1.200,00
Ploegstraat 2a, Schiedam		€ 2.166,65
Prinses Wilhelminastraat 9, Hekendorp		€ 3.200,00
Professor Poelslaan 58c Rotterdam		€ 2.840,41
Putsebocht 136 B01		€ 1.494,99
Rembrandtstraat 20B Naaldwijk		€ 1.603,14
Roerdompstraat 4B, Alblasserdam		€ 3.200,00
Rotterdamsedijk 154b Schiedam		€ 895,00
Rubensplein 3b Schiedam		€ 895,00
Rubensplein 6B3 Schiedam		€ 2.238,15
Schalkeroord 389 Rotterdam		€ 1.623,90
Schere 238 Rotterdam		€ 1.345,37
Schoonegge 110 Rotterdam		€ 1.327,00
Schoonegge 84 Rotterdam		€ 4.141,50
Singelweg 95, Axel		€ 614,82
Sint Liduinastraat 76A Schiedam		€ 900,00
Sint Liduinastraat 80 A B Schiedam		€ 4.216,22
Socratesstraat 168 Rotterdam		€ 1.200,00
Spoorsingel 154B, Vlaardingen		€ 2.129,12
St. Annalandstraat 116 Rotterdam		€ 1.415,00
Steenen Dijck 87, Maassluis		€ 3.383,25
Stuifkenszand apart. 2c t/m 4e		€ 12.150,00
Sweelinckstraat 32 Vlaardingen		€ 730,44
Tholenstraat 114 Rotterdam		€ 1.400,53
Tulpenstraat 45 Rozenburg		€ 441,00
v.d. Waalstraat 16 Vlaardingen		€ 895,00
Vaartweg 106C Vlaardingen		€ 1.830,43
Van der Waalsstraat 70 Vlaardingen		€ 895,00
Van der Werffstraat 166, Vlaardingen		€ 1.250,00
Van der Werffstraat 240 Vlaardingen		€ 895,00
Van der Werffstraat 370 Vlaardingen		€ 895,00
Van Ruijsdaellaan 72A, Schiedam		€ 1.560,00
Van Ruijsdaellaan 72B, Schiedam		€ 1.560,00
Van Ruijsdaellaan 72C, Schiedam		€ 1.560,00
van Scorelstraat 73 Maassluis		€ 2.364,30
Voorstraat 25, Vlaardingen		€ 2.170,00
W.M. Bakkerslaan 34, Maasluis		€ 2.509,85
Wagenstraat 70, Wagenberg		€ 7.570,00
Westlandse Langeweg 14		€ 7.047,00
Woutersweg 20		€ 2.600,00
Wouwsestraat 65		€ 2.916,00
Zuidhoek 209D Rotterdam		€ 1.872,00
Zwethkade Zuid 30A, Den Hoorn		€ 3.500,00
Zwingel 8B		€ 13.043,23

Grootboekrekening	Gas, water en electra woningen	
		
Omschrijving	Per.	Max. of Debet
2e Maasbosstraat 2A Vlaardingen		179,57
2e Maasbosstraat 2B Vlaardingen		168,87
2e Maasbosstraat 2C Vlaardingen		106,43
2e van Leyden Gaelstraat 6, Vlaardingen		482,84
Acacialaan 9 Pijnacker		112,25
Admiraliteitskade 80-02 Rotterdam		71,06
Algemeen woningen		19375,27
Amperestraat 36A, Schiedam		331,67
Archimedesstraat 6B, Schiedam		174,24
Beeklaan 294-1/294-2, Den Haag		158,71
Broekweg 166B Rotterdam		40,37
Broekweg 25 Vlaardingen		260,15
Broersveld 150B Schiedam		50,28
Broersvest 74c Schiedam		165,62
Buizerdstraat 210 Maassluis		142,75
Burchstraat 16A, Oostburg		450
Burgemeester Stulemeijerlaan 71, Schiedam		47,03
Chopinstraat 33c Vlaardingen		230,16
Chopinstraat 35A, Vlaardingen		146,31
Chopinstraat 39C Vlaardingen		255,59
Cloosterstraat 23A, Kloosterzande		467,98
Compierekade 15, Alphen a/d Rijn		650
Coornhertstraat 95 Vlaardingen		223,96
Cubalaan 25 Poeldijk		450
Curacaolaan 24 Vlaardingen		406,25
Curacaolaan 88 Vlaardingen		297,55
De Driesprong 17 Kwintsheul		902,75
Dorpstraat 46, Aarlanderveen		236,42
Dorpstraat 48 Lopik		118,94
Dorpstraat 48, Aarlanderveen		180,1
Energieweg 40 Vlaardingen		266,49
Engelsestraat 16L01 Rotterdam		240,27
Engelsestraat 16L3, Rotterdam		58,43
Europalaan 50, Sas van Gent		517,88
Franselaan 273-B		272,56
Franz Liszstraat 5, Terneuzen		631,65
G.A. Brederolaan 75B Maassluis		208,85
Galgeweg 48A, 's-Gravenzande		773,78
Goghlaan 36, Roosendaal		309,4
Goudestein 30 Rotterdam		2374,49
Groenelaan 30B Schiedam		190,22
Groenelaan 35 Schiedam		34,12
Groeneweg 127 's Gravenzande		711,47
Groeneweg 71 's Granzande		424,43
Groeneweg 74 's Gravenzande		200
Hagastraat 8 Schiedam		208,34
Herautpad 22 Schiedam		116,38
Herenpad 20A, Schiedam		234,76
Hoge Noordweg 26A Naaldwijk		665,09
Hoge Noordweg 27A Naaldwijk		430
Hoge Noordweg 27B Naaldwijk		1144
Hoge Noordweg 28 Naaldwijk		11040,15
Hogenbanweg 331 Schiedam		195,97
Hontenissestraat 124A Rotterdam		385,02
Hontenissestraat 162 Rotterdam		380
Hugo de Vriesstraat 54 Vlaardingen		189,37
J. van Lennepstraat 13A Schiedam		273,62
J. van Lennepstraat 13B Schiedam		482,46
J. van Lennepstraat 34 Schiedam		2472,37
Jacob van Ruijsdaelstraat 28 Roosendaal		69,73
Jan van Arkelstraat 118 Vlaardingen		203,11
Kaapsebos 11 Maasdijk		927
Kapershoek 11 Rotterdam		190,11
Keesomstraat 22 Vlaardingen		971,97
Keesomstraat 50 Vlaardingen		236,33
Keesomstraat 54 Vlaardingen		276,32
Kerkwervesingel 127 Rotterdam		70,04
Kerstendijk 125 Rotterdam		519,95
Kethelweg 1B Vlaardingen		85,24
Kethelweg 1C Vlaardingen		32,11
Kethelweg 60 Vlaardingen		49,54
Kethelweg 66A, Vlaardingen		151,41
Kethelweg 66B, Vlaardingen		329,99
Kethelweg 66C		370,02
Kethelweg 68A		491,73
Kimbrenoord 15 Rotterdam		210,1
Kimbrenoord 49, Rotterdam		27,03
Knuttelstraat 17 Delft		558,91
Kreekrug 1 De Lier		475
Kruiningenstraat 152 Rotterdam		240,59
Kruiningenstraat 185, Rotterdam		19,39
Kruisweg 16, Wobrugge		600
Kwekerslaan 7, 's-Gravenzande		450
Kwikstaartweg 45		350,03
L.A. Kesperweg 31a Vlaardingen		189,37
Laan van Adrichem 12 De Lier		692,92
Laan van Zuid 949		159
Lange Kruisweg 12 Maasdijk		272,64
Lauwersmeer 4, Barendrecht		394
Liesveld 100 Vlaardingen		336,51
Lorentzstraat 73 Vlaardingen		345,28
Maasdijk 206 's Gravenzande		602,67
Maasdijk 67, 's-gravenzande		193,05
Maasdijk 69		2470,8
Markt 5 Bovenwoning, Massluis		395,02
Mendelssohnplein 10C Vlaardingen		75,67
Mendelssohnplein 13D Vlaardingen		96,38
Mendelssohnplein 46A Vlaardingen		569,98
Messchaertplein 39, Vlaardingen		160,42
Messchaertplein 40, Vlaardingen		332,55
Middelrode 8 Rotterdam		91,33
Miltonstraat 55 Rotterdam		88,84
Miltonstraat 85 Rotterdam		25,69
Molenstraat 10 Naaldwijk		1600
Molenstraat 23 Naaldwijk		477,68
Mr. Troelstrastraat 11 Vlaardingen		283,56
Mr. Troelstrastraat 37 Vlaardingen		181,36
Narcissenstraat 23 Rozenburg		250
Nic. Beetsstraat 29 Vlaardingen		202,99
Noordstraat 26, Walsoorden		740
Ofwegen 1A, Woubrugge		350
Oosterstraat 89 Vlaardingen 		315,48
Oosthavenkade 39		807,23
Oostlaan 3 De Lier		463,53
Parallelweg 114C		250
Parallelweg 122a Vlaardingen		381,26
Parallelweg 134B		250
Parallelweg 98B Vlaardingen		167,62
Pasteursingel 61B Rotterdam		450
Pieter Jelle Troelstraweg 2A Maassluis		13,76
Plaats 10, Montfoort		250
Platostraat 38 Rotterdam		4,67
Platostraat 80 Rotterdam		266,32
Ploegstraat 2a, Schiedam		107,58
Prinses Wilhelminastraat 9, Hekendorp		300,05
Professor Kamerlingh Onneslaan 98A Schiedam		26,62
Professor Poelslaan 58c Rotterdam		224,26
Putsebocht 136 B01		112,58
Ranaholm 3, Schiedam		159,39
Rembrandtstraat 20B Naaldwijk		2877,7
Rotterdamsedijk 104a2 Vlaardingen		452,17
Rotterdamsedijk 154b Schiedam		452,17
Rubensplein 3b Schiedam		117,03
Rubensplein 6B3 Schiedam		200
Ruigenhoek 69, Rotterdam		15,65
Schalkeroord 389 Rotterdam		462
Schere 238 Rotterdam		43,23
Schoonegge 110 Rotterdam		5320,3
Schoonegge 84 Rotterdam		2198,99
Sint Liduinastraat 76A Schiedam		332,77
Sint Liduinastraat 80 A B Schiedam		334,43
Socratesstraat 168 Rotterdam		265,08
St. Annalandstraat 116 Rotterdam		273,81
Steenen Dijck 87, Maassluis		503,72
Tholenstraat 114 Rotterdam		260,59
v.d. Waalstraat 16 Vlaardingen		411,41
Vaartweg 106C Vlaardingen		256,89
Van der Waalsstraat 70 Vlaardingen		411,41
Van der Werffstraat 166, Vlaardingen		35,88
Van der Werffstraat 240 Vlaardingen		186,36
Van der Werffstraat 370 Vlaardingen		231,94
Van Ruijsdaellaan 72A, Schiedam		95,67
Van Ruijsdaellaan 72B, Schiedam		134,4
Van Ruijsdaellaan 72C, Schiedam		153,15
van Scorelstraat 73 Maassluis		218,11
Voorstraat 25, Vlaardingen		553,95
W.M. Bakkerslaan 34, Maasluis		267,5
Wagenstraat 70, Wagenberg		750
Westfrankelandsestraat 108 Schiedam		30,28
Wilgensingel 63 Rozenburg		275,99
Woutersweg 20		1888,57
Zuidhoek 209D Rotterdam		95,6
Zwethkade Zuid 30A, Den Hoorn		390
Zwingel 8B		718,97

Grootboekrekening	Internet en telefoonkosten woningen	
		
Omschrijving	Per.	Max. of Debet
2e Maasbosstraat 2A Vlaardingen		67,35
2e Maasbosstraat 2B Vlaardingen		69,57
2e Maasbosstraat 2C Vlaardingen		69,56
2e van Leyden Gaelstraat 6, Vlaardingen		25,1
Algemeen woningen		5187,65
Allard Piersonlaan 142 Den Haag		25,1
Amberberg 14, Roosendaal		25,1
Beeklaan 294-1/294-2, Den Haag		25,1
Broekweg 25 Vlaardingen		25,2
Broersvest 74c Schiedam		69,56
Burg. Knappertlaan 176A Schiedam		67,35
Chopinstraat 33c Vlaardingen		25,1
Chopinstraat 39C Vlaardingen		25,1
Coornhertstraat 95 Vlaardingen		25,1
Curacaolaan 24 Vlaardingen		43,9
Curacaolaan 88 Vlaardingen		25,1
De Driesprong 17 Kwintsheul		50,37
Deensestraat 91A Rotterdam		67,36
Energieweg 40 Vlaardingen		25,1
Engelsestraat 16L01 Rotterdam		25,1
Engelsestraat 16L3, Rotterdam		25,1
Europalaan 50, Sas van Gent		85,25
Franselaan 273-B		25,1
G.A. Brederolaan 75B Maassluis		33,06
Galgeweg 48A, 's-Gravenzande		50,37
Goudestein 30 Rotterdam		25,1
Groenelaan 30B Schiedam		117,18
Groeneweg 71 's Granzande		50,37
Groeneweg 74 's Gravenzande		50,37
Hagastraat 8 Schiedam		69,56
Herautpad 22 Schiedam		67,35
Hoge Noordweg 27B Naaldwijk		53,72
Hoge Noordweg 28 Naaldwijk		53,72
Hogenbanweg 331 Schiedam		43,49
Hontenissestraat 124A Rotterdam		25,1
Hontenissestraat 162 Rotterdam		85,25
Hugo de Vriesstraat 54 Vlaardingen		25,1
J. van Lennepstraat 13A Schiedam		67,36
J. van Lennepstraat 13B Schiedam		67,35
J. van Lennepstraat 34 Schiedam		67,35
Jacob van Ruijsdaelstraat 28 Roosendaal		67,35
Jan van Arkelstraat 118 Vlaardingen		25,1
Kaapsebos 11 Maasdijk		53,72
Kapershoek 11 Rotterdam		25,1
Keesomstraat 22 Vlaardingen		43,11
Keesomstraat 50 Vlaardingen		25,1
Keesomstraat 54 Vlaardingen		25,1
Kerkwervesingel 127 Rotterdam		25,1
Kerstendijk 125 Rotterdam		25,1
Kethelweg 1B Vlaardingen		25,1
Kethelweg 1C Vlaardingen		25,1
Kethelweg 66C		22,82
Kethelweg 68A		22,82
Kimbrenoord 15 Rotterdam		25,1
Kruiningenstraat 152 Rotterdam		25,1
Kruiningenstraat 185, Rotterdam		25,1
Kwikstaartweg 45		30
L.A. Kesperweg 31a Vlaardingen		25,1
Lauwersmeer 4, Barendrecht		59
Liesveld 100 Vlaardingen		24,3
Lorentzstraat 73 Vlaardingen		25,2
Maasdijk 206 's Gravenzande		53,72
Markt 5 Bovenwoning, Massluis		43,39
Mendelssohnplein 10C Vlaardingen		43,9
Mendelssohnplein 13D Vlaardingen		43,9
Mendelssohnplein 46A Vlaardingen		35
Messchaertplein 40, Vlaardingen		25,1
Middelrode 8 Rotterdam		25,1
Miltonstraat 55 Rotterdam		25,1
Miltonstraat 85 Rotterdam		0
Molenstraat 10 Naaldwijk		72,57
Molenstraat 23 Naaldwijk		43,39
Mr. Troelstrastraat 11 Vlaardingen		25,1
Mr. Troelstrastraat 37 Vlaardingen		25,1
Narcissenstraat 23 Rozenburg		24,3
Nic. Beetsstraat 29 Vlaardingen		25,1
Noordstraat 26, Walsoorden		85,25
Nunspeetlaan 14		22,82
Nunspeetlaan 53		22,82
Parallelweg 110A Vlaardingen 		22,82
Parallelweg 122a Vlaardingen		25,1
Parallelweg 98B Vlaardingen		25,1
Pasteursingel 61B Rotterdam		25,1
Platostraat 80 Rotterdam		25,1
Rembrandtstraat 20B Naaldwijk		43,39
Rotterdamsedijk 154b Schiedam		69,57
Rubensplein 3b Schiedam		69,56
Schalkeroord 16 Rotterdam		23,41
Schalkeroord 389 Rotterdam		69,57
Schere 238 Rotterdam		24,3
Schoonegge 110 Rotterdam		25,1
Schoonegge 84 Rotterdam		75
Sint Liduinastraat 76A Schiedam		69,56
Sint Liduinastraat 80 A B Schiedam		69,57
Socratesstraat 168 Rotterdam		25,1
Spoorsingel 154B, Vlaardingen		25,1
St. Annalandstraat 116 Rotterdam		25,1
Tholenstraat 114 Rotterdam		25,1
v.d. Waalstraat 16 Vlaardingen		25,1
Vaartweg 106C Vlaardingen		25,1
Van der Waalsstraat 70 Vlaardingen		25,1
Van der Werffstraat 166, Vlaardingen		25,1
Van der Werffstraat 240 Vlaardingen		25,1
Van der Werffstraat 370 Vlaardingen		25,1
van Scorelstraat 73 Maassluis		67,36
W.M. Bakkerslaan 34, Maasluis		43,39
Westfrankelandsestraat 106 Schiedam		67,35
Westfrankelandsestraat 108 Schiedam		43,49
Woutersweg 20		27,44
Zuidhoek 209D Rotterdam		25,1
Zwingel 8B		153,76

Grootboekrekening	Kosten VvE woningen	
		
Omschrijving	Per.	Max. of Debet
Algemeen woningen		0
Curacaolaan 88 Vlaardingen		329,66
Hugo de Vriesstraat 54 Vlaardingen		300
Jan van Arkelstraat 118 Vlaardingen		185
Keesomstraat 50 Vlaardingen		205,35
L.A. Kesperweg 31a Vlaardingen		186,34
Mr. Troelstrastraat 11 Vlaardingen		150
Nic. Beetsstraat 29 Vlaardingen		115
Parallelweg 114C		110
Parallelweg 122a Vlaardingen		110
Rotterdamsedijk 154b Schiedam		50
Schalkeroord 389 Rotterdam		95,64
v.d. Waalstraat 16 Vlaardingen		1077,81
Van der Waalsstraat 70 Vlaardingen		157
Van der Werffstraat 240 Vlaardingen		185,9
Van der Werffstraat 370 Vlaardingen		726,26
"""

def normalize_address(addr):
    """Simple normalization for comparison"""
    import re
    if not addr: return ""
    addr = addr.lower().strip()
    # Remove common suffixes for matching
    addr = re.sub(r',?\s*(vlaardingen|rotterdam|schiedam|naaldwijk|maassluis|den haag|delft|putte).*$', '', addr, flags=re.IGNORECASE)
    addr = addr.strip().rstrip(',')
    return addr

def parse_amount(amt_str):
    if not amt_str: return 0.0
    # format: € 1.570,24 or 179,57
    clean = amt_str.replace('€', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(clean)
    except:
        return 0.0

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Get all DB houses mapping
    cursor.execute("SELECT object_id, adres, plaats FROM huizen")
    db_houses = []
    for row in cursor.fetchall():
        full_addr = f"{row['adres']} {row['plaats'] or ''}".strip().lower()
        simple_addr = normalize_address(row['adres'])
        db_houses.append({
            'id': row['object_id'],
            'full': full_addr,
            'simple': simple_addr
        })
        
    print(f"📦 Loaded {len(db_houses)} houses from DB")

    # 2. Parse text sections
    sections = RAW_DATA.split("Grootboekrekening")
    
    category_map = {
        "Huur (belast) woningen": "huur",
        "Gas, water en electra woningen": "gwe",
        "Internet en telefoonkosten woningen": "internet",
        "Kosten VvE woningen": "vve"
    }
    
    updates = {'huur': 0, 'gwe': 0, 'internet': 0, 'vve': 0}
    
    for section in sections:
        if not section.strip(): continue
        
        lines = section.strip().split('\n')
        header_line = lines[0].strip()
        
        category = None
        for key, val in category_map.items():
            if key in header_line:
                category = val
                break
        
        if not category:
            continue
            
        print(f"\nProcessing category: {category.upper()}")
        
        # Skip until data starts (skip header lines)
        data_start = 0
        for i, line in enumerate(lines):
            if "Omschrijving" in line and "Max. of Debet" in line:
                data_start = i + 1
                break
        
        for line in lines[data_start:]:
            if not line.strip(): continue
            parts = line.split('\t')
            if len(parts) < 2: continue
            
            # Extract Address and Amount
            # Structure usually: Address [tab] [tab] Amount
            # Or: Address [tab] Amount
            
            # Filter empty parts
            clean_parts = [p.strip() for p in parts if p.strip()]
            if len(clean_parts) < 2: continue
            
            address = clean_parts[0]
            amount_str = clean_parts[-1]
            amount = parse_amount(amount_str)
            
            if "Algemeen woningen" in address: continue
            
            # Match to DB
            norm_addr = normalize_address(address)
            matched_id = None
            
            # Try exact match first
            for house in db_houses:
                if house['simple'] == norm_addr:
                    matched_id = house['id']
                    break
            
            # Try fuzzy/contains match
            if not matched_id:
                for house in db_houses:
                    if norm_addr in house['full'] or house['simple'] in norm_addr:
                        matched_id = house['id']
                        break
            
            if matched_id:
                if category == 'huur':
                    # Update/Create Inhuur Contract
                    # Check if active contract exists
                    cursor.execute("""
                        SELECT id FROM inhuur_contracten 
                        WHERE object_id = ? 
                        ORDER BY end_date DESC LIMIT 1
                    """, (matched_id,))
                    contract = cursor.fetchone()
                    
                    if contract:
                        cursor.execute("""
                            UPDATE inhuur_contracten 
                            SET kale_inhuurprijs = ?, 
                                inhuur_prijs_excl_btw = ?,
                                inhuur_prijs_incl_btw = ?
                            WHERE id = ?
                        """, (amount, amount, amount * 1.21, contract['id']))
                    else:
                        cursor.execute("""
                            INSERT INTO inhuur_contracten 
                            (object_id, kale_inhuurprijs, inhuur_prijs_excl_btw, inhuur_prijs_incl_btw, start_date)
                            VALUES (?, ?, ?, ?, '2025-01-01')
                        """, (matched_id, amount, amount, amount * 1.21))
                    updates['huur'] += 1
                    
                elif category == 'gwe':
                    cursor.execute("UPDATE huizen SET voorschot_gwe = ? WHERE object_id = ?", (amount, matched_id))
                    updates['gwe'] += 1
                    
                elif category == 'internet':
                    cursor.execute("UPDATE huizen SET internet = ? WHERE object_id = ?", (amount, matched_id))
                    updates['internet'] += 1
                    
                elif category == 'vve':
                    cursor.execute("UPDATE huizen SET vve_kosten = ? WHERE object_id = ?", (amount, matched_id))
                    updates['vve'] += 1
            else:
                # print(f"⚠️ No match for: {address}")
                pass

    conn.commit()
    conn.close()
    
    print("\n✅ Import Summary:")
    print(f"  - Huur updates: {updates['huur']}")
    print(f"  - GWE updates: {updates['gwe']}")
    print(f"  - Internet updates: {updates['internet']}")
    print(f"  - VvE updates: {updates['vve']}")

if __name__ == "__main__":
    main()
