// Core Configuration
import 'package:flutter/foundation.dart';

class ApiConfig {
  static const String _baseUrlFromEnv = String.fromEnvironment(
    'API_URL',
  );

  static String get baseUrl {
    if (_baseUrlFromEnv.isNotEmpty) {
      return _baseUrlFromEnv;
    }

    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }

    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }

    return 'http://localhost:8000/api/v1';
  }
  
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  
  static Map<String, String> get headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
}

class AppConfig {
  static const String appName = 'Link1Die';
  static const String appVersion = '1.0.0';
  static const int maxFileSize = 100 * 1024 * 1024; // 100MB
  static const List<String> allowedFileTypes = [
    'pdf', 'doc', 'docx', 'txt', 'xlsx', 'csv'
  ];
}

class ApiEndpoints {
  // Auth
  static const String login = '/auth/login';
  static const String refresh = '/auth/refresh';
  static const String logout = '/auth/logout';
  
  // Documents
  static const String documents = '/documents';
  static String document(String id) => '/documents/$id';
  static const String uploadDocument = '/documents/upload';
  
  // Access Control
  static String shareDocument(String docId) => '/access/documents/$docId/share';
  static String makePublic(String docId) => '/access/documents/$docId/make-public';
  static String makePrivate(String docId) => '/access/documents/$docId/make-private';
}
