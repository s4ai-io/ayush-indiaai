'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, ChevronDown, X, Loader2 } from 'lucide-react';

interface DiseaseSearchDropdownProps {
    value: string;
    onChange: (value: string) => void;
    required?: boolean;
    placeholder?: string;
    className?: string;
}

export function DiseaseSearchDropdown({
    value,
    onChange,
    required = false,
    placeholder = 'Search or select a disease...',
    className = '',
}: DiseaseSearchDropdownProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState(value);
    const [allDiseases, setAllDiseases] = useState<string[]>([]);
    const [filteredDiseases, setFilteredDiseases] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [highlightedIndex, setHighlightedIndex] = useState(-1);

    const wrapperRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLUListElement>(null);

    // Fetch all diseases once on mount
    useEffect(() => {
        const fetchDiseases = async () => {
            setLoading(true);
            try {
                const res = await fetch('/api/ml/diseases');
                const data = await res.json();
                setAllDiseases(data.diseases || []);
            } catch (err) {
                console.error('Failed to fetch diseases:', err);
                setAllDiseases([]);
            } finally {
                setLoading(false);
            }
        };
        fetchDiseases();
    }, []);

    // Filter locally when search query changes
    useEffect(() => {
        if (!searchQuery.trim()) {
            setFilteredDiseases(allDiseases);
        } else {
            const q = searchQuery.toLowerCase();
            setFilteredDiseases(
                allDiseases.filter(d => d.toLowerCase().includes(q))
            );
        }
        setHighlightedIndex(-1);
    }, [searchQuery, allDiseases]);

    // Sync external value changes
    useEffect(() => {
        setSearchQuery(value);
    }, [value]);

    // Close on outside click
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
                setIsOpen(false);
                // If typed text doesn't match any disease, keep whatever was selected
                if (value && searchQuery !== value) {
                    setSearchQuery(value);
                }
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [value, searchQuery]);

    // Scroll highlighted item into view
    useEffect(() => {
        if (highlightedIndex >= 0 && listRef.current) {
            const items = listRef.current.querySelectorAll('li');
            items[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
        }
    }, [highlightedIndex]);

    const selectDisease = useCallback((disease: string) => {
        setSearchQuery(disease);
        onChange(disease);
        setIsOpen(false);
        setHighlightedIndex(-1);
    }, [onChange]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setSearchQuery(val);
        onChange(val);
        setIsOpen(true);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen) {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                setIsOpen(true);
                e.preventDefault();
            }
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setHighlightedIndex(prev =>
                    prev < filteredDiseases.length - 1 ? prev + 1 : 0
                );
                break;
            case 'ArrowUp':
                e.preventDefault();
                setHighlightedIndex(prev =>
                    prev > 0 ? prev - 1 : filteredDiseases.length - 1
                );
                break;
            case 'Enter':
                e.preventDefault();
                if (highlightedIndex >= 0 && highlightedIndex < filteredDiseases.length) {
                    selectDisease(filteredDiseases[highlightedIndex]);
                }
                break;
            case 'Escape':
                setIsOpen(false);
                setHighlightedIndex(-1);
                break;
        }
    };

    const clearSelection = () => {
        setSearchQuery('');
        onChange('');
        inputRef.current?.focus();
        setIsOpen(true);
    };

    const highlightMatch = (text: string, query: string) => {
        if (!query.trim()) return text;
        const idx = text.toLowerCase().indexOf(query.toLowerCase());
        if (idx === -1) return text;
        return (
            <>
                {text.slice(0, idx)}
                <span className="font-bold text-purple-700 bg-purple-50">{text.slice(idx, idx + query.length)}</span>
                {text.slice(idx + query.length)}
            </>
        );
    };

    return (
        <div ref={wrapperRef} className={`relative ${className}`}>
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                    ref={inputRef}
                    type="text"
                    value={searchQuery}
                    onChange={handleInputChange}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    required={required}
                    className="w-full pl-9 pr-16 p-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all text-sm"
                    autoComplete="off"
                    role="combobox"
                    aria-expanded={isOpen}
                    aria-haspopup="listbox"
                    aria-autocomplete="list"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    {loading && <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />}
                    {searchQuery && !loading && (
                        <button
                            type="button"
                            onClick={clearSelection}
                            className="p-0.5 hover:bg-slate-100 rounded transition-colors"
                            tabIndex={-1}
                        >
                            <X className="w-3.5 h-3.5 text-slate-400" />
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={() => { setIsOpen(!isOpen); inputRef.current?.focus(); }}
                        className="p-0.5 hover:bg-slate-100 rounded transition-colors"
                        tabIndex={-1}
                    >
                        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                    </button>
                </div>
            </div>

            {isOpen && (
                <ul
                    ref={listRef}
                    className="absolute z-50 w-full mt-1 max-h-60 overflow-y-auto bg-white border border-slate-200 rounded-lg shadow-lg py-1"
                    role="listbox"
                >
                    {loading ? (
                        <li className="px-3 py-2 text-sm text-slate-400 text-center flex items-center justify-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin" /> Loading diseases...
                        </li>
                    ) : filteredDiseases.length === 0 ? (
                        <li className="px-3 py-2 text-sm text-slate-400 text-center">
                            No matching diseases found
                        </li>
                    ) : (
                        filteredDiseases.map((disease, idx) => (
                            <li
                                key={disease}
                                role="option"
                                aria-selected={highlightedIndex === idx}
                                onClick={() => selectDisease(disease)}
                                onMouseEnter={() => setHighlightedIndex(idx)}
                                className={`px-3 py-2 text-sm cursor-pointer transition-colors ${highlightedIndex === idx
                                        ? 'bg-purple-50 text-purple-900'
                                        : value === disease
                                            ? 'bg-purple-50/50 text-purple-800'
                                            : 'text-slate-700 hover:bg-slate-50'
                                    }`}
                            >
                                {highlightMatch(disease, searchQuery)}
                            </li>
                        ))
                    )}
                </ul>
            )}
        </div>
    );
}
