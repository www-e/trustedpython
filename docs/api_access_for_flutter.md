# Backend API Documentation Access for Flutter Team

## API Base URLs

- **Development**: `http://localhost:8000` (when running locally)
- **Development Server**: Your deployed Render URL
- **Production**: Your deployed Coolify URL

## CORS Configuration
The backend is configured to work with any Flutter development server:

- **Development**: Uses `ALLOWED_ORIGINS=*` in backend environment, so it works with any Flutter port
- **Production**: Backend will be configured with specific Flutter app URLs

## Accessing API Documentation

### Interactive Documentation (Swagger)
- **URL**: `http://localhost:8000/docs` (local) or `{your-server}/docs`
- **Best for**: Testing endpoints manually and seeing request/response examples
- **Features**: 
  - Execute API calls directly from browser
  - See detailed endpoint documentation
  - View example requests/responses
  - Authentication testing built-in

### Alternative Documentation (ReDoc)
- **URL**: `http://localhost:8000/redoc` (local) or `{your-server}/redoc`
- **Best for**: Reading API specification in a clean format

## API Structure Overview

### Authentication Endpoints
```
POST /auth/register     - User registration
POST /auth/login        - Login and get tokens
POST /auth/token/refresh - Refresh access token
GET  /auth/me           - Get current user info
```

### User Management Endpoints
```
GET /users              - Get all users (admin only)
GET /users/{id}         - Get specific user (admin only)
PUT /users/{id}/approve - Approve/reject user (admin only)
PUT /users/profile      - Update own profile
```

## Authentication Flow for Flutter App

1. **User Registration/Login**: Get tokens from auth endpoints
2. **API Calls**: Include `Authorization: Bearer {access_token}` header
3. **Token Refresh**: Use refresh token when access token expires
4. **Error Handling**: Handle 401/403 responses appropriately

## Testing the API

### Before Integration
1. Start backend server: `uvicorn main:app --reload`
2. Visit: `http://localhost:8000/docs`
3. Test endpoints using the interactive interface
4. Verify responses match expected data structure

### With Flutter App
1. Make sure backend is running at correct URL
2. Use HTTP client to call API endpoints
3. Handle authentication and tokens properly
4. Test all user flows (registration, login, profile updates)

## Troubleshooting

- **Backend not accessible**: Verify backend server is running and URL is correct
- **Authentication errors**: Check token format and expiration
- **Database issues**: Ensure PostgreSQL is configured correctly
- **CORS errors**: Backend is configured to allow all origins (will be restricted in production)