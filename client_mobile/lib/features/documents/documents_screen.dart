import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../../core/services/api_service.dart';
import '../../core/services/supabase_service.dart';
import '../../core/theme/app_theme.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  final ApiService _api = ApiService();
  final SupabaseService _supabase = SupabaseService();

  List<DocumentRecord> _documents = [];
  bool _isLoading = true;
  bool _isUploading = false;
  String? _uploadStatus;

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    final token = _supabase.currentToken;
    if (token == null) return;

    try {
      final docs = await _api.getDocuments(token);
      if (mounted) {
        setState(() {
          _documents = docs;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _pickAndUploadDocument() async {
    final token = _supabase.currentToken;
    if (token == null) return;

    try {
      final files = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'txt', 'md'],
      );

      if (files.isEmpty) return;

      final platformFile = files.first;
      final bytes = await platformFile.readAsBytes();

      if (bytes.isEmpty) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not read file data.')),
        );
        return;
      }

      setState(() {
        _isUploading = true;
        _uploadStatus = 'Uploading ${platformFile.name}...';
      });

      await _api.uploadDocumentBytes(
        bytes: bytes,
        filename: platformFile.name,
        token: token,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Uploaded ${platformFile.name}. Processing chunks...')),
      );

      await _loadDocuments();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Upload failed: $e')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isUploading = false;
          _uploadStatus = null;
        });
      }
    }
  }

  Future<void> _deleteDoc(DocumentRecord doc) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.cardNavyElevated,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: AppTheme.borderSubtle),
        ),
        title: const Text('Delete Document', style: TextStyle(color: AppTheme.textPrimary)),
        content: Text(
          'Permanently delete "${doc.name}" and its grounded vector chunks?',
          style: const TextStyle(color: AppTheme.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.statusError),
            child: const Text('Delete', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    final token = _supabase.currentToken;
    if (token == null) return;

    try {
      await _api.deleteDocument(doc.id, token);
      if (!mounted) return;
      setState(() {
        _documents.removeWhere((d) => d.id == doc.id);
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Delete failed: $e')),
      );
    }
  }

  Widget _buildStatusBadge(String status) {
    Color bg;
    Color fg;
    Color border;
    Widget icon;

    switch (status) {
      case 'completed':
        bg = AppTheme.statusSuccessBg;
        fg = AppTheme.statusSuccess;
        border = AppTheme.statusSuccess.withValues(alpha: 0.4);
        icon = const Icon(Icons.check_circle_rounded, size: 12, color: AppTheme.statusSuccess);
        break;
      case 'processing':
      case 'pending':
        bg = AppTheme.citationBg;
        fg = AppTheme.citationGold;
        border = AppTheme.citationBorder;
        icon = const SizedBox(
          width: 10,
          height: 10,
          child: CircularProgressIndicator(strokeWidth: 1.5, color: AppTheme.citationGold),
        );
        break;
      default:
        bg = AppTheme.statusErrorBg;
        fg = AppTheme.statusError;
        border = AppTheme.statusError.withValues(alpha: 0.4);
        icon = const Icon(Icons.error_outline_rounded, size: 12, color: AppTheme.statusError);
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: border, width: 0.8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          icon,
          const SizedBox(width: 4),
          Text(
            status.toUpperCase(),
            style: TextStyle(color: fg, fontSize: 10, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: AppTheme.cardNavy,
                borderRadius: BorderRadius.circular(9),
                border: Border.all(
                  color: AppTheme.brandLime.withValues(alpha: 0.5),
                  width: 1.2,
                ),
              ),
              padding: const EdgeInsets.all(3),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: Image.asset(
                  'assets/images/logo.png',
                  fit: BoxFit.contain,
                ),
              ),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'AK-RAG(18) Documents',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.3,
                    color: AppTheme.textPrimary,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Isolated Tenant Knowledge Base',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppTheme.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, size: 20, color: AppTheme.textSecondary),
            tooltip: 'Refresh Documents',
            onPressed: _loadDocuments,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Upload Banner
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.cardNavy,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.borderSubtle),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryTeal.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: AppTheme.primaryTeal.withValues(alpha: 0.3),
                      ),
                    ),
                    child: const Icon(Icons.upload_file_rounded, color: AppTheme.primaryTeal),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _isUploading ? _uploadStatus! : 'Ingest Document',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'PDF / TXT / MD with automatic page tracking',
                          style: TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton(
                    onPressed: _isUploading ? null : _pickAndUploadDocument,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryTeal,
                      foregroundColor: const Color(0xFF042F2E),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      elevation: 0,
                    ),
                    child: _isUploading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF042F2E)),
                          )
                        : const Text(
                            'Upload',
                            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
                          ),
                  ),
                ],
              ),
            ),

            // Document List
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryTeal))
                  : _documents.isEmpty
                      ? const Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.folder_open_rounded, size: 48, color: AppTheme.textMuted),
                              SizedBox(height: 12),
                              Text(
                                'No documents ingested yet',
                                style: TextStyle(color: AppTheme.textSecondary, fontSize: 14),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Upload a document above to begin grounded Q&A',
                                style: TextStyle(color: AppTheme.textMuted, fontSize: 12),
                              ),
                            ],
                          ),
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          itemCount: _documents.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (ctx, i) {
                            final doc = _documents[i];
                            return Container(
                              decoration: BoxDecoration(
                                color: AppTheme.cardNavy,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: AppTheme.borderSubtle),
                              ),
                              child: ListTile(
                                leading: Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryTeal.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Icon(
                                    Icons.picture_as_pdf_rounded,
                                    color: AppTheme.primaryTeal,
                                    size: 20,
                                  ),
                                ),
                                title: Text(
                                  doc.name,
                                  style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.textPrimary,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                subtitle: Text(
                                  '${doc.pageCount} pages • ${(doc.fileSize / 1024).toStringAsFixed(1)} KB',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: AppTheme.textSecondary,
                                  ),
                                ),
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    _buildStatusBadge(doc.status),
                                    IconButton(
                                      icon: const Icon(
                                        Icons.delete_outline_rounded,
                                        size: 18,
                                        color: AppTheme.statusError,
                                      ),
                                      onPressed: () => _deleteDoc(doc),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}

