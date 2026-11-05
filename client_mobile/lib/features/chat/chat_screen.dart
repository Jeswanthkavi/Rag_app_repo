import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import '../../core/services/supabase_service.dart';
import '../../core/theme/app_theme.dart';
import 'widgets/message_bubble.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final ApiService _api = ApiService();
  final SupabaseService _supabase = SupabaseService();

  final List<ChatMessage> _messages = [];
  String? _conversationId;
  bool _isLoading = false;

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _resetChat() {
    setState(() {
      _conversationId = null;
      _messages.clear();
      _messageController.clear();
    });
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _isLoading) return;

    final token = _supabase.currentToken;
    if (token == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please log in again.')),
      );
      return;
    }

    _messageController.clear();

    // Optimistically add user message
    final userMessage = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      sender: 'user',
      content: text,
      citations: [],
    );

    setState(() {
      _messages.add(userMessage);
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final res = await _api.sendChatQuery(
        message: text,
        conversationId: _conversationId,
        token: token,
      );

      _conversationId = res['conversation_id'] as String?;
      final answer = res['answer'] as String? ?? 'No response';
      final rawCitations = res['citations'] as List? ?? [];
      final citations = rawCitations
          .map((c) => CitationItem.fromJson(c as Map<String, dynamic>))
          .toList();

      final botMessage = ChatMessage(
        id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
        sender: 'assistant',
        content: answer,
        citations: citations,
      );

      setState(() {
        _messages.add(botMessage);
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Chat error: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppTheme.cardNavy,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: AppTheme.brandLime.withValues(alpha: 0.5),
                  width: 1.2,
                ),
              ),
              padding: const EdgeInsets.all(3),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(7),
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
                  'AK-RAG(18)',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.3,
                    color: AppTheme.textPrimary,
                  ),
                ),
                SizedBox(height: 2),
                Row(
                  children: [
                    Icon(Icons.circle, size: 7, color: AppTheme.statusSuccess),
                    SizedBox(width: 4),
                    Text(
                      'Grounded Engine Active',
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
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_comment_outlined, size: 20),
            tooltip: 'New Conversation',
            onPressed: _resetChat,
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded, size: 20),
            tooltip: 'Sign Out',
            onPressed: () async {
              await _supabase.signOut();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Messages View
            Expanded(
              child: _messages.isEmpty && !_isLoading
                  ? Center(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(32.0),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                color: AppTheme.cardNavy,
                                borderRadius: BorderRadius.circular(22),
                                border: Border.all(
                                  color: AppTheme.brandLime.withValues(alpha: 0.5),
                                  width: 1.5,
                                ),
                                boxShadow: const [
                                  BoxShadow(
                                    color: AppTheme.brandLimeGlow,
                                    blurRadius: 24,
                                    spreadRadius: 2,
                                  ),
                                ],
                              ),
                              padding: const EdgeInsets.all(10),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(14),
                                child: Image.asset(
                                  'assets/images/logo.png',
                                  fit: BoxFit.contain,
                                ),
                              ),
                            ),
                            const SizedBox(height: 20),
                            const Text(
                              'AK-RAG(18) Intelligence',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -0.4,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Ask grounded questions against your uploaded documents.\nEvery statement is backed by verifiable citations.',
                              style: TextStyle(
                                fontSize: 13,
                                color: AppTheme.textSecondary,
                                height: 1.4,
                              ),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                  decoration: BoxDecoration(
                                    color: AppTheme.citationBg,
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: AppTheme.citationBorder),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.bookmark, size: 12, color: AppTheme.citationGold),
                                      SizedBox(width: 4),
                                      Text(
                                        'Warm Gold Citations',
                                        style: TextStyle(
                                          color: AppTheme.citationGold,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                  decoration: BoxDecoration(
                                    color: AppTheme.primaryTeal.withValues(alpha: 0.14),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: AppTheme.primaryTeal.withValues(alpha: 0.4)),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.verified_outlined, size: 12, color: AppTheme.primaryTeal),
                                      SizedBox(width: 4),
                                      Text(
                                        'Verified Grounds',
                                        style: TextStyle(
                                          color: AppTheme.primaryTeal,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      itemCount: _messages.length,
                      itemBuilder: (ctx, i) => MessageBubble(message: _messages[i]),
                    ),
            ),

            if (_isLoading)
              Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: const BoxDecoration(
                  color: AppTheme.surfaceNavy,
                  border: Border(
                    top: BorderSide(color: AppTheme.borderSlate, width: 0.5),
                  ),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox(
                      height: 14,
                      width: 14,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppTheme.citationGold,
                      ),
                    ),
                    SizedBox(width: 10),
                    Text(
                      'Synthesizing grounded citations...',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppTheme.citationGold,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),

            // Input Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: const BoxDecoration(
                color: AppTheme.surfaceNavy,
                border: Border(top: BorderSide(color: AppTheme.borderSlate)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14),
                      decoration: const InputDecoration(
                        hintText: 'Ask AK-RAG(18) a grounded question...',
                        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    decoration: BoxDecoration(
                      color: AppTheme.primaryTeal,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: IconButton(
                      onPressed: _isLoading ? null : _sendMessage,
                      icon: const Icon(
                        Icons.send_rounded,
                        color: Color(0xFF042F2E),
                        size: 20,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

