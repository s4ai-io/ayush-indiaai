import React from "react";
import { IoArrowForward } from "react-icons/io5";
import "../styles/BrandCard.css";

const BrandCard = ({ brand }) => {
  // Extract data from new Strapi structure with fallbacks
  const logo = brand.attributes?.round_logo?.data?.attributes?.url || "";
  const name = brand.attributes?.brand_name || "";
  const category =
    brand.attributes?.brand_categories?.data?.[0]?.attributes?.categoryname ||
    "Fashion";
  const discount = `${brand.attributes?.discount_percentage || 0}% off`;
  const redirectionUrl = brand.attributes?.redirection_url || "#";

  // Handler for card click/navigation
  const handleRedirect = () => {
    if (redirectionUrl && redirectionUrl !== "#") {
      window.open(redirectionUrl, "_blank");
    }
  };

  return (
    <div
      className="brand-card"
      role="button"
      tabIndex={0}
      onClick={handleRedirect}
      onKeyPress={(e) => e.key === "Enter" && handleRedirect()}
    >
      <div className="brand-card-inner">
        <div className="brand-card-logo">
          <img src={logo} alt={name} className="brand-logo" loading="lazy" />
        </div>

        <div className="brand-card-content">
          <div className="brand-header-info">
            <p className="brand-info-label">Get upto</p>
            <h3 className="brand-discount">{discount}</h3>
          </div>

          <div className="brand-footer-info">
            <h2 className="brand-name">{name}</h2>
            <p className="brand-category">{category}</p>
          </div>
        </div>

        <div
          className="brand-card-arrow"
          onClick={(e) => {
            e.stopPropagation();
            handleRedirect();
          }}
        >
          <IoArrowForward size={24} />
        </div>
      </div>
    </div>
  );
};

export default BrandCard;
