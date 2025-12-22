# RyanRent Property Status Dashboard - Technical Specification

## 🎯 Executive Summary

Build a **property-centric status dashboard** that provides real-time visibility into the operational status of rental properties, combining data from multiple sources (uitchecks, inchecks, bookings, clients) to generate actionable insights and warnings for the operations team.

### Key Objectives

1. **Property Status Overview** - See complete status of each property at a glance
2. **Automated Warnings** - Alert team when critical steps are missing or deadlines approaching
3. **Action Generation** - Auto-generate to-do lists based on missing steps and priorities
4. **Timeline Visibility** - Visual timeline showing all upcoming events per property

---

## 📊 Core Concept: Property-Centric vs Task-Centric

### Current System (Task-Centric)
```
UITCHECKS TABLE
├─ Uitcheck 1: Kerkweg 9a, 10 dec
├─ Uitcheck 2: Lekdijk 14, 11 dec
└─ Uitcheck 3: Akkerweg 42, 12 dec

Problem: No holistic view of property status
```

### Target System (Property-Centric)
```
PROPERTY: Kerkweg 9a
├─ Uitcheck: 10 dec (✅ Scheduled)
├─ Pre-inspectie: ❌ NOT PLANNED
├─ Nieuwe klant: ✅ Jan Bakker (Timing)
├─ VIS: ❌ NOT PLANNED (🚨 Incheck in 5 days!)
├─ Incheck: 15 dec (✅ Scheduled)
└─ 🚨 ACTION REQUIRED: Plan pre-inspectie + VIS

PROPERTY: Lekdijk 14
├─ Uitcheck: 11 dec (✅ Scheduled)
├─ Pre-inspectie: ✅ 5 dec (Ana)
├─ Nieuwe klant: ✅ Marie B.V. (Tradiro)
├─ VIS: ⚠️ NOT PLANNED (Incheck in 7 days)
├─ Incheck: 18 dec (✅ Scheduled)
└─ ⚠️ ACTION: Plan VIS before 15 dec

PROPERTY: Herenpad 20B
├─ Uitcheck: 8 dec (✅ Completed)
├─ Nieuwe klant: ❌ None
└─ 🔄 Returning to owner (Low priority)
```

**The Insight:** By viewing data per property instead of per task, the team can immediately see what's complete, what's missing, and what needs urgent attention.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Dashboard  │  │   Timeline   │  │  Action List │ │
│  │     View     │  │     View     │  │     View     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                    AI LAYER (Optional)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • Natural language queries                       │  │
│  │  • Smart priority calculation                     │  │
│  │  • Anomaly detection                              │  │
│  │  • Predictive warnings                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  • Property aggregation                           │  │
│  │  • Status calculation                             │  │
│  │  • Warning generation                             │  │
│  │  • Priority scoring                               │  │
│  │  • Action item creation                           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                      DATA LAYER                          │
│  ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐ │
│  │Properties │ │ Uitchecks │ │ Inchecks │ │ Clients │ │
│  └───────────┘ └───────────┘ └──────────┘ └─────────┘ │
│  ┌───────────┐ ┌───────────┐                           │
│  │ Bookings  │ │Inspectors │                           │
│  └───────────┘ └───────────┘                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Core Tables

#### 1. `properties`
```sql
CREATE TABLE properties (
    property_id VARCHAR(50) PRIMARY KEY,
    address VARCHAR(255) NOT NULL UNIQUE,
    property_code VARCHAR(50),  -- e.g., "HUIS-135"
    owner_id VARCHAR(50),
    property_type VARCHAR(50),  -- RR Eigendom, Klant Eigendom
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_properties_address ON properties(address);
CREATE INDEX idx_properties_code ON properties(property_code);
```

**Purpose:** Central registry of all properties. Every other table references this.

---

#### 2. `clients`
```sql
CREATE TABLE clients (
    client_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    client_type VARCHAR(50),  -- Bureau, Direct, Eigenaar
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_clients_name ON clients(name);
```

**Purpose:** Master list of clients (Tradiro, NL Realty, etc.)

---

