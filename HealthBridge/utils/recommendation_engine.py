class RecommendationEngine:
    def __init__(self, profile, medical_records):
        self.profile = profile
        self.records = medical_records

    def generate(self):
        recs = []
        if self.profile.age > 60:
            recs.append("Consider senior citizen health schemes.")
        if any("fever" in r.description.lower() for r in self.records):
            recs.append("Monitor for recurring fever symptoms.")
        if self.profile.gender == "Female":
            recs.append("Eligible for women-specific wellness programs.")
        return recs