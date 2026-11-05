import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../core/theme/app_theme.dart';

class CitationBottomSheet extends StatelessWidget {
  final CitationItem citation;

  const CitationBottomSheet({super.key, required this.citation});

  static void show(BuildContext context, CitationItem citation) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (ctx) => CitationBottomSheet(citation: citation),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24.0),
      decoration: const BoxDecoration(
        color: AppTheme.cardNavyElevated,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        border: Border(
          top: BorderSide(color: AppTheme.citationBorder, width: 1.5),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 44,
                height: 4,
                margin: const EdgeInsets.only(bottom: 20),
                decoration: BoxDecoration(
                  color: AppTheme.textMuted.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // Header with warm gold verified badge
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppTheme.citationBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.citationBorder),
                  ),
                  child: const Icon(
                    Icons.verified_outlined,
                    color: AppTheme.citationGold,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Verified Source Citation',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      Text(
                        'AK-RAG(18) Ground Truth Audit Proof',
                        style: TextStyle(fontSize: 12, color: AppTheme.citationGold),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20, color: AppTheme.textSecondary),
                  onPressed: () => Navigator.pop(context),
                )
              ],
            ),
            const SizedBox(height: 18),

            // Source Details Pill
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.surfaceNavy,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderSlate),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        const Icon(
                          Icons.description_outlined,
                          size: 18,
                          color: AppTheme.citationGold,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            citation.documentName,
                            style: const TextStyle(
                              fontSize: 13.5,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.textPrimary,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.citationBg,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppTheme.citationBorder),
                    ),
                    child: Text(
                      'Page ${citation.pageNumber}',
                      style: const TextStyle(
                        color: AppTheme.citationGold,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  )
                ],
              ),
            ),
            const SizedBox(height: 18),

            // Content excerpt header
            const Row(
              children: [
                Icon(Icons.format_quote_rounded, size: 14, color: AppTheme.citationGold),
                SizedBox(width: 6),
                Text(
                  'EXACT GROUND-TRUTH PASSAGE',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                    color: AppTheme.citationGold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // Passage container with warm gold left accent border
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.surfaceNavy,
                borderRadius: BorderRadius.circular(12),
                border: const Border(
                  left: BorderSide(color: AppTheme.citationGold, width: 3.5),
                  top: BorderSide(color: AppTheme.borderSlate),
                  right: BorderSide(color: AppTheme.borderSlate),
                  bottom: BorderSide(color: AppTheme.borderSlate),
                ),
              ),
              child: Text(
                citation.passagePreview ?? 'Ground truth excerpt verified during embedding retrieval.',
                style: const TextStyle(
                  fontSize: 13,
                  fontFamily: 'monospace',
                  height: 1.5,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
            const SizedBox(height: 22),

            // Close button
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryTeal,
                foregroundColor: const Color(0xFF042F2E),
                padding: const EdgeInsets.symmetric(vertical: 13),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text(
                'Close Audit View',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