#### 3. `inspectors`
```sql
CREATE TABLE inspectors (
    inspector_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Team members who perform inspections (Ana, Ricky, Christa, etc.)

---

#### 4. `uitchecks`
```sql
CREATE TABLE uitchecks (
    uitcheck_id VARCHAR(50) PRIMARY KEY,  -- UC-2025-001
    property_id VARCHAR(50) NOT NULL REFERENCES properties(property_id),
    client_id VARCHAR(50) REFERENCES clients(client_id),
    
    -- Dates
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    actual_date DATE,
    actual_time TIME,
    pre_inspection_date DATE,
    
    -- Assignment
    inspector_id VARCHAR(50) REFERENCES inspectors(inspector_id),
    pre_inspector_id VARCHAR(50) REFERENCES inspectors(inspector_id),
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- Gepland, Bezig, Voltooid, Geannuleerd
    priority VARCHAR(50),  -- Kritisch, Hoog, Normaal, Laag
    
    -- Operational details
    returning_to_owner BOOLEAN DEFAULT FALSE,
    furniture_removal BOOLEAN DEFAULT FALSE,
    keys_collected BOOLEAN DEFAULT FALSE,
    damage_reported BOOLEAN DEFAULT FALSE,
    
    -- Cleaning
    cleaning_required VARCHAR(100),  -- RR Schoonmaak, Park Schoonmaak, etc.
    cleaning_paid_by VARCHAR(50),  -- Huurder, RR, Eigenaar
    cleaning_cost DECIMAL(10,2),
    
    -- Financial
    settlement_status VARCHAR(50),  -- Niet Gestart, In Afwachting, Bezig, Voltooid
    settlement_amount DECIMAL(10,2),
    
    -- Notes
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_uitchecks_property ON uitchecks(property_id);
CREATE INDEX idx_uitchecks_scheduled_date ON uitchecks(scheduled_date);
CREATE INDEX idx_uitchecks_status ON uitchecks(status);
CREATE INDEX idx_uitchecks_priority ON uitchecks(priority);
CREATE INDEX idx_uitchecks_inspector ON uitchecks(inspector_id);
```

**Purpose:** Track all checkout inspections and related activities.

---

#### 5. `inchecks`
```sql
CREATE TABLE inchecks (
    incheck_id VARCHAR(50) PRIMARY KEY,  -- IC-2025-001
    property_id VARCHAR(50) NOT NULL REFERENCES properties(property_id),
    linked_uitcheck_id VARCHAR(50) REFERENCES uitchecks(uitcheck_id),
    
    -- New tenant info
    new_tenant_name VARCHAR(255),
    new_tenant_company_id VARCHAR(50) REFERENCES clients(client_id),
    
    -- Dates
    planned_date DATE NOT NULL,
    actual_date DATE,
    vis_date DATE,  -- Voor-incheck inspectie
    
    -- Assignment
    inspector_id VARCHAR(50) REFERENCES inspectors(inspector_id),
    vis_inspector_id VARCHAR(50) REFERENCES inspectors(inspector_id),
    
    -- Status
    status VARCHAR(50) NOT NULL,  -- Gepland, VIS Gedaan, Voltooid, Geannuleerd
    vis_approved BOOLEAN,  -- Did new tenant approve during VIS?
    
    -- Reference
    vis_reference TEXT,
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_inchecks_property ON inchecks(property_id);
CREATE INDEX idx_inchecks_linked_uitcheck ON inchecks(linked_uitcheck_id);
CREATE INDEX idx_inchecks_planned_date ON inchecks(planned_date);
CREATE INDEX idx_inchecks_status ON inchecks(status);
CREATE INDEX idx_inchecks_company ON inchecks(new_tenant_company_id);
```

**Purpose:** Track all check-in inspections and new tenant move-ins.

---

#### 6. `bookings` (Optional - for future)
```sql
CREATE TABLE bookings (
    booking_id VARCHAR(50) PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL REFERENCES properties(property_id),
    client_id VARCHAR(50) REFERENCES clients(client_id),
    tenant_name VARCHAR(255),
    
    start_date DATE NOT NULL,
    end_date DATE,
    
    status VARCHAR(50),  -- Active, Ending, Ended
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_bookings_property ON bookings(property_id);
CREATE INDEX idx_bookings_dates ON bookings(start_date, end_date);
CREATE INDEX idx_bookings_status ON bookings(status);
```

**Purpose:** Track rental periods. Links to uitchecks (end) and inchecks (start).

---

## 🧮 Business Logic Layer

### Core Query: Property Status Aggregation

This is the **heart of the application** - combining all data sources to create property status.

```sql
-- property_status_view.sql
CREATE VIEW property_status_view AS
SELECT 
    -- Property info
    p.property_id,
    p.address,
    p.property_code,
    
    -- Uitcheck info
    u.uitcheck_id,
    u.scheduled_date as uitcheck_scheduled,
    u.actual_date as uitcheck_actual,
    u.pre_inspection_date,
    u.status as uitcheck_status,
    u.priority as uitcheck_priority,
    u.returning_to_owner,
    ui.name as uitcheck_inspector,
    
    -- Incheck info
    i.incheck_id,
    i.planned_date as incheck_planned,
    i.actual_date as incheck_actual,
    i.vis_date,
    i.vis_approved,
    i.new_tenant_name,
    i.status as incheck_status,
    ii.name as incheck_inspector,
    c.name as new_tenant_company,
    
    -- Client info
    cl.name as current_client,
    
    -- Calculated fields
    CASE 
        WHEN i.planned_date IS NOT NULL THEN
            i.planned_date - CURRENT_DATE
        ELSE NULL
    END as days_until_incheck,
    
    CASE
        WHEN u.scheduled_date IS NOT NULL THEN
            u.scheduled_date - CURRENT_DATE
        ELSE NULL
    END as days_until_uitcheck,
    
    -- Priority calculation (business logic)
    CASE
        -- Kritisch: Incheck within 7 days AND missing critical steps
        WHEN i.planned_date IS NOT NULL 
            AND i.planned_date - CURRENT_DATE <= 7
            AND (u.pre_inspection_date IS NULL OR i.vis_date IS NULL)
        THEN 'KRITISCH'
        
        -- Hoog: Incheck within 14 days
        WHEN i.planned_date IS NOT NULL 
            AND i.planned_date - CURRENT_DATE <= 14
        THEN 'HOOG'
        
        -- Normaal: Incheck within 30 days
        WHEN i.planned_date IS NOT NULL 
            AND i.planned_date - CURRENT_DATE <= 30
        THEN 'NORMAAL'
        
        -- Laag: No new tenant or distant incheck
        ELSE 'LAAG'
    END as calculated_priority,
    
    -- Status completeness score (0-100)
    (
        CASE WHEN u.uitcheck_id IS NOT NULL THEN 20 ELSE 0 END +
        CASE WHEN u.pre_inspection_date IS NOT NULL THEN 20 ELSE 0 END +
        CASE WHEN u.actual_date IS NOT NULL THEN 20 ELSE 0 END +
        CASE WHEN i.vis_date IS NOT NULL THEN 20 ELSE 0 END +
        CASE WHEN i.actual_date IS NOT NULL THEN 20 ELSE 0 END
    ) as completeness_score

FROM properties p

LEFT JOIN uitchecks u ON p.property_id = u.property_id
    AND u.scheduled_date >= CURRENT_DATE - 7  -- Only recent/upcoming
    AND u.scheduled_date <= CURRENT_DATE + 30
    AND u.status != 'Voltooid'

LEFT JOIN inchecks i ON u.uitcheck_id = i.linked_uitcheck_id

LEFT JOIN inspectors ui ON u.inspector_id = ui.inspector_id
LEFT JOIN inspectors ii ON i.inspector_id = ii.inspector_id

LEFT JOIN clients cl ON u.client_id = cl.client_id
LEFT JOIN clients c ON i.new_tenant_company_id = c.client_id

WHERE u.uitcheck_id IS NOT NULL  -- Only properties with active uitchecks

ORDER BY 
    calculated_priority DESC,
    days_until_incheck ASC;
```

---

### Warning Generation Logic

```python
# business_logic/warnings.py

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

@dataclass
class Warning:
    """Represents a warning or alert for a property"""
    severity: str  # CRITICAL, WARNING, INFO
    category: str  # PRE_INSPECTION, VIS, CLEANING, TIMELINE, etc.
    message: str
    action_required: str
    days_remaining: Optional[int] = None

class WarningGenerator:
    """Generate warnings based on property status"""
    
    @staticmethod
    def generate_warnings(property_status: dict) -> List[Warning]:
        """
        Generate all applicable warnings for a property status
        
        Args:
            property_status: Dict containing property status data
            
        Returns:
            List of Warning objects
        """
        warnings = []
        
        # Extract relevant data
        uitcheck_date = property_status.get('uitcheck_scheduled')
        incheck_date = property_status.get('incheck_planned')
        pre_inspection_date = property_status.get('pre_inspection_date')
        vis_date = property_status.get('vis_date')
        has_new_tenant = property_status.get('new_tenant_name') is not None
        returning_to_owner = property_status.get('returning_to_owner', False)
        
        today = date.today()
        
        # Skip if returning to owner (low priority)
        if returning_to_owner:
            return warnings
        
        # CRITICAL: Missing pre-inspection close to uitcheck
        if uitcheck_date and not pre_inspection_date:
            days_until_uitcheck = (uitcheck_date - today).days
            
            if days_until_uitcheck <= 7:
                warnings.append(Warning(
                    severity='CRITICAL',
                    category='PRE_INSPECTION',
                    message='Pre-inspectie niet gepland!',
                    action_required=f'Plan pre-inspectie vóór uitcheck ({days_until_uitcheck} dagen)',
                    days_remaining=days_until_uitcheck
                ))
            elif days_until_uitcheck <= 14:
                warnings.append(Warning(
                    severity='WARNING',
                    category='PRE_INSPECTION',
                    message='Pre-inspectie moet binnenkort gepland worden',
                    action_required=f'Plan pre-inspectie (uitcheck over {days_until_uitcheck} dagen)',
                    days_remaining=days_until_uitcheck
                ))
        
        # CRITICAL: Missing VIS close to incheck
        if has_new_tenant and incheck_date and not vis_date:
            days_until_incheck = (incheck_date - today).days
            
            if days_until_incheck <= 7:
                warnings.append(Warning(
                    severity='CRITICAL',
                    category='VIS',
                    message=f'🚨 VIS URGENT - Incheck over {days_until_incheck} dagen!',
                    action_required=f'Plan VIS onmiddellijk (minimaal 2 dagen voor incheck)',
                    days_remaining=days_until_incheck
                ))
            elif days_until_incheck <= 14:
                warnings.append(Warning(
                    severity='WARNING',
                    category='VIS',
                    message=f'VIS niet gepland (incheck over {days_until_incheck} dagen)',
                    action_required=f'Plan VIS voor {incheck_date - timedelta(days=3)}',
                    days_remaining=days_until_incheck
                ))
        
        # WARNING: Insufficient time between uitcheck and VIS
        if uitcheck_date and vis_date:
            days_between = (vis_date - uitcheck_date).days
            
            if days_between < 3:
                warnings.append(Warning(
                    severity='WARNING',
                    category='TIMELINE',
                    message=f'Te weinig tijd tussen uitcheck en VIS ({days_between} dagen)',
                    action_required='Controleer of schoonmaak/herstel op tijd klaar kan zijn',
                    days_remaining=days_between
                ))
        
        # WARNING: VIS too close to incheck
        if vis_date and incheck_date:
            days_between = (incheck_date - vis_date).days
            
            if days_between < 2:
                warnings.append(Warning(
                    severity='WARNING',
                    category='TIMELINE',
                    message=f'VIS te dicht bij incheck ({days_between} dagen)',
                    action_required='Overweeg VIS eerder te plannen voor meer flexibiliteit',
                    days_remaining=days_between
                ))
        
        # INFO: Pre-inspection should be scheduled
        if uitcheck_date and not pre_inspection_date:
            days_until_uitcheck = (uitcheck_date - today).days
            ideal_pre_inspection_date = uitcheck_date - timedelta(days=10)
            
            if days_until_uitcheck > 14 and today >= ideal_pre_inspection_date - timedelta(days=7):
                warnings.append(Warning(
                    severity='INFO',
                    category='PRE_INSPECTION',
                    message='Pre-inspectie kan nu gepland worden',
                    action_required=f'Ideale datum: rond {ideal_pre_inspection_date.strftime("%d-%m-%Y")}',
                    days_remaining=days_until_uitcheck
                ))
        
        # Sort warnings by severity
        severity_order = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
        warnings.sort(key=lambda w: severity_order.get(w.severity, 3))
        
        return warnings
```

---

### Action Item Generation

```python
# business_logic/actions.py

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

@dataclass
class ActionItem:
    """Represents a to-do item for the team"""
    property_id: str
    address: str
    action_type: str  # PLAN_PRE, PLAN_VIS, DO_UITCHECK, DO_VIS, DO_INCHECK
    priority: str  # CRITICAL, HIGH, NORMAL, LOW
    description: str
    due_date: Optional[date]
    assigned_to: Optional[str]
    related_date: Optional[date]  # The event date (uitcheck, incheck, etc.)
    days_remaining: Optional[int]

class ActionGenerator:
    """Generate action items from property statuses"""
    
    @staticmethod
    def generate_actions(property_statuses: List[dict]) -> List[ActionItem]:
        """
        Generate all action items from property statuses
        
        Args:
            property_statuses: List of property status dicts
            
        Returns:
            Sorted list of ActionItem objects
        """
        actions = []
        today = date.today()
        
        for ps in property_statuses:
            property_id = ps['property_id']
            address = ps['address']
            
            uitcheck_date = ps.get('uitcheck_scheduled')
            incheck_date = ps.get('incheck_planned')
            pre_inspection_date = ps.get('pre_inspection_date')
            vis_date = ps.get('vis_date')
            has_new_tenant = ps.get('new_tenant_name') is not None
            uitcheck_inspector = ps.get('uitcheck_inspector')
            incheck_inspector = ps.get('incheck_inspector')
            
            # Action: Plan pre-inspection
            if uitcheck_date and not pre_inspection_date:
                days_until_uitcheck = (uitcheck_date - today).days
                
                # Ideal pre-inspection: 7-10 days before uitcheck
                ideal_pre_date = uitcheck_date - timedelta(days=10)
                
                priority = 'CRITICAL' if days_until_uitcheck <= 7 else \
                          'HIGH' if days_until_uitcheck <= 14 else 'NORMAL'
                
                actions.append(ActionItem(
                    property_id=property_id,
                    address=address,
                    action_type='PLAN_PRE',
                    priority=priority,
                    description=f'Plan pre-inspectie voor {address}',
                    due_date=ideal_pre_date,
                    assigned_to=uitcheck_inspector,
                    related_date=uitcheck_date,
                    days_remaining=days_until_uitcheck
                ))
            
            # Action: Do pre-inspection (if scheduled for today/soon)
            if pre_inspection_date and pre_inspection_date <= today + timedelta(days=3):
                days_until_pre = (pre_inspection_date - today).days
                
                if days_until_pre >= 0:  # Not in the past
                    actions.append(ActionItem(
                        property_id=property_id,
                        address=address,
                        action_type='DO_PRE',
                        priority='HIGH' if days_until_pre <= 1 else 'NORMAL',
                        description=f'Doe pre-inspectie {address}',
                        due_date=pre_inspection_date,
                        assigned_to=uitcheck_inspector,
                        related_date=pre_inspection_date,
                        days_remaining=days_until_pre
                    ))
            
            # Action: Plan VIS
            if has_new_tenant and incheck_date and not vis_date:
                days_until_incheck = (incheck_date - today).days
                
                # Ideal VIS: 3-5 days before incheck
                ideal_vis_date = incheck_date - timedelta(days=4)
                
                priority = 'CRITICAL' if days_until_incheck <= 7 else \
                          'HIGH' if days_until_incheck <= 14 else 'NORMAL'
                
                actions.append(ActionItem(
                    property_id=property_id,
                    address=address,
                    action_type='PLAN_VIS',
                    priority=priority,
                    description=f'Plan VIS voor nieuwe huurder {address}',
                    due_date=ideal_vis_date,
                    assigned_to=incheck_inspector,
                    related_date=incheck_date,
                    days_remaining=days_until_incheck
                ))
            
            # Action: Do uitcheck (if scheduled for today/soon)
            if uitcheck_date and uitcheck_date <= today + timedelta(days=3):
                days_until_uitcheck = (uitcheck_date - today).days
                
                if days_until_uitcheck >= 0:
                    actions.append(ActionItem(
                        property_id=property_id,
                        address=address,
                        action_type='DO_UITCHECK',
                        priority='CRITICAL' if days_until_uitcheck <= 1 else 'HIGH',
                        description=f'Doe uitcheck {address}',
                        due_date=uitcheck_date,
                        assigned_to=uitcheck_inspector,
                        related_date=uitcheck_date,
                        days_remaining=days_until_uitcheck
                    ))
            
            # Action: Do VIS (if scheduled for today/soon)
            if vis_date and vis_date <= today + timedelta(days=3):
                days_until_vis = (vis_date - today).days
                
                if days_until_vis >= 0:
                    actions.append(ActionItem(
                        property_id=property_id,
                        address=address,
                        action_type='DO_VIS',
                        priority='CRITICAL' if days_until_vis <= 1 else 'HIGH',
                        description=f'Doe VIS met nieuwe huurder {address}',
                        due_date=vis_date,
                        assigned_to=incheck_inspector,
                        related_date=vis_date,
                        days_remaining=days_until_vis
                    ))
            
            # Action: Do incheck (if scheduled for today/soon)
            if incheck_date and incheck_date <= today + timedelta(days=3):
                days_until_incheck = (incheck_date - today).days
                
                if days_until_incheck >= 0:
                    actions.append(ActionItem(
                        property_id=property_id,
                        address=address,
                        action_type='DO_INCHECK',
                        priority='CRITICAL' if days_until_incheck <= 1 else 'HIGH',
                        description=f'Doe incheck nieuwe huurder {address}',
                        due_date=incheck_date,
                        assigned_to=incheck_inspector,
                        related_date=incheck_date,
                        days_remaining=days_until_incheck
                    ))
        
        # Sort actions
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'NORMAL': 2, 'LOW': 3}
        actions.sort(key=lambda a: (
            priority_order.get(a.priority, 4),
            a.due_date if a.due_date else date.max
        ))
        
        return actions
```

---

## 🤖 AI Layer (Optional Enhancement)

### Natural Language Query Interface

```python
# ai_layer/nl_query.py

from typing import Dict, List
import anthropic

class NaturalLanguageQuery:
    """
    Allow team to query the system using natural language
    Examples:
    - "Show me all properties with critical status"
    - "Which inspections does Ana have this week?"
    - "What properties need VIS planning?"
    """
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def query(self, user_query: str, context_data: Dict) -> str:
        """
        Convert natural language query to insights
        
        Args:
            user_query: User's question in natural language
            context_data: Current property statuses, actions, warnings
            
        Returns:
            Natural language response
        """
        
        system_prompt = """
        You are an AI assistant for RyanRent's property management system.
        You have access to real-time property status data, warnings, and action items.
        
        Your role:
        - Answer questions about property statuses
        - Provide insights and recommendations
        - Help prioritize work
        - Explain warnings and suggest solutions
        
        Be concise, actionable, and use Dutch terminology where appropriate.
        """
        
        # Format context data for AI
        context_str = self._format_context(context_data)
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"""
                Context Data:
                {context_str}
                
                User Question: {user_query}
                
                Provide a helpful answer based on the context data.
                """
            }]
        )
        
        return response.content[0].text
    
    def _format_context(self, context_data: Dict) -> str:
        """Format context data for AI consumption"""
        
        lines = []
        
        # Properties overview
        if 'properties' in context_data:
            lines.append("PROPERTY STATUSES:")
            for prop in context_data['properties']:
                lines.append(f"- {prop['address']}: Priority {prop['priority']}, "
                           f"Uitcheck {prop['uitcheck_date']}, "
                           f"Incheck {prop['incheck_date']}")
        
        # Warnings
        if 'warnings' in context_data:
            lines.append("\nWARNINGS:")
            for warning in context_data['warnings']:
                lines.append(f"- [{warning['severity']}] {warning['address']}: "
                           f"{warning['message']}")
        
        # Actions
        if 'actions' in context_data:
            lines.append("\nACTION ITEMS:")
            for action in context_data['actions']:
                lines.append(f"- [{action['priority']}] {action['description']} "
                           f"(Due: {action['due_date']})")
        
        return "\n".join(lines)
