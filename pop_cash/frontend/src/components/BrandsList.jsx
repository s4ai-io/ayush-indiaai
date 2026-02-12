import React, { useState, useMemo } from "react";
import BrandCard from "./BrandCard";
import SearchFilter from "./SearchFilter";
import "../styles/BrandsList.css";

const BrandsList = ({ brands }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  // Transform new data structure to old format for filtering
  const transformedBrands = useMemo(() => {
    return brands.map((brand) => ({
      id: brand.id,
      name: brand.attributes?.brand_name || "",
      category:
        brand.attributes?.brand_categories?.data?.[0]?.attributes
          ?.categoryname || "Fashion",
      description: brand.attributes?.about_brand || "",
      logo: brand.attributes?.round_logo?.data?.attributes?.url || "",
      discount: `${brand.attributes?.discount_percentage || 0}% off`,
      deal: brand.attributes?.burn_callout || "",
      popcoin_rate: brand.attributes?.earn_callout || "",
      about: brand.attributes?.sub_title || "",
      // Keep original data for reference
      original: brand,
    }));
  }, [brands]);

  // Extract categories from transformed brands
  const categories = useMemo(() => {
    const cats = new Set(transformedBrands.map((brand) => brand.category));
    return Array.from(cats).sort();
  }, [transformedBrands]);

  // Filter based on search and category
  const filteredBrands = useMemo(() => {
    return transformedBrands.filter((brand) => {
      const matchesSearch =
        brand.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        brand.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        brand.category.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCategory =
        selectedCategory === "all" || brand.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [transformedBrands, searchTerm, selectedCategory]);

  return (
    <div className="brands-list-container">
      <SearchFilter
        onSearchChange={setSearchTerm}
        onCategoryChange={setSelectedCategory}
        categories={categories}
      />

      {filteredBrands.length > 0 ? (
        <div className="brands-grid">
          {filteredBrands.map((brand) => (
            <BrandCard key={brand.id} brand={brand.original} />
          ))}
        </div>
      ) : (
        <div className="no-results">
          <p>No brands found matching your search.</p>
          <p className="no-results-subtitle">
            Try adjusting your filters or search term.
          </p>
        </div>
      )}
    </div>
  );
};

export default BrandsList;
