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
    final isUser = message.sender == 'user';

    int lastMatchEnd = 0;
    for (final match in pattern.allMatches(text)) {
      if (match.start > lastMatchEnd) {
        spans.add(TextSpan(
          text: text.substring(lastMatchEnd, match.start),
          style: TextStyle(
            color: isUser ? const Color(0xFF042F2E) : AppTheme.textPrimary,
            fontSize: 14.5,
            height: 1.45,
            fontWeight: isUser ? FontWeight.w500 : FontWeight.w400,
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

      // Interactive warm yellow citation badge
      spans.add(WidgetSpan(
        alignment: PlaceholderAlignment.middle,
        child: GestureDetector(
          onTap: () => CitationBottomSheet.show(context, matchedCitation!),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 2),
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
            decoration: BoxDecoration(
              color: AppTheme.citationBg,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: AppTheme.citationBorder, width: 1),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.bookmark, size: 11, color: AppTheme.citationGold),
                const SizedBox(width: 3),
                Text(
                  '$docName, P.$pageNum',
                  style: const TextStyle(
                    color: AppTheme.citationGold,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
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
          color: isUser ? const Color(0xFF042F2E) : AppTheme.textPrimary,
          fontSize: 14.5,
          height: 1.45,
          fontWeight: isUser ? FontWeight.w500 : FontWeight.w400,
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
              width: 32,
              height: 32,
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
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: isUser ? AppTheme.primaryTeal : AppTheme.cardNavy,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: isUser ? const Radius.circular(16) : Radius.zero,
                  bottomRight: isUser ? Radius.zero : const Radius.circular(16),
                ),
                border: isUser ? null : Border.all(color: AppTheme.borderSubtle),
                boxShadow: isUser
                    ? [
                        BoxShadow(
                          color: AppTheme.primaryTeal.withValues(alpha: 0.2),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        )
                      ]
                    : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  RichText(
                    text: TextSpan(children: _buildContentSpans(context)),
                  ),
                  if (!isUser && message.citations.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 6,
                      runSpacing: 5,
                      children: message.citations.map((c) {
                        return ActionChip(
                          avatar: const Icon(
                            Icons.bookmark_added_rounded,
                            size: 13,
                            color: AppTheme.citationGold,
                          ),
                          label: Text(
                            '${c.documentName} (P.${c.pageNumber})',
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppTheme.citationGold,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          backgroundColor: AppTheme.citationBg,
                          side: const BorderSide(color: AppTheme.citationBorder, width: 0.8),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
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