```

### Smart Priority Calculation

```python
# ai_layer/smart_priority.py

class SmartPriorityCalculator:
    """
    Use AI to calculate priority based on multiple factors:
    - Timeline constraints
    - Historical patterns
    - Resource availability
    - Client importance
    """
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def calculate_priority(self, property_status: Dict) -> Dict:
        """
        Calculate smart priority and reasoning
        
        Returns:
            {
                'priority': 'KRITISCH',
                'score': 95,
                'reasoning': 'Nieuwe huurder intrekt over 5 dagen...',
                'recommendations': ['Plan VIS vandaag', ...]
            }
        """
        
        prompt = f"""
        Analyze this property status and determine priority level:
        
        Property: {property_status['address']}
        Uitcheck: {property_status.get('uitcheck_date')}
        Incheck: {property_status.get('incheck_date')}
        Pre-inspectie: {property_status.get('pre_inspection_date', 'Not planned')}
        VIS: {property_status.get('vis_date', 'Not planned')}
        New tenant: {property_status.get('new_tenant_name', 'None')}
        
        Consider:
        1. Timeline urgency (days until incheck)
        2. Missing critical steps
        3. Risk of delays
        4. Impact on client satisfaction
        
        Provide:
        - Priority level (KRITISCH, HOOG, NORMAAL, LAAG)
        - Numeric score (0-100)
        - Brief reasoning (2-3 sentences)
        - Top 2-3 recommendations
        
        Format as JSON.
        """
        
        # Call AI
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse and return
        import json
        return json.loads(response.content[0].text)
