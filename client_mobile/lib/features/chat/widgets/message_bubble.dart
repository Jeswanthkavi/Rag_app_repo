import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../core/theme/app_theme.dart';
import 'citation_bottom_sheet.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  List<InlineSpan> _buildContentSpans(BuildContext context) {
    final List<InlineSpan> spans = [];
    final pattern = RegExp(r'\[([^,\]]+?),\s*Page\s*(\d+)\]', caseSensitive: false);
    final text = message.content;

    int lastMatchEnd = 0;
    for (final match in pattern.allMatches(text)) {
      if (match.start > lastMatchEnd) {
        spans.add(TextSpan(
          text: text.substring(lastMatchEnd, match.start),
          style: TextStyle(
            color: message.sender == 'user' ? Colors.black : Colors.white70,
            fontSize: 14,
            height: 1.4,
          ),
        ));
      }

      final docName = match.group(1)?.trim() ?? 'Document';
      final pageNum = int.tryParse(match.group(2)?.trim() ?? '1') ?? 1;

      // Find matching citation object if available
      CitationItem? matchedCitation;
      for (final cit in message.citations) {
        if (cit.documentName.toLowerCase().contains(docName.toLowerCase()) &&
            cit.pageNumber == pageNum) {
          matchedCitation = cit;
          break;
        }
      }
      matchedCitation ??= CitationItem(
        documentName: docName,
        pageNumber: pageNum,
        passagePreview: 'Verified excerpt from $docName (Page $pageNum).',
      );

      // Interactive citation badge
      spans.add(WidgetSpan(
        alignment: PlaceholderAlignment.middle,
        child: GestureDetector(
          onTap: () => CitationBottomSheet.show(context, matchedCitation!),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 2),
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: AppTheme.primaryTeal.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: AppTheme.primaryTeal.withValues(alpha: 0.5)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.bookmark_outline, size: 12, color: AppTheme.primaryTeal),
                const SizedBox(width: 4),
                Text(
                  '$docName, P.$pageNum',
                  style: const TextStyle(
                    color: AppTheme.primaryTeal,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ),
      ));

      lastMatchEnd = match.end;
    }

    if (lastMatchEnd < text.length) {
      spans.add(TextSpan(
        text: text.substring(lastMatchEnd),
        style: TextStyle(
          color: message.sender == 'user' ? Colors.black : Colors.white70,
          fontSize: 14,
          height: 1.4,
        ),
      ));
    }

    return spans;
  }

  @override
  Widget build(BuildContext context) {
    final isUser = message.sender == 'user';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser)
            Container(
              margin: const EdgeInsets.only(right: 8, top: 2),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppTheme.primaryTeal.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.primaryTeal.withValues(alpha: 0.3)),
              ),
              child: const Icon(Icons.smart_toy_outlined, size: 16, color: AppTheme.primaryTeal),
            ),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: isUser ? AppTheme.primaryTeal : AppTheme.cardDark,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: isUser ? const Radius.circular(16) : Radius.zero,
                  bottomRight: isUser ? Radius.zero : const Radius.circular(16),
                ),
                border: isUser ? null : Border.all(color: AppTheme.borderDark),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  RichText(
                    text: TextSpan(children: _buildContentSpans(context)),
                  ),
                  if (!isUser && message.citations.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      children: message.citations.map((c) {
                        return ActionChip(
                          avatar: const Icon(Icons.check_circle_outline, size: 12, color: AppTheme.primaryTeal),
                          label: Text(
                            '${c.documentName} (P.${c.pageNumber})',
                            style: const TextStyle(fontSize: 10, color: Colors.white70),
                          ),
                          backgroundColor: AppTheme.backgroundBlack,
                          side: const BorderSide(color: AppTheme.borderDark),
                          onPressed: () => CitationBottomSheet.show(context, c),
                          visualDensity: VisualDensity.compact,
                        );
                      }).toList(),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
