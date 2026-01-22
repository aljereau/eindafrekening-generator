flowchart LR

%% Swimlanes
subgraph UZ["Uitzendkracht"]
  UZ1["Meldt klacht/storing\n(bij coördinator of HT)"]
end

subgraph CO["Tradiro Coördinator"]
  CO1["Ontvangt melding"]
  CO2["Zet door naar HT\n(afdeling huisvesting)"]
end

subgraph HT["Tradiro Huisvesting (HT)"]
  HT1["Ontvangt melding van coördinator"]
  HT2["Registreert melding in SIMA\n+ zet door naar Ryan Rent"]
  HT3["Beslist: opschalen bij vertraging\n(escalatie trigger)"]
end

subgraph RR["Ryan Rent (RR)"]
  RR1["Ontvangt melding via SIMA"]
  RR2["Classificeert urgentie\n(Hoog/Middel/Laag)"]
  RR3{"Urgentie?"}
  RR4["Start actie: Hoog urgent\n(onmiddellijk)"]
  RR5["Start actie: Middel urgent\n(binnen 24 uur)"]
  RR6["Plant actie: Laag urgent\n(binnen 5 werkdagen)"]
  RR7["Uitvoering herstel\n(technische dienst/leverancier)"]
  RR8["Update status & planning in SIMA"]
  RR9["Markeert uitvoering afgerond in SIMA\n+ genereert e-mail binnen 24 uur"]
  RR10["Escalatie afhandeling\n(prioriteren / resources / leverancier)"]
end

subgraph FA["Financiële administratie (FA)"]
  FA1["Geïnformeerd (I)\nvoor facturatie/afrekening\n(indien relevant)"]
end

%% Main flow
UZ1 --> CO1 --> CO2 --> HT1 --> HT2 --> RR1 --> RR2 --> RR3

RR3 -->|Hoog urgent| RR4 --> RR7
RR3 -->|Middel urgent| RR5 --> RR7
RR3 -->|Laag urgent| RR6 --> RR7

RR7 --> RR8 --> RR9 --> HT1

%% Escalation path
RR8 -->|Vertraging / risico op overschrijding SLA| HT3
HT3 -->|Escalatie| RR10 --> RR8

%% Optional FA info
RR9 -.->|Indien impact op facturatie,\nG/W/E, borg, of kosten| FA1