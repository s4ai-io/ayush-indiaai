import React, { useState, useEffect } from 'react';
import Header from '../../components/Header';
import BrandsList from '../../components/BrandsList';
import '../../styles/AllBrands.css';
import brandsData from '../../data/brandsData.json';

const AllBrands = () => {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadBrands = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 300));
        setBrands(brandsData.brands);
      } catch (error) {
        console.error('Error loading brands:', error);
      } finally {
        setLoading(false);
      }
    };

    loadBrands();
  }, []);

  if (loading) {
    return (
      <div className="all-brands-page">
        <Header />
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading brands...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="all-brands-page">
      <Header />
      <BrandsList brands={brands} />
    </div>
  );
};

export default AllBrands;
