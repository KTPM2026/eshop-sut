"""Private request preparation tests use synthetic sessions, never Burp evidence."""

import csv
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]


class BurpHandoffTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / "Nhu/N1_burp/case-matrix.csv").open(encoding="utf-8-sig", newline="") as stream:
            self.matrix = list(csv.DictReader(stream))
        self.session = {
            "api_origin": "http://127.0.0.1:3000", "sut_commit": "a" * 40,
            "actors": {
                "guest": {"id": None, "role": "guest"},
                "user_a": {"id": 2, "role": "user", "token": "TEST_ONLY.A.SIGNATURE"},
                "user_b": {"id": 3, "role": "user", "token": "TEST_ONLY.B.SIGNATURE"},
                "admin": {"id": 1, "role": "admin", "token": "TEST_ONLY.ADMIN.SIGNATURE"},
            },
            "orders": {"user_a": {"id": 11}, "user_b": {"id": 12}},
        }

    def build(self, session=None, matrix=None):
        program = (
            "const fs=require('node:fs');"
            "const {buildKit}=require('./Nhu/N1_burp/start_burp_lab.cjs');"
            "const input=JSON.parse(fs.readFileSync(0,'utf8'));"
            "try {process.stdout.write(JSON.stringify(buildKit(input.session,input.matrix)));}"
            "catch(e) {process.stderr.write(e.message);process.exitCode=1;}"
        )
        return subprocess.run(
            ["node", "-e", program], cwd=ROOT, text=True, encoding="utf-8",
            input=json.dumps({"session": session or self.session, "matrix": matrix or self.matrix}),
            capture_output=True, check=False,
        )

    def test_all_cases_are_prepared_not_executed(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        kit = json.loads(result.stdout)
        self.assertEqual(len(kit["requests"]), 11)
        self.assertTrue(kit["manifest"]["is_preparation_only"])
        self.assertFalse(kit["manifest"]["burp_executed"])
        self.assertFalse(kit["manifest"]["student_performed"])
        self.assertIsNone(kit["manifest"]["executed_at_utc"])
        self.assertEqual(kit["manifest"]["cases"], [])
        self.assertNotIn("token", json.dumps(kit["identities"]))
        for row in kit["requests"]:
            self.assertIsNone(row["actual_status"])
            self.assertIsNone(row["checkpoint_result"])
            self.assertFalse(row["burp_executed"])
            self.assertTrue(row["raw"].endswith("\r\n\r\n"))

    def test_owner_cross_user_guest_and_admin_requests(self):
        rows = {r["case_id"]: r for r in json.loads(self.build().stdout)["requests"]}
        self.assertIn("GET /api/orders/11 HTTP/1.1", rows["N1-01"]["raw"])
        self.assertIn("Bearer TEST_ONLY.A.SIGNATURE", rows["N1-01"]["raw"])
        self.assertIn("GET /api/orders/11 HTTP/1.1", rows["N1-06"]["raw"])
        self.assertIn("Bearer TEST_ONLY.B.SIGNATURE", rows["N1-06"]["raw"])
        self.assertIn("Bearer TEST_ONLY.ADMIN.SIGNATURE", rows["N1-10"]["raw"])
        self.assertIn("GET /api/orders/2147483647 HTTP/1.1", rows["N1-11"]["raw"])
        for row in rows.values():
            self.assertNotIn("Cookie:", row["raw"])
            if row["actor"] == "guest":
                self.assertNotIn("Authorization", row["raw"])

    def test_rejects_nonlocal_origin_and_wrong_roles(self):
        for value in ("https://example.invalid", "http://localhost:3000"):
            session = deepcopy(self.session)
            session["api_origin"] = value
            self.assertNotEqual(self.build(session=session).returncode, 0)
        session = deepcopy(self.session)
        session["actors"]["user_a"]["role"] = "admin"
        self.assertNotEqual(self.build(session=session).returncode, 0)

    def test_rejects_tokens_for_guest_and_header_injection(self):
        session = deepcopy(self.session)
        session["actors"]["guest"]["token"] = "TEST_ONLY.A.SIGNATURE"
        self.assertNotEqual(self.build(session=session).returncode, 0)
        session = deepcopy(self.session)
        session["actors"]["user_a"]["token"] += "\r\nCookie: TEST_ONLY"
        self.assertNotEqual(self.build(session=session).returncode, 0)

    def test_rejects_invalid_ids_and_unscoped_matrix(self):
        session = deepcopy(self.session)
        session["orders"]["user_a"]["id"] = "11 HTTP/1.1\r\nHost: example.invalid"
        self.assertNotEqual(self.build(session=session).returncode, 0)
        for changes in ({"method": "DELETE"}, {"case_id": "../outside"},
                        {"path_template": "/api/admin/users/1"}):
            matrix = deepcopy(self.matrix)
            matrix[0].update(changes)
            self.assertNotEqual(self.build(matrix=matrix).returncode, 0)

    def test_rejects_missing_reset_confirmation_without_starting_api(self):
        result = subprocess.run(
            ["node", "Nhu/N1_burp/start_burp_lab.cjs"], cwd=ROOT,
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--reset-lab", result.stderr)


if __name__ == "__main__":
    unittest.main()
