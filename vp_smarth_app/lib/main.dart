import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:livekit_client/livekit_client.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Doorbell Residente',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0F172A), // Slate 900
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // CONFIGURACIÓN LOCAL (Ajusta la IP de tu PC si pruebas en un celular físico)
  final String _apiUrlBase = "http://192.168.1.33:8000"; 
  final String _livekitWsUrl = "ws://192.168.1.33:7880"; // Puerto local por defecto de LiveKit

  Room? _room;
  bool _estaConectado = false;
  bool _abriendoPuerta = false;
  RemoteTrackPublication? _videoTrackPublication;

  // Variables simuladas que en producción vendrían en el Push de Firebase
  final int _edificioIdPrueba = 1;
  final String _tokenResidentePrueba = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWRlbyI6eyJyb29tSm9pbiI6dHJ1ZSwicm9vbSI6InJvb21fcXJfZGVwdG9fOCIsImNhblB1Ymxpc2giOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWV9LCJzdWIiOiJ2aXNpdGFudGVfRGF2aWQgRm9uc2VjYSIsImlzcyI6ImRldmtleSIsIm5iZiI6MTc5MDc3ODIyNywiZXhwIjoxNzkwNzk5ODI3fQ.noMTncWEzCfECFtcXosrGcg_jc1lp_IJdWbB6iCFEJE";

  Future<void> _conectarVideollamada() async {
    if (_estaConectado) return;

    try {
      // 1. Instanciar el objeto Room de LiveKit
      _room = Room(
        roomOptions: const RoomOptions(
          adaptiveStream: true,
          dynacast: true,
        ),
      );

      // 2. Crear los listeners para detectar cuándo el visitante transmite su cámara
      final listener = _room!.createListener();
      listener.on<TrackSubscribedEvent>((event) {
        if (event.track.kind == TrackType.VIDEO) {
          setState(() {
            _videoTrackPublication = event.publication;
          });
        }
      });

      // 3. Conectarse síncronamente al servidor WebRTC local
      await _room!.connect(_livekitWsUrl, _tokenResidentePrueba);
      
      // 4. Habilitar el micrófono del residente para hablar hacia la calle
      await _room!.localParticipant!.setMicrophoneEnabled(true);

      setState(() {
        _estaConectado = true;
      });
      _mostrarSnackBar("✅ Conectado al videoportero");
    } catch (e) {
      if (kDebugMode) {
        print("Error LiveKit Local: $e");
      }
      _mostrarSnackBar("❌ Error al conectar con LiveKit local");
    }
  }

  Future<void> _accionarApertura() async {
    if (_abriendoPuerta) return;
    setState(() { _abriendoPuerta = true; });

    try {
      final response = await http.post(
        Uri.parse("$_apiUrlBase/api/v1/puertas/abrir"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "edificio_id": _edificioIdPrueba,
          "usuario_id": 1,
        }),
      );

      if (response.statusCode == 200) {
        _mostrarSnackBar("🔓 ¡Comando de apertura enviado!");
      }
    } catch (e) {
      _mostrarSnackBar("❌ Fallo de conexión con la API");
    } finally {
      setState(() { _abriendoPuerta = false; });
    }
  }

  void _colgar() {
    _room?.disconnect();
    setState(() {
      _estaConectado = false;
      _videoTrackPublication = null;
    });
    _mostrarSnackBar("📞 Llamada finalizada");
  }

  void _mostrarSnackBar(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  void dispose() {
    _room?.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Encabezado
            const Padding(
              padding: EdgeInsets.all(20.0),
              child: Column(
                children: [
                  Text(
                    'Torre Madero Residencial',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Monitoreo en Vivo - Frente de Calle',
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                  ),
                ],
              ),
            ),

// Visor de Video WebRTC
Expanded(
              child: Padding(padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: const Color(0xFF020617),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: const Color(0xFF1E293B)),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: _estaConectado && _videoTrackPublication != null && _videoTrackPublication!.track != null
                      ? VideoTrackRenderer(_videoTrackPublication!.track as VideoTrack)
                      : Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.videocam_off_rounded, size: 48, color: Color(0xFF334155)),
                              const SizedBox(height: 12),
                              Text(_estaConectado ? "Esperando video..." : "Llamada inactiva", style: const TextStyle(color: Color(0xFF64748B))),
                            ],
                          ),
                        ),
                ),
              ),
            ),

            // Botonera de Control Inferior
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                children: [
                  if (!_estaConectado)
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton.icon(
                        onPressed: _conectarVideollamada,
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                        icon: const Icon(Icons.call, color: Colors.white),
                        label: const Text("Contestar Portero", style: TextStyle(fontSize: 16, color: Colors.white)),
                      ),
                    ),
                  if (_estaConectado) ...[
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton.icon(
                        onPressed: _accionarApertura,
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        icon: _abriendoPuerta 
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                            : const Icon(Icons.lock_open_rounded, color: Colors.white),
                        label: const Text("🔓 Abrir Puerta de Calle", style: TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    CircleAvatar(
                      radius: 28,
                      backgroundColor: Colors.red.shade600,
                      child: IconButton(
                        icon: const Icon(Icons.call_end, color: Colors.white),
                        onPressed: _colgar,
                      ),
                    )
                  ]
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}