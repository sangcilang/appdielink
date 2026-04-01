// Upload Feature Screen
import 'package:flutter/material.dart';
import '../../services/document_service.dart';

class UploadScreen extends StatefulWidget {
  final DocumentService documentService;
  
  const UploadScreen({Key? key, required this.documentService}) : super(key: key);
  
  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_upload_outlined,
              size: 80,
              color: Colors.blue.shade300,
            ),
            const SizedBox(height: 24),
            Text(
              'Upload Document',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 12),
            const Text(
              'Backend upload is ready, but the native file picker is not wired into this mobile build yet.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _showUploadUnavailableMessage,
              icon: const Icon(Icons.add),
              label: const Text('Upload Coming Soon'),
            ),
          ],
        ),
      ),
    );
  }

  void _showUploadUnavailableMessage() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Mobile upload still needs a file picker integration in this build.',
        ),
      ),
    );
  }
}
