// Documents Feature Screen
import 'package:flutter/material.dart';
import '../../services/document_service.dart';
import '../../models/models.dart';

class DocumentsScreen extends StatefulWidget {
  final DocumentService documentService;
  
  const DocumentsScreen({Key? key, required this.documentService}) : super(key: key);
  
  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  late Future<List<Document>> _documentsFuture;
  
  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }
  
  void _loadDocuments() {
    _documentsFuture = widget.documentService.getDocuments();
  }
  
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Document>>(
      future: _documentsFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        
        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }
        
        final documents = snapshot.data ?? [];
        
        if (documents.isEmpty) {
          return const Center(
            child: Text('No documents yet. Upload one to get started!'),
          );
        }
        
        return ListView.builder(
          itemCount: documents.length,
          itemBuilder: (context, index) {
            final doc = documents[index];
            return ListTile(
              leading: Icon(
                _getFileIcon(doc.fileType),
                color: Colors.blue,
              ),
              title: Text(doc.title),
              subtitle: Text('${(doc.fileSize / 1024 / 1024).toStringAsFixed(2)} MB'),
              trailing: PopupMenuButton(
                itemBuilder: (context) => [
                  PopupMenuItem(
                    child: const Text('Share'),
                    onTap: () => _shareDocument(doc.id),
                  ),
                  PopupMenuItem(
                    child: const Text('Delete'),
                    onTap: () => _deleteDocument(doc.id),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
  
  IconData _getFileIcon(String fileType) {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return Icons.picture_as_pdf;
      case 'doc':
      case 'docx':
        return Icons.description;
      case 'xls':
      case 'xlsx':
        return Icons.table_chart;
      default:
        return Icons.file_present;
    }
  }
  
  void _shareDocument(String docId) async {
    try {
      await widget.documentService.makePublic(docId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Document is now public')),
        );
        _loadDocuments();
        setState(() {});
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
  
  void _deleteDocument(String docId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Document'),
        content: const Text('Are you sure?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              try {
                await widget.documentService.deleteDocument(docId);
                if (mounted) {
                  _loadDocuments();
                  setState(() {});
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Document deleted')),
                  );
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e')),
                  );
                }
              }
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
