import csv

def read_csv(filename):
    """Read a CSV file and return a list of dictionaries."""
    with open(filename, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def analyze_incidents(data):
    """Example analysis: count high severity incidents."""
    # Convert severity field to int, handle missing values safely
    incidents = [int(row["severity"]) for row in data if row["severity"].isdigit()]
    high_severity = [s for s in incidents if s >= 4]
    average = sum(incidents) / len(incidents) if incidents else 0
    return {
        "total_incidents": len(incidents),
        "high_severity_count": len(high_severity),
        "average_severity": round(average, 2)
    }

def write_results(output_filename, analysis):
    """Write analysis summary to a CSV output file."""
    with open(output_filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Value"])
        for key, value in analysis.items():
            writer.writerow([key, value])

def main():
    input_file = "incidents.csv"  # Replace with your actual CSV path
    output_file = "incident_summary.csv"

    data = read_csv(input_file)
    summary = analyze_incidents(data)
    write_results(output_file, summary)

    print(f"Processed {summary['total_incidents']} incidents.")
    print(f"Results saved to '{output_file}'.")

if __name__ == "_main_":
    main()