"""Đọc alert chuẩn hóa hoặc JSON report ZAP có site/alerts/instances."""

import hashlib
import json

from Lan.A3a_ai_config.contracts import Alert
from Lan.A3a_ai_config.safety import redact, redact_url


RISKS = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}


def parse_alerts(document: dict | list) -> list[dict]:
    """Chuẩn hóa theo từng instance; ID tự sinh ổn định, không dùng làm nhãn chuẩn.

    [TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT] Một instance là một record; số record có thể
    khác số alert type trong ZAP. H1/N3 cần thống nhất đơn vị trước benchmark.
    """
    if isinstance(document, list):
        groups = document
    elif isinstance(document, dict) and "site" in document:
        sites = document["site"]
        if not isinstance(sites, list) or any(not isinstance(site, dict) for site in sites):
            raise ValueError("site phải là danh sách object.")
        groups = []
        for site in sites:
            alerts = site.get("alerts", [])
            if not isinstance(alerts, list):
                raise ValueError("site.alerts phải là danh sách.")
            groups.extend(alerts)
    elif isinstance(document, dict) and "alerts" in document:
        groups = document["alerts"]
    else:
        raise ValueError("Cần danh sách alert hoặc object alerts/site của ZAP.")
    if not isinstance(groups, list):
        raise ValueError("alerts phải là danh sách.")
    records = []
    seen_ids = set()
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("Mỗi alert phải là object.")
        instances = group.get("instances")
        if instances is None:
            instances = [group]
        if not isinstance(instances, list) or not instances:
            raise ValueError("instances phải là danh sách không rỗng.")
        for instance in instances:
            if not isinstance(instance, dict):
                raise ValueError("Instance phải là object.")
            raw_risk = str(group.get("riskcode", group.get("risk", "")))
            risk = RISKS.get(raw_risk)
            if risk is None:
                word = str(group.get("risk", group.get("riskdesc", "Unknown"))).split(" ")[0].title()
                risk = word if word in {"High", "Medium", "Low", "Informational"} else "Unknown"
            cwe = group.get("cweid")
            item = {
                "name": group.get("name") or group.get("alert"),
                "risk": risk,
                "url": instance.get("uri") or instance.get("url") or group.get("url"),
                "param": instance.get("param", group.get("param", "")),
                "evidence": instance.get("evidence", group.get("evidence", "")),
                "cweid": None if cwe in {None, "", "0", 0, -1, "-1"} else str(cwe),
            }
            safe = redact(item)
            if isinstance(safe["url"], str):
                safe["url"] = redact_url(safe["url"])
            fingerprint = hashlib.sha256(json.dumps(safe, sort_keys=True).encode("utf-8")).hexdigest()[:16]
            explicit_id = instance.get("alert_id") or group.get("alert_id")
            item_id = explicit_id if len(instances) == 1 and explicit_id else "zap-" + fingerprint
            normalized = Alert.model_validate({"alert_id": item_id, **safe}).model_dump()
            if normalized["alert_id"] in seen_ids:
                raise ValueError("Alert ID trùng; cần làm rõ duplicate trước khi xử lý.")
            seen_ids.add(normalized["alert_id"])
            records.append(normalized)
    return records
