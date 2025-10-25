import csv
from datetime import date
import calendar
from collections import defaultdict

 
# company name and date
beautify_it = "=" * 70
comp_name = " TechCorp AB"
#now = datetime.now()
#report_taken_date = now.strftime("%Y-%m-%d %H:%M:%S")
#last_updated = data["last_updated"]
SEVERITY_MAPPING = {
    'low': 1,
    'medium': 2,
    'high': 3,
    'critical': 4
    }
# read csv file as DictReader
def read_csv(filename):
    """Read a CSV file and return a list of dictionaries."""
    with open(filename, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)
# function to convert week to days monday to sunday
def week_to_dates(y, w):
    monday = date.fromisocalendar(y, w, 1)
    sunday = date.fromisocalendar(y, w, 7)
    return monday, sunday
 
# get total cost 
def get_total_costs(data):
    total_cost = 0.0
    max_cost = 0.0
    max_incident = None
    for row in data:
        cost_string = row.get("cost_sek", "").strip()
        if cost_string:
            cost_value = float(cost_string.replace(" ", "").replace(",", "."))
            total_cost += cost_value
            if cost_value > max_cost:
                max_cost = cost_value
                max_incident = row
    return {
        "total_cost": total_cost,
        "max_cost": max_cost,
        "max_incident": max_incident
        }
 
#analyase data for incidents
def analyze_incidents(data):
    incidents = [
        SEVERITY_MAPPING.get(row.get("severity", "").lower(), 0)
        for row in data
    ]
    high_severity = [s for s in incidents if s >= 4]
     # get i severity by device
    high_sever_by_device = defaultdict(int)
    for row in data:
        severity_limit = SEVERITY_MAPPING.get(row.get("severity", "").lower(), 0)
        if severity_limit >= 4:
            device = row.get("device_hostname", "Unknown")
            high_sever_by_device[device] += 1
    average = sum(incidents) / len(incidents) if incidents else 0
    return {
        "total_incidents": len(incidents),
        "high_severity_count": len(high_severity),
        "average_severity": round(average, 2),
        "high_sever_by_device" : dict(high_sever_by_device)
    }
 
def write_results(output_filename, analysis):
    """Write analysis summary to a CSV output file."""
    with open(output_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Value"])
        for key, value in analysis.items():
            writer.writerow([key, value])
 
def main():
    input_file = "network_incidents.csv"  # Replace with your actual CSV path
    output_file = "incident_summary.csv"
    data = read_csv(input_file)
    # def extract date and week number
    weeks =  [int(row["week_number"]) for row in data if row.get("week_number")]
    #now get first and last week for the report 
    first_week = min(weeks)
    last_week = max(weeks)
    # now get year from ticket id
    ticket_number = data[0]["ticket_id"]
    year = int(ticket_number.split("-")[1])
    # now using the above week and date get analysis date and year
    start_date, _ = week_to_dates(year, first_week)
    _ , end_date = week_to_dates(year, first_week)
    month_number = start_date.month
    month_name = calendar.month_name[month_number]
    #create report 
    full_report =  beautify_it + "\n" + (" " * int(len(beautify_it)/3)) + comp_name + " - " + month_name + " " +  str(year) + "\n" + beautify_it + "\n"
    full_report += f"Analysperiod: {start_date} till {end_date} \n"
    # analyze data for incidents
    summary = analyze_incidents(data)
    # add total_incidents to report 
    full_report += f"Total incidents: {summary["total_incidents"]} st\n"
    #get total_cost
    get_cost = get_total_costs(data)
    total_cost = get_cost["total_cost"]
    max_cost = get_cost["max_cost"]
    max_incident=get_cost["max_incident"]
    high_cost_device_summary = None
    if (get_cost["max_incident"]):
        high_cost_device_summary = f"⚠ cost: Most expensive incident: {max_cost:.2f} SEK ({max_incident['device_hostname']} {max_incident['category']} failure)\n"
    full_report += f"Total cost : {total_cost:.2f} SEK \n"
    #add exective summary 
    full_report += f"\nEXECTIVE SUMMARY \n-------------------------------\n"
#    print("summary " + str(summary))
    # let get high_sever_by_device 
    top_severity_device = None
    top_severity_count = 0
    # now get high severity device with number of incidents
    if summary["high_sever_by_device"]:
        for device , count_high in summary["high_sever_by_device"].items():
            if count_high > top_severity_count:
               top_severity_device = device
               top_severity_count = count_high
    # last week data
    # get device with incidents from previous week 
    previous_week_data = [row for row in data if int(row["week_number"]) == last_week - 1]
    # Set of devices that had incidents last week
    last_week_devices ={row["device_hostname"] for row in previous_week_data}
    week_device_count = len(last_week_devices)
    week_device_report ="⚠ " + str(week_device_count) + " devices from last week's  problem devices have generated incidents \n"
 
               
    full_report += f"⚠ critical: {top_severity_device} has {top_severity_count} incidents (same unit that had warning last week!)\n"
    full_report += high_cost_device_summary
    full_report += week_device_report
    summary_to_write = dict(list(summary.items())[:-1])
    # write analyze_incidents to summary file
    write_results(output_file,  summary_to_write)
    #print(f"Processed {summary['total_incidents']} incidents.")
    #print(f"Results saved to '{output_file}'.")
    #print(full_report)
    # create report file for report
    with open('incident_analysis.txt', 'w', encoding='utf-8') as f:
       f.write(full_report)
if __name__ == "__main__":
    main()