```

### Anomaly Detection

```python
# ai_layer/anomaly_detection.py

class AnomalyDetector:
    """
    Detect unusual patterns that might indicate problems:
    - Properties that consistently run late
    - Inspectors with high workload
    - Clients with frequent issues
    - Seasonal patterns
    """
    
    def detect_anomalies(self, historical_data: List[Dict]) -> List[Dict]:
        """
        Analyze historical data for anomalies
        
        Returns list of detected anomalies with:
        - Type (TIMELINE_DELAY, WORKLOAD_IMBALANCE, FREQUENT_ISSUES)
        - Severity
        - Description
        - Recommendation
        """
        
        anomalies = []
        
        # Example: Detect properties with frequent delays
        property_delays = self._calculate_average_delays(historical_data)
        
        for property_id, avg_delay in property_delays.items():
            if avg_delay > 3:  # Average delay > 3 days
                anomalies.append({
                    'type': 'TIMELINE_DELAY',
                    'severity': 'WARNING',
                    'entity': property_id,
                    'description': f'Property has average delay of {avg_delay} days',
                    'recommendation': 'Add buffer time when planning this property'
                })
        
        # More detection logic...
        
        return anomalies
```

---

## 🎨 Frontend Views

### 1. Dashboard View (Primary)

```python
# views/dashboard.py

