import React, { useState, useRef, useEffect } from "react";
import { FiSearch, FiChevronDown } from "react-icons/fi";
import "../styles/SearchFilter.css";

const SearchFilter = ({ onSearchChange, onCategoryChange, categories }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Pick a Category");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchChange = (e) => {
    const term = e.target.value;
    setSearchTerm(term);
    onSearchChange(term);
  };

  const handleCategoryClick = (category) => {
    setSelectedCategory(category);
    setIsDropdownOpen(false);
    onCategoryChange(category);
  };

  return (
    <div className="search-filter-container">
      <h1 className="brand-spotlight-title">Brand Spotlight</h1>

      <div className="filter-controls">
        <div className="search-box">
          <FiSearch className="search-icon" size={20} />
          <input
            type="text"
            placeholder="Search brands..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="search-input"
          />
        </div>

        <div className="category-dropdown" ref={dropdownRef}>
          <button
            className="dropdown-toggle"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <span>{selectedCategory}</span>
            <FiChevronDown
              className={`dropdown-icon ${isDropdownOpen ? "open" : ""}`}
            />
          </button>

          {isDropdownOpen && (
            <div className="dropdown-menu">
              {categories.map((category) => (
                <button
                  key={category}
                  className="dropdown-item"
                  onClick={() => handleCategoryClick(category)}
                >
                  {category}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchFilter;
