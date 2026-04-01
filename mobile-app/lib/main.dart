// Main App Entry Point
import 'package:flutter/material.dart';
import 'core/api_client.dart';
import 'core/config.dart';
import 'services/auth_service.dart';
import 'services/document_service.dart';
import 'features/upload/upload_screen.dart';
import 'features/documents/documents_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    final authService = AuthService(apiClient);
    final documentService = DocumentService(apiClient);

    return MaterialApp(
      title: AppConfig.appName,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: AuthWrapper(
        authService: authService,
        documentService: documentService,
      ),
    );
  }
}

class AuthWrapper extends StatefulWidget {
  final AuthService authService;
  final DocumentService documentService;

  const AuthWrapper({
    Key? key,
    required this.authService,
    required this.documentService,
  }) : super(key: key);
  
  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  late Future<bool> _checkAuth;
  
  @override
  void initState() {
    super.initState();
    _checkAuth = widget.authService.hasValidToken();
  }
  
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _checkAuth,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        
        if (snapshot.data == true) {
          return HomeScreen(
            authService: widget.authService,
            documentService: widget.documentService,
          );
        } else {
          return LoginScreen(
            authService: widget.authService,
            documentService: widget.documentService,
          );
        }
      },
    );
  }
}

class LoginScreen extends StatefulWidget {
  final AuthService authService;
  final DocumentService documentService;
  
  const LoginScreen({
    Key? key,
    required this.authService,
    required this.documentService,
  }) : super(key: key);
  
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _error;
  
  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
  
  Future<void> _handleLogin() async {
    setState(() => _isLoading = true);
    try {
      await widget.authService.login(
        _usernameController.text,
        _passwordController.text,
      );
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => HomeScreen(
              authService: widget.authService,
              documentService: widget.documentService,
            ),
          ),
        );
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Link1Die Login')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextField(
                controller: _usernameController,
                decoration: const InputDecoration(
                  labelText: 'Username',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Password',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              if (_error != null)
                Text(_error!, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _isLoading ? null : _handleLogin,
                child: _isLoading
                    ? const SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Login'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends StatelessWidget {
  final AuthService authService;
  final DocumentService documentService;

  const HomeScreen({
    Key? key,
    required this.authService,
    required this.documentService,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Link1Die'),
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.cloud_upload), text: 'Upload'),
              Tab(icon: Icon(Icons.description), text: 'Documents'),
            ],
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: () async {
                await authService.logout();
                if (context.mounted) {
                  Navigator.of(context).pushReplacement(
                    MaterialPageRoute(
                      builder: (_) => LoginScreen(
                        authService: authService,
                        documentService: documentService,
                      ),
                    ),
                  );
                }
              },
            ),
          ],
        ),
        body: TabBarView(
          children: [
            UploadScreen(documentService: documentService),
            DocumentsScreen(documentService: documentService),
          ],
        ),
      ),
    );
  }
}
