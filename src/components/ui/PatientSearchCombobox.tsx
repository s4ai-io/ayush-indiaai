'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Loader2, User, Phone, X } from 'lucide-react';

export interface PatientSearchResult {
    id: string;
    first_name?: string;
    firstName?: string;
    last_name?: string;
    lastName?: string;
    mobile?: string;
    age?: string | number;
    gender?: string;
    marital_status?: string;
    maritalStatus?: string;
    address?: string;
    city?: string;
    state?: string;
    pincode?: string;
    occupation?: string;
    blood_group?: string;
    bloodGroup?: string;
    id_type?: string;
    idType?: string;
    id_number?: string;
    idNumber?: string;
}

interface PatientSearchComboboxProps {
    onSelect: (patient: PatientSearchResult) => void;
    placeholder?: string;
    className?: string;
}

export function PatientSearchCombobox({
    onSelect,
    placeholder = 'Search by Name or Mobile No...',
    className = ''
}: PatientSearchComboboxProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [results, setResults] = useState<PatientSearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [highlightedIndex, setHighlightedIndex] = useState(-1);

    const wrapperRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLUListElement>(null);

    // Debounced search effect
    useEffect(() => {
        const fetchResults = async () => {
            if (!searchQuery.trim() || searchQuery.length < 3) {
                setResults([]);
                return;
            }

            setLoading(true);
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${API_URL}/api/patients/search?q=${encodeURIComponent(searchQuery)}`);
                if (res.ok) {
                    const data = await res.json();
                    setResults(data || []);
                    if (data && data.length > 0) {
                        setIsOpen(true);
                    }
                }
            } catch (err) {
                console.error('Failed to search patients:', err);
                setResults([]);
            } finally {
                setLoading(false);
            }
        };

        const timeoutId = setTimeout(() => {
            fetchResults();
        }, 300); // 300ms debounce

        return () => clearTimeout(timeoutId);
    }, [searchQuery]);

    // Close on outside click
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Scroll highlighted item into view
    useEffect(() => {
        if (highlightedIndex >= 0 && listRef.current) {
            const items = listRef.current.querySelectorAll('li');
            items[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
        }
    }, [highlightedIndex]);

    const handleSelect = useCallback((patient: PatientSearchResult) => {
        const name = `${patient.first_name || patient.firstName || ''} ${patient.last_name || patient.lastName || ''}`.trim();
        setSearchQuery(name);
        onSelect(patient);
        setIsOpen(false);
        setHighlightedIndex(-1);
    }, [onSelect]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen && results.length > 0) {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                setIsOpen(true);
                e.preventDefault();
            }
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setHighlightedIndex(prev => prev < results.length - 1 ? prev + 1 : 0);
                break;
            case 'ArrowUp':
                e.preventDefault();
                setHighlightedIndex(prev => prev > 0 ? prev - 1 : results.length - 1);
                break;
            case 'Enter':
                e.preventDefault();
                if (highlightedIndex >= 0 && highlightedIndex < results.length) {
                    handleSelect(results[highlightedIndex]);
                } else if (results.length === 1) {
                    // Auto-select if there's only one result
                    handleSelect(results[0]);
                }
                break;
            case 'Escape':
                setIsOpen(false);
                setHighlightedIndex(-1);
                break;
        }
    };

    const clearSearch = () => {
        setSearchQuery('');
        setResults([]);
        setIsOpen(false);
        inputRef.current?.focus();
    };

    return (
        <div ref={wrapperRef} className={`relative ${className}`}>
            <div className="relative flex items-center w-full">
                <Search className="absolute left-3 w-4 h-4 text-emerald-500 pointer-events-none" />
                <input
                    ref={inputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                        setSearchQuery(e.target.value);
                        setIsOpen(true);
                    }}
                    onFocus={() => {
                        if (results.length > 0 || (searchQuery.length >= 3 && loading)) {
                            setIsOpen(true);
                        }
                    }}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className="w-full pl-9 pr-10 py-2.5 bg-white border border-emerald-200 rounded-lg shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all text-sm text-slate-800 placeholder:text-slate-400"
                    autoComplete="off"
                    role="combobox"
                    aria-expanded={isOpen}
                    aria-haspopup="listbox"
                />
                <div className="absolute right-3 flex items-center">
                    {loading ? (
                        <Loader2 className="w-4 h-4 text-emerald-500 animate-spin" />
                    ) : searchQuery ? (
                        <button
                            type="button"
                            onClick={clearSearch}
                            className="p-1 hover:bg-slate-100 rounded-full transition-colors text-slate-400 hover:text-slate-600"
                            title="Clear search"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    ) : null}
                </div>
            </div>

            {isOpen && (searchQuery.length >= 3) && (
                <div className="absolute top-[calc(100%+0.5rem)] left-0 z-[100] w-full">
                    <ul
                        ref={listRef}
                        className="max-h-72 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-2xl py-2 ring-1 ring-black/5"
                        role="listbox"
                    >
                        {loading && results.length === 0 ? (
                            <li className="px-4 py-3 text-sm text-emerald-600 text-center flex justify-center items-center">
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Fetching records...
                            </li>
                        ) : results.length === 0 ? (
                            <li className="px-4 py-4 text-sm text-slate-500 text-center bg-slate-50 mx-2 rounded-lg border border-dashed border-slate-200">
                                No matching patients found.
                            </li>
                        ) : (
                            results.map((patient, idx) => (
                                <li
                                    key={patient.id || idx}
                                    role="option"
                                    aria-selected={highlightedIndex === idx}
                                    onClick={() => handleSelect(patient)}
                                    onMouseEnter={() => setHighlightedIndex(idx)}
                                    className={`px-4 py-3 cursor-pointer transition-colors border-l-2 ${highlightedIndex === idx
                                        ? 'bg-emerald-50 border-emerald-500'
                                        : 'border-transparent hover:bg-slate-50'
                                        }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="font-semibold text-slate-800 flex items-center text-sm">
                                                <User className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                                                {patient.first_name || patient.firstName} {patient.last_name || patient.lastName}
                                            </div>
                                            <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                                                <span className="flex items-center text-emerald-700 font-medium">
                                                    <Phone className="w-3 h-3 mr-1" />
                                                    {patient.mobile || "N/A"}
                                                </span>
                                                {patient.age && <span>{patient.age} yrs</span>}
                                                {patient.gender && <span>{patient.gender}</span>}
                                            </div>
                                        </div>
                                    </div>
                                </li>
                            ))
                        )}
                    </ul>
                </div>
            )}
        </div>
    );
}