class DashboardView:
    """
    Main dashboard showing property statuses grouped by priority
    """
    
    def render(self, property_statuses: List[Dict]) -> str:
        """
        Render property status dashboard
        
        Groups properties by priority:
        - KRITISCH (red)
        - HOOG (orange)
        - NORMAAL (green)
        - LAAG (gray)
        
        For each property, show:
        - Address
        - Key dates
        - Completion status
        - Warnings
        - Next actions
        """
        
        # Group by priority
        grouped = {
            'KRITISCH': [],
            'HOOG': [],
            'NORMAAL': [],
            'LAAG': []
        }
        
        for ps in property_statuses:
            priority = ps.get('calculated_priority', 'LAAG')
            grouped[priority].append(ps)
        
        # Render HTML
        html = ['<div class="dashboard">']
        
        for priority in ['KRITISCH', 'HOOG', 'NORMAAL', 'LAAG']:
            properties = grouped[priority]
            
            if not properties:
                continue
            
            html.append(f'<div class="priority-section {priority.lower()}">')
            html.append(f'<h2>{self._priority_icon(priority)} {priority} ({len(properties)})</h2>')
            
            for prop in properties:
                html.append(self._render_property_card(prop))
            
            html.append('</div>')
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _render_property_card(self, prop: Dict) -> str:
        """Render individual property card"""
        
        warnings = WarningGenerator.generate_warnings(prop)
        
        card = f"""
        <div class="property-card">
            <h3>🏠 {prop['address']}</h3>
            
            <div class="timeline">
                {self._render_timeline_item('Uitcheck', prop.get('uitcheck_scheduled'), prop.get('uitcheck_status'))}
                {self._render_timeline_item('Pre-inspectie', prop.get('pre_inspection_date'), 'Scheduled' if prop.get('pre_inspection_date') else 'Missing')}
                {self._render_timeline_item('VIS', prop.get('vis_date'), 'Scheduled' if prop.get('vis_date') else 'Missing')}
                {self._render_timeline_item('Incheck', prop.get('incheck_planned'), prop.get('incheck_status'))}
            </div>
            
            {self._render_warnings(warnings)}
            
            <div class="property-meta">
                {f"<span>Nieuwe huurder: {prop.get('new_tenant_name')}</span>" if prop.get('new_tenant_name') else ""}
                {f"<span>Klant: {prop.get('new_tenant_company')}</span>" if prop.get('new_tenant_company') else ""}
                {f"<span>Inspecteur: {prop.get('uitcheck_inspector')}</span>" if prop.get('uitcheck_inspector') else ""}
            </div>
        </div>
        """
        
        return card
    
    def _render_timeline_item(self, label: str, date, status: str) -> str:
        """Render a timeline item with status indicator"""
        
        if not date:
            icon = '❌'
            date_str = 'Not planned'
            status_class = 'missing'
        elif status in ['Voltooid', 'Gedaan']:
            icon = '✅'
            date_str = date.strftime('%d-%m')
            status_class = 'completed'
        else:
            icon = '📅'
            date_str = date.strftime('%d-%m')
            status_class = 'scheduled'
        
        return f"""
        <div class="timeline-item {status_class}">
            <span class="icon">{icon}</span>
            <span class="label">{label}</span>
            <span class="date">{date_str}</span>
        </div>
        """
    
    def _render_warnings(self, warnings: List[Warning]) -> str:
        """Render warnings section"""
        
        if not warnings:
            return '<div class="warnings">✅ Alles op schema!</div>'
        
        html = ['<div class="warnings">']
        
        for warning in warnings:
            severity_icon = {
                'CRITICAL': '🚨',
                'WARNING': '⚠️',
                'INFO': 'ℹ️'
            }.get(warning.severity, 'ℹ️')
            
            html.append(f"""
            <div class="warning {warning.severity.lower()}">
                <span class="icon">{severity_icon}</span>
                <span class="message">{warning.message}</span>
                <span class="action">{warning.action_required}</span>
            </div>
            """)
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _priority_icon(self, priority: str) -> str:
        """Get icon for priority level"""
        icons = {
            'KRITISCH': '🔴',
            'HOOG': '🟡',
            'NORMAAL': '🟢',
            'LAAG': '⚪'
        }
        return icons.get(priority, '⚪')
