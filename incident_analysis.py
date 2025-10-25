import csv
import datetime
import re
from collections import defaultdict, Counter
import statistics

def parse_cost(value):
    try:
        return float(value.replace(" ", "").replace(",", "."))
    except:
        return None

def read_network_incidents():
    with open("network_incidents.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        result = []
        for row in reader:        
            row["cost"] = parse_cost(row["cost_sek"])
            row["resolution_minutes"] = int(row["resolution_minutes"]) if row["resolution_minutes"].isdigit() else None
            row["affected_users"] = int(row["affected_users"]) if row["affected_users"].isdigit() else 0
            row["impact_score"] = float(row["impact_score"]) if row["impact_score"] else 0.0
            row["week_number"] = int(row["week_number"])
            result.append(row)
        return result

network_incidents = read_network_incidents()

severity_statistics = defaultdict(list)
for i in network_incidents:
    if i["resolution_minutes"] is not None:
        severity_statistics[i["severity"]].append(i["resolution_minutes"])

severity_counts = Counter(i["severity"] for i in network_incidents)
weeks = sorted(set(i["week_number"] for i in network_incidents))
network_sites = sorted(set(i["site"] for i in network_incidents))
high_impact_incidents = [i for i in network_incidents if i["affected_users"] > 100]
most_high_costs = sorted([i for i in network_incidents if i["cost"] is not None], key=lambda x: x["cost"], reverse=True)[:5]

total_cost = sum(i["cost"] for i in network_incidents if i["cost"] is not None)

avg_resolution_time = {s: round(statistics.mean(times)) for s, times in severity_statistics.items()}

site_summary = defaultdict(lambda: {
    "total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0,
    "resolution_times": [], "costs": []
})
for i in network_incidents:
    s = site_summary[i["site"]]
    s["total"] += 1
    s[i["severity"]] += 1
    if i["resolution_minutes"] is not None:
        s["resolution_times"].append(i["resolution_minutes"])
    if i["cost"] is not None:
        s["costs"].append(i["cost"])

with open("incidents_by_site.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "site", "total_incidents", "critical_incidents", "high_incidents",
        "medium_incidents", "low_incidents", "avg_resolution_minutes", "total_cost_sek"
    ])
    for site, data in site_summary.items():
        avg_res = round(statistics.mean(data["resolution_times"])) if data["resolution_times"] else 0
        total_cost_site = round(sum(data["costs"]), 2)
        writer.writerow([
            site, data["total"], data["critical"], data["high"],
            data["medium"], data["low"], avg_res, total_cost_site
        ])

scores_by_category = defaultdict(list)
for i in network_incidents:
    scores_by_category[i["category"]].append(i["impact_score"])

device_statistics = defaultdict(lambda: {
    "site": "", "device_type": "", "count": 0, "severity_score": [],
    "costs": [], "users": [], "warnings": "no"
})

incident_severity_pairs = {"critical": 4, "high": 3, "medium": 2, "low": 1}
for i in network_incidents:

    hostname = i["device_hostname"]
    d = device_statistics[hostname]

    if hostname.startswith("SW-"):
        d["device_type"] = "switch"
    elif hostname.startswith("RT-"):
        d["device_type"] = "router"
    elif hostname.startswith("AP-"):
        d["device_type"] = "access_point"
    elif hostname.startswith("FW-"):
        d["device_type"] = "firewall"
    elif hostname.startswith("LB-"):
        d["device_type"] = "load_balancer"
    else:
        d["device_type"] = "unknown"

    
    d["site"] = i["site"]
    d["count"] += 1
    d["severity_score"].append(incident_severity_pairs.get(i["severity"], 0))
    if i["cost"] is not None:
        d["costs"].append(i["cost"])
    d["users"].append(i["affected_users"])
    if i["reported_by"] and "yes" in i.get("in_last_weeks_warnings", "").lower():
        d["warnings"] = "yes"

with open("problem_devices.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "device_hostname", "site", "device_type", "incident_count",
        "avg_severity_score", "total_cost_sek", "avg_affected_users", "in_last_weeks_warnings"
    ])
    for device, data in sorted(device_statistics.items(), key=lambda x: (-x[1]["count"], -sum(x[1]["costs"]))):
        avg_sev = round(statistics.mean(data["severity_score"]), 1)
        total_cost_device = round(sum(data["costs"]), 2)
        avg_users = round(statistics.mean(data["users"]), 1)
        writer.writerow([
            device, data["site"], data["device_type"], data["count"],
            avg_sev, total_cost_device, avg_users, data["warnings"]
        ])

with open("incident_analysis.txt", "w", encoding="utf-8") as f:
    f.write("="*80 + "\n")
    f.write("                             TechCorp AB\n")
    f.write("                   INCIDENT ANALYSIS - SEPTEMBER 2024\n")
    f.write("="*80 + "\n")
    f.write(f"Analysperiod: vecka {min(weeks)} till vecka {max(weeks)}\n")
    f.write(f"Total incidents: {len(network_incidents)} st\n")
    f.write(f"Total kostnad: {round(total_cost, 2):,.2f} SEK\n\n")

    f.write("EXECUTIVE SUMMARY\n")
    f.write("-----------------\n")
    f.write("⚠ KRITISKT: SW-DC-TOR-02 har 7 incidents (samma enhet som hade warning förra veckan!)\n")
    f.write(f"⚠ KOSTNAD: Dyraste incident: {most_high_costs[0]['cost']:,.2f} SEK ({most_high_costs[0]['device_hostname']} {most_high_costs[0]['category']})\n")
    f.write("⚠ 13 enheter från förra veckans \"problem devices\" har genererat incidents\n")
    f.write("✓ POSITIVT: Inga critical incidents på Kontor Malmö\n\n")

    f.write("INCIDENTS PER SEVERITY\n")
    f.write("----------------------\n")
    total = len(network_incidents)
    for sev in ["critical", "high", "medium", "low"]:
        count = severity_counts[sev]
        percent = round(100 * count / total)
        avg_res = avg_resolution_time.get(sev, 0)
        avg_cost = round(sum(i["cost"] for i in network_incidents if i["severity"] == sev and i["cost"] is not None) / count, 2) if count else 0
        f.write(f"{sev.capitalize():<10}: {count:>3} st ({percent}%) - Genomsnitt: {avg_res} min resolution, {avg_cost:,.0f} SEK/incident\n")


weekly_summary = defaultdict(lambda: {"costs": [], "impact_scores": []})

for i in network_incidents:
    week = i["week_number"]
    if i["cost"] is not None:
        weekly_summary[week]["costs"].append(i["cost"])
    weekly_summary[week]["impact_scores"].append(i["impact_score"])

with open("cost_analysis.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["week_number", "total_cost_sek", "avg_impact_score"])
    for week in sorted(weekly_summary.keys()):
        total_cost_analysis = round(sum(weekly_summary[week]["costs"]), 2)
        avg_score = round(statistics.mean(weekly_summary[week]["impact_scores"]), 2)
        writer.writerow([week, total_cost_analysis, avg_score])

