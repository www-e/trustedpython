# API Endpoints Reference

## Authentication
- `POST /api/v1/auth/register` - Register new user with phone and password
- `POST /api/v1/auth/login` - Authenticate user and receive JWT access token
- `POST /api/v1/auth/logout` - Logout user (client-side token removal)

## User Profile
- `GET /api/v1/me` - Get current authenticated user profile
- `PUT /api/v1/me` - Update current user profile (username, avatar, bio)
- `PUT /api/v1/me/password` - Change current user password
- `GET /api/v1/me/stats` - Get current user statistics (deals, rating)
- `GET /api/v1/me/trades` - Get current user's trade history (buyer and seller deals)
- `GET /api/v1/users/{user_id}` - Get public user profile
- `GET /api/v1/users/{user_id}/stats` - Get user statistics (public)

## Categories
- `POST /api/v1/categories` - Create new category (admin only)
- `GET /api/v1/categories` - Get all categories (filter by active_only, popular_only)
- `GET /api/v1/categories/search` - Search categories by name
- `GET /api/v1/categories/{category_id}` - Get category by ID
- `PATCH /api/v1/categories/{category_id}` - Update category (admin only)
- `DELETE /api/v1/categories/{category_id}` - Delete category (admin only)

## Listings
- `POST /api/v1/listings` - Create new gaming account listing (seller only)
- `GET /api/v1/listings` - Get all listings (filter by category_id, active_only)
- `GET /api/v1/listings/featured` - Get featured listings for home screen
- `GET /api/v1/listings/search` - Search listings with filters (query, category, game_type, price)
- `GET /api/v1/listings/{listing_id}` - Get listing details by ID
- `PUT /api/v1/listings/{listing_id}` - Update listing (seller only)
- `DELETE /api/v1/listings/{listing_id}` - Delete listing (seller only)
- `POST /api/v1/listings/{listing_id}/images` - Add image to listing (seller only)
- `PATCH /api/v1/listings/{listing_id}/publish` - Publish listing from draft to active (seller only)
- `PATCH /api/v1/listings/{listing_id}/pause` - Pause active listing (seller only)

## Deals
- `POST /api/v1/deals` - Create new deal (buyer initiates purchase)
- `GET /api/v1/deals` - Get all deals for current user (as buyer or seller)
- `GET /api/v1/deals/{deal_id}` - Get deal details by ID
- `PUT /api/v1/deals/{deal_id}` - Update deal status (mediator only)
- `POST /api/v1/deals/{deal_id}/cancel` - Cancel deal (buyer or seller)
- `POST /api/v1/deals/{deal_id}/messages` - Send message in deal chat
- `GET /api/v1/deals/{deal_id}/messages` - Get deal chat messages

## Mediators
- `GET /api/v1/mediators` - Get all mediators (filter by tier, online status, rating)
- `GET /api/v1/mediators/{mediator_id}` - Get mediator profile
- `GET /api/v1/mediators/{mediator_id}/stats` - Get mediator statistics
- `GET /api/v1/mediators/{mediator_id}/reviews` - Get mediator reviews

## Exclusive Cards (Home Screen)
- `GET /api/v1/exclusive-cards` - Get all active exclusive cards for home screen

## Admin
- `GET /api/v1/admin/exclusive-cards` - Get all exclusive cards including inactive (admin)
- `POST /api/v1/admin/exclusive-cards` - Create new exclusive card (admin)
- `PUT /api/v1/admin/exclusive-cards/{card_id}` - Update exclusive card (admin)
- `DELETE /api/v1/admin/exclusive-cards/{card_id}` - Delete exclusive card (admin)
- `PUT /api/v1/admin/listings/{listing_id}/featured` - Toggle listing featured status (admin)
- `PUT /api/v1/admin/categories/{category_id}/popular` - Toggle category popular status (admin)

## System
- `GET /` - Root endpoint with welcome message
- `GET /api/v1/health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
