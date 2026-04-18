import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

CAMPAIGNS = {
    "mkt_cmp_001": {
        "campaign_id": "mkt_cmp_001",
        "name": "Spring launch",
        "objective": "Acquire waitlist signups",
        "audience": "Seed-stage founders",
        "channels": ["x", "email", "landing_page"],
        "owner": "marketing_lead",
        "status": "draft",
    }
}

ROADMAP = {
    "rdm_024": {
        "roadmap_item_id": "rdm_024",
        "title": "Onboarding revamp",
        "status": "planned",
        "summary": "Improve first-run activation",
        "owner": "product",
        "target_date": "2026-05-10",
        "notes": ["Marketing launch support required"],
    }
}


def json_response(handler, code, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8"))

        if parsed.path == "/marketing.create_campaign":
            campaign_id = f"mkt_cmp_{len(CAMPAIGNS) + 1:03d}"
            campaign = {
                "campaign_id": campaign_id,
                "status": "draft",
                **data,
            }
            CAMPAIGNS[campaign_id] = campaign
            return json_response(self, 200, {"campaign_id": campaign_id, "status": "draft", "created_at": "2026-04-18T12:00:00Z"})

        if parsed.path == "/marketing.update_campaign":
            campaign_id = data["campaign_id"]
            CAMPAIGNS[campaign_id].update(data)
            return json_response(self, 200, {"campaign_id": campaign_id, "status": CAMPAIGNS[campaign_id].get("status", "draft"), "updated_at": "2026-04-18T12:30:00Z"})

        if parsed.path == "/marketing.list_campaigns":
            status = data.get("status")
            campaigns = list(CAMPAIGNS.values())
            if status:
                campaigns = [c for c in campaigns if c.get("status") == status]
            return json_response(self, 200, {"campaigns": campaigns})

        if parsed.path == "/marketing.get_metrics":
            return json_response(self, 200, {
                "campaign_id": data.get("campaign_id", "mkt_cmp_001"),
                "window": data.get("window", "last_7_days"),
                "metrics": {
                    "impressions": 12000,
                    "clicks": 430,
                    "signups": 39,
                    "ctr": 0.0358,
                    "cvr": 0.0907,
                    "spend": 420.0,
                    "cac": 10.77,
                },
            })

        if parsed.path == "/marketing.record_experiment":
            return json_response(self, 200, {"experiment_id": "mkt_exp_001", "saved": True})

        if parsed.path == "/marketing.submit_spend_request":
            return json_response(self, 200, {"request_id": "mkt_spend_001", "status": "submitted"})

        if parsed.path == "/roadmap.list_items":
            return json_response(self, 200, {"items": list(ROADMAP.values())})

        if parsed.path == "/roadmap.get_item":
            item_id = data["roadmap_item_id"]
            return json_response(self, 200, ROADMAP[item_id])

        return json_response(self, 404, {"error": "unknown endpoint"})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("Mock MCP server listening on http://127.0.0.1:8765")
    server.serve_forever()
