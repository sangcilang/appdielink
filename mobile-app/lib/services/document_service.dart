// Document Service
import '../core/api_client.dart';
import '../core/config.dart';
import '../models/models.dart';

class DocumentService {
  final ApiClient _apiClient;
  
  DocumentService(this._apiClient);
  
  Future<List<Document>> getDocuments({int skip = 0, int limit = 100}) async {
    final response = await _apiClient.get(
      ApiEndpoints.documents,
      queryParameters: {'skip': skip, 'limit': limit},
    );
    
    final documents = (response.data as List)
        .map((doc) => Document.fromJson(doc as Map<String, dynamic>))
        .toList();
    return documents;
  }
  
  Future<Document> getDocument(String docId) async {
    final response = await _apiClient.get(ApiEndpoints.document(docId));
    return Document.fromJson(response.data);
  }
  
  Future<Document> uploadFile(String filePath) async {
    final response = await _apiClient.uploadFile(
      ApiEndpoints.uploadDocument,
      filePath,
    );
    return Document.fromJson(response.data);
  }
  
  Future<void> deleteDocument(String docId) async {
    await _apiClient.delete(ApiEndpoints.document(docId));
  }
  
  Future<void> makePublic(String docId) async {
    await _apiClient.post(ApiEndpoints.makePublic(docId));
  }
  
  Future<void> makePrivate(String docId) async {
    await _apiClient.post(ApiEndpoints.makePrivate(docId));
  }
}
