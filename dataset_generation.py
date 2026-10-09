import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import pickle
import os

def generate_synthetic_data(n_samples):
    categories = ['Road/Pothole', 'Water Supply', 'Garbage/Sanitation', 'Street Lights', 'Drainage ', ' Human security']
    
    data = []
    for _ in range(n_samples):
        cat = np.random.choice(categories)
        if cat == 'Road/Pothole':
            desc = np.random.choice([
                      "Huge pothole on the main road causing traffic.",
    "Road is completely broken after the rains.",
    "Very deep pothole near the intersection.",
    "The street has not been repaired, multiple potholes.",
    "Large pothole causing difficulty for vehicles.",
    "Deep pothole creating a serious road safety hazard.",
    "Multiple potholes reported along the main road.",
    "Damaged road surface causing traffic congestion.",
    "Road has cracks and uneven surfaces after heavy rain.",
    "Potholes near a school or busy pedestrian area.",
    "Broken road causing vehicles to slow down suddenly.",
    "Severely damaged section of road requires urgent repair."
            ])
            priority = 'High' if 'huge' in desc or 'deep' in desc or 'serious' in desc or 'school' in desc or 'urgent' in desc or 'traffic'  else 'Medium'


        elif cat == 'Water Supply':
            desc = np.random.choice([
                "No water supply since 3 days.",
                "Dirty water coming from the taps.",
                "Low pressure in water supply line.",
                "Pipeline broken and water is leaking."
            ])
            priority = 'High' if 'No water' in desc or 'broken' in desc else 'Medium'


        elif cat == 'Garbage/Sanitation':
            desc = np.random.choice([
                "Garbage has not been collected for a week.",
                "People are dumping trash on the open plot.",
                "Foul smell from the uncollected garbage bin.",
                "Street sweeping is not happening regularly."
            ])
            priority = 'Medium' if 'week' not in desc else 'High'


        elif cat == 'Street Lights':
            desc = np.random.choice([
                "Street light is not working in our lane.",
                "The entire street is dark, causing safety issues.",
                "Pole light flickering continuously."
            ])
            priority = 'Low' if 'flickering' in desc else 'Medium'


        elif cat == 'Drainage':
            desc = np.random.choice([
                "Open manhole in the middle of the road.",
                "Drainage water overflowing on the street.",
                "Sewage line blocked and smelling bad."
            ])
            priority = 'High' if 'Open manhole' in desc else 'Medium'


        elif cat == 'Human Security':

          desc = np.random.choice([
        "Rape or sexual assault incident reported.",
        "Person facing harassment in a public area.",
        "Physical assault or violent behavior reported.",
        "Missing person reported by family members.",
        "Person injured or in immediate danger.",
        "Suspicious activity reported in a public place.",
        "Child or vulnerable person requiring assistance.",
        "Domestic violence incident reported.",
        "Person being threatened or intimidated.",
        "Human trafficking or exploitation suspected.",
        "Person unconscious or requiring emergency help.",
        "Public fight or violent confrontation reported."
    ])

        priority = 'High' if 'rape' in desc or 'assault' in desc or 'injured' in desc or 'immediate danger' in desc or 'violence' in desc or 'trafficking' in desc or 'unconscious' in desc or 'threatened' in desc else 'Medium'

        data.append({'description': desc, 'category': cat, 'priority': priority})
    
    return pd.DataFrame(data)

print(generate_synthetic_data(500))