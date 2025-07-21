def detect_misrepresentation(key_info, policy_data):
    try:
        incident_date = key_info.get("Incident Date")
        dol = policy_data["dol"]
        policy_date = policy_data["policy_date"]

        dol_dt = dol
        pol_dt = policy_date

        misrep_flag = False
        reason = ""

        if incident_date:
            from datetime import datetime
            try:
                incident_dt = datetime.strptime(incident_date, "%B %d")
                incident_dt = incident_dt.replace(year=pol_dt.year)
                if incident_dt < pol_dt:
                    misrep_flag = True
                    reason = "Incident occurred before policy inception."
                elif incident_dt != dol_dt:
                    misrep_flag = True
                    reason = "Date of Loss and incident date mismatch."
            except:
                pass

        return {
            "misrepresentation_found": "Yes" if misrep_flag else "No",
            "reason": reason
        }
    except:
        return {
            "misrepresentation_found": "No",
            "reason": ""
        }
