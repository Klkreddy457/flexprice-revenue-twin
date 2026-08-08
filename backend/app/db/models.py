from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    segment = Column(String, nullable=False)  # Free, Startup, Growth, Enterprise
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    events = relationship("UsageEvent", back_populates="customer", cascade="all, delete-orphan")

class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_name = Column(String, nullable=False, default="research_completed")
    
    # Usage metrics
    tasks = Column(Integer, default=1)
    agent_calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    documents_processed = Column(Integer, default=0)
    compute_seconds = Column(Integer, default=0)
    premium_model_calls = Column(Integer, default=0)

    # Relationships
    customer = relationship("Customer", back_populates="events")

class PricingModel(Base):
    __tablename__ = "pricing_models"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    base_price = Column(Float, nullable=False)
    included_units = Column(Integer, nullable=False)
    overage_price = Column(Float, nullable=False)
    pricing_metric = Column(String, default="research_tasks")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    current_pricing_id = Column(String, ForeignKey("pricing_models.id"), nullable=False)
    proposed_pricing_data = Column(JSON, nullable=False) # Stores base_price, included_units, overage_price, pricing_metric
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(String, primary_key=True, index=True)
    simulation_id = Column(String, ForeignKey("simulations.id"), nullable=False)
    summary_data = Column(JSON, nullable=False) # Stores aggregate metrics: revenue, margin, customer impacts
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CustomerImpact(Base):
    __tablename__ = "customer_impacts"

    id = Column(String, primary_key=True, index=True)
    simulation_id = Column(String, ForeignKey("simulations.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    current_bill = Column(Float, nullable=False)
    proposed_bill = Column(Float, nullable=False)
    bill_change = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False) # LOW, MEDIUM, HIGH, CRITICAL

class FlexpriceDeployment(Base):
    __tablename__ = "flexprice_deployments"

    id = Column(String, primary_key=True, index=True)
    pricing_model_id = Column(String, ForeignKey("pricing_models.id"), nullable=False)
    status = Column(String, nullable=False)  # simulated, active, deployed
    details = Column(JSON, nullable=False)  # Flexprice entity details created
    deployed_at = Column(DateTime, default=datetime.datetime.utcnow)
