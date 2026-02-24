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
            <div className="flex items-center gap-1 bg-transparent hover:bg-primary/5 rounded-full px-2 py-1 transition-all cursor-pointer border border-transparent hover:border-primary/20">
                <Languages className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
                <select
                    value={selectedLanguage}
                    onChange={(e) => onLanguageChange(e.target.value)}
                    className="appearance-none bg-transparent border-none text-xs font-medium text-muted-foreground group-hover:text-primary focus:ring-0 focus:outline-none cursor-pointer pr-4 min-w-[70px] transition-colors"
                    style={{ backgroundImage: 'none' }}
                >
                    {INDIAN_LANGUAGES.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                            {lang.native}
                        </option>
                    ))}
                </select>
                <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-3 h-3 text-muted-foreground group-hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </div>
        </div>
    );
}
