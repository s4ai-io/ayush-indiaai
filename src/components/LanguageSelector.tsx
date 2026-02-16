import React from 'react';
import { Languages } from 'lucide-react';

export const INDIAN_LANGUAGES = [
    { code: 'en-IN', name: 'English (India)', native: 'English' },
    { code: 'hi-IN', name: 'Hindi', native: 'हिन्दी' },
    { code: 'mr-IN', name: 'Marathi', native: 'मराठी' },
    { code: 'gu-IN', name: 'Gujarati', native: 'ગુજરાતી' },
    { code: 'ta-IN', name: 'Tamil', native: 'தமிழ்' },
    { code: 'te-IN', name: 'Telugu', native: 'తెలుగు' },
    { code: 'kn-IN', name: 'Kannada', native: 'ಕನ್ನಡ' },
    { code: 'ml-IN', name: 'Malayalam', native: 'മലയാളം' },
    { code: 'bn-IN', name: 'Bengali', native: 'বাংলা' },
    { code: 'pa-IN', name: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
    { code: 'or-IN', name: 'Odia', native: 'ଓଡ଼ିଆ' },
];

interface LanguageSelectorProps {
    selectedLanguage: string;
    onLanguageChange: (langCode: string) => void;
}

export function LanguageSelector({ selectedLanguage, onLanguageChange }: LanguageSelectorProps) {
    return (
        <div className="relative group">
            <div className="flex items-center gap-2 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-full px-3 py-1.5 shadow-sm hover:shadow-md transition-all cursor-pointer">
                <Languages className="w-4 h-4 text-teal-600" />
                <select
                    value={selectedLanguage}
                    onChange={(e) => onLanguageChange(e.target.value)}
                    className="appearance-none bg-transparent border-none text-sm font-medium text-gray-700 focus:ring-0 focus:outline-none cursor-pointer pr-6 min-w-[100px]"
                    style={{ backgroundImage: 'none' }}
                >
                    {INDIAN_LANGUAGES.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                            {lang.native} ({lang.name})
                        </option>
                    ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </div>
        </div>
    );
}
