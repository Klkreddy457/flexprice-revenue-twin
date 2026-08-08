import random
import datetime
from sqlalchemy.orm import Session
from app.db.models import Customer, UsageEvent, PricingModel

def generate_customer_names():
    adjectives = [
        "Alpha", "Beta", "Apex", "Nova", "Stellar", "Quantum", "Hyper", "Cognitive", 
        "Synthetix", "Prism", "Vortex", "Matrix", "Helix", "Infinitum", "Optima", "Aether",
        "Cyber", "Deep", "Flux", "Nexus", "Omicron", "Spectra", "Vector", "Zenith"
    ]
    nouns = [
        "AI", "Labs", "Tech", "Systems", "Research", "Computing", "Agents", "Solutions", 
        "Software", "Intelligence", "Analytics", "Data", "Node", "Flow", "Net", "Grid",
        "Scale", "Engine", "Logic", "Mind", "Core", "Link", "Sync", "Loop"
    ]
    suffixes = ["Corp", "Inc", "Co", "Group", "LLC", ""]
    
    names = set()
    while len(names) < 1000:
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        suff = random.choice(suffixes)
        name = f"{adj} {noun} {suff}".strip()
        names.add(name)
    
    return list(names)

def seed_data(db: Session):
    # Check if pricing models already exist
    default_pm = db.query(PricingModel).filter_by(id="pm_pro_default").first()
    if not default_pm:
        # Create standard Pro pricing model
        pm_pro = PricingModel(
            id="pm_pro_default",
            name="ResearchPilot Pro Default",
            description="Default Pro Plan ($49/mo, 100 tasks, $0.75 overage)",
            base_price=49.00,
            included_units=100,
            overage_price=0.75,
            pricing_metric="research_tasks",
            created_at=datetime.datetime.utcnow()
        )
        db.add(pm_pro)
        
        # Also create a seed pricing model matching current pricing of ResearchPilot
        db.commit()

    # Check if customers exist
    if db.query(Customer).count() > 0:
        print("Database already seeded.")
        return

    print("Generating seed data...")
    customer_names = generate_customer_names()
    
    # Define segments
    # Free: 40%, Startup: 35%, Growth: 20%, Enterprise: 5%
    segments = (
        ["Free"] * 400 +
        ["Startup"] * 350 +
        ["Growth"] * 200 +
        ["Enterprise"] * 50
    )
    random.shuffle(segments)
    
    customers_to_insert = []
    customers_list = []
    
    for i in range(1000):
        cust_id = f"cust_{i+1:04d}"
        segment = segments[i]
        name = customer_names[i]
        
        cust = Customer(
            id=cust_id,
            name=name,
            segment=segment,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=120) # 120 days ago
        )
        customers_to_insert.append(cust)
        customers_list.append((cust_id, segment))
    
    db.add_all(customers_to_insert)
    db.commit()
    print("Seeded 1,000 customers.")
    
    # Generate events
    events_to_insert = []
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    
    # Seed configuration per segment for event generation over 90 days
    # (event_count_range, agent_calls_range, tokens_range, docs_range, compute_range, premium_calls_range)
    seg_config = {
        "Free": ((0, 6), (1, 5), (1000, 10000), (0, 1), (5, 30), (0, 0)),
        "Startup": ((20, 80), (5, 15), (5000, 50000), (0, 5), (10, 100), (0, 3)),
        "Growth": ((100, 300), (10, 40), (20000, 200000), (1, 20), (50, 500), (1, 15)),
        "Enterprise": ((500, 1500), (20, 100), (100000, 1000000), (5, 100), (200, 2000), (5, 120))
    }
    
    # To introduce extreme outliers in Enterprise segment:
    # We will pick 3 "extreme" customers that use massive amounts of premium calls and tokens
    extreme_customers = random.sample([c[0] for c in customers_list if c[1] == "Enterprise"], 3)
    
    print("Generating 100,000+ usage events...")
    for cust_id, segment in customers_list:
        cfg = seg_config[segment]
        event_count = random.randint(cfg[0][0], cfg[0][1])
        
        is_extreme = cust_id in extreme_customers
        if is_extreme:
            # Boost event count and usage parameters for these extreme users
            event_count = random.randint(1800, 3000)
            
        for _ in range(event_count):
            # Distribute events over the last 90 days
            offset_seconds = random.randint(0, 90 * 24 * 3600)
            event_time = start_date + datetime.timedelta(seconds=offset_seconds)
            
            # Base ranges
            calls_rng = cfg[1]
            tokens_rng = cfg[2]
            docs_rng = cfg[3]
            comp_rng = cfg[4]
            prem_rng = cfg[5]
            
            if is_extreme:
                agent_calls = random.randint(50, 200)
                tokens_used = random.randint(500000, 3000000)
                documents_processed = random.randint(50, 200)
                compute_seconds = random.randint(1000, 5000)
                premium_model_calls = random.randint(50, 300)
            else:
                agent_calls = random.randint(calls_rng[0], calls_rng[1])
                tokens_used = random.randint(tokens_rng[0], tokens_rng[1])
                documents_processed = random.randint(docs_rng[0], docs_rng[1])
                compute_seconds = random.randint(comp_rng[0], comp_rng[1])
                premium_model_calls = random.randint(prem_rng[0], prem_rng[1]) if prem_rng[1] > 0 else 0
                
            events_to_insert.append({
                "customer_id": cust_id,
                "timestamp": event_time,
                "event_name": "research_completed",
                "tasks": 1,
                "agent_calls": agent_calls,
                "tokens_used": tokens_used,
                "documents_processed": documents_processed,
                "compute_seconds": compute_seconds,
                "premium_model_calls": premium_model_calls
            })
            
    # Bulk insert for speed
    # Chunk inserts to prevent memory spikes
    chunk_size = 10000
    for i in range(0, len(events_to_insert), chunk_size):
        chunk = events_to_insert[i:i+chunk_size]
        db.execute(UsageEvent.__table__.insert(), chunk)
        
    db.commit()
    print(f"Seeded {len(events_to_insert)} usage events successfully.")
