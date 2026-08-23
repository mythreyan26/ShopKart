import React, { useState, useEffect, createContext, useContext } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  Image,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  FlatList,
  Alert,
  SafeAreaView,
  StatusBar,
  Dimensions,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import api, { BASE_URL } from './src/services/api';

const { width } = Dimensions.get('window');

// -------------------------------------------------------------
// App State Context
// -------------------------------------------------------------
const AppContext = createContext();

export const useApp = () => useContext(AppContext);

// Helper for full image URLs
const getImgUrl = (path) => {
  if (!path) return 'https://via.placeholder.com/300?text=ShopKart';
  if (path.startsWith('http')) return path;
  return `${BASE_URL}${path.startsWith('/') ? '' : '/'}${path}`;
};

// -------------------------------------------------------------
// Screen 1: Home Screen
// -------------------------------------------------------------
function HomeScreen({ navigation }) {
  const [trending, setTrending] = useState([]);
  const [featured, setFeatured] = useState([]);
  const [bestsellers, setBestsellers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const { wishlistIds, toggleWishlist, addToCart } = useApp();

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      const [catsRes, trendRes, featRes, bestRes] = await Promise.all([
        api.getCategories(),
        api.getProducts({ trending: 1, limit: 8 }),
        api.getProducts({ featured: 1, limit: 8 }),
        api.getProducts({ bestseller: 1, limit: 8 }),
      ]);
      setCategories(catsRes.categories || []);
      setTrending(trendRes.products || []);
      setFeatured(featRes.products || []);
      setBestsellers(bestRes.products || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = () => {
    if (searchQuery.trim()) {
      navigation.navigate('SearchResults', { query: searchQuery.trim() });
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#FF6A00" />
        <Text style={styles.loadingText}>Loading ShopKart...</Text>
      </View>
    );
  }

  const renderProductCard = ({ item }) => {
    const isWishlisted = wishlistIds.includes(item.id);
    return (
      <TouchableOpacity
        style={styles.productCard}
        onPress={() => navigation.navigate('ProductDetail', { slug: item.slug })}
        activeOpacity={0.88}
      >
        <View style={styles.productImageContainer}>
          <Image source={{ uri: getImgUrl(item.product_image) }} style={styles.productImage} resizeMode="contain" />
          {item.discount_percent > 0 && (
            <View style={styles.discountBadge}>
              <Text style={styles.discountText}>{item.discount_percent}% OFF</Text>
            </View>
          )}
          <TouchableOpacity
            style={styles.wishlistBtn}
            onPress={() => toggleWishlist(item.id)}
          >
            <Text style={styles.wishlistHeart}>{isWishlisted ? '❤️' : '🤍'}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.productInfo}>
          <Text style={styles.productCategory}>{item.category_name || item.brand}</Text>
          <Text style={styles.productTitle} numberOfLines={2}>{item.name}</Text>
          
          <View style={styles.ratingRow}>
            <Text style={styles.ratingBadge}>★ {item.avg_rating || '4.8'}</Text>
            <Text style={styles.ratingCount}>({item.review_count || '12'})</Text>
          </View>

          <View style={styles.priceRow}>
            <Text style={styles.sellingPrice}>₹{Math.round(item.selling_price).toLocaleString('en-IN')}</Text>
            {item.original_price > item.selling_price && (
              <Text style={styles.origPrice}>₹{Math.round(item.original_price).toLocaleString('en-IN')}</Text>
            )}
          </View>

          <TouchableOpacity
            style={styles.addCartBtn}
            onPress={() => addToCart(item.id, null)}
          >
            <Text style={styles.addCartBtnText}>Add to Cart</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#131A2B" />
      
      {/* Header & Search */}
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <Text style={styles.brandLogo}>🛍️ Shop<Text style={{ color: '#FF6A00' }}>Kart</Text></Text>
          <Text style={styles.fastDeliveryTag}>⚡ Fast Delivery</Text>
        </View>
        
        <View style={styles.searchBarContainer}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Search electronics, fashion, home..."
            placeholderTextColor="#94A3B8"
            value={searchQuery}
            onChangeText={setSearchQuery}
            onSubmitEditing={handleSearchSubmit}
            returnKeyType="search"
          />
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 30 }}>
        
        {/* Banner */}
        <View style={styles.heroBanner}>
          <Text style={styles.bannerTag}>🔥 MEGA SAVINGS</Text>
          <Text style={styles.bannerTitle}>Up to 60% OFF On Top Brands</Text>
          <Text style={styles.bannerSubtitle}>Free Delivery on Orders Over ₹499</Text>
        </View>

        {/* Categories Strip */}
        <View style={styles.sectionContainer}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>Shop by Category</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Categories')}>
              <Text style={styles.seeAllText}>See All →</Text>
            </TouchableOpacity>
          </View>

          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, gap: 12 }}>
            {categories.map((cat) => (
              <TouchableOpacity
                key={cat.id}
                style={styles.categoryItem}
                onPress={() => navigation.navigate('CategoryProducts', { slug: cat.slug, name: cat.name })}
              >
                <View style={styles.categoryIconCircle}>
                  <Image source={{ uri: getImgUrl(cat.image) }} style={styles.categoryImg} resizeMode="contain" />
                </View>
                <Text style={styles.categoryName} numberOfLines={1}>{cat.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Trending Section */}
        <View style={styles.sectionContainer}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>🔥 Trending Deals</Text>
          </View>
          <FlatList
            data={trending}
            keyExtractor={(i) => i.id.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, gap: 14 }}
            renderItem={renderProductCard}
          />
        </View>

        {/* Featured Products Grid */}
        <View style={styles.sectionContainer}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>⭐ Featured Products</Text>
          </View>
          <FlatList
            data={featured}
            keyExtractor={(i) => i.id.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, gap: 14 }}
            renderItem={renderProductCard}
          />
        </View>

        {/* Bestsellers Section */}
        <View style={styles.sectionContainer}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>🏆 Bestsellers</Text>
          </View>
          <FlatList
            data={bestsellers}
            keyExtractor={(i) => i.id.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, gap: 14 }}
            renderItem={renderProductCard}
          />
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 2: Categories Screen
// -------------------------------------------------------------
function CategoriesScreen({ navigation }) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCategories().then((res) => {
      setCategories(res.categories || []);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#FF6A00" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <Text style={styles.subHeaderTitle}>All Categories</Text>
      </View>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        {categories.map((cat) => (
          <View key={cat.id} style={styles.categoryCard}>
            <TouchableOpacity
              style={styles.categoryMainRow}
              onPress={() => navigation.navigate('CategoryProducts', { slug: cat.slug, name: cat.name })}
            >
              <Image source={{ uri: getImgUrl(cat.image) }} style={styles.categoryCardImg} resizeMode="contain" />
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text style={styles.categoryCardTitle}>{cat.name}</Text>
                <Text style={styles.categoryCardDesc} numberOfLines={1}>{cat.description || 'Explore top collections'}</Text>
              </View>
              <Text style={styles.arrowIcon}>→</Text>
            </TouchableOpacity>

            {cat.subcategories && cat.subcategories.length > 0 && (
              <View style={styles.subcatChipsContainer}>
                {cat.subcategories.map((sub) => (
                  <TouchableOpacity
                    key={sub.id}
                    style={styles.subcatChip}
                    onPress={() => navigation.navigate('CategoryProducts', { slug: sub.slug, name: sub.name })}
                  >
                    <Text style={styles.subcatChipText}>{sub.name}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 3: Category Products Screen
// -------------------------------------------------------------
function CategoryProductsScreen({ route, navigation }) {
  const { slug, name } = route.params;
  const [products, setProducts] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCategoryDetail(slug).then((res) => {
      setProducts(res.products || []);
      setSubcategories(res.subcategories || []);
      setLoading(false);
    });
  }, [slug]);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#FF6A00" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ paddingRight: 10 }}>
          <Text style={{ fontSize: 20 }}>←</Text>
        </TouchableOpacity>
        <Text style={styles.subHeaderTitle}>{name}</Text>
      </View>

      {subcategories.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxHeight: 50, paddingHorizontal: 16, marginVertical: 8 }}>
          {subcategories.map((s) => (
            <TouchableOpacity
              key={s.id}
              style={styles.filterChip}
              onPress={() => navigation.push('CategoryProducts', { slug: s.slug, name: s.name })}
            >
              <Text style={styles.filterChipText}>{s.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      <FlatList
        data={products}
        keyExtractor={(i) => i.id.toString()}
        numColumns={2}
        columnWrapperStyle={{ justifyContent: 'space-between', paddingHorizontal: 16, marginBottom: 14 }}
        contentContainerStyle={{ paddingTop: 10, paddingBottom: 40 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.productCard, { width: (width - 44) / 2 }]}
            onPress={() => navigation.navigate('ProductDetail', { slug: item.slug })}
          >
            <View style={styles.productImageContainer}>
              <Image source={{ uri: getImgUrl(item.product_image) }} style={styles.productImage} resizeMode="contain" />
            </View>
            <View style={styles.productInfo}>
              <Text style={styles.productTitle} numberOfLines={2}>{item.name}</Text>
              <Text style={styles.sellingPrice}>₹{Math.round(item.selling_price).toLocaleString('en-IN')}</Text>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={{ fontSize: 40 }}>📦</Text>
            <Text style={styles.emptyText}>No products found in this category.</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 4: Product Detail Screen
// -------------------------------------------------------------
function ProductDetailScreen({ route, navigation }) {
  const { slug } = route.params;
  const [product, setProduct] = useState(null);
  const [selectedColor, setSelectedColor] = useState(null);
  const [activeImage, setActiveImage] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToCart, toggleWishlist, wishlistIds } = useApp();

  useEffect(() => {
    api.getProductDetail(slug).then((res) => {
      const p = res.product;
      setProduct(p);
      if (p && p.colors && p.colors.length > 0) {
        const def = p.colors.find(c => c.is_default) || p.colors[0];
        setSelectedColor(def);
        setActiveImage(def.gallery && def.gallery.length > 0 ? def.gallery[0] : def.image || p.product_image);
      } else if (p) {
        setActiveImage(p.product_image);
      }
      setLoading(false);
    });
  }, [slug]);

  if (loading || !product) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#FF6A00" />
      </View>
    );
  }

  const effectivePrice = selectedColor ? selectedColor.price : product.selling_price;
  const isWishlisted = wishlistIds.includes(product.id);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ paddingRight: 10 }}>
          <Text style={{ fontSize: 20 }}>←</Text>
        </TouchableOpacity>
        <Text style={styles.subHeaderTitle} numberOfLines={1}>{product.name}</Text>
        <TouchableOpacity onPress={() => toggleWishlist(product.id)} style={{ paddingLeft: 10 }}>
          <Text style={{ fontSize: 22 }}>{isWishlisted ? '❤️' : '🤍'}</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        {/* Main Photo Gallery */}
        <View style={styles.detailImageWrapper}>
          <Image source={{ uri: getImgUrl(activeImage) }} style={styles.detailMainImage} resizeMode="contain" />
        </View>

        {/* Thumbnail Strip */}
        {selectedColor && selectedColor.gallery && selectedColor.gallery.length > 1 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, gap: 8, marginVertical: 10 }}>
            {selectedColor.gallery.map((img, idx) => (
              <TouchableOpacity
                key={idx}
                onPress={() => setActiveImage(img)}
                style={[styles.galleryThumb, activeImage === img && styles.activeGalleryThumb]}
              >
                <Image source={{ uri: getImgUrl(img) }} style={{ width: '100%', height: '100%' }} resizeMode="contain" />
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}

        <View style={styles.detailContent}>
          <Text style={styles.detailBrand}>{product.brand}</Text>
          <Text style={styles.detailTitle}>{product.name}</Text>

          <View style={styles.detailPriceRow}>
            <Text style={styles.detailPrice}>₹{Math.round(effectivePrice).toLocaleString('en-IN')}</Text>
            {product.original_price > effectivePrice && (
              <Text style={styles.detailOrigPrice}>₹{Math.round(product.original_price).toLocaleString('en-IN')}</Text>
            )}
            <View style={styles.detailRatingBadge}>
              <Text style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: 12 }}>★ {product.avg_rating || '4.9'}</Text>
            </View>
          </View>

          {/* Color Selector */}
          {product.colors && product.colors.length > 0 && (
            <View style={styles.detailSection}>
              <Text style={styles.sectionLabel}>Select Color: <Text style={{ fontWeight: 'bold', color: '#131A2B' }}>{selectedColor?.name}</Text></Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10, marginTop: 8 }}>
                {product.colors.map((c) => (
                  <TouchableOpacity
                    key={c.id}
                    style={[styles.colorOptionCard, selectedColor?.id === c.id && styles.activeColorOption]}
                    onPress={() => {
                      setSelectedColor(c);
                      setActiveImage(c.gallery && c.gallery.length > 0 ? c.gallery[0] : c.image || product.product_image);
                    }}
                  >
                    <View style={[styles.colorDot, { backgroundColor: c.color_code || '#000' }]} />
                    <Text style={styles.colorOptionText}>{c.name}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          )}

          {/* Overview */}
          {product.description ? (
            <View style={styles.detailSection}>
              <Text style={styles.sectionLabel}>Product Overview</Text>
              <Text style={styles.descriptionText}>{product.description}</Text>
            </View>
          ) : null}

          {/* Highlights */}
          {product.highlights && product.highlights.length > 0 && (
            <View style={styles.detailSection}>
              <Text style={styles.sectionLabel}>Key Highlights</Text>
              {product.highlights.map((h, i) => (
                <View key={i} style={styles.highlightRow}>
                  <Text style={{ color: '#10B981', fontWeight: 'bold', marginRight: 6 }}>✓</Text>
                  <Text style={styles.highlightText}>{h}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>

      {/* Sticky Bottom Bar */}
      <View style={styles.stickyBottomBar}>
        <View>
          <Text style={{ fontSize: 11, color: '#64748B' }}>Total</Text>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#131A2B' }}>₹{Math.round(effectivePrice).toLocaleString('en-IN')}</Text>
        </View>
        <TouchableOpacity
          style={styles.primaryBtn}
          onPress={() => addToCart(product.id, selectedColor?.id)}
        >
          <Text style={styles.primaryBtnText}>Add to Cart 🛍️</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 5: Cart Screen
// -------------------------------------------------------------
function CartScreen({ navigation }) {
  const { cart, refreshCart, updateCartItem, removeFromCart, user } = useApp();

  if (!user) {
    return (
      <View style={styles.centerContainer}>
        <Text style={{ fontSize: 50, marginBottom: 12 }}>🔒</Text>
        <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#131A2B' }}>Please Login</Text>
        <Text style={{ fontSize: 13, color: '#64748B', marginTop: 4, textAlign: 'center', paddingHorizontal: 30 }}>
          Login to your ShopKart account to view your cart items and checkout.
        </Text>
        <TouchableOpacity style={[styles.primaryBtn, { marginTop: 20 }]} onPress={() => navigation.navigate('Profile')}>
          <Text style={styles.primaryBtnText}>Go to Login</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const items = cart?.items || [];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <Text style={styles.subHeaderTitle}>Shopping Cart ({cart?.total_items_count || 0})</Text>
      </View>

      {items.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={{ fontSize: 60 }}>🛒</Text>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#131A2B', marginTop: 12 }}>Your Cart is Empty</Text>
          <Text style={{ fontSize: 13, color: '#64748B', marginTop: 4 }}>Explore our top deals and add items!</Text>
          <TouchableOpacity style={[styles.primaryBtn, { marginTop: 20 }]} onPress={() => navigation.navigate('Home')}>
            <Text style={styles.primaryBtnText}>Start Shopping</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 120 }}>
            {cart.amount_needed_for_free_delivery > 0 ? (
              <View style={styles.deliveryNotice}>
                <Text style={{ fontSize: 12, color: '#FF6A00', fontWeight: 'bold' }}>
                  🚚 Add ₹{cart.amount_needed_for_free_delivery} more for FREE Delivery!
                </Text>
              </View>
            ) : (
              <View style={[styles.deliveryNotice, { backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' }]}>
                <Text style={{ fontSize: 12, color: '#059669', fontWeight: 'bold' }}>
                  🎉 You unlocked FREE Delivery!
                </Text>
              </View>
            )}

            {items.map((it) => (
              <View key={it.id} style={styles.cartItemCard}>
                <Image source={{ uri: getImgUrl(it.image) }} style={styles.cartItemImg} resizeMode="contain" />
                <View style={{ flex: 1, marginLeft: 12 }}>
                  <Text style={styles.cartItemTitle} numberOfLines={2}>{it.product_name}</Text>
                  {it.color_name && <Text style={{ fontSize: 11, color: '#64748B', marginTop: 2 }}>Color: {it.color_name}</Text>}
                  <Text style={styles.cartItemPrice}>₹{Math.round(it.unit_price).toLocaleString('en-IN')}</Text>

                  <View style={styles.cartQtyRow}>
                    <View style={styles.qtyControl}>
                      <TouchableOpacity style={styles.qtyBtn} onPress={() => updateCartItem(it.id, 'decrease')}>
                        <Text style={{ fontWeight: 'bold' }}>-</Text>
                      </TouchableOpacity>
                      <Text style={{ paddingHorizontal: 12, fontWeight: 'bold' }}>{it.quantity}</Text>
                      <TouchableOpacity style={styles.qtyBtn} onPress={() => updateCartItem(it.id, 'increase')}>
                        <Text style={{ fontWeight: 'bold' }}>+</Text>
                      </TouchableOpacity>
                    </View>

                    <TouchableOpacity onPress={() => removeFromCart(it.id)}>
                      <Text style={{ color: '#EF4444', fontSize: 12, fontWeight: 'bold' }}>Remove</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            ))}

            {/* Price Summary */}
            <View style={styles.summaryCard}>
              <Text style={{ fontSize: 14, fontWeight: 'bold', color: '#131A2B', marginBottom: 10 }}>Order Summary</Text>
              <View style={styles.summaryRow}>
                <Text style={{ color: '#64748B' }}>Subtotal</Text>
                <Text style={{ fontWeight: 'bold' }}>₹{cart.subtotal}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={{ color: '#64748B' }}>Delivery Fee</Text>
                <Text style={{ fontWeight: 'bold', color: cart.delivery_fee === 0 ? '#059669' : '#131A2B' }}>
                  {cart.delivery_fee === 0 ? 'FREE' : `₹${cart.delivery_fee}`}
                </Text>
              </View>
              <View style={[styles.summaryRow, { borderTopWidth: 1, borderTopColor: '#E2E8F0', paddingTop: 10, marginTop: 6 }]}>
                <Text style={{ fontSize: 16, fontWeight: 'bold', color: '#131A2B' }}>Total Amount</Text>
                <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#FF6A00' }}>₹{cart.grand_total}</Text>
              </View>
            </View>
          </ScrollView>

          <View style={styles.stickyBottomBar}>
            <View>
              <Text style={{ fontSize: 11, color: '#64748B' }}>Grand Total</Text>
              <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#131A2B' }}>₹{cart.grand_total}</Text>
            </View>
            <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('Checkout')}>
              <Text style={styles.primaryBtnText}>Proceed to Checkout →</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 6: Wishlist Screen
// -------------------------------------------------------------
function WishlistScreen({ navigation }) {
  const { wishlist, toggleWishlist, addToCart, user } = useApp();

  if (!user) {
    return (
      <View style={styles.centerContainer}>
        <Text style={{ fontSize: 50, marginBottom: 12 }}>🤍</Text>
        <Text style={{ fontSize: 18, fontWeight: 'bold' }}>Login to view your Wishlist</Text>
        <TouchableOpacity style={[styles.primaryBtn, { marginTop: 20 }]} onPress={() => navigation.navigate('Profile')}>
          <Text style={styles.primaryBtnText}>Login</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <Text style={styles.subHeaderTitle}>My Wishlist ({wishlist.length})</Text>
      </View>

      {wishlist.length === 0 ? (
        <View style={styles.centerContainer}>
          <Text style={{ fontSize: 60 }}>❤️</Text>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#131A2B', marginTop: 12 }}>Your Wishlist is Empty</Text>
          <Text style={{ fontSize: 13, color: '#64748B', marginTop: 4 }}>Save your favorite products for later!</Text>
        </View>
      ) : (
        <FlatList
          data={wishlist}
          keyExtractor={(i) => i.id.toString()}
          contentContainerStyle={{ padding: 16, gap: 12 }}
          renderItem={({ item }) => (
            <View style={styles.wishlistCard}>
              <Image source={{ uri: getImgUrl(item.product.product_image) }} style={styles.cartItemImg} resizeMode="contain" />
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text style={styles.productTitle} numberOfLines={2}>{item.product.name}</Text>
                <Text style={styles.sellingPrice}>₹{Math.round(item.product.selling_price).toLocaleString('en-IN')}</Text>
                <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
                  <TouchableOpacity
                    style={[styles.addCartBtn, { flex: 1 }]}
                    onPress={() => addToCart(item.product.id, null)}
                  >
                    <Text style={styles.addCartBtnText}>Move to Cart</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={{ padding: 8, borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 8 }}
                    onPress={() => toggleWishlist(item.product.id)}
                  >
                    <Text style={{ fontSize: 12, color: '#EF4444' }}>✕</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 7: Profile & Auth Screen
// -------------------------------------------------------------
function ProfileScreen({ navigation }) {
  const { user, loginUser, registerUser, logoutUser } = useApp();
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    if (user) {
      api.getOrders().then(res => setOrders(res.orders || []));
    }
  }, [user]);

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={{ padding: 24 }}>
          <View style={{ alignItems: 'center', marginVertical: 20 }}>
            <Text style={{ fontSize: 40 }}>🛍️</Text>
            <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#131A2B', marginTop: 8 }}>ShopKart App</Text>
            <Text style={{ fontSize: 13, color: '#64748B' }}>Sign in to enjoy all mobile features</Text>
          </View>

          <View style={styles.authCard}>
            <View style={{ flexDirection: 'row', borderBottomWidth: 1, borderBottomColor: '#E2E8F0', marginBottom: 16 }}>
              <TouchableOpacity
                style={{ flex: 1, paddingVertical: 10, borderBottomWidth: isRegister ? 0 : 2, borderBottomColor: '#FF6A00' }}
                onPress={() => setIsRegister(false)}
              >
                <Text style={{ textAlign: 'center', fontWeight: 'bold', color: isRegister ? '#64748B' : '#FF6A00' }}>Login</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={{ flex: 1, paddingVertical: 10, borderBottomWidth: isRegister ? 2 : 0, borderBottomColor: '#FF6A00' }}
                onPress={() => setIsRegister(true)}
              >
                <Text style={{ textAlign: 'center', fontWeight: 'bold', color: isRegister ? '#FF6A00' : '#64748B' }}>Sign Up</Text>
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.formInput}
              placeholder="Username"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
            />
            {isRegister && (
              <TextInput
                style={styles.formInput}
                placeholder="Email Address"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            )}
            <TextInput
              style={styles.formInput}
              placeholder="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            <TouchableOpacity
              style={[styles.primaryBtn, { marginTop: 12 }]}
              onPress={() => {
                if (isRegister) {
                  registerUser(username, email, password);
                } else {
                  loginUser(username, password);
                }
              }}
            >
              <Text style={styles.primaryBtnText}>{isRegister ? 'Create Account' : 'Login'}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <Text style={styles.subHeaderTitle}>My Account</Text>
      </View>
      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.avatarCircle}>
            <Text style={{ fontSize: 24, color: '#FFFFFF', fontWeight: 'bold' }}>{user.username.charAt(0).toUpperCase()}</Text>
          </View>
          <View style={{ marginLeft: 14 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#131A2B' }}>{user.username}</Text>
            <Text style={{ fontSize: 12, color: '#64748B' }}>{user.email || 'ShopKart Premium Member'}</Text>
          </View>
        </View>

        {/* Orders Preview */}
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Recent Orders ({orders.length})</Text>
          {orders.slice(0, 3).map((o) => (
            <View key={o.id} style={styles.orderCard}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                <Text style={{ fontWeight: 'bold', color: '#131A2B' }}>Order #{o.id}</Text>
                <Text style={styles.orderStatusBadge}>{o.status_display}</Text>
              </View>
              <Text style={{ fontSize: 12, color: '#64748B' }}>{o.created_at}</Text>
              <Text style={{ fontSize: 14, fontWeight: 'bold', color: '#FF6A00', marginTop: 4 }}>₹{o.total_amount}</Text>
            </View>
          ))}
        </View>

        <TouchableOpacity style={styles.logoutBtn} onPress={logoutUser}>
          <Text style={{ color: '#EF4444', fontWeight: 'bold', textAlign: 'center' }}>Logout</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Screen 8: Checkout Screen
// -------------------------------------------------------------
function CheckoutScreen({ navigation }) {
  const { cart, refreshCart } = useApp();
  const [addresses, setAddresses] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getAddresses().then((res) => {
      const addrs = res.addresses || [];
      setAddresses(addrs);
      if (addrs.length > 0) setSelectedAddress(addrs[0].id);
    });
  }, []);

  const handlePlaceOrder = async () => {
    if (!selectedAddress) {
      Alert.alert('Address Required', 'Please select or add a delivery address.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.createOrder(selectedAddress, paymentMethod);
      if (res.success) {
        Alert.alert('Order Placed! 🎉', `Your order #${res.order_id} has been placed successfully!`);
        refreshCart();
        navigation.navigate('Home');
      }
    } catch (e) {
      Alert.alert('Error', 'Could not place order.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.subHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ paddingRight: 10 }}>
          <Text style={{ fontSize: 20 }}>←</Text>
        </TouchableOpacity>
        <Text style={styles.subHeaderTitle}>Checkout</Text>
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 100 }}>
        {/* Address Selection */}
        <Text style={styles.sectionTitle}>Delivery Address</Text>
        {addresses.map((a) => (
          <TouchableOpacity
            key={a.id}
            style={[styles.addressOption, selectedAddress === a.id && styles.activeAddressOption]}
            onPress={() => setSelectedAddress(a.id)}
          >
            <Text style={{ fontWeight: 'bold', color: '#131A2B' }}>{a.full_name} ({a.phone})</Text>
            <Text style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>{a.address_line}, {a.city} - {a.pincode}</Text>
          </TouchableOpacity>
        ))}

        {/* Payment Method */}
        <Text style={[styles.sectionTitle, { marginTop: 20 }]}>Payment Method</Text>
        {[
          { id: 'cod', title: '💵 Cash on Delivery (COD)' },
          { id: 'upi', title: '⚡ UPI / QR Code' },
          { id: 'card', title: '💳 Credit / Debit Card' },
        ].map((pm) => (
          <TouchableOpacity
            key={pm.id}
            style={[styles.addressOption, paymentMethod === pm.id && styles.activeAddressOption]}
            onPress={() => setPaymentMethod(pm.id)}
          >
            <Text style={{ fontWeight: 'bold' }}>{pm.title}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.stickyBottomBar}>
        <View>
          <Text style={{ fontSize: 11, color: '#64748B' }}>To Pay</Text>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#FF6A00' }}>₹{cart?.grand_total || 0}</Text>
        </View>
        <TouchableOpacity style={styles.primaryBtn} onPress={handlePlaceOrder} disabled={loading}>
          <Text style={styles.primaryBtnText}>{loading ? 'Placing Order...' : 'Confirm Order 🛍️'}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// -------------------------------------------------------------
// Tab & Stack Navigators
// -------------------------------------------------------------
const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function HomeStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeMain" component={HomeScreen} />
      <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
      <Stack.Screen name="CategoryProducts" component={CategoryProductsScreen} />
    </Stack.Navigator>
  );
}

function CategoryStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CategoriesMain" component={CategoriesScreen} />
      <Stack.Screen name="CategoryProducts" component={CategoryProductsScreen} />
      <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
    </Stack.Navigator>
  );
}

function CartStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CartMain" component={CartScreen} />
      <Stack.Screen name="Checkout" component={CheckoutScreen} />
    </Stack.Navigator>
  );
}

// -------------------------------------------------------------
// Root App Component with Providers
// -------------------------------------------------------------
export default function App() {
  const [user, setUser] = useState(null);
  const [cart, setCart] = useState(null);
  const [wishlist, setWishlist] = useState([]);
  const [wishlistIds, setWishlistIds] = useState([]);

  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    try {
      const userRes = await api.getCurrentUser();
      if (userRes.authenticated) {
        setUser(userRes.user);
        refreshCart();
        refreshWishlist();
      }
    } catch (e) {}
  };

  const refreshCart = async () => {
    try {
      const res = await api.getCart();
      if (res.success) setCart(res.cart);
    } catch (e) {}
  };

  const refreshWishlist = async () => {
    try {
      const res = await api.getWishlist();
      if (res.success) {
        setWishlist(res.items);
        setWishlistIds(res.items.map(i => i.product.id));
      }
    } catch (e) {}
  };

  const addToCart = async (productId, colorId, qty = 1) => {
    if (!user) {
      Alert.alert('Login Required', 'Please login to add items to your cart.');
      return;
    }
    try {
      const res = await api.addToCart(productId, colorId, qty);
      if (res.success) {
        setCart(res.cart);
        Alert.alert('Added to Cart! 🛍️', res.message);
      }
    } catch (e) {
      Alert.alert('Error', 'Could not add to cart.');
    }
  };

  const updateCartItem = async (itemId, action) => {
    try {
      const res = await api.updateCart(itemId, action);
      if (res.success) setCart(res.cart);
    } catch (e) {}
  };

  const removeFromCart = async (itemId) => {
    try {
      const res = await api.removeFromCart(itemId);
      if (res.success) setCart(res.cart);
    } catch (e) {}
  };

  const toggleWishlist = async (productId) => {
    if (!user) {
      Alert.alert('Login Required', 'Please login to save wishlist items.');
      return;
    }
    try {
      const res = await api.toggleWishlist(productId);
      if (res.success) {
        refreshWishlist();
      }
    } catch (e) {}
  };

  const loginUser = async (u, p) => {
    try {
      const res = await api.login(u, p);
      if (res.success) {
        setUser(res.user);
        refreshCart();
        refreshWishlist();
      } else {
        Alert.alert('Login Failed', res.error || 'Invalid credentials');
      }
    } catch (e) {
      Alert.alert('Error', 'Unable to connect to server.');
    }
  };

  const registerUser = async (u, e, p) => {
    try {
      const res = await api.register(u, e, p);
      if (res.success) {
        setUser(res.user);
        refreshCart();
        refreshWishlist();
      } else {
        Alert.alert('Registration Failed', res.error);
      }
    } catch (e) {
      Alert.alert('Error', 'Unable to connect to server.');
    }
  };

  const logoutUser = async () => {
    await api.logout();
    setUser(null);
    setCart(null);
    setWishlist([]);
    setWishlistIds([]);
  };

  const cartBadge = cart?.total_items_count > 0 ? cart.total_items_count : null;
  const wishlistBadge = wishlist.length > 0 ? wishlist.length : null;

  return (
    <AppContext.Provider
      value={{
        user,
        cart,
        wishlist,
        wishlistIds,
        refreshCart,
        refreshWishlist,
        addToCart,
        updateCartItem,
        removeFromCart,
        toggleWishlist,
        loginUser,
        registerUser,
        logoutUser,
      }}
    >
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerShown: false,
            tabBarActiveTintColor: '#FF6A00',
            tabBarInactiveTintColor: '#64748B',
            tabBarStyle: {
              backgroundColor: '#FFFFFF',
              borderTopColor: '#E2E8F0',
              paddingTop: 6,
              height: 60,
            },
            tabBarLabelStyle: {
              fontSize: 11,
              fontWeight: '600',
              paddingBottom: 6,
            },
          })}
        >
          <Tab.Screen
            name="Home"
            component={HomeStack}
            options={{
              tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>🏠</Text>,
            }}
          />
          <Tab.Screen
            name="Categories"
            component={CategoryStack}
            options={{
              tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>📦</Text>,
            }}
          />
          <Tab.Screen
            name="Wishlist"
            component={WishlistScreen}
            options={{
              tabBarBadge: wishlistBadge,
              tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>❤️</Text>,
            }}
          />
          <Tab.Screen
            name="Cart"
            component={CartStack}
            options={{
              tabBarBadge: cartBadge,
              tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>🛍️</Text>,
            }}
          />
          <Tab.Screen
            name="Profile"
            component={ProfileScreen}
            options={{
              tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>👤</Text>,
            }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </AppContext.Provider>
  );
}

// -------------------------------------------------------------
// Stylesheet
// -------------------------------------------------------------
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC', padding: 20 },
  loadingText: { marginTop: 12, color: '#64748B', fontWeight: 'bold' },

  // Header
  header: { backgroundColor: '#131A2B', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 14 },
  brandRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  brandLogo: { fontSize: 22, fontWeight: '900', color: '#FFFFFF', letterSpacing: -0.5 },
  fastDeliveryTag: { fontSize: 11, color: '#FFD166', fontWeight: 'bold' },
  searchBarContainer: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 10, paddingHorizontal: 12, height: 42 },
  searchIcon: { fontSize: 16, marginRight: 8 },
  searchInput: { flex: 1, color: '#131A2B', fontSize: 13 },

  subHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#E2E8F0' },
  subHeaderTitle: { fontSize: 17, fontWeight: 'bold', color: '#131A2B' },

  // Banner
  heroBanner: { margin: 16, padding: 18, borderRadius: 16, backgroundColor: '#FF6A00' },
  bannerTag: { fontSize: 11, fontWeight: '900', color: '#FFF1E6', letterSpacing: 1 },
  bannerTitle: { fontSize: 20, fontWeight: 'bold', color: '#FFFFFF', marginTop: 4 },
  bannerSubtitle: { fontSize: 12, color: '#FFF1E6', marginTop: 4 },

  // Sections
  sectionContainer: { marginTop: 18 },
  sectionHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#131A2B' },
  seeAllText: { fontSize: 13, color: '#FF6A00', fontWeight: 'bold' },

  // Categories
  categoryItem: { alignItems: 'center', width: 68 },
  categoryIconCircle: { width: 56, height: 56, borderRadius: 28, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E2E8F0', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' },
  categoryImg: { width: 40, height: 40 },
  categoryName: { fontSize: 11, fontWeight: '600', color: '#131A2B', marginTop: 6, textAlign: 'center' },

  categoryCard: { backgroundColor: '#FFFFFF', borderRadius: 16, padding: 14, borderWidth: 1, borderColor: '#E2E8F0' },
  categoryMainRow: { flexDirection: 'row', alignItems: 'center' },
  categoryCardImg: { width: 50, height: 50, borderRadius: 10, backgroundColor: '#F8FAFC' },
  categoryCardTitle: { fontSize: 16, fontWeight: 'bold', color: '#131A2B' },
  categoryCardDesc: { fontSize: 12, color: '#64748B', marginTop: 2 },
  arrowIcon: { fontSize: 18, color: '#94A3B8', fontWeight: 'bold' },
  subcatChipsContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F1F5F9' },
  subcatChip: { backgroundColor: '#F1F5F9', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  subcatChipText: { fontSize: 11, color: '#475569', fontWeight: '500' },
  filterChip: { backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E2E8F0', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, marginRight: 8 },
  filterChipText: { fontSize: 12, color: '#131A2B', fontWeight: '600' },

  // Product Card
  productCard: { width: 175, backgroundColor: '#FFFFFF', borderRadius: 16, borderWidth: 1, borderColor: '#E2E8F0', overflow: 'hidden' },
  productImageContainer: { width: '100%', height: 140, backgroundColor: '#F8FAFC', justifyContent: 'center', alignItems: 'center', position: 'relative' },
  productImage: { width: '85%', height: '85%' },
  discountBadge: { position: 'absolute', top: 8, left: 8, backgroundColor: '#059669', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6 },
  discountText: { fontSize: 9, fontWeight: '900', color: '#FFFFFF' },
  wishlistBtn: { position: 'absolute', top: 6, right: 6, backgroundColor: '#FFFFFF', padding: 4, borderRadius: 14 },
  wishlistHeart: { fontSize: 14 },
  productInfo: { padding: 10 },
  productCategory: { fontSize: 10, color: '#64748B', textTransform: 'uppercase', fontWeight: 'bold' },
  productTitle: { fontSize: 13, fontWeight: 'bold', color: '#131A2B', marginTop: 2 },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  ratingBadge: { fontSize: 11, fontWeight: 'bold', color: '#059669' },
  ratingCount: { fontSize: 10, color: '#94A3B8' },
  priceRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  sellingPrice: { fontSize: 15, fontWeight: 'bold', color: '#131A2B' },
  origPrice: { fontSize: 12, color: '#94A3B8', textDecorationLine: 'line-through' },
  addCartBtn: { backgroundColor: '#FFF1E6', paddingVertical: 6, borderRadius: 8, marginTop: 8, alignItems: 'center' },
  addCartBtnText: { color: '#FF6A00', fontSize: 11, fontWeight: 'bold' },

  // Product Detail
  detailImageWrapper: { width: width, height: 320, backgroundColor: '#FFFFFF', justifyContent: 'center', alignItems: 'center' },
  detailMainImage: { width: '85%', height: '85%' },
  galleryThumb: { width: 60, height: 60, borderRadius: 10, borderWidth: 1, borderColor: '#E2E8F0', padding: 4, backgroundColor: '#FFFFFF' },
  activeGalleryThumb: { borderColor: '#FF6A00', borderWidth: 2 },
  detailContent: { padding: 16 },
  detailBrand: { fontSize: 12, color: '#64748B', fontWeight: 'bold', textTransform: 'uppercase' },
  detailTitle: { fontSize: 20, fontWeight: 'bold', color: '#131A2B', marginTop: 4 },
  detailPriceRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 10 },
  detailPrice: { fontSize: 24, fontWeight: '900', color: '#131A2B' },
  detailOrigPrice: { fontSize: 16, color: '#94A3B8', textDecorationLine: 'line-through' },
  detailRatingBadge: { backgroundColor: '#059669', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  detailSection: { marginTop: 20, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#E2E8F0' },
  sectionLabel: { fontSize: 14, fontWeight: 'bold', color: '#475569' },
  colorOptionCard: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, borderWidth: 1, borderColor: '#E2E8F0', backgroundColor: '#FFFFFF' },
  activeColorOption: { borderColor: '#FF6A00', borderWidth: 2, backgroundColor: '#FFF1E6' },
  colorDot: { width: 14, height: 14, borderRadius: 7, marginRight: 6, borderWidth: 1, borderColor: '#CBD5E1' },
  colorOptionText: { fontSize: 12, fontWeight: 'bold', color: '#131A2B' },
  descriptionText: { fontSize: 13, color: '#475569', lineHeight: 20, marginTop: 6 },
  highlightRow: { flexDirection: 'row', alignItems: 'center', marginTop: 6 },
  highlightText: { fontSize: 12, color: '#334155' },

  // Sticky Bar
  stickyBottomBar: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: '#FFFFFF', borderTopWidth: 1, borderTopColor: '#E2E8F0', paddingHorizontal: 20, paddingVertical: 12, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  primaryBtn: { backgroundColor: '#FF6A00', paddingHorizontal: 22, paddingVertical: 12, borderRadius: 12 },
  primaryBtnText: { color: '#FFFFFF', fontWeight: 'bold', fontSize: 14 },

  // Cart
  deliveryNotice: { padding: 10, borderRadius: 10, backgroundColor: '#FFF1E6', borderWidth: 1, borderColor: '#FED7AA', marginBottom: 12 },
  cartItemCard: { flexDirection: 'row', backgroundColor: '#FFFFFF', borderRadius: 14, padding: 12, marginBottom: 10, borderWidth: 1, borderColor: '#E2E8F0' },
  cartItemImg: { width: 70, height: 70, borderRadius: 10, backgroundColor: '#F8FAFC' },
  cartItemTitle: { fontSize: 13, fontWeight: 'bold', color: '#131A2B' },
  cartItemPrice: { fontSize: 15, fontWeight: 'bold', color: '#FF6A00', marginTop: 4 },
  cartQtyRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  qtyControl: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: '#CBD5E1', borderRadius: 8 },
  qtyBtn: { paddingHorizontal: 8, paddingVertical: 4 },
  summaryCard: { backgroundColor: '#FFFFFF', borderRadius: 14, padding: 16, borderWidth: 1, borderColor: '#E2E8F0', marginTop: 10 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 4 },

  // Wishlist
  wishlistCard: { flexDirection: 'row', backgroundColor: '#FFFFFF', borderRadius: 14, padding: 12, borderWidth: 1, borderColor: '#E2E8F0' },

  // Profile & Auth
  authCard: { backgroundColor: '#FFFFFF', borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#E2E8F0' },
  formInput: { backgroundColor: '#F8FAFC', borderWidth: 1, borderColor: '#E2E8F0', borderRadius: 10, paddingHorizontal: 14, paddingVertical: 10, marginBottom: 12, fontSize: 13 },
  userCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', padding: 16, borderRadius: 16, borderWidth: 1, borderColor: '#E2E8F0' },
  avatarCircle: { width: 50, height: 50, borderRadius: 25, backgroundColor: '#FF6A00', justifyContent: 'center', alignItems: 'center' },
  orderCard: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 12, marginTop: 8, borderWidth: 1, borderColor: '#E2E8F0' },
  orderStatusBadge: { fontSize: 11, color: '#059669', fontWeight: 'bold', backgroundColor: '#ECFDF5', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  logoutBtn: { padding: 14, borderRadius: 12, backgroundColor: '#FEE2E2', marginTop: 20 },

  // Address
  addressOption: { padding: 14, borderRadius: 12, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E2E8F0', marginBottom: 10 },
  activeAddressOption: { borderColor: '#FF6A00', borderWidth: 2, backgroundColor: '#FFF1E6' },
  emptyState: { alignItems: 'center', padding: 40 },
  emptyText: { color: '#64748B', marginTop: 10, fontWeight: 'bold' },
});