```

### 2. Timeline View (Gantt-style)

```python
# views/timeline.py

class TimelineView:
    """
    Visual timeline showing all properties and their key dates
    Gantt-style chart
    """
    
    def render(self, property_statuses: List[Dict], 
               start_date: date, end_date: date) -> str:
        """
        Render timeline view
        
        Shows:
        - Property on Y-axis
        - Time on X-axis
        - Events as markers/bars
        """
        
        html = ['<div class="timeline-view">']
        
        # Date header
        html.append(self._render_date_header(start_date, end_date))
        
        # Property rows
        for prop in property_statuses:
            html.append(self._render_property_timeline(prop, start_date, end_date))
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _render_date_header(self, start: date, end: date) -> str:
        """Render date header row"""
        
        days = (end - start).days
        
        html = ['<div class="timeline-header">']
        html.append('<div class="property-label">Property</div>')
        
        current = start
        while current <= end:
            html.append(f'<div class="date-cell">{current.strftime("%d/%m")}</div>')
            current += timedelta(days=1)
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _render_property_timeline(self, prop: Dict, start: date, end: date) -> str:
        """Render timeline row for a property"""
        
        html = ['<div class="timeline-row">']
        
        # Property label
        html.append(f'<div class="property-label">{prop["address"]}</div>')
        
        # Timeline cells
        events = self._get_events(prop)
        days = (end - start).days
        
        current = start
        while current <= end:
            event = next((e for e in events if e['date'] == current), None)
            
            if event:
                html.append(f'<div class="timeline-cell event {event["type"]}">{event["icon"]}</div>')
            else:
                html.append('<div class="timeline-cell"></div>')
            
            current += timedelta(days=1)
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _get_events(self, prop: Dict) -> List[Dict]:
        """Extract events from property status"""
        
        events = []
        
        if prop.get('pre_inspection_date'):
            events.append({
                'date': prop['pre_inspection_date'],
                'type': 'pre',
                'icon': '🔍'
            })
        
        if prop.get('uitcheck_scheduled'):
            events.append({
                'date': prop['uitcheck_scheduled'],
                'type': 'uitcheck',
                'icon': '⬇️'
            })
        
        if prop.get('vis_date'):
            events.append({
                'date': prop['vis_date'],
                'type': 'vis',
                'icon': '👁️'
            })
        
        if prop.get('incheck_planned'):
            events.append({
                'date': prop['incheck_planned'],
                'type': 'incheck',
                'icon': '⬆️'
            })
        
        return events
```

### 3. Action List View

```python
# views/actions.py

