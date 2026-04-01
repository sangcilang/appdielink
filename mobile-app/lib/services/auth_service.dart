// Authentication Service
import 'package:shared_preferences/shared_preferences.dart';
import '../core/api_client.dart';
import '../core/config.dart';
import '../models/models.dart';

class AuthService {
  final ApiClient _apiClient;
  
  AuthService(this._apiClient);
  
  Future<TokenResponse> login(String username, String password) async {
    final response = await _apiClient.post(
      ApiEndpoints.login,
      data: {'username': username, 'password': password},
    );
    
    final tokenResponse = TokenResponse.fromJson(response.data);
    await _saveTokens(tokenResponse);
    return tokenResponse;
  }
  
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString('refresh_token');
    
    try {
      await _apiClient.post(
        ApiEndpoints.logout,
        data: {'refresh_token': refreshToken},
      );
    } catch (e) {
      // Continue logout even if API call fails
    }
    
    await prefs.clear();
  }
  
  Future<void> _saveTokens(TokenResponse tokenResponse) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', tokenResponse.accessToken);
    if (tokenResponse.refreshToken != null) {
      await prefs.setString('refresh_token', tokenResponse.refreshToken!);
    }
  }
  
  Future<bool> hasValidToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey('access_token');
  }
}
