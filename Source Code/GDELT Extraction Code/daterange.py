from datetime import datetime, timedelta

def generate_GDELT_timestamps(start_date, end_date):
    """
    Generates GDELT GKG timestamps every 15 minutes between two dates.
    """
    current = start_date
    while current <= end_date:
        yield current.strftime("%Y%m%d%H%M%S")
        current += timedelta(minutes=15)
        # for debugging
        # print("Generated timestamps:", current)