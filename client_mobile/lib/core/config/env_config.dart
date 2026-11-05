import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

class EnvConfig {
  static const String supabaseUrl = 'https://sbkxmevrereobziaubsl.supabase.co';
  static const String supabaseAnonKey =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNia3htZXZyZXJlb2J6aWF1YnNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM0OTkzMDgsImV4cCI6MjEwOTA3NTMwOH0.VO1Xg9HImv5YmJHi2uaqonZt-UPK54zEJL-EuVIydzs';

  /// Allows overriding the backend URL via: --dart-define=API_URL=https://your-domain.com
  /// or by setting this variable directly for production release.
  static const String _configuredApiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: '', // Set your public backend URL here (e.g., 'https://my-rag-api.onrender.com')
  );

  /// Dynamically resolves the API base URL based on runtime platform
  static String get apiBaseUrl {
    if (_configuredApiUrl.isNotEmpty) {
      return _configuredApiUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8000';
    }
    try {
      if (Platform.isAndroid) {
        // Android emulator loopback pointing to host machine
        return 'http://10.0.2.2:8000';
      }
    } catch (_) {
      // Platform check fallback
    }
    return 'http://localhost:8000';
  }
}

