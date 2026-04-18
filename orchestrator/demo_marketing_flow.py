import json
import urllib.request

BASE = "http://127.0.0.1:8765"


def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def router_classify(founder_request):
    text = founder_request.lower()
    if any(word in text for word in ["launch", "campaign", "messaging", "positioning"]):
        return "marketing"
    return "unknown"


def marketing_content_worker(founder_request, roadmap_item):
    return {
        "messaging_angle": f"Position {roadmap_item['title']} as a faster path to activation for startup teams.",
        "content_brief": "Draft launch post, landing page headline, and founder email."
    }


def marketing_performance_worker(founder_request, roadmap_item):
    return {
        "channels": ["x", "email", "landing_page"],
        "budget_request": 1500,
        "experiment": "Test founder-led vs product-led headline on landing page."
    }


def marketing_ops_worker(founder_request):
    return {
        "success_metrics": ["signups", "cac", "landing_page_cvr"],
        "reporting_window": "last_7_days"
    }


def marketing_lead(founder_request):
    roadmap = post("/roadmap.get_item", {"roadmap_item_id": "rdm_024"})
    content = marketing_content_worker(founder_request, roadmap)
    performance = marketing_performance_worker(founder_request, roadmap)
    ops = marketing_ops_worker(founder_request)

    campaign = post("/marketing.create_campaign", {
        "name": "Launch for onboarding revamp",
        "objective": "Acquire waitlist signups",
        "audience": "Startup founders and operators",
        "channels": performance["channels"],
        "owner": "marketing_lead",
        "start_date": "2026-05-01",
        "end_date": "2026-05-21"
    })

    spend = post("/marketing.submit_spend_request", {
        "campaign_id": campaign["campaign_id"],
        "amount": performance["budget_request"],
        "reason": "Paid test budget for launch week",
        "expected_outcome": "150 qualified signups",
        "time_horizon": "14_days"
    })

    return {
        "event_type": "marketing.plan_ready",
        "source": "marketing",
        "target": "router",
        "correlation_id": "demo-corr-001",
        "payload": {
            "campaign": campaign,
            "spend_request": spend,
            "roadmap_item": roadmap["title"],
            "messaging_angle": content["messaging_angle"],
            "content_brief": content["content_brief"],
            "channels": performance["channels"],
            "experiment": performance["experiment"],
            "success_metrics": ops["success_metrics"]
        }
    }


def main():
    founder_request = "Create a launch campaign for the onboarding revamp"
    domain = router_classify(founder_request)
    if domain != "marketing":
        print(json.dumps({"error": "router could not classify request"}, indent=2))
        return

    result = marketing_lead(founder_request)
    print(json.dumps({
        "router_dispatch": {
            "domain": domain,
            "request": founder_request
        },
        "domain_result": result
    }, indent=2))


if __name__ == "__main__":
    main()
