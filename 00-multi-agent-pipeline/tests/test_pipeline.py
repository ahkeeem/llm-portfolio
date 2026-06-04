"""
Tests for the multi-agent pipeline orchestration.

Tests routing logic directly. Full graph execution tests are
gated behind langgraph availability.
"""
import sys
import os
import unittest
from unittest.mock import patch

# Ensure the 00-multi-agent-pipeline root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.graph import should_retry_policy


class TestConditionalRouting(unittest.TestCase):
    """Verify the Auditor's self-correction routing logic."""

    def test_audit_passed_routes_to_finalize(self):
        state = {"audit_passed": True, "revision_count": 0}
        self.assertEqual(should_retry_policy(state), "finalize")

    def test_audit_failed_under_limit_routes_to_re_reason(self):
        state = {"audit_passed": False, "revision_count": 1}
        self.assertEqual(should_retry_policy(state), "re-reason")

    def test_audit_failed_at_limit_routes_to_finalize(self):
        """After 3 revisions, pipeline escalates rather than looping."""
        state = {"audit_passed": False, "revision_count": 3}
        self.assertEqual(should_retry_policy(state), "finalize")

    def test_audit_failed_over_limit_routes_to_finalize(self):
        state = {"audit_passed": False, "revision_count": 5}
        self.assertEqual(should_retry_policy(state), "finalize")

    def test_default_state_routes_to_finalize(self):
        """When audit_passed is missing from state, defaults to True → finalize."""
        state = {}
        self.assertEqual(should_retry_policy(state), "finalize")

    def test_edge_case_zero_revisions_failed_audit(self):
        state = {"audit_passed": False, "revision_count": 0}
        self.assertEqual(should_retry_policy(state), "re-reason")


class TestFullPipelineExecution(unittest.TestCase):
    """Full graph compile + invoke (requires langgraph)."""

    def test_pipeline_end_to_end(self):
        try:
            from langgraph.graph import StateGraph, END
        except ImportError:
            self.skipTest("langgraph not installed — skipping graph execution test")

        # Patch all external dependencies so the test is hermetic
        with patch("core.nodes.extract_node.extract_receipt_fields") as mock_extract, \
             patch("core.nodes.policy_node.query_rag") as mock_rag, \
             patch("core.nodes.audit_node.score_faithfulness") as mock_faith, \
             patch("core.nodes.audit_node.score_relevancy") as mock_rel, \
             patch("core.nodes.triage_node.call_llm") as mock_llm:

            mock_extract.return_value = {
                "fields": {"company": "Whole Foods", "total": "11.48", "item": "Apples"},
                "model": "fine-tuned-local"
            }
            mock_rag.return_value = {
                "answer": "Refund approved per policy §4.2.",
                "sources": [{"metadata": {"source": "policy_v2.pdf"}}],
                "retrieved_context": "§4.2: organic produce refunds up to $20."
            }
            mock_faith.return_value = 0.92
            mock_rel.return_value = 0.88
            mock_llm.return_value = "Dear customer, your refund has been approved."

            from core.graph import create_pipeline
            graph = create_pipeline()

            result = graph.invoke({
                "raw_input": "I need a refund for bad apples.",
                "claim_id": "claim-test",
                "extracted_data": {},
                "extraction_confidence": 0.0,
                "policy_verdict": "",
                "policy_citations": [],
                "policy_context": "",
                "audit_scores": {},
                "audit_feedback": None,
                "audit_passed": False,
                "final_email_draft": "",
                "requires_approval": True,
                "human_feedback": None,
                "trace_id": "test-trace",
                "revision_count": 0,
                "status": "starting"
            })

            self.assertEqual(result["status"], "ready_for_human")
            self.assertTrue(result["audit_passed"])
            self.assertIn("approved", result["final_email_draft"].lower())
            self.assertEqual(result["revision_count"], 0)


if __name__ == "__main__":
    unittest.main()
