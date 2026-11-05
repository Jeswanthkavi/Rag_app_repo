import 'package:flutter/material.dart';

class AppTheme {
  // Brand Backgrounds (Deep Dark Navy)
  static const Color backgroundNavy = Color(0xFF070B14);
  static const Color surfaceNavy = Color(0xFF0C1322);
  static const Color cardNavy = Color(0xFF111C32);
  static const Color cardNavyElevated = Color(0xFF16223D);
  static const Color borderSlate = Color(0xFF1E293B);
  static const Color borderSubtle = Color(0xFF28354D);

  // Primary Action Color (Vibrant Teal)
  static const Color primaryTeal = Color(0xFF14B8A6);
  static const Color primaryTealDark = Color(0xFF0D9488);
  static const Color primaryTealLight = Color(0xFF2DD4BF);
  static const Color primaryTealGlow = Color(0x3314B8A6);

  // Evidence & Citations (Warm Amber / Gold Accents)
  static const Color citationGold = Color(0xFFFBBF24);
  static const Color citationAmber = Color(0xFFF59E0B);
  static const Color citationYellow = Color(0xFFFDE047);
  static const Color citationBg = Color(0x24F59E0B);
  static const Color citationBorder = Color(0x5DF59E0B);
  static const Color citationBadgeBg = Color(0x33FBBF24);

  // Brand Logo Accent (Neon Lime)
  static const Color brandLime = Color(0xFFA3E635);
  static const Color brandLimeGlow = Color(0x33A3E635);

  // Semantic Status Colors
  static const Color statusSuccess = Color(0xFF10B981);
  static const Color statusSuccessBg = Color(0x2210B981);
  static const Color statusWarning = Color(0xFFF59E0B);
  static const Color statusWarningBg = Color(0x22F59E0B);
  static const Color statusError = Color(0xFFEF4444);
  static const Color statusErrorBg = Color(0x22EF4444);

  // High-Contrast Typography Colors
  static const Color textPrimary = Color(0xFFF8FAFC);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF64748B);

  // Legacy Compatibility Getters
  static const Color primaryDark = cardNavy;
  static const Color backgroundBlack = backgroundNavy;
  static const Color cardDark = cardNavy;
  static const Color borderDark = borderSlate;

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: backgroundNavy,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryTeal,
        brightness: Brightness.dark,
        primary: primaryTeal,
        secondary: citationGold,
        tertiary: brandLime,
        surface: cardNavy,
        onSurface: textPrimary,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: backgroundNavy,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 19,
          fontWeight: FontWeight.bold,
          letterSpacing: -0.3,
        ),
        iconTheme: IconThemeData(color: textSecondary),
      ),
      cardTheme: CardThemeData(
        color: cardNavy,
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: const BorderSide(color: borderSubtle),
          borderRadius: BorderRadius.circular(16),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: cardNavyElevated,
        shape: RoundedRectangleBorder(
          side: const BorderSide(color: borderSubtle),
          borderRadius: BorderRadius.circular(20),
        ),
        titleTextStyle: const TextStyle(
          color: textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
        contentTextStyle: const TextStyle(
          color: textSecondary,
          fontSize: 14,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: cardNavy,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        hintStyle: const TextStyle(color: textMuted, fontSize: 14),
        labelStyle: const TextStyle(color: textSecondary, fontSize: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: borderSlate),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: borderSlate),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: primaryTeal, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: statusError),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryTeal,
          foregroundColor: const Color(0xFF042F2E),
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.2,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }
}
