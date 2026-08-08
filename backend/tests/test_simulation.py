import sys
import os
import uuid

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.db.models import Simulation, SimulationResult, CustomerImpact, Customer, PricingModel
from app.services.simulation_service import run_pricing_simulation

def run_tests():
    print("Starting simulation database persistence tests against database...")
    db = SessionLocal()
    
    try:
        # Check if database is populated (needs at least one pricing model and customers)
        pm = db.query(PricingModel).filter_by(id="pm_pro_default").first()
        if not pm:
            print("ERROR: No default pricing model found in database. Please run seed script first.")
            return False
            
        customers_count = db.query(Customer).count()
        if customers_count == 0:
            print("ERROR: No customers found in database. Please run seed script first.")
            return False
            
        print(f"Verified base data: default pricing model exists, {customers_count} customers in DB.")

        # Test Case 1: Run a successful simulation with persist=True
        print("\n--- Running Test Case 1: Successful Simulation Persist ---")
        results = run_pricing_simulation(
            db=db,
            current_pricing_id="pm_pro_default",
            proposed_base_price=99.00,
            proposed_included_units=150,
            proposed_overage_price=0.90,
            pricing_metric="research_tasks",
            simulation_name="Integrity Verification Sim",
            persist=True
        )
        
        sim_id = results["simulation_id"]
        print(f"Simulation run completed. ID: {sim_id}")

        # Verify simulation row exists
        sim = db.query(Simulation).filter_by(id=sim_id).first()
        assert sim is not None, "Simulation row was not created in DB!"
        print("PASS: Simulation row exists.")

        # Verify simulation result row exists and references correct simulation
        sim_res = db.query(SimulationResult).filter_by(simulation_id=sim_id).first()
        assert sim_res is not None, "SimulationResult row was not created in DB!"
        assert sim_res.simulation_id == sim_id, "SimulationResult has wrong simulation_id reference!"
        print("PASS: SimulationResult exists and references the parent Simulation.")

        # Verify customer impact rows exist and reference correct simulation
        impacts = db.query(CustomerImpact).filter_by(simulation_id=sim_id).all()
        assert len(impacts) > 0, "No CustomerImpact rows created in DB!"
        for imp in impacts:
            assert imp.simulation_id == sim_id, f"CustomerImpact {imp.id} has incorrect simulation_id reference!"
        print(f"PASS: {len(impacts)} CustomerImpact rows exist and correctly reference the parent Simulation.")

        # Test Case 2: Verification of transaction rollback on failure
        print("\n--- Running Test Case 2: Failed Simulation Rollback Verification ---")
        
        # We will mock/sabotage the impacts insertion inside run_pricing_simulation by passing invalid database values.
        # But a simpler way to trigger an database-level insertion failure during the transaction is to add an object
        # with an invalid foreign key or missing required columns directly inside the transaction, OR we can cause a mock error.
        # Let's inspect what happens if an error occurs.
        
        # Let's run a simulation that we deliberately fail by using a dummy proposed base price and capturing the error.
        # To force a Database/SQLAlchemy level failure, we can temporarily patch db.add_all or trigger a validation error.
        # Let's check if the simulation rolls back cleanly when an exception is thrown.
        original_add_all = db.add_all
        
        # Override add_all to raise a clean exception to test database rollback
        def failing_add_all(instances):
            raise RuntimeError("Forced rollback test exception")
            
        db.add_all = failing_add_all
        
        rollback_tested = False
        try:
            run_pricing_simulation(
                db=db,
                current_pricing_id="pm_pro_default",
                proposed_base_price=10.0,
                proposed_included_units=10,
                proposed_overage_price=0.10,
                pricing_metric="research_tasks",
                simulation_name="Rollback Test Sim",
                persist=True
            )
        except RuntimeError as e:
            if str(e) == "Forced rollback test exception":
                rollback_tested = True
                print("Captured expected forced exception.")
        finally:
            # Restore original add_all
            db.add_all = original_add_all
            
        assert rollback_tested, "Forced exception was not raised!"
        
        # Verify that NO simulation record with this name exists (since it should have rolled back)
        sim_rollback = db.query(Simulation).filter_by(name="Rollback Test Sim").first()
        assert sim_rollback is None, "ERROR: Simulation record was not rolled back and persists in DB!"
        print("PASS: Clean transaction rollback verified. No orphan Simulation row was left in DB.")

        print("\nAll integrity tests passed successfully!")
        return True

    except AssertionError as ae:
        print(f"\nASSERTION ERROR: {ae}")
        return False
    except Exception as e:
        print(f"\nUNEXPECTED EXCEPTION: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
