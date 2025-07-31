
from django.db import models

Employment_Type = [
    ("Full Time","Full Time" ),
    ("Part Time","Part Time" ),
    ("Contract","Contract" ),
]


Experience_Level = [
    ("Entry Level", "Entry Level"),
    ("Mid Level", "Mid Level"),
    ("Senior Level", "Senior Level"),
   ]


LocationTypeChoice = [
    ("Onsite", "Onsite"),
    ("Hybrid", "Hybrid"),
    ("Remote", "Remote"),    
]

class ApplicationStatus(models.TextChoices):
    APPLIED = ("APPLIED","APPLIED")
    REJECTED = ("REJECTED","REJECTED")
    INTERVIEW = ("INTERVIEW","INTERVIEW")