// HTTP Client with interceptors
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config.dart';

class ApiClient {
  late Dio _dio;
  
  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: ApiConfig.headers,
    ));
    
    _setupInterceptors();
  }
  
  void _setupInterceptors() {
    // Request interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final prefs = await SharedPreferences.getInstance();
          final token = prefs.getString('access_token');
          
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) async {
          final requestOptions = error.requestOptions;
          final isRefreshRequest = requestOptions.path == ApiEndpoints.refresh;
          final hasRetried = requestOptions.extra['retried'] == true;

          if (error.response?.statusCode == 401 && !isRefreshRequest && !hasRetried) {
            final prefs = await SharedPreferences.getInstance();
            final refreshToken = prefs.getString('refresh_token');
            
            if (refreshToken != null) {
              try {
                final response = await _dio.post(
                  ApiEndpoints.refresh,
                  data: {'refresh_token': refreshToken},
                );
                
                final newAccessToken = response.data['access_token'];
                final newRefreshToken = response.data['refresh_token'];
                
                await prefs.setString('access_token', newAccessToken);
                await prefs.setString('refresh_token', newRefreshToken);
                
                // Retry request
                requestOptions.extra['retried'] = true;
                requestOptions.headers['Authorization'] = 'Bearer $newAccessToken';
                return handler.resolve(await _retry(requestOptions));
              } catch (e) {
                await prefs.clear();
              }
            }
          }
          return handler.next(error);
        },
      ),
    );
  }
  
  Future<Response<dynamic>> _retry(RequestOptions requestOptions) async {
    final options = Options(
      method: requestOptions.method,
      headers: requestOptions.headers,
    );
    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }
  
  Dio get dio => _dio;
  
  // API Methods
  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) {
    return _dio.get(path, queryParameters: queryParameters);
  }
  
  Future<Response> post(String path, {dynamic data}) {
    return _dio.post(path, data: data);
  }
  
  Future<Response> put(String path, {dynamic data}) {
    return _dio.put(path, data: data);
  }
  
  Future<Response> delete(String path) {
    return _dio.delete(path);
  }
  
  Future<Response> uploadFile(String path, String filePath) async {
    FormData formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    return _dio.post(path, data: formData);
  }
}

final apiClient = ApiClient();
