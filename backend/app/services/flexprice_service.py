import httpx
import uuid
import datetime
from typing import Dict, Any, List
from app.core.config import settings

class FlexpriceService:
    def __init__(self):
        self.api_key = settings.FLEXPRICE_API_KEY
        self.base_url = settings.FLEXPRICE_URL.rstrip('/')
        
        # Temporary in-memory list for live events stream simulation
        # Stores logs: timestamp, customer, event, usage, status
        self.simulated_stream_logs: List[Dict[str, Any]] = []

    def get_mode(self) -> str:
        return "LIVE" if self.api_key else "DEMO"

    async def deploy_pricing_to_flexprice(
        self,
        base_price: float,
        included_units: int,
        overage_price: float,
        plan_name: str,
        pricing_metric: str = "research_tasks"
    ) -> Dict[str, Any]:
        """
        Deploys a pricing plan configuration. Creates Meter, Plan, Price, and Entitlement.
        """
        mode = self.get_mode()
        logs = []
        entities = {}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 1. Create/Retrieve Meter
        meter_payload = {
            "name": f"{pricing_metric}_meter",
            "event_name": "research_completed",
            "aggregation": "sum",
            "property_name": "tasks"
        }
        meter_url = f"{self.base_url}/v1/meters"
        
        logs.append({
            "step": "1. Create Meter",
            "endpoint": "POST /v1/meters",
            "payload": meter_payload,
            "status": "pending"
        })

        meter_id = f"met_{uuid.uuid4().hex[:8]}"
        if mode == "LIVE":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(meter_url, json=meter_payload, headers=headers, timeout=10.0)
                    if resp.status_code in [200, 201]:
                        meter_data = resp.json()
                        meter_id = meter_data.get("id", meter_id)
                        logs[-1]["status"] = "success"
                        logs[-1]["response"] = meter_data
                    else:
                        logs[-1]["status"] = f"failed (HTTP {resp.status_code})"
                        logs[-1]["response"] = resp.text
            except Exception as e:
                logs[-1]["status"] = "failed"
                logs[-1]["response"] = str(e)
        else:
            logs[-1]["status"] = "success"
            logs[-1]["response"] = {
                "id": meter_id,
                "object": "meter",
                "name": meter_payload["name"],
                "event_name": meter_payload["event_name"],
                "aggregation": meter_payload["aggregation"],
                "property_name": meter_payload["property_name"],
                "created_at": datetime.datetime.utcnow().isoformat()
            }
        
        entities["meter"] = logs[-1]["response"]

        # 2. Create Plan
        plan_payload = {
            "name": plan_name,
            "description": f"Generated plan: ${base_price}/mo, includes {included_units} tasks, ${overage_price} overage.",
            "interval": "month"
        }
        plan_url = f"{self.base_url}/v1/plans"
        
        logs.append({
            "step": "2. Create Billing Plan",
            "endpoint": "POST /v1/plans",
            "payload": plan_payload,
            "status": "pending"
        })

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        if mode == "LIVE":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(plan_url, json=plan_payload, headers=headers, timeout=10.0)
                    if resp.status_code in [200, 201]:
                        plan_data = resp.json()
                        plan_id = plan_data.get("id", plan_id)
                        logs[-1]["status"] = "success"
                        logs[-1]["response"] = plan_data
                    else:
                        logs[-1]["status"] = f"failed (HTTP {resp.status_code})"
                        logs[-1]["response"] = resp.text
            except Exception as e:
                logs[-1]["status"] = "failed"
                logs[-1]["response"] = str(e)
        else:
            logs[-1]["status"] = "success"
            logs[-1]["response"] = {
                "id": plan_id,
                "object": "plan",
                "name": plan_payload["name"],
                "description": plan_payload["description"],
                "interval": plan_payload["interval"],
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            
        entities["plan"] = logs[-1]["response"]

        # 3. Create Overage Metered Price
        price_payload = {
            "plan_id": plan_id,
            "meter_id": meter_id,
            "amount": overage_price,
            "currency": "usd",
            "billing_scheme": "per_unit",
            "type": "usage"
        }
        price_url = f"{self.base_url}/v1/prices"
        
        logs.append({
            "step": "3. Configure Overage Metered Price",
            "endpoint": "POST /v1/prices",
            "payload": price_payload,
            "status": "pending"
        })

        price_id = f"pr_{uuid.uuid4().hex[:8]}"
        if mode == "LIVE":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(price_url, json=price_payload, headers=headers, timeout=10.0)
                    if resp.status_code in [200, 201]:
                        price_data = resp.json()
                        price_id = price_data.get("id", price_id)
                        logs[-1]["status"] = "success"
                        logs[-1]["response"] = price_data
                    else:
                        logs[-1]["status"] = f"failed (HTTP {resp.status_code})"
                        logs[-1]["response"] = resp.text
            except Exception as e:
                logs[-1]["status"] = "failed"
                logs[-1]["response"] = str(e)
        else:
            logs[-1]["status"] = "success"
            logs[-1]["response"] = {
                "id": price_id,
                "object": "price",
                "plan_id": plan_payload,
                "meter_id": meter_id,
                "amount": price_payload["amount"],
                "currency": price_payload["currency"],
                "billing_scheme": price_payload["billing_scheme"],
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            
        entities["overage_price"] = logs[-1]["response"]

        # 4. Create Entitlement (Included Units)
        entitlement_payload = {
            "plan_id": plan_id,
            "feature_id": f"feat_{pricing_metric}",
            "type": "metered_limit",
            "limit": included_units
        }
        entitlement_url = f"{self.base_url}/v1/entitlements"
        
        logs.append({
            "step": "4. Set Subscription Entitlement Limit",
            "endpoint": "POST /v1/entitlements",
            "payload": entitlement_payload,
            "status": "pending"
        })

        entitlement_id = f"ent_{uuid.uuid4().hex[:8]}"
        if mode == "LIVE":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(entitlement_url, json=entitlement_payload, headers=headers, timeout=10.0)
                    if resp.status_code in [200, 201]:
                        ent_data = resp.json()
                        entitlement_id = ent_data.get("id", entitlement_id)
                        logs[-1]["status"] = "success"
                        logs[-1]["response"] = ent_data
                    else:
                        logs[-1]["status"] = f"failed (HTTP {resp.status_code})"
                        logs[-1]["response"] = resp.text
            except Exception as e:
                logs[-1]["status"] = "failed"
                logs[-1]["response"] = str(e)
        else:
            logs[-1]["status"] = "success"
            logs[-1]["response"] = {
                "id": entitlement_id,
                "object": "entitlement",
                "plan_id": plan_id,
                "feature_id": entitlement_payload["feature_id"],
                "type": entitlement_payload["type"],
                "limit": entitlement_payload["limit"],
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            
        entities["entitlement"] = logs[-1]["response"]

        # 5. Create Base Subscription Price
        base_price_payload = {
            "plan_id": plan_id,
            "amount": base_price,
            "currency": "usd",
            "billing_scheme": "per_unit",
            "type": "recurring",
            "recurring": {
                "interval": "month"
            }
        }
        logs.append({
            "step": "5. Configure Base Recurring Price",
            "endpoint": "POST /v1/prices",
            "payload": base_price_payload,
            "status": "pending"
        })

        if mode == "LIVE":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(price_url, json=base_price_payload, headers=headers, timeout=10.0)
                    if resp.status_code in [200, 201]:
                        base_price_data = resp.json()
                        logs[-1]["status"] = "success"
                        logs[-1]["response"] = base_price_data
                    else:
                        logs[-1]["status"] = f"failed (HTTP {resp.status_code})"
                        logs[-1]["response"] = resp.text
            except Exception as e:
                logs[-1]["status"] = "failed"
                logs[-1]["response"] = str(e)
        else:
            logs[-1]["status"] = "success"
            logs[-1]["response"] = {
                "id": f"pr_rec_{uuid.uuid4().hex[:8]}",
                "object": "price",
                "plan_id": plan_id,
                "amount": base_price,
                "currency": "usd",
                "type": "recurring",
                "created_at": datetime.datetime.utcnow().isoformat()
            }

        entities["base_price"] = logs[-1]["response"]

        return {
            "deployment_id": f"dep_{uuid.uuid4().hex[:8]}",
            "mode": mode,
            "status": "success" if all(log["status"] == "success" for log in logs) else "partially_failed",
            "entities": entities,
            "api_call_logs": logs
        }

    async def ingest_usage_event(
        self,
        customer_id: str,
        customer_name: str,
        tasks: int,
        agent_calls: int,
        tokens_used: int,
        documents_processed: int,
        compute_seconds: int,
        premium_model_calls: int
    ) -> Dict[str, Any]:
        """
        Sends an event to Flexprice or simulates event ingestion.
        """
        mode = self.get_mode()
        
        event_payload = {
            "customer_id": customer_id,
            "event_name": "research_completed",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "properties": {
                "tasks": tasks,
                "agent_calls": agent_calls,
                "tokens_used": tokens_used,
                "documents_processed": documents_processed,
                "compute_seconds": compute_seconds,
                "premium_model_calls": premium_model_calls
            }
        }
        
        status = "pending"
        resp_payload = {}
        
        if mode == "LIVE":
            url = f"{self.base_url}/v1/events"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=event_payload, headers=headers, timeout=5.0)
                    if resp.status_code in [200, 202]:
                        status = "success"
                        resp_payload = resp.json()
                    else:
                        status = f"failed (HTTP {resp.status_code})"
                        resp_payload = {"error": resp.text}
            except Exception as e:
                status = "failed"
                resp_payload = {"error": str(e)}
        else:
            status = "success"
            resp_payload = {
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "status": "ingested",
                "received_at": datetime.datetime.utcnow().isoformat()
            }
            
        # Log to in-memory stream log
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "customer_id": customer_id,
            "customer_name": customer_name,
            "event_name": event_payload["event_name"],
            "usage": f"{tasks} task, {agent_calls} calls, {tokens_used} tokens",
            "status": status,
            "mode": mode
        }
        self.simulated_stream_logs.insert(0, log_entry) # Put at beginning of list
        # Keep stream logs limited to 100 entries
        if len(self.simulated_stream_logs) > 100:
            self.simulated_stream_logs = self.simulated_stream_logs[:100]
            
        return {
            "status": status,
            "event_payload": event_payload,
            "response": resp_payload
        }

flexprice_service = FlexpriceService()