class ActionListView:
    """
    To-do list view showing all actions grouped by urgency
    """
    
    def render(self, actions: List[ActionItem]) -> str:
        """
        Render action list
        
        Groups by:
        - URGENT (due today/tomorrow)
        - THIS WEEK
        - NEXT WEEK
        - LATER
        """
        
        today = date.today()
        
        grouped = {
            'URGENT': [],
            'THIS_WEEK': [],
            'NEXT_WEEK': [],
            'LATER': []
        }
        
        for action in actions:
            if action.days_remaining is not None:
                if action.days_remaining <= 1:
                    grouped['URGENT'].append(action)
                elif action.days_remaining <= 7:
                    grouped['THIS_WEEK'].append(action)
                elif action.days_remaining <= 14:
                    grouped['NEXT_WEEK'].append(action)
                else:
                    grouped['LATER'].append(action)
            else:
                grouped['LATER'].append(action)
        
        html = ['<div class="action-list">']
        
        # URGENT
        if grouped['URGENT']:
            html.append('<div class="action-group urgent">')
            html.append('<h2>🚨 URGENT</h2>')
            for action in grouped['URGENT']:
                html.append(self._render_action_item(action))
            html.append('</div>')
        
        # THIS WEEK
        if grouped['THIS_WEEK']:
            html.append('<div class="action-group this-week">')
            html.append('<h2>⏰ DEZE WEEK</h2>')
            for action in grouped['THIS_WEEK']:
                html.append(self._render_action_item(action))
            html.append('</div>')
        
        # NEXT WEEK
        if grouped['NEXT_WEEK']:
            html.append('<div class="action-group next-week">')
            html.append('<h2>📅 VOLGENDE WEEK</h2>')
            for action in grouped['NEXT_WEEK']:
                html.append(self._render_action_item(action))
            html.append('</div>')
        
        # LATER
        if grouped['LATER']:
            html.append('<div class="action-group later">')
            html.append('<h2>🔜 LATER</h2>')
            for action in grouped['LATER']:
                html.append(self._render_action_item(action))
            html.append('</div>')
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _render_action_item(self, action: ActionItem) -> str:
        """Render individual action item"""
        
        priority_class = action.priority.lower()
        
        return f"""
        <div class="action-item {priority_class}">
            <input type="checkbox" class="action-checkbox" />
            <div class="action-content">
                <div class="action-description">{action.description}</div>
                <div class="action-meta">
                    <span class="address">{action.address}</span>
                    {f'<span class="assigned">{action.assigned_to}</span>' if action.assigned_to else ''}
                    {f'<span class="due-date">Due: {action.due_date.strftime("%d-%m")}</span>' if action.due_date else ''}
                    {f'<span class="days-remaining">({action.days_remaining} dagen)</span>' if action.days_remaining is not None else ''}
                </div>
            </div>
        </div>
        """
```

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
```
✅ Database setup
  ├─ Create all tables
  ├─ Set up indexes
  ├─ Import existing data from Excel
  └─ Validate data integrity

✅ Core queries
  ├─ property_status_view
  ├─ Basic aggregation queries
  └─ Test with sample data

✅ Basic Python API
  ├─ Database connection
  ├─ Query execution
  └─ Data models (dataclasses)
```

### Phase 2: Business Logic (Week 3)
```
✅ Warning generator
  ├─ Implement all warning rules
  ├─ Test edge cases
  └─ Unit tests

✅ Action generator
  ├─ Implement action creation logic
  ├─ Priority calculation
  └─ Unit tests

✅ Priority calculator
  └─ Smart priority based on multiple factors
```

### Phase 3: Frontend (Week 4)
```
✅ Dashboard view
  ├─ Property cards with status
  ├─ Warning display
  └─ Responsive design

✅ Timeline view
  ├─ Gantt-style chart
  ├─ Event markers
  └─ Interactive elements

✅ Action list view
  ├─ Grouped by urgency
  ├─ Checkboxes for completion
  └─ Filter/sort options
```

### Phase 4: AI Layer (Week 5 - Optional)
```
✅ Natural language queries
✅ Smart priority calculation
✅ Anomaly detection
✅ Predictive insights
```

### Phase 5: Polish & Deploy (Week 6)
```
✅ Error handling
✅ Loading states
✅ Mobile responsiveness
✅ Performance optimization
✅ Documentation
✅ Deployment
```

---

## 📁 Project Structure

```
ryanrent-dashboard/
├── README.md
├── requirements.txt
├── .env.example
├── setup.py
│
├── database/
│   ├── __init__.py
│   ├── schema.sql
│   ├── migrations/
│   │   ├── 001_create_tables.sql
│   │   ├── 002_add_indexes.sql
│   │   └── 003_create_views.sql
│   ├── connection.py
│   └── queries.py
│
├── business_logic/
│   ├── __init__.py
│   ├── warnings.py
│   ├── actions.py
│   ├── priority.py
│   └── models.py
│
├── ai_layer/
│   ├── __init__.py
│   ├── nl_query.py
│   ├── smart_priority.py
│   └── anomaly_detection.py
│
├── views/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── timeline.py
│   ├── actions.py
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── timeline.html
│       └── actions.html
│
├── api/
│   ├── __init__.py
│   ├── routes.py
│   ├── middleware.py
│   └── utils.py
│
├── tests/
│   ├── test_warnings.py
│   ├── test_actions.py
│   ├── test_priority.py
│   └── test_queries.py
│
└── static/
    ├── css/
    │   └── styles.css
    ├── js/
    │   └── app.js
    └── images/
```

---

## 🔧 Key Configuration

### requirements.txt
```
# Database
psycopg2-binary==2.9.9  # PostgreSQL
# OR
sqlite3  # SQLite for development

# Web framework
flask==3.0.0
flask-cors==4.0.0

# AI layer (optional)
anthropic==0.18.0

# Utilities
python-dotenv==1.0.0
python-dateutil==2.8.2
```

### .env.example
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ryanrent
# OR for SQLite
DATABASE_URL=sqlite:///ryanrent.db

# AI (optional)
ANTHROPIC_API_KEY=your_api_key_here

# Application
SECRET_KEY=your_secret_key
DEBUG=True
PORT=5000
```

---

## 💡 Key Implementation Tips for Cursor

### 1. Start with the Database
```
First prompt to Cursor:
"Create a PostgreSQL database schema for a property management system with tables for properties, uitchecks, inchecks, clients, inspectors, and bookings. Include all indexes and foreign keys as specified in the schema section."
```

