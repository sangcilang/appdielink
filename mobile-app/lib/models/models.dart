// Document Model
class Document {
  final String id;
  final String title;
  final String? description;
  final int fileSize;
  final String fileType;
  final String ownerId;
  final bool isPublic;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  Document({
    required this.id,
    required this.title,
    this.description,
    required this.fileSize,
    required this.fileType,
    required this.ownerId,
    required this.isPublic,
    required this.createdAt,
    required this.updatedAt,
  });
  
  factory Document.fromJson(Map<String, dynamic> json) {
    return Document(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      fileSize: json['file_size'],
      fileType: json['file_type'],
      ownerId: json['owner_id'],
      isPublic: json['is_public'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'file_size': fileSize,
      'file_type': fileType,
      'owner_id': ownerId,
      'is_public': isPublic,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

// Token Model
class TokenResponse {
  final String accessToken;
  final String? refreshToken;
  final String tokenType;
  
  TokenResponse({
    required this.accessToken,
    this.refreshToken,
    required this.tokenType,
  });
  
  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      tokenType: json['token_type'],
    );
  }
}
