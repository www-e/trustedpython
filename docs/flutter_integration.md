# TrustedPython Backend API Integration Guide for Flutter

## Overview
This guide explains how to integrate your Flutter application with the TrustedPython backend API.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: Your deployed backend URL

## CORS Configuration
The backend is configured to work with any Flutter development port:

- **Development**: Uses `ALLOWED_ORIGINS=*` to allow any Flutter development server
- **Production**: Configure `ALLOWED_ORIGINS` in environment variables with exact URLs (comma-separated)

## Authentication Flow

### 1. User Registration
Register a new user with the following endpoint:

```dart
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password",
  "phone_number": "+1234567890",
  "second_phone_number": "+1234567891", // optional
  "account_info": "Personal account details",
  "role": "regular_user" // or "mediator"
}
```

**Note**: Regular users are auto-approved, mediators require admin approval.

Response:
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "bearer",
  "user_id": 1,
  "username": "john_doe",
  "role": "regular_user",
  "state": "approved" // or "pending" for mediators
}
```

### 2. User Login
Authenticate an existing user:

```dart
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=secure_password
```

Response:
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "bearer",
  "user_id": 1,
  "username": "john_doe",
  "role": "regular_user",
  "state": "approved"
}
```

### 3. Using Access Token
Include the access token in the Authorization header for protected endpoints:

```dart
GET /auth/me
Authorization: Bearer {access_token}
```

### 4. Token Refresh
Refresh the access token using the refresh token:

```dart
POST /auth/token/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

## API Endpoints

### Authentication Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - Authenticate user
- `POST /auth/token/refresh` - Refresh access token
- `GET /auth/me` - Get current user info (requires valid token)

### User Management Endpoints (Admin Only)
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get specific user
- `PUT /users/{user_id}/approve` - Approve/reject user

### Profile Endpoints (Authenticated Users)
- `PUT /users/profile` - Update user profile

## Error Handling

The API returns standard HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate username)
- `500 Internal Server Error` - Server error

## Flutter Implementation Example

### Basic API Client
```dart
class ApiClient {
  static const String baseUrl = 'http://localhost:8000';
  String? _accessToken;
  String? _refreshToken;

  Future<Map<String, String>> getHeaders() async {
    if (_accessToken != null) {
      return {'Authorization': 'Bearer $_accessToken'};
    }
    return {};
  }

  Future<void> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      body: {
        'username': username,
        'password': password,
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];
    } else {
      throw Exception('Login failed');
    }
  }

  Future<void> register({
    required String username,
    required String password,
    required String phoneNumber,
    String? secondPhoneNumber,
    required String accountInfo,
    String role = 'regular_user',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
        'phone_number': phoneNumber,
        'second_phone_number': secondPhoneNumber,
        'account_info': accountInfo,
        'role': role,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];
    } else {
      throw Exception('Registration failed');
    }
  }

  Future<Map<String, dynamic>?> getCurrentUser() async {
    final headers = await getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 401) {
      // Token might be expired, try to refresh
      await refreshToken();
      // Retry the request
      final retryHeaders = await getHeaders();
      final retryResponse = await http.get(
        Uri.parse('$baseUrl/auth/me'),
        headers: retryHeaders,
      );
      
      if (retryResponse.statusCode == 200) {
        return jsonDecode(retryResponse.body);
      }
    }
    return null;
  }

  Future<void> refreshToken() async {
    if (_refreshToken == null) {
      throw Exception('No refresh token available');
    }

    final response = await http.post(
      Uri.parse('$baseUrl/auth/token/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': _refreshToken}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _accessToken = data['access_token'];
      _refreshToken = data['refresh_token'];
    } else {
      // Refresh failed, user needs to log in again
      _accessToken = null;
      _refreshToken = null;
      throw Exception('Token refresh failed');
    }
  }
}
```

### User Registration Example
```dart
// In your registration screen
void registerUser() async {
  try {
    await apiClient.register(
      username: usernameController.text,
      password: passwordController.text,
      phoneNumber: phoneController.text,
      secondPhoneNumber: secondPhoneController.text.isEmpty ? null : secondPhoneController.text,
      accountInfo: accountController.text,
      role: roleController.text, // 'regular_user' or 'mediator'
    );
    
    // Navigate to home screen or show success message
    Navigator.pushReplacementNamed(context, '/home');
  } catch (e) {
    // Show error message
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Registration failed: $e')),
    );
  }
}
```

## Important Notes

1. **State Management**: Mediators have a "pending" state until approved by an admin, while regular users are auto-approved.

2. **Token Storage**: Store tokens securely using Flutter's secure storage packages like `flutter_secure_storage`.

3. **Rate Limiting**: The API has rate limiting in place (10 requests per minute). Handle rate limit errors appropriately.

4. **Validation**: The API validates all inputs. Common validation rules:
   - Username: 3-50 characters, alphanumeric with underscores/hyphens
   - Password: Minimum 6 characters
   - Phone numbers: 10-15 digits with possible formatting characters (+, -, parentheses)

5. **Security**: Always use HTTPS in production environments.