### 2. Build Core Query First
```
Second prompt:
"Create a SQL view called property_status_view that joins properties, uitchecks, and inchecks, and calculates priority and completeness_score based on the business logic specified."
```

### 3. Implement Warning Generator
```
Third prompt:
"Implement the WarningGenerator class in Python that generates warnings based on property status. Include all warning types: missing pre-inspection, missing VIS, insufficient timeline, etc."
```

### 4. Test Each Component
```
"Create unit tests for the WarningGenerator that cover all edge cases: properties with new tenants, properties returning to owner, various timeline scenarios."
```

### 5. Build Views Incrementally
```
"Create a Flask route that returns property statuses as JSON, then create an HTML dashboard view that displays them grouped by priority with color coding."
```

---

## 🎯 Success Criteria

### MVP (Minimum Viable Product)
- ✅ Database with all tables populated
- ✅ property_status_view working correctly
- ✅ Dashboard showing properties grouped by priority
- ✅ At least 5 critical warning types implemented
- ✅ Basic action list generated automatically

### Full Product
- ✅ All views implemented (Dashboard, Timeline, Actions)
- ✅ All warning types implemented
- ✅ AI layer for natural language queries
- ✅ Mobile responsive
- ✅ Real-time updates
- ✅ User authentication (per inspector)

---

## 📊 Example API Endpoints

```python
# api/routes.py

from flask import Flask, jsonify, request
from business_logic.warnings import WarningGenerator
from business_logic.actions import ActionGenerator
from database.queries import get_property_statuses

app = Flask(__name__)

@app.route('/api/properties', methods=['GET'])
def get_properties():
    """
    Get all property statuses
    
    Query params:
    - priority: Filter by priority (KRITISCH, HOOG, NORMAAL, LAAG)
    - inspector: Filter by inspector name
    - date_from: Filter by date range start
    - date_to: Filter by date range end
    """
    priority = request.args.get('priority')
    inspector = request.args.get('inspector')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    statuses = get_property_statuses(
        priority=priority,
        inspector=inspector,
        date_from=date_from,
        date_to=date_to
    )
    
    # Generate warnings for each
    for status in statuses:
        status['warnings'] = WarningGenerator.generate_warnings(status)
    
    return jsonify(statuses)

@app.route('/api/actions', methods=['GET'])
def get_actions():
    """Get all action items"""
    
    statuses = get_property_statuses()
    actions = ActionGenerator.generate_actions(statuses)
    
    return jsonify([{
        'property_id': a.property_id,
        'address': a.address,
        'action_type': a.action_type,
        'priority': a.priority,
        'description': a.description,
        'due_date': a.due_date.isoformat() if a.due_date else None,
        'assigned_to': a.assigned_to,
        'days_remaining': a.days_remaining
    } for a in actions])

@app.route('/api/properties/<property_id>', methods=['GET'])
def get_property(property_id):
    """Get detailed status for a single property"""
    
    status = get_property_status(property_id)
    
    if not status:
        return jsonify({'error': 'Property not found'}), 404
    
    warnings = WarningGenerator.generate_warnings(status)
    
    return jsonify({
        'status': status,
        'warnings': warnings
    })

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get complete dashboard data"""
    
    statuses = get_property_statuses()
    actions = ActionGenerator.generate_actions(statuses)
    
    # Add warnings to each status
    for status in statuses:
        status['warnings'] = WarningGenerator.generate_warnings(status)
    
    # Group by priority
    grouped = {
        'KRITISCH': [],
        'HOOG': [],
        'NORMAAL': [],
        'LAAG': []
    }
    
    for status in statuses:
        priority = status.get('calculated_priority', 'LAAG')
        grouped[priority].append(status)
    
    # Calculate summary stats
    summary = {
        'total_properties': len(statuses),
        'kritisch_count': len(grouped['KRITISCH']),
        'hoog_count': len(grouped['HOOG']),
        'total_warnings': sum(len(s['warnings']) for s in statuses),
        'total_actions': len(actions),
        'urgent_actions': len([a for a in actions if a.priority == 'CRITICAL'])
    }
    
    return jsonify({
        'properties': grouped,
        'actions': actions[:20],  # Top 20 actions
        'summary': summary
    })

@app.route('/api/query', methods=['POST'])
def natural_language_query():
    """
    Natural language query endpoint (AI layer)
    
    Body:
    {
        "query": "Show me all properties with critical status this week"
    }
    """
    from ai_layer.nl_query import NaturalLanguageQuery
    
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Get context
    statuses = get_property_statuses()
    actions = ActionGenerator.generate_actions(statuses)
    
    context = {
        'properties': statuses,
        'actions': actions
    }
    
    # Query AI
    nl = NaturalLanguageQuery(api_key=os.getenv('ANTHROPIC_API_KEY'))
    response = nl.query(query, context)
    
    return jsonify({'response': response})
```

---

## 🎉 Final Notes

This specification provides everything you need to build the property status dashboard in Cursor. The system is designed to be:

1. **Modular** - Each component can be built and tested independently
2. **Extensible** - Easy to add new features (more warning types, new views)
3. **Maintainable** - Clear separation of concerns (data, logic, presentation)
4. **Scalable** - Database-first design supports growth

### Getting Started in Cursor

1. **Create project structure** - Use the folder structure provided
2. **Set up database** - Start with the schema.sql
3. **Build incrementally** - Follow the phase roadmap
4. **Test continuously** - Write tests as you build
5. **Iterate** - Get feedback from the team and improve

### Key Success Factors

- ✅ **Property-centric view** is the killer feature
- ✅ **Automatic warnings** save time and prevent mistakes
- ✅ **Action generation** turns insights into work
- ✅ **Simple, clear UI** beats complex dashboards
- ✅ **Fast queries** with proper indexes

Good luck building! 🚀