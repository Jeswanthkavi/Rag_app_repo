import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/env_config.dart';

class CitationItem {
  final String? documentId;
  final String documentName;
  final int pageNumber;
  final String? passagePreview;
  final double? similarity;

  CitationItem({
    this.documentId,
    required this.documentName,
    required this.pageNumber,
    this.passagePreview,
    this.similarity,
  });

  factory CitationItem.fromJson(Map<String, dynamic> json) {
    return CitationItem(
      documentId: json['document_id'] as String?,
      documentName: (json['document_name'] ?? 'Document') as String,
      pageNumber: (json['page_number'] ?? 1) as int,
      passagePreview: json['passage_preview'] as String?,
      similarity: json['similarity'] != null
          ? (json['similarity'] as num).toDouble()
          : null,
    );
  }
}

class ChatMessage {
  final String id;
  final String sender;
  final String content;
  final List<CitationItem> citations;

  ChatMessage({
    required this.id,
    required this.sender,
    required this.content,
    required this.citations,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    var rawCitations = json['citations'] as List? ?? [];
    return ChatMessage(
      id: json['id'] as String? ?? DateTime.now().millisecondsSinceEpoch.toString(),
      sender: json['sender'] as String? ?? 'user',
      content: json['content'] as String? ?? '',
      citations: rawCitations
          .map((c) => CitationItem.fromJson(c as Map<String, dynamic>))
          .toList(),
    );
  }
}

class DocumentRecord {
  final String id;
  final String name;
  final int fileSize;
  final int pageCount;
  final String status;
  final String? errorMessage;
  final String createdAt;

  DocumentRecord({
    required this.id,
    required this.name,
    required this.fileSize,
    required this.pageCount,
    required this.status,
    this.errorMessage,
    required this.createdAt,
  });

  factory DocumentRecord.fromJson(Map<String, dynamic> json) {
    return DocumentRecord(
      id: json['id'] as String,
      name: json['name'] as String,
      fileSize: json['file_size'] as int? ?? 0,
      pageCount: json['page_count'] as int? ?? 1,
      status: json['status'] as String? ?? 'pending',
      errorMessage: json['error_message'] as String?,
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class ApiService {
  final String baseUrl = EnvConfig.apiBaseUrl;

  String _extractErrorMessage(String responseBody, String defaultMsg) {
    try {
      final decoded = jsonDecode(responseBody);
      if (decoded is Map && decoded['detail'] != null) {
        return decoded['detail'].toString();
      }
    } catch (_) {}
    return defaultMsg;
  }

  Future<List<DocumentRecord>> getDocuments(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/documents'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body);
      return data.map((d) => DocumentRecord.fromJson(d)).toList();
    }
    throw Exception(_extractErrorMessage(response.body, 'Failed to load documents.'));
  }

  Future<DocumentRecord> uploadDocumentBytes({
    required List<int> bytes,
    required String filename,
    required String token,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/documents/upload'),
    );
    request.headers['Authorization'] = 'Bearer $token';
    request.files.add(
      http.MultipartFile.fromBytes('file', bytes, filename: filename),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 201 || response.statusCode == 200) {
      return DocumentRecord.fromJson(jsonDecode(response.body));
    }
    throw Exception(_extractErrorMessage(response.body, 'Upload failed.'));
  }

  Future<void> deleteDocument(String documentId, String token) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/documents/$documentId'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode != 200) {
      throw Exception(_extractErrorMessage(response.body, 'Delete failed.'));
    }
  }

  Future<Map<String, dynamic>> sendChatQuery({
    required String message,
    String? conversationId,
    required String token,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'message': message,
        'conversation_id': conversationId,
        'stream': false,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception(_extractErrorMessage(response.body, 'Chat query failed.'));
  }
}
