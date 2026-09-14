import unittest
from fastapi.testclient import TestClient

from backend.api import app
from backend.database import init_db
from backend.ml_service import ml_service


class TestDisputeShieldIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from backend.config import settings
        settings.API_KEY = ""
        init_db()
        ml_service.load_model()
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_02_process_dispute_flow(self):
        res = self.client.post("/disputes/TXN100001/process")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["transaction_id"], "TXN100001")
        self.assertIn("prediction", data)
        self.assertIn("confidence", data)
        self.assertIn("decision", data)

    def test_03_update_analyst_action_persistence(self):
        # 1. Update action
        res = self.client.post(
            "/disputes/TXN100001/action",
            json={"action": "CONTEST", "override_reason": "customer_provided_proof"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "CONTESTED")

        # 2. Re-query dispute process and verify persisted human action
        proc_res = self.client.post("/disputes/TXN100001/process")
        self.assertEqual(proc_res.status_code, 200)
        proc_data = proc_res.json()
        self.assertEqual(proc_data["case_status"], "CONTESTED")
        self.assertEqual(proc_data["human_action"], "CONTEST")
        self.assertEqual(proc_data["override_reason"], "customer_provided_proof")

    def test_04_get_metrics_endpoint(self):
        res = self.client.get("/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("precision", data)
        self.assertIn("roc_auc", data)
        self.assertIn("benchmarks", data)

    def test_05_get_audit_endpoint(self):
        res = self.client.get("/audit")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_06_simulate_endpoint_no_side_effects(self):
        """Simulation endpoint evaluates ML & policy without modifying audit logs or DB."""
        audit_before = self.client.get("/audit").json()
        
        sim_payload = {
            "amount_inr": 2500.0,
            "reason_code": "duplicate_charge",
            "duplicate_txn_id_found": True,
            "delivery_confirmed": True
        }
        res = self.client.post("/simulate", json=sim_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_simulation"])
        self.assertEqual(data["decision"]["action"], "RECOMMEND_CONTEST")

        audit_after = self.client.get("/audit").json()
        self.assertEqual(len(audit_before), len(audit_after))

    def test_07_exported_package_no_unmasked_pii(self):
        """Verify dispute process response evidence contains no unmasked email/IP fields."""
        res = self.client.post("/disputes/TXN100001/process")
        self.assertEqual(res.status_code, 200)
        evidence = res.json()["evidence"]
        for k, v in evidence.items():
            if isinstance(v, str):
                self.assertNotIn("@example.com", v)
                self.assertNotRegex(v, r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')


if __name__ == "__main__":
    unittest.main()
