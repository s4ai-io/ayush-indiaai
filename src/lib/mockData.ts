
// Synthetic Real-World Data for AYUSH Health System

// 1. Disease Trends: Seasonal & Regional specifics in India
export const diseaseTrendsData = [
  { month: 'Jan (Magha)', flu: 850, covid: 420, dengue: 120, arthritis: 4500, asthma: 3200 }, // Winter: Vata aggravation (Joints/Respiratory)
  { month: 'Feb (Phalguna)', flu: 1200, covid: 500, dengue: 150, arthritis: 4100, asthma: 2800 },
  { month: 'Mar (Chaitra)', flu: 3500, covid: 1200, dengue: 200, arthritis: 3000, asthma: 2100 }, // Spring: Kapha melting (Respiratory flu)
  { month: 'Apr (Vaisakha)', flu: 1500, covid: 800, dengue: 350, arthritis: 2200, asthma: 1500 },
  { month: 'May (Jyeshtha)', flu: 900, covid: 300, dengue: 500, arthritis: 1800, asthma: 1200 }, // Summer: Pitta (Heat)
  { month: 'Jun (Ashadha)', flu: 1100, covid: 400, dengue: 1800, arthritis: 2400, asthma: 1800 }, // Monsoon start: Vata (Joints) & Water-borne
  { month: 'Jul (Shravana)', flu: 2500, covid: 600, dengue: 4500, arthritis: 3500, asthma: 2500 }, // Peak Monsoon
];

// 2. Public Health Forecast: Specific Indian Regions & Weather Correlations
export const riskForecastData = [
  {
    region: 'Kerala (South)',
    riskLevel: 'Moderate',
    threat: 'Monsoon Fevers (Vata-Kapha)',
    probability: 65,
    details: 'High humidity aggravating Kapha. Risk of vector-borne diseases.'
  },
  {
    region: 'Rajasthan (West)',
    riskLevel: 'High',
    threat: 'Heat Stroke (Pitta)',
    probability: 92,
    details: 'Extreme temperatures causing dehydration and heat exhaustion.'
  },
  {
    region: 'Uttar Pradesh (North)',
    riskLevel: 'High',
    threat: 'Respiratory Infections',
    probability: 78,
    details: 'Pollution/Smog coupled with seasonal change triggering Asthma.'
  },
  {
    region: 'Assam (North East)',
    riskLevel: 'Moderate',
    threat: 'Malaria',
    probability: 58,
    details: 'Post-flood vector proliferation.'
  },
  {
    region: 'Maharashtra (Central)',
    riskLevel: 'Low',
    threat: 'Viral Flu',
    probability: 35,
    details: 'Stable weather currently.'
  },
];

// 3. Personalized Recommendations: Detailed Classical Protocols
// Categorized by condition rather than just Prakriti, utilizing Prakriti as a modifier.
export const conditionProtocols = {
  'Diabetes (Madhumeha)': {
    Vata: {
      herbs: ['Ashwagandha (Withania somnifera)', 'Guduchi (Tinospora cordifolia)'],
      diet: 'Avoid dry/cold foods. Favor whole grains like Barley (Yava).',
      yoga: ['Surya Namaskar', 'Paschimottanasana'],
      lifestyle: 'Oil massage (Abhyanga), warm baths.'
    },
    Pitta: {
      herbs: ['Amalaki (Emblica officinalis)', 'Neem (Azadirachta indica)'],
      diet: 'Bitter/Astringent tastes. Avoid spicy/sour.',
      yoga: ['Chandra Namaskar', 'Sheetali Pranayama'],
      lifestyle: 'Cool showers, moonlight walks.'
    },
    Kapha: {
      herbs: ['Triphala', 'Shilajit', 'Turmeric (Haridra)'],
      diet: 'Light, dry foods. Millet (Bajra/Jowar). Avoid dairy/sugar.',
      yoga: ['Kapalabhati', 'Mandukasana', 'Ardha Matsyendrasana'],
      lifestyle: 'Vigorous exercise (Vyayama), dry massage (Udvartana).'
    }
  },
  'Hypertension (Raktagata Vata)': {
    General: {
      herbs: ['Sarpagandha (Rauvolfia serpentina)', 'Arjuna (Terminalia arjuna)', 'Brahmi'],
      diet: 'Low salt, plenty of seasonal fruits (pomegranate/Dadima).',
      yoga: ['Shavasana', 'Anulom Vilom', 'Bhramari Pranayama'],
      lifestyle: 'Stress management, adequate sleep (Nidra), meditation.'
    }
  },
  'Arthritis (Amavata/Sandhivata)': {
    General: {
      herbs: ['Shallaki (Boswellia)', 'Guggulu formulations (Yograj Guggulu)', 'Rasna'],
      diet: 'Warm, cooked foods with Ginger/Garlic. Avoid curd/heavy pulses.',
      yoga: ['Pawanamuktasana series', 'Gentle joint rotations'],
      lifestyle: 'Fomentation (Swedana), prevent exposure to cold wind.'
    }
  }
};

// Helper for the frontend to get simple string-based suggestions if needed
export const ayushRecommendations = {
  // Maintaining backward compatibility structure if needed
  Vata: conditionProtocols['Diabetes (Madhumeha)']['Vata'],
  Pitta: conditionProtocols['Diabetes (Madhumeha)']['Pitta'],
  Kapha: conditionProtocols['Diabetes (Madhumeha)']['Kapha'],
  General: conditionProtocols['Hypertension (Raktagata Vata)']['General']
};
