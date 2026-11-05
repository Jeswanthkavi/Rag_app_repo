import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'core/services/supabase_service.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/auth_screen.dart';
import 'features/chat/chat_screen.dart';
import 'features/documents/documents_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SupabaseService.initialize();
  runApp(const RAGMobileApp());
}

class RAGMobileApp extends StatelessWidget {
  const RAGMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AK-RAG(18)',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  final SupabaseService _supabase = SupabaseService();
  User? _user;

  @override
  void initState() {
    super.initState();
    _user = _supabase.currentUser;
    _supabase.authStateChanges.listen((state) {
      if (mounted) {
        setState(() {
          _user = state.session?.user;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_user == null) {
      return AuthScreen(
        onAuthenticated: () {
          setState(() {
            _user = _supabase.currentUser;
          });
        },
      );
    }
    return const MainNavigationScaffold();
  }
}

class MainNavigationScaffold extends StatefulWidget {
  const MainNavigationScaffold({super.key});

  @override
  State<MainNavigationScaffold> createState() => _MainNavigationScaffoldState();
}

class _MainNavigationScaffoldState extends State<MainNavigationScaffold> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    ChatScreen(),
    DocumentsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: AppTheme.surfaceNavy,
          border: Border(
            top: BorderSide(color: AppTheme.borderSlate, width: 1),
          ),
        ),
        child: NavigationBar(
          selectedIndex: _currentIndex,
          backgroundColor: AppTheme.surfaceNavy,
          indicatorColor: AppTheme.primaryTeal.withValues(alpha: 0.18),
          elevation: 0,
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          onDestinationSelected: (idx) {
            setState(() => _currentIndex = idx);
          },
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.chat_bubble_outline_rounded, color: AppTheme.textSecondary),
              selectedIcon: Icon(Icons.chat_bubble_rounded, color: AppTheme.primaryTeal),
              label: 'AK-RAG Chat',
            ),
            NavigationDestination(
              icon: Icon(Icons.folder_outlined, color: AppTheme.textSecondary),
              selectedIcon: Icon(Icons.folder_rounded, color: AppTheme.primaryTeal),
              label: 'Documents',
            ),
          ],
        ),
      ),
    );
  }
}

