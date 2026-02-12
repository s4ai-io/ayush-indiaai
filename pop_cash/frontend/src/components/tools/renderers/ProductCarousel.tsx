import React, { useState, useRef } from 'react';
import { ChevronLeft, ChevronRight, ShoppingBag, Tag, TrendingUp, Check, Plus } from "lucide-react";

const ProductCard = ({ product }: { product: any }) => {
    let images = product.image_list || (product.image ? [product.image] : []);
    if (typeof images === 'string') {
        images = images.split(',').map((img: string) => img.trim()).filter(Boolean);
    }
    const [currentImageIdx, setCurrentImageIdx] = useState(0);
    const [imageError, setImageError] = useState(false);

    const nextImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (currentImageIdx < images.length - 1) {
            setCurrentImageIdx((prev) => prev + 1);
            setImageError(false);
        }
    };

    const prevImage = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (currentImageIdx > 0) {
            setCurrentImageIdx((prev) => prev - 1);
            setImageError(false);
        }
    };

    const discount = product.savings_percentage
        ? Math.round(product.savings_percentage)
        : product.mrp && product.selling_price
            ? Math.round(((product.mrp - product.selling_price) / product.mrp) * 100)
            : 0;

    const [isAdded, setIsAdded] = useState(false);

    const handleAddToCart = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsAdded(true);
        // Simulate API call or global state update
        setTimeout(() => setIsAdded(false), 2000);
    };

    return (
        <div className="min-w-[280px] max-w-[280px] bg-card-bg rounded-2xl shadow-lg border border-white/10 overflow-hidden flex flex-col h-full snap-start group hover:border-neon-purple/30 transition-all duration-300 bg-black/20 text-sm overflow-none">
            {/* Image Area */}
            <div className="relative h-48 bg-white/5 group">
                {images.length > 0 && !imageError ? (
                    <img
                        src={images[currentImageIdx]}
                        alt={product.product_title}
                        className="w-full h-full object-contain p-4 mix-blend-normal transition-transform duration-500 group-hover:scale-105"
                        onError={() => {
                            console.error('Failed to load image:', images[currentImageIdx]);
                            setImageError(true);
                        }}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-500">
                        <ShoppingBag size={48} />
                    </div>
                )}

                {/* Add to Cart Overlay Button (Top Right) */}
                <button
                    onClick={handleAddToCart}
                    className={`absolute top-2 right-2 p-2 rounded-full shadow-md transition-all duration-300 z-10 ${isAdded
                        ? "bg-green-500 text-white scale-110"
                        : "bg-black/50 text-white hover:bg-neon-purple hover:text-white opacity-0 group-hover:opacity-100 backdrop-blur-sm"
                        }`}
                    title={isAdded ? "Added to Cart" : "Add to Cart"}
                >
                    {isAdded ? <Check size={18} /> : <Plus size={18} />}
                </button>

                {/* Image Navigation */}
                {images.length > 1 && (
                    <>
                        {currentImageIdx > 0 && (
                            <button
                                onClick={prevImage}
                                className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 p-1.5 rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70 text-white backdrop-blur-sm z-10"
                            >
                                <ChevronLeft size={16} />
                            </button>
                        )}
                        {currentImageIdx < images.length - 1 && (
                            <button
                                onClick={nextImage}
                                className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 p-1.5 rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70 text-white backdrop-blur-sm z-10"
                            >
                                <ChevronRight size={16} />
                            </button>
                        )}
                        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                            {images.map((_: any, idx: number) => (
                                <div
                                    key={idx}
                                    className={`w-1 h-1 rounded-full transition-all ${idx === currentImageIdx ? 'bg-neon-purple w-3' : 'bg-gray-500'}`}
                                />
                            ))}
                        </div>
                    </>
                )}

                {/* Badge */}
                {discount > 0 && (
                    <div className="absolute top-3 left-3 bg-red-500/90 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-sm flex items-center gap-1">
                        <TrendingUp size={12} /> {discount}% OFF
                    </div>
                )}
            </div>

            {/* Content Area */}
            <div className="p-4 flex flex-col flex-1">
                <div className="mb-1">
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                        {product.brand || product.brand_name || "Brand"}
                    </span>
                    <h3 className="font-semibold text-gray-200 text-sm leading-snug line-clamp-2 min-h-[2.5em]" title={product.product_title}>
                        {product.product_title || product.title || `Product ${product.product_id}`}
                    </h3>
                </div>

                <div className="mt-auto pt-3 border-t border-white/5">
                    <div className="flex items-end justify-between mb-2">
                        <div>
                            <div className="text-lg font-bold text-white">₹{product.selling_price || product.sp}</div>
                            {product.mrp && <div className="text-xs text-gray-500 line-through">₹{product.mrp}</div>}
                        </div>
                        {product.popcoins_required && (
                            <div className="text-right">
                                <div className="text-xs font-medium text-neon-purple flex items-center justify-end gap-1">
                                    <div className="w-4 h-4 rounded-full bg-neon-purple/20 flex items-center justify-center text-[10px]">P</div>
                                    {product.popcoins_required}
                                </div>
                                <div className="text-[10px] text-gray-500">PopCoins</div>
                            </div>
                        )}
                    </div>

                    <div className="flex gap-2 mt-2">
                        {product.value_efficiency_score && (
                            <div className="flex-1 bg-white/5 rounded-lg p-2.5 flex items-center justify-between border border-white/5">
                                <span className="text-[10px] font-semibold text-gray-400 uppercase">Score</span>
                                <span className="text-xs font-bold text-neon-blue">{product.value_efficiency_score.toFixed(1)}/5</span>
                            </div>
                        )}
                        <button
                            onClick={handleAddToCart}
                            className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1 shadow-sm ${isAdded
                                ? "bg-green-500/20 text-green-400 border border-green-500/30"
                                : "bg-white text-black hover:bg-neon-purple hover:text-white hover:border-neon-purple"
                                }`}
                        >
                            {isAdded ? (
                                <>
                                    <Check size={14} /> Added
                                </>
                            ) : (
                                "Add to Cart"
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export const ProductCarousel = ({ products }: { products: any[] }) => {
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [canScrollLeft, setCanScrollLeft] = useState(false);
    const [canScrollRight, setCanScrollRight] = useState(true);

    const checkScroll = () => {
        if (scrollContainerRef.current) {
            const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
            setCanScrollLeft(scrollLeft > 10);
            setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 10);
        }
    };

    const scroll = (direction: 'left' | 'right') => {
        if (scrollContainerRef.current) {
            const scrollAmount = 300; // Approx one card width
            scrollContainerRef.current.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
            // checkScroll will be triggered by the onScroll event
        }
    };

    React.useEffect(() => {
        checkScroll();
        window.addEventListener('resize', checkScroll);
        return () => window.removeEventListener('resize', checkScroll);
    }, [products]);

    if (!products || products.length === 0) return null;

    return (
        <div className="relative group/carousel -mx-2">
            {/* Carousel Controls */}
            {canScrollLeft && (
                <div className="absolute top-1/2 -translate-y-1/2 left-0 z-10 -ml-3">
                    <button
                        onClick={() => scroll('left')}
                        className="bg-card-bg text-white p-2 rounded-full shadow-lg border border-white/10 hover:bg-white/10 transition-all opacity-0 group-hover/carousel:opacity-100"
                    >
                        <ChevronLeft size={20} />
                    </button>
                </div>
            )}
            {canScrollRight && (
                <div className="absolute top-1/2 -translate-y-1/2 right-0 z-10 -mr-3">
                    <button
                        onClick={() => scroll('right')}
                        className="bg-card-bg text-white p-2 rounded-full shadow-lg border border-white/10 hover:bg-white/10 transition-all opacity-0 group-hover/carousel:opacity-100"
                    >
                        <ChevronRight size={20} />
                    </button>
                </div>
            )}

            {/* Scrollable Container */}
            <div
                ref={scrollContainerRef}
                onScroll={checkScroll}
                className={`flex gap-4 overflow-x-auto pb-6 pt-2 px-2 scrollbar-none snap-x snap-mandatory ${products.length === 1 ? 'justify-center' : ''}`}
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
            >
                {products.map((product, idx) => (
                    <ProductCard key={idx} product={product} />
                ))}
            </div>
        </div>
    );
};
