# Gesture AI Desk — Product Requirements Document

> Controle seu computador com gestos da mão em tempo real. Sem teclado, sem mouse, sem toque.

---

## 1. Visão geral

**Gesture AI Desk** é uma aplicação desktop que transforma a webcam em um painel de controle por gestos. O usuário faz sinais com a mão direita e controla ações reais no computador — trocar filtros visuais, executar comandos de mídia e ajustar parâmetros contínuos como volume — tudo em tempo real.

O projeto combina um backend Python de visão computacional com um frontend React (Next.js) que funciona como dashboard de controle e visualização, demonstrando domínio simultâneo de CV, automação de desktop e desenvolvimento full-stack.

### 1.1 Objetivo

Projeto de portfólio com alto impacto visual. O resultado deve parecer produto, não experimento. Demável em vídeo de 30 segundos.

### 1.2 Público-alvo do portfólio

Recrutadores técnicos e não-técnicos. O impacto visual é imediato — qualquer pessoa entende o que está acontecendo ao ver a demo.

### 1.3 Plataforma

- **OS:** Windows (desktop)
- **GPU:** NVIDIA dedicada (CUDA disponível)
- **Webcam:** 1080p (Logitech ou equivalente)
- **Mão:** Direita apenas

---

## 2. Stack técnica

### 2.1 Backend Python

| Pacote | Versão | Função |
|---|---|---|
| `python` | 3.11+ | Runtime |
| `opencv-python` | 4.9+ | Captura de frames e filtros visuais |
| `mediapipe` | 0.10+ | Hand Landmarker (21 landmarks 3D) |
| `fastapi` | 0.110+ | WebSocket server |
| `uvicorn` | 0.29+ | ASGI server |
| `pynput` | 1.7+ | Controle de teclado e teclas de mídia |
| `pycaw` | 20240210+ | Controle de volume do Windows (COM API) |
| `numpy` | 1.26+ | Cálculos geométricos sobre landmarks |
| `Pillow` | 10+ | Manipulação de imagem (screenshots) |

### 2.2 Frontend React

| Pacote | Versão | Função |
|---|---|---|
| `next` | 14+ | Framework React |
| `tailwindcss` | 3.4+ | Estilização |
| `typescript` | 5+ | Tipagem |
| WebSocket API | nativo | Comunicação com backend |
| Canvas API | nativo | Renderização de frames |

### 2.3 Ferramentas de desenvolvimento

| Ferramenta | Função |
|---|---|
| `uv` ou `poetry` | Gerenciamento de dependências Python |
| `pnpm` | Gerenciamento de dependências Node |
| `ruff` | Linter e formatter Python |
| `eslint` + `prettier` | Linter e formatter JS/TS |

---

## 3. Arquitetura

O sistema opera em 3 camadas conectadas por WebSocket:

```
┌─────────────────────────────────────────────────────────┐
│                    HARDWARE                              │
│   Webcam 1080p ──────────────────── GPU NVIDIA (CUDA)   │
└──────────┬──────────────────────────────────────────────┘
           │ frames
           ▼
┌─────────────────────────────────────────────────────────┐
│                 PYTHON BACKEND                           │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ OpenCV       │──▶│ MediaPipe    │──▶│ Gesture      │ │
│  │ Capture      │   │ Hand         │   │ Engine       │ │
│  │ (30fps loop) │   │ (21 landmarks│   │ (regras      │ │
│  │              │   │  3D)         │   │  geométricas)│ │
│  └──────────────┘   └──────────────┘   └──────┬───────┘ │
│                                               │          │
│                    ┌──────────────────────┬────┘          │
│                    ▼                      ▼               │
│  ┌──────────────────────┐  ┌───────────────────────────┐ │
│  │ System Actions       │  │ Visual Filters            │ │
│  │ (pynput + pycaw)     │  │ (OpenCV transforms)       │ │
│  │ play/mute/vol/screenshot│ │ gray/edge/blur/landmarks │ │
│  └──────────────────────┘  └───────────────────────────┘ │
│                                               │          │
│  ┌────────────────────────────────────────────┘          │
│  │ WebSocket Server (FastAPI + uvicorn)                   │
│  │ ws://localhost:8765                                    │
│  └──────────┬────────────────────────────────────────────┘
│             │ JSON + base64 frames
              ▼
┌─────────────────────────────────────────────────────────┐
│               FRONTEND REACT (Next.js)                   │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │ Camera     │  │ Gesture    │  │ Config Panel       │ │
│  │ Feed       │  │ HUD        │  │ (mapeamento de     │ │
│  │ (canvas)   │  │ (overlay)  │  │  gestos + settings)│ │
│  └────────────┘  └────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.1 Fluxo de dados

1. OpenCV captura frame da webcam a 30fps
2. Frame é enviado ao MediaPipe Hand Landmarker
3. MediaPipe retorna 21 landmarks 3D (x, y, z normalizados)
4. Gesture Engine aplica regras geométricas sobre os landmarks
5. Se gesto detectado:
   - **Ação de sistema** → `pynput`/`pycaw` executa no OS
   - **Filtro visual** → OpenCV aplica transformação no frame
6. Frame processado + estado do gesto são enviados via WebSocket
7. Frontend renderiza frame no canvas e atualiza HUD

### 3.2 Protocolo WebSocket

O backend envia mensagens JSON ao frontend a cada frame:

```json
{
  "frame": "<base64 encoded JPEG>",
  "timestamp": 1710000000.123,
  "hand_detected": true,
  "gesture": {
    "name": "open_hand",
    "confidence": 0.92,
    "hold_progress": 0.75,
    "action_triggered": false
  },
  "pinch": {
    "active": false,
    "type": null,
    "value": null
  },
  "active_filter": "normal",
  "landmarks": [[0.45, 0.62, 0.01], ...]
}
```

O frontend pode enviar comandos de configuração:

```json
{
  "command": "update_config",
  "payload": {
    "hold_duration": 0.5,
    "pinch_threshold": 30,
    "gesture_mappings": { ... }
  }
}
```

---

## 4. Mapeamento de gestos

### 4.1 MediaPipe Hand Landmarks — referência

```
         8 (INDEX_TIP)
         |
         7 (INDEX_DIP)
         |
         6 (INDEX_PIP)
         |
    12   5 (INDEX_MCP)    4 (THUMB_TIP)
     |   |                 |
    11   |            3 (THUMB_IP)
     |   |                 |
    10   |            2 (THUMB_MCP)
     |   |               /
16   9   |             1 (THUMB_CMC)
 |   |   |           /
15   |   |         /
 |   |   |       /
14   |   |     /
 |   |   |   /
20  13   | /
 |   |   0 (WRIST)
19   |
 |   |
18  17
```

**Landmarks-chave:**
- `0` = wrist (base da mão)
- `4` = thumb tip (ponta do polegar)
- `8` = index tip (ponta do indicador)
- `12` = middle tip (ponta do médio)
- `16` = ring tip (ponta do anelar)
- `20` = pinky tip (ponta do mindinho)
- PIPs = juntas intermediárias (3, 6, 10, 14, 18)

### 4.2 Regra geral de dedo estendido

```python
def is_finger_extended(landmarks, tip_id, pip_id):
    """Dedo está estendido se a ponta está acima da junta PIP (eixo Y invertido)."""
    return landmarks[tip_id].y < landmarks[pip_id].y

def is_thumb_extended(landmarks):
    """Polegar usa eixo X (lateral) — estendido se tip está longe do MCP."""
    return abs(landmarks[4].x - landmarks[2].x) > 0.05
```

### 4.3 Gestos — system actions (hold 0.5s)

Todos os gestos de ação exigem manter a pose por 0.5 segundo antes de disparar. Um indicador visual (anel radial) mostra o progresso do hold na tela.

#### Mão aberta ✋ → Play / Pause

```python
def detect_open_hand(landmarks):
    return all([
        is_thumb_extended(landmarks),
        is_finger_extended(landmarks, 8, 6),    # indicador
        is_finger_extended(landmarks, 12, 10),   # médio
        is_finger_extended(landmarks, 16, 14),   # anelar
        is_finger_extended(landmarks, 20, 18),   # mindinho
    ])
```

**Ação:** Simula tecla `Key.media_play_pause` via `pynput`.

#### Punho fechado ✊ → Mute / Unmute

```python
def detect_fist(landmarks):
    return all([
        not is_thumb_extended(landmarks),
        not is_finger_extended(landmarks, 8, 6),
        not is_finger_extended(landmarks, 12, 10),
        not is_finger_extended(landmarks, 16, 14),
        not is_finger_extended(landmarks, 20, 18),
    ])
```

**Ação:** Alterna mute do sistema via `pycaw` (Windows Core Audio API).

#### Indicador + médio ✌️ → Next track

```python
def detect_peace(landmarks):
    return all([
        is_finger_extended(landmarks, 8, 6),     # indicador up
        is_finger_extended(landmarks, 12, 10),    # médio up
        not is_finger_extended(landmarks, 16, 14), # anelar down
        not is_finger_extended(landmarks, 20, 18), # mindinho down
    ])
```

**Ação:** Simula tecla `Key.media_next` via `pynput`.

#### Polegar pra cima 👍 → Volume up (+5%)

```python
def detect_thumb_up(landmarks):
    thumb_above_mcp = landmarks[4].y < landmarks[2].y
    all_fingers_closed = all([
        not is_finger_extended(landmarks, 8, 6),
        not is_finger_extended(landmarks, 12, 10),
        not is_finger_extended(landmarks, 16, 14),
        not is_finger_extended(landmarks, 20, 18),
    ])
    # Anti-conflito com pinça: polegar deve estar longe do indicador
    thumb_far_from_index = distance(landmarks[4], landmarks[8]) > 50
    return thumb_above_mcp and all_fingers_closed and thumb_far_from_index
```

**Ação:** Incrementa volume do sistema em +5% via `pycaw`.

#### Polegar pra baixo 👎 → Volume down (-5%)

```python
def detect_thumb_down(landmarks):
    thumb_below_wrist = landmarks[4].y > landmarks[0].y
    all_fingers_closed = all([
        not is_finger_extended(landmarks, 8, 6),
        not is_finger_extended(landmarks, 12, 10),
        not is_finger_extended(landmarks, 16, 14),
        not is_finger_extended(landmarks, 20, 18),
    ])
    return thumb_below_wrist and all_fingers_closed
```

**Ação:** Decrementa volume do sistema em -5% via `pycaw`.

#### Indicador apontando ☝️ → Screenshot

```python
def detect_point(landmarks):
    return all([
        is_finger_extended(landmarks, 8, 6),      # indicador up
        not is_finger_extended(landmarks, 12, 10), # médio down
        not is_finger_extended(landmarks, 16, 14), # anelar down
        not is_finger_extended(landmarks, 20, 18), # mindinho down
    ])
```

**Ação:** Captura screenshot via `Pillow.ImageGrab` e salva em `~/Pictures/gesture_screenshots/`.

#### Hang loose 🤙 → Pause / Resume detecção

```python
def detect_hang_loose(landmarks):
    return all([
        is_thumb_extended(landmarks),               # polegar out
        not is_finger_extended(landmarks, 8, 6),     # indicador down
        not is_finger_extended(landmarks, 12, 10),   # médio down
        not is_finger_extended(landmarks, 16, 14),   # anelar down
        is_finger_extended(landmarks, 20, 18),       # mindinho up
    ])
```

**Ação:** Alterna flag `detection_paused`. Quando pausado, o sistema continua mostrando o feed da câmera mas não interpreta nenhum gesto. Útil pra descansar a mão.

### 4.4 Gestos — troca de filtro visual (swipe)

Os filtros visuais são trocados por swipe horizontal com mão aberta.

```python
FILTERS = ["normal", "grayscale", "edge_detection", "blur", "landmark_highlight"]
current_filter_index = 0

def detect_swipe(wrist_history, threshold_px=100, time_window=0.4):
    """
    Detecta swipe horizontal baseado no deslocamento do wrist (landmark 0)
    entre frames dentro de uma janela de tempo.
    """
    if len(wrist_history) < 2:
        return None
    
    recent = [p for p in wrist_history if time.time() - p['t'] < time_window]
    if len(recent) < 2:
        return None
    
    dx = recent[-1]['x'] - recent[0]['x']
    
    if dx > threshold_px:
        return "swipe_right"  # próximo filtro
    elif dx < -threshold_px:
        return "swipe_left"   # filtro anterior
    
    return None
```

**Ciclo de filtros:** Normal → Grayscale → Edge detection → Blur → Landmark highlight → Normal

**Implementação dos filtros OpenCV:**

```python
def apply_filter(frame, filter_name, intensity=1.0):
    if filter_name == "normal":
        return frame
    elif filter_name == "grayscale":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif filter_name == "edge_detection":
        edges = cv2.Canny(frame, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    elif filter_name == "blur":
        ksize = int(15 * intensity) | 1  # deve ser ímpar
        return cv2.GaussianBlur(frame, (ksize, ksize), 0)
    elif filter_name == "landmark_highlight":
        return frame  # landmarks são desenhados pelo MediaPipe drawing utils
```

### 4.5 Gestos — pinch control (contínuo, instantâneo)

A pinça oferece controle analógico contínuo via um único gesto (polegar + indicador). O eixo do movimento determina qual parâmetro é controlado. Não usa hold — a resposta é imediata.

**Design atualizado (baseado na análise do Computer-Automation, seção 11.4):** Em vez de usar dois tipos de pinch com dedos diferentes, usamos um único pinch com detecção de eixo. Movimento vertical (↑↓) controla volume, horizontal (←→) controla intensidade do filtro. Isso é mais intuitivo e robusto.

#### Pinça polegar + indicador → Volume (eixo Y) / Intensidade do filtro (eixo X)

```python
class PinchController:
    """
    Controle contínuo por pinça com detecção de eixo.
    - Ativa quando polegar e indicador se tocam (dist < 0.05 normalizado)
    - Desativa quando se afastam (dist > 0.12 normalizado)
    - Primeiro movimento significativo determina o eixo (lock-in)
    - Vertical = volume, Horizontal = intensidade do filtro
    """
    def __init__(self, threshold: float = 0.3):
        self.active = False
        self.start_x = 0.0
        self.start_y = 0.0
        self.direction = None  # 'vertical' ou 'horizontal'
        self.threshold = threshold
        self.smoother = PinchSmoother()  # seção 11.3
    
    def update(self, landmarks) -> dict:
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        dist = euclidean_distance(thumb_tip, index_tip)
        
        # Ativação: dedos se tocam
        if dist < 0.05 and not self.active:
            self.active = True
            self.start_x = index_tip.x
            self.start_y = index_tip.y
            self.direction = None
            return {"active": True, "value": 0, "axis": None}
        
        # Desativação: dedos se afastaram demais
        if dist > 0.12:
            self.active = False
            self.direction = None
            return {"active": False}
        
        if self.active:
            dx = (index_tip.x - self.start_x) * 10
            dy = (self.start_y - index_tip.y) * 10  # Y invertido
            
            # Lock-in de direção no primeiro movimento significativo
            if self.direction is None:
                if abs(dy) > abs(dx) and abs(dy) > self.threshold:
                    self.direction = 'vertical'
                elif abs(dx) > self.threshold:
                    self.direction = 'horizontal'
            
            if self.direction == 'vertical':
                smoothed = self.smoother.smooth(dy)
                return {"active": True, "value": smoothed, "axis": "volume"}
            elif self.direction == 'horizontal':
                smoothed = self.smoother.smooth(dx)
                return {"active": True, "value": smoothed, "axis": "filter_intensity"}
        
        return {"active": True, "value": 0, "axis": None}
```

### 4.6 Regras de conflito e prioridade

Para evitar acionamentos acidentais, o sistema segue estas regras:

```python
GESTURE_PRIORITY = [
    "pinch",             # prioridade máxima (contínuo, eixo X/Y)
    "hang_loose",        # toggle de pausa
    "swipe",             # troca de filtro
    "open_hand",         # play/pause
    "peace",             # next track
    "point",             # screenshot
    "thumb_up",          # volume up
    "thumb_down",        # volume down
    "fist",              # mute
]
```

**Regras de exclusão:**

1. **Pinça vs thumbs up/down:** A pinça só ativa quando `dist(tip4, tip8) < 30px`. O thumbs up exige `dist(tip4, tip8) > 50px` E todos os dedos fechados. Não há overlap.
2. **Só um gesto por frame:** O engine avalia na ordem de prioridade e retorna o primeiro match. Se a pinça está ativa, nenhuma outra ação é avaliada.
3. **Cooldown entre ações:** Após disparar uma ação hold, há 1 segundo de cooldown antes de aceitar outro gesto hold. Isso evita double-triggers.
4. **Detecção pausada:** Quando `hang_loose` pausa a detecção, nenhum gesto é processado exceto outro `hang_loose` pra reativar.

### 4.7 Feedback visual — anel radial de confirmação

Quando um gesto hold está sendo mantido, um anel radial aparece ao redor da mão na tela:

```python
def draw_hold_indicator(frame, hand_center, progress, color=(0, 200, 100)):
    """
    Desenha anel circular que preenche de 0° a 360° conforme o hold progress.
    
    Args:
        frame: frame OpenCV
        hand_center: (x, y) centro da mão detectada
        progress: float 0.0 a 1.0 (0.5s de hold)
        color: BGR color do anel
    """
    radius = 60
    thickness = 4
    start_angle = -90  # começa no topo
    end_angle = start_angle + int(360 * progress)
    
    cv2.ellipse(
        frame, hand_center, (radius, radius),
        0, start_angle, end_angle,
        color, thickness, cv2.LINE_AA
    )
    
    # Anel de fundo (cinza translúcido)
    cv2.ellipse(
        frame, hand_center, (radius, radius),
        0, 0, 360,
        (100, 100, 100), 1, cv2.LINE_AA
    )
```

Quando o anel completa 100%, a ação dispara e um breve flash visual confirma a execução.

---

## 5. Frontend — UI components

### 5.1 Layout principal

```
┌───────────────────────────────────────────────────────┐
│  Gesture AI Desk                        [⚙️ Settings] │
├───────────────────────────────┬────────────────────────┤
│                               │                        │
│                               │  Gesture detected      │
│        Camera Feed            │  ┌──────────────────┐  │
│        (canvas)               │  │  ✋ Open Hand     │  │
│                               │  │  Hold: ████░ 80% │  │
│        + Landmark overlay     │  └──────────────────┘  │
│        + Hold indicator       │                        │
│        + Filter applied       │  Active filter         │
│                               │  ┌──────────────────┐  │
│                               │  │  🎨 Edge Detect  │  │
│                               │  │  Intensity: 72%  │  │
│                               │  └──────────────────┘  │
│                               │                        │
│                               │  System status         │
│                               │  ┌──────────────────┐  │
│                               │  │  🔊 Volume: 65%  │  │
│                               │  │  ▶️  Playing      │  │
│                               │  │  🎵 Spotify      │  │
│                               │  └──────────────────┘  │
│                               │                        │
├───────────────────────────────┴────────────────────────┤
│  Gesture Log (últimas 5 ações)                         │
│  14:32:05  ✋ Play/Pause triggered                     │
│  14:31:58  🤏 Volume → 65%                             │
│  14:31:42  👉 Swipe → Edge Detection                   │
└───────────────────────────────────────────────────────┘
```

### 5.2 Config panel (settings)

Acessível por modal ou sidebar, permite customizar:

- **Hold duration:** slider 0.3s — 1.0s (default 0.5s)
- **Pinch sensitivity:** slider para threshold de ativação (default 30px)
- **Gesture mappings:** dropdown pra remapear qual gesto dispara qual ação
- **Cooldown:** slider 0.5s — 2.0s (default 1.0s)
- **Camera:** seleção de webcam (se houver múltiplas)
- **FPS target:** 24 / 30 / 60

### 5.3 Componentes React principais

```
src/
├── app/
│   ├── page.tsx              # Layout principal
│   └── layout.tsx            # Root layout
├── components/
│   ├── CameraFeed.tsx        # Canvas com feed da webcam
│   ├── GestureHUD.tsx        # Overlay do gesto detectado
│   ├── FilterStatus.tsx      # Badge do filtro ativo
│   ├── SystemStatus.tsx      # Volume, playback state
│   ├── GestureLog.tsx        # Lista das últimas ações
│   ├── ConfigPanel.tsx       # Modal de configurações
│   └── HoldIndicator.tsx     # Anel radial (CSS/SVG)
├── hooks/
│   ├── useWebSocket.ts       # Conexão WebSocket
│   ├── useGestureState.ts    # Estado do gesto atual
│   └── useConfig.ts          # Configurações do usuário
├── lib/
│   ├── websocket.ts          # Client WebSocket
│   └── types.ts              # TypeScript interfaces
└── styles/
    └── globals.css
```

---

## 6. Estrutura do backend Python

```
gesture-ai-desk/
├── backend/
│   ├── main.py               # Entry point — inicia capture loop + WS server
│   ├── capture.py            # OpenCV camera capture
│   ├── hand_tracker.py       # MediaPipe Hand Landmarker wrapper
│   ├── gesture_engine.py     # Detecção de gestos (regras geométricas)
│   ├── actions.py            # System actions (pynput, pycaw, screenshot)
│   ├── filters.py            # Filtros visuais OpenCV
│   ├── ws_server.py          # FastAPI WebSocket server
│   ├── hold_manager.py       # Lógica de hold timer + cooldown
│   ├── config.py             # Configurações default + runtime
│   └── utils.py              # Helpers (distance, normalize, etc.)
├── frontend/
│   └── (Next.js project)
├── pyproject.toml
├── README.md
├── GESTURE_AI_DESK_PRD.md    # Este documento
└── .gitignore
```

---

## 7. Cronograma MVP (2 semanas)

### Semana 1 — Core Python

| Dia | Entrega |
|---|---|
| D1 | Setup do repo, ambiente virtual, OpenCV capture loop funcionando |
| D2 | MediaPipe Hand Landmarker integrado, landmarks visíveis no frame |
| D3 | Gesture engine: detecção de mão aberta, punho, peace, point |
| D4 | System actions: play/pause, mute, next track via pynput/pycaw |
| D5 | Pinch control: volume contínuo funcionando |
| D6 | Filtros visuais + swipe pra trocar. Hold manager + anel radial |
| D7 | FastAPI WebSocket server enviando frames + estado pro frontend |

### Semana 2 — Frontend + Polish

| Dia | Entrega |
|---|---|
| D8 | Next.js setup, WebSocket hook, CameraFeed renderizando frames |
| D9 | GestureHUD + FilterStatus + SystemStatus componentes |
| D10 | Config panel com sliders de hold/pinch/cooldown |
| D11 | GestureLog + HoldIndicator (anel SVG/CSS) |
| D12 | Polish visual: animações, transições, responsividade |
| D13 | README com GIFs, badges, instruções de setup |
| D14 | Testes finais, bug fixes, gravação de demo |

---

## 8. Roadmap — Fase 2 (pós-MVP)

Features adiadas para iteração futura:

### 8.1 Scanner inteligente (YOLO/MobileNet)
- Apontar para objeto na mesa e classificar visualmente
- Stack: YOLOv8 nano via ultralytics ou MobileNet via TFLite
- GPU NVIDIA + CUDA permite inferência rápida
- Highlight visual com bounding box + label no frame

### 8.2 Modo apresentador
- Troca de slides (próximo/anterior) por gesto
- "Laser virtual" — ponto vermelho na tela que segue a ponta do indicador
- Anotações no ar — desenhar com o dedo no espaço da câmera
- Integração com teclas de seta / Page Up / Page Down

### 8.3 Perfis de uso
- **Modo streamer:** gestos mapeados pra OBS (start/stop recording, switch scene)
- **Modo produtividade:** alt-tab, win+d, snap windows
- **Modo custom:** perfis salvos pelo usuário no config panel

### 8.4 Melhorias técnicas
- Suporte a mão esquerda (toggle ou detecção automática)
- Calibração automática de thresholds por tamanho da mão
- Histórico de gestos com analytics no dashboard
- Export de configurações (JSON)
- Tray icon com status (rodando/pausado)

---

## 9. Considerações técnicas

### 9.1 Performance

- **Target:** 30fps no pipeline completo (captura → landmarks → gesto → filtro → WebSocket)
- **Bottleneck esperado:** Encoding JPEG dos frames pra base64. Mitigação: usar `cv2.imencode` com quality 70-80, ou enviar frames reduzidos (640x480) pro WebSocket enquanto processa em 1080p
- **MediaPipe:** Hand Landmarker é otimizado pra CPU e roda a ~30fps em hardware moderno. Não precisa de CUDA pra essa parte
- **Thread separation:** Capture loop em thread separada do WebSocket server. Usar `asyncio.Queue` pra comunicação

### 9.2 Robustez da detecção

- **Iluminação:** MediaPipe é razoavelmente robusto, mas iluminação lateral forte causa sombras que confundem. Documentar no README que luz frontal funciona melhor
- **Distância:** Ideal entre 40-80cm da câmera. Muito perto satura, muito longe perde precisão nos landmarks
- **Smoothing:** Aplicar média móvel (3-5 frames) nos landmarks pra evitar jitter. MediaPipe já tem `min_tracking_confidence` que ajuda
- **Debounce de ações:** Cooldown de 1s entre ações hold evita repetição acidental

### 9.3 Segurança

- WebSocket roda em `localhost` apenas — sem exposição externa
- Nenhuma imagem é salva ou transmitida fora da máquina (exceto screenshots explícitos)
- Sem dependência de API externa — 100% offline

---

## 10. Definição de "pronto" (MVP)

O MVP está completo quando:

- [ ] Webcam captura e exibe feed em tempo real no frontend React
- [ ] 7 gestos estáticos são detectados corretamente (mão aberta, punho, peace, point, thumb up, thumb down, hang loose)
- [ ] Swipe horizontal troca filtros visuais
- [ ] Pinça polegar+indicador controla volume (eixo vertical) e intensidade de filtro (eixo horizontal)
- [ ] Hold de 0.5s com anel radial visual antes de disparar ações
- [ ] Play/pause, mute, next track, volume ±5%, screenshot funcionam
- [ ] Hang loose pausa/retoma detecção
- [ ] Config panel permite ajustar hold duration, pinch sensitivity e cooldown
- [ ] Gesture log mostra últimas 5 ações com timestamp
- [ ] README com instruções de setup, GIFs de demo e badges
- [ ] Zero dependência de API externa — roda 100% offline

---

## 11. Lições extraídas do Computer-Automation (referência)

Análise do repositório [Viral-Doshi/Gesture-Controlled-Virtual-Mouse](https://github.com/Viral-Doshi/Gesture-Controlled-Virtual-Mouse) (773 stars, mesmo codebase que gaurav-aditya/Computer-Automation). Abaixo, os padrões técnicos úteis extraídos e como adaptá-los ao nosso projeto.

### 11.1 Gesture encoding via binary bitmask (ADOTAR)

O repo original codifica gestos como bitmask binário — cada dedo é 1 bit. Isso permite comparar gestos com operações bitwise em vez de `if/elif` encadeados.

**O padrão deles:**
```python
# Cada dedo = 1 bit: THUMB(16) INDEX(8) MID(4) RING(2) PINKY(1)
FIST  = 0b00000  # 0  — nenhum dedo
PALM  = 0b11111  # 31 — todos abertos
V_GEST = 0b01100  # 12 — indicador + médio
INDEX  = 0b01000  # 8  — só indicador
```

**Como adaptar no nosso projeto:**
```python
from enum import IntEnum

class Gesture(IntEnum):
    """Gestos codificados como bitmask de 5 bits: THUMB|INDEX|MID|RING|PINKY"""
    FIST        = 0b00000  # 0  — Mute toggle
    PALM        = 0b11111  # 31 — Play/Pause
    PEACE       = 0b01100  # 12 — Next track
    POINT       = 0b01000  # 8  — Screenshot
    THUMB_UP    = 0b10000  # 16 — Volume up
    HANG_LOOSE  = 0b10001  # 17 — Pause detecção

    # Gestos especiais (não mapeáveis por bitmask simples)
    PINCH_VOLUME  = 33  # Pinça polegar+indicador
    PINCH_FILTER  = 34  # Pinça polegar+médio
    SWIPE_LEFT    = 35
    SWIPE_RIGHT   = 36
    THUMB_DOWN    = 37  # Requer check adicional de posição Y
```

**Vantagem:** O `set_finger_state()` computa o bitmask uma vez por frame, e o gesto cai direto num `IntEnum` sem cascata de ifs. Gestos especiais (pinch, swipe, thumb_down) são tratados separadamente antes do lookup por bitmask.

### 11.2 Gesture stabilization com frame counter (ADOTAR)

O repo original usa um padrão de estabilização que é simples e eficaz: o gesto só é "oficializado" após ser detectado consistentemente por N frames consecutivos. Isso elimina flickering.

**Como adaptar:**
```python
class GestureStabilizer:
    """
    Exige que um gesto seja detectado por `threshold` frames consecutivos
    antes de ser considerado válido. Evita falsos positivos por ruído.
    """
    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self.prev_gesture = Gesture.PALM
        self.frame_count = 0
        self.stable_gesture = Gesture.PALM

    def update(self, detected_gesture: Gesture) -> Gesture:
        if detected_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0
        
        self.prev_gesture = detected_gesture
        
        if self.frame_count >= self.threshold:
            self.stable_gesture = detected_gesture
        
        return self.stable_gesture
```

**Nota:** No repo original o threshold é 4 frames. Para nosso projeto, recomendamos 5 frames (~170ms a 30fps). Isso trabalha *junto* com o hold timer de 0.5s — primeiro o gesto estabiliza (170ms), depois o hold começa a contar (500ms). Total: ~670ms entre iniciar o gesto e disparar a ação. Parece muito, mas na prática é imperceptível porque o anel radial dá feedback visual imediato.

### 11.3 Cursor dampening / smoothing (ADOTAR ADAPTADO)

O repo original implementa dampening proporcional à velocidade do movimento. Movimentos pequenos (<5px) são ignorados, médios são amortecidos, e grandes passam quase direto. Isso elimina o jitter sem adicionar lag perceptível.

**Como adaptar para o nosso caso (não controlamos cursor, mas usamos para smoothing do pinch):**
```python
class PinchSmoother:
    """
    Aplica dampening ao valor do pinch para evitar jitter.
    Movimentos pequenos são filtrados, grandes passam direto.
    """
    def __init__(self):
        self.prev_value = 0.0
    
    def smooth(self, raw_value: float) -> float:
        delta = raw_value - self.prev_value
        abs_delta = abs(delta)
        
        if abs_delta < 0.01:      # ruído — ignorar
            ratio = 0.0
        elif abs_delta < 0.05:    # movimento pequeno — amortecer
            ratio = 0.3
        else:                     # movimento intencional — passar
            ratio = 0.8
        
        smoothed = self.prev_value + delta * ratio
        self.prev_value = smoothed
        return smoothed
```

### 11.4 Pinch control com direção X/Y separada (ADOTAR)

O repo original detecta se o movimento do pinch é predominantemente horizontal ou vertical, e mapeia cada eixo para uma função diferente (X = brightness, Y = volume). Isso é mais intuitivo que a nossa proposta original de usar dedos diferentes para funções diferentes.

**Decisão de design atualizada:**
```
Pinça polegar + indicador (ativação):
  - Movimento vertical (↑↓) → Controle de volume
  - Movimento horizontal (←→) → Intensidade do filtro ativo

Pinça polegar + médio → REMOVIDA (simplificar para 1 tipo de pinch)
```

**Justificativa:** Usar dois tipos de pinch (polegar+indicador vs polegar+médio) é confuso na prática — o usuário não consegue fazer polegar+médio sem que o indicador atrapalhe. O mapeamento por eixo (X/Y) do mesmo pinch é mais natural e mais robusto. Isso também simplifica o código.

**Implementação atualizada:**
```python
class PinchController:
    def __init__(self, threshold: float = 0.3):
        self.active = False
        self.start_x = 0.0
        self.start_y = 0.0
        self.direction = None  # 'horizontal' ou 'vertical'
        self.threshold = threshold
    
    def update(self, thumb_tip, index_tip) -> dict:
        dist = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        
        if dist < 0.05 and not self.active:  # ativação
            self.active = True
            self.start_x = index_tip.x
            self.start_y = index_tip.y
            self.direction = None
            return {"active": True, "value": 0, "axis": None}
        
        if dist > 0.12:  # desativação (dedos se afastaram)
            self.active = False
            self.direction = None
            return {"active": False}
        
        if self.active:
            dx = (index_tip.x - self.start_x) * 10
            dy = (self.start_y - index_tip.y) * 10  # Y invertido
            
            # Determina direção no primeiro movimento significativo
            if self.direction is None:
                if abs(dy) > abs(dx) and abs(dy) > self.threshold:
                    self.direction = 'vertical'
                elif abs(dx) > self.threshold:
                    self.direction = 'horizontal'
            
            if self.direction == 'vertical':
                return {"active": True, "value": dy, "axis": "volume"}
            elif self.direction == 'horizontal':
                return {"active": True, "value": dx, "axis": "filter_intensity"}
        
        return {"active": True, "value": 0, "axis": None}
```

### 11.5 Volume control via pycaw COM API (ADOTAR)

O repo original usa pycaw para controle direto de volume via Windows COM API, sem simular teclas de mídia. Isso é mais preciso e permite set absoluto.

```python
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(level: float):
    """level: 0.0 a 1.0"""
    volume = get_volume_interface()
    volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level)), None)

def get_volume() -> float:
    volume = get_volume_interface()
    return volume.GetMasterVolumeLevelScalar()

def toggle_mute():
    volume = get_volume_interface()
    current = volume.GetMute()
    volume.SetMute(not current, None)
```

**Nota:** Isso substitui `pynput` para volume. Mantemos `pynput` apenas para media keys (play/pause, next track) e screenshot.

### 11.6 Finger state via signed distance ratio (ADOTAR)

O repo original determina se um dedo está aberto usando a razão entre distâncias (tip→PIP vs PIP→wrist), em vez de comparar coordenadas Y diretamente. Isso é mais robusto para diferentes ângulos da mão.

**Atualização no nosso `is_finger_extended`:**
```python
def is_finger_extended(landmarks, tip_id: int, pip_id: int, wrist_id: int = 0) -> bool:
    """
    Usa razão de distâncias signed em vez de comparação Y pura.
    Mais robusto para mão inclinada ou rotacionada.
    """
    dist_tip_pip = signed_distance(landmarks[tip_id], landmarks[pip_id])
    dist_pip_wrist = signed_distance(landmarks[pip_id], landmarks[wrist_id])
    
    if abs(dist_pip_wrist) < 0.01:
        return False  # evita divisão por zero
    
    ratio = dist_tip_pip / dist_pip_wrist
    return ratio > 0.5

def signed_distance(p1, p2) -> float:
    """Distância euclidiana com sinal baseado no eixo Y."""
    sign = 1 if p1.y < p2.y else -1
    dist = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    return dist * sign
```

### 11.7 O que NÃO adotar do repo original

- **Classe monolítica `GestureController`** — 600 linhas num arquivo. Nosso projeto mantém separação em módulos (`capture.py`, `hand_tracker.py`, `gesture_engine.py`, etc.)
- **Variáveis de classe estáticas em `Controller`** — estado global. Nosso projeto usa instâncias com state management adequado.
- **`pyautogui` para mouse** — desnecessário, nosso projeto não controla cursor.
- **Voice assistant (Proton)** — completamente fora do escopo.
- **Python 3.8.5** — nosso projeto usa 3.11+.
- **`image.flags.writeable = False`** — otimização prematura que complica debug.
- **Suporte a duas mãos com major/minor** — complexidade desnecessária para MVP com mão direita apenas.

---

## 12. Guia de implementação com IA (Claude Code + Codex no VS Code)

Este guia descreve como usar o PRD para construir o projeto de forma eficiente usando coding agents no VS Code.

### 12.1 Setup inicial do ambiente

Execute no terminal do Windows (PowerShell):

```powershell
# 1. Criar diretório do projeto
mkdir gesture-ai-desk
cd gesture-ai-desk

# 2. Inicializar git
git init

# 3. Criar ambiente virtual Python
python -m venv .venv
.venv\Scripts\activate

# 4. Instalar dependências Python
pip install opencv-python mediapipe fastapi uvicorn pynput pycaw numpy Pillow comtypes websockets

# 5. Criar frontend Next.js
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --no-import-alias
cd frontend && pnpm install && cd ..

# 6. Criar estrutura de pastas do backend
mkdir backend
cd backend
New-Item main.py, capture.py, hand_tracker.py, gesture_engine.py, actions.py, filters.py, ws_server.py, hold_manager.py, config.py, utils.py -ItemType File
cd ..

# 7. Copiar o PRD para o repositório
# (copie GESTURE_AI_DESK_PRD.md para a raiz do projeto)

# 8. Criar .gitignore
```

Conteúdo do `.gitignore`:
```
.venv/
__pycache__/
*.pyc
node_modules/
.next/
.env
```

### 12.2 Estratégia de prompting — dividir em sprints

**REGRA DE OURO:** Nunca peça ao agente para construir tudo de uma vez. Divida em tasks pequenas e atômicas. Cada prompt deve gerar um resultado testável isoladamente.

### 12.3 Sprint 1 — Camera capture + MediaPipe (Dia 1-2)

**Prompt para Claude Code / Codex:**
```
Leia o arquivo GESTURE_AI_DESK_PRD.md na raiz do projeto — ele é a spec 
completa do projeto. Foque nas seções 3 (Arquitetura), 4.1-4.2 
(MediaPipe Landmarks) e 11.6 (signed distance ratio).

TASK: Implemente os seguintes arquivos do backend:

1. backend/config.py — Dataclass com todas as configurações:
   - CAMERA_INDEX = 0
   - CAMERA_WIDTH = 1280, CAMERA_HEIGHT = 720
   - MEDIAPIPE_MIN_DETECTION = 0.7, MIN_TRACKING = 0.7
   - MAX_HANDS = 1
   - TARGET_FPS = 30

2. backend/utils.py — Funções helper:
   - signed_distance(p1, p2) -> float (seção 11.6 do PRD)
   - euclidean_distance(p1, p2) -> float
   - normalize_value(value, min_val, max_val) -> float (0-1)

3. backend/capture.py — Classe CameraCapture:
   - __init__(config) — abre cv2.VideoCapture
   - read_frame() -> np.ndarray ou None
   - release() — libera câmera
   - Flip horizontal (cv2.flip(img, 1)) aplicado automaticamente

4. backend/hand_tracker.py — Classe HandTracker:
   - __init__(config) — inicializa mp.solutions.hands
   - process(frame) -> HandResult | None
   - HandResult contém: landmarks (list), handedness (str), 
     raw_result (para drawing utils)
   - Retorna None se nenhuma mão detectada

5. backend/main.py — Script de teste:
   - Loop que captura frame, processa landmarks, desenha na tela 
     com mp_drawing, mostra com cv2.imshow
   - Pressionar 'q' sai
   - Deve mostrar os 21 landmarks na tela em tempo real

Não implemente gestos ainda. Foco total em captura + landmarks 
funcionando. Use type hints em tudo. Docstrings em inglês.

Teste: ao rodar `python backend/main.py`, a webcam deve abrir e 
mostrar os landmarks da mão desenhados no frame.
```

### 12.4 Sprint 2 — Gesture engine (Dia 3-4)

**Prompt para Claude Code / Codex:**
```
Leia GESTURE_AI_DESK_PRD.md, foque nas seções 4.3-4.6 (mapeamento 
de gestos), 11.1 (bitmask encoding), 11.2 (stabilizer), e 11.6 
(signed distance ratio).

TASK: Implemente o gesture engine:

1. backend/gesture_engine.py:
   - Enum Gesture (IntEnum) com bitmask encoding (seção 11.1)
   - Classe GestureStabilizer (seção 11.2, threshold=5 frames)
   - Classe GestureDetector:
     * compute_finger_state(landmarks) -> int (bitmask)
     * detect_pinch(landmarks) -> dict (seção 11.4, PinchController)
     * detect_swipe(wrist_history) -> str|None (seção 4.4)
     * detect_gesture(landmarks) -> Gesture
       - Primeiro checa pinch (prioridade máxima)
       - Depois checa swipe
       - Depois resolve bitmask para Gesture enum
       - Aplica GestureStabilizer
     * Regra de conflito thumbs vs pinch (seção 4.6)
   - Classe PinchController com detecção de eixo X/Y (seção 11.4)
   - Classe PinchSmoother com dampening (seção 11.3)

2. Atualize backend/main.py:
   - Após detectar landmarks, passe pelo GestureDetector
   - Imprima o gesto detectado no console
   - Desenhe o nome do gesto no frame com cv2.putText

Gestos a detectar: PALM, FIST, PEACE, POINT, THUMB_UP, THUMB_DOWN, 
HANG_LOOSE, PINCH (com eixo), SWIPE_LEFT, SWIPE_RIGHT.

Teste: rodar main.py, fazer gestos na câmera, ver o nome correto 
impresso no frame e no console.
```

### 12.5 Sprint 3 — System actions + Hold manager (Dia 5-6)

**Prompt para Claude Code / Codex:**
```
Leia GESTURE_AI_DESK_PRD.md, seções 4.3 (ações), 4.5 (pinch), 
4.7 (anel radial), 11.5 (pycaw volume).

TASK: Implemente ações do sistema e hold manager:

1. backend/hold_manager.py:
   - Classe HoldManager:
     * __init__(hold_duration=0.5, cooldown=1.0)
     * update(gesture, timestamp) -> dict com:
       - hold_progress: float 0.0 a 1.0
       - action_triggered: bool
       - in_cooldown: bool
     * Lógica: gesto precisa ser mantido por hold_duration 
       segundos antes de disparar. Após disparar, cooldown 
       impede re-trigger.
     * Pinch NÃO passa pelo hold — é contínuo.

2. backend/actions.py:
   - Funções isoladas para cada ação:
     * toggle_play_pause() — Key.media_play_pause via pynput
     * toggle_mute() — pycaw (seção 11.5)
     * next_track() — Key.media_next via pynput
     * set_volume(level: float) — pycaw SetMasterVolumeLevelScalar
     * get_volume() -> float — pycaw GetMasterVolumeLevelScalar
     * volume_up(step=0.05) / volume_down(step=0.05)
     * take_screenshot(save_dir) — Pillow ImageGrab
     * Cada função tem try/except e logging

3. backend/filters.py:
   - apply_filter(frame, filter_name, intensity=1.0) -> frame
   - Filtros: normal, grayscale, edge_detection, blur, 
     landmark_highlight
   - get_filter_list() -> list[str]
   - next_filter(current_index) / prev_filter(current_index)

4. Atualize backend/main.py:
   - Integre HoldManager com o GestureDetector
   - Desenhe anel radial de progresso (seção 4.7) no frame
   - Ações disparam de verdade (play/pause, volume, etc.)
   - Pinch controla volume em tempo real
   - Swipe troca filtros visuais aplicados ao frame

Teste: rodar main.py, fazer gesto de mão aberta por 0.5s, 
play/pause deve disparar. Pinch deve ajustar volume do sistema.
```

### 12.6 Sprint 4 — WebSocket bridge (Dia 7)

**Prompt para Claude Code / Codex:**
```
Leia GESTURE_AI_DESK_PRD.md, seções 3.1-3.2 (fluxo e protocolo 
WebSocket).

TASK: Implemente o servidor WebSocket:

1. backend/ws_server.py:
   - FastAPI app com WebSocket endpoint em ws://localhost:8765
   - Classe GestureServer:
     * Integra CameraCapture, HandTracker, GestureDetector, 
       HoldManager, Actions, Filters
     * Loop assíncrono que processa frames e envia JSON 
       (formato exato da seção 3.2)
     * Frame encoded como base64 JPEG (quality 75, resize 
       para 640x480 para reduzir bandwidth)
     * Recebe comandos de config do frontend (update_config)
   - Entry point: uvicorn ws_server:app --host 0.0.0.0 --port 8765

2. O main.py antigo deve continuar funcionando como modo standalone 
   (sem WebSocket, com cv2.imshow). Adicione flag --mode ws|standalone.

Teste: rodar `python backend/ws_server.py`, conectar via wscat ou 
browser console a ws://localhost:8765, verificar que JSON com frame 
base64 é recebido a cada ~33ms.
```

### 12.7 Sprint 5 — Frontend React (Dia 8-11)

**Prompt para Claude Code / Codex:**
```
Leia GESTURE_AI_DESK_PRD.md, seção 5 (Frontend UI components) 
completa.

TASK: Implemente o frontend Next.js:

1. frontend/src/lib/types.ts — Interfaces TypeScript para o 
   protocolo WebSocket (seção 3.2)

2. frontend/src/hooks/useWebSocket.ts — Custom hook:
   - Conecta a ws://localhost:8765
   - Reconnect automático com backoff exponencial
   - Retorna: frame (base64), gestureState, pinchState, 
     activeFilter, connected, sendConfig()

3. frontend/src/components/CameraFeed.tsx:
   - Canvas que renderiza frame base64 recebido via WebSocket
   - Overlay com landmarks (opcional, toggle)
   - Aspect ratio 16:9

4. frontend/src/components/GestureHUD.tsx:
   - Card mostrando gesto atual detectado
   - Barra de progresso do hold (0-100%)
   - Ícone/emoji do gesto
   - Animação suave de transição entre gestos

5. frontend/src/components/FilterStatus.tsx:
   - Badge com nome do filtro ativo
   - Barra de intensidade (quando pinch está controlando)

6. frontend/src/components/SystemStatus.tsx:
   - Volume atual (barra + percentual)
   - Estado de playback (playing/paused)
   - Estado de mute (on/off)

7. frontend/src/components/GestureLog.tsx:
   - Lista das últimas 5 ações com timestamp
   - Auto-scroll, animação de entrada

8. frontend/src/components/ConfigPanel.tsx:
   - Modal/sidebar com sliders:
     * Hold duration (0.3-1.0s)
     * Pinch sensitivity
     * Cooldown (0.5-2.0s)
   - Envia config via WebSocket sendConfig()

9. frontend/src/app/page.tsx — Layout conforme seção 5.1:
   - Grid: câmera (esquerda) + painel de status (direita)
   - Gesture log embaixo
   - Header com título + botão de settings

Design: Tailwind CSS, tema escuro por padrão, visual clean e 
moderno. Sem bibliotecas de componentes externas além de Tailwind.
O visual deve parecer dashboard de produto, não projeto acadêmico.
```

### 12.8 Sprint 6 — Polish e README (Dia 12-14)

**Prompt para Claude Code / Codex:**
```
Leia GESTURE_AI_DESK_PRD.md, seção 10 (definition of done).

TASK: Polish final e README:

1. Revise TODOS os arquivos e garanta:
   - Type hints completos
   - Docstrings em inglês
   - Error handling adequado (try/except com logging)
   - Nenhum print() solto (usar logging module)

2. Crie README.md com:
   - Hero section com título + descrição + badges (Python, Next.js, 
     MediaPipe, OpenCV)
   - GIF placeholder (instruções de como gravar e inserir)
   - Features list com emoji
   - Seção "How it works" com diagrama ASCII simplificado
   - Quick start (prereqs, install, run backend, run frontend)
   - Tabela de gestos com colunas: Gesto | Ação | Tipo (hold/contínuo)
   - Stack section
   - Project structure (tree)
   - Roadmap (Phase 2 features)
   - License (MIT)
   - Link para o PRD

3. Crie requirements.txt com versões pinadas

4. Crie package.json scripts:
   - "dev" — roda frontend
   - "backend" — roda backend ws_server
   - "start" — roda ambos (concurrently)

Passe pelo checklist da seção 10 e confirme cada item.
```

### 12.9 Dicas práticas para usar os agents

**Com Claude Code (terminal):**
```bash
# Iniciar Claude Code no diretório do projeto
claude

# Primeiro comando — sempre dar contexto
> Leia o arquivo GESTURE_AI_DESK_PRD.md e me diga se entendeu 
  a arquitetura. Não implemente nada ainda.

# Depois, copie os prompts dos sprints acima um por um
```

**Com Codex no VS Code:**
- Abra o PRD como tab fixo — o Codex usa arquivos abertos como contexto
- Abra também o arquivo que quer que ele edite
- Use o prompt do sprint correspondente no chat lateral
- Após cada sprint, **teste manualmente** antes de seguir pro próximo

**Regras de ouro:**
1. **Um sprint por vez.** Não pule sprints. Cada um depende do anterior.
2. **Teste antes de avançar.** Se o sprint 1 não funciona, o sprint 2 vai quebrar.
3. **Comite após cada sprint.** `git add . && git commit -m "Sprint N: descrição"`
4. **Se o agente errar,** não descarte tudo. Diga: "O arquivo X tem um bug: [descreva]. Corrija mantendo o resto."
5. **PRD é a source of truth.** Se o agente propuser algo diferente do PRD, questione. O PRD foi pensado com cuidado.
6. **Cole erros inteiros.** Quando algo falhar, copie o traceback completo pro agente. Não resuma o erro.

### 12.10 Ordem de execução resumida

```
Dia 1-2:  Sprint 1 → Câmera + MediaPipe landmarks funcionando
Dia 3-4:  Sprint 2 → Gesture engine detectando todos os gestos
Dia 5-6:  Sprint 3 → Ações do sistema + hold + pinch + filtros
Dia 7:    Sprint 4 → WebSocket bridge conectando back→front
Dia 8-11: Sprint 5 → Frontend React completo
Dia 12-14: Sprint 6 → Polish + README + testes finais
```

Cada sprint tem um teste claro. Se o teste passa, avance. Se não passa, corrija antes de seguir.

---

*Documento gerado em março de 2026. Versão 2.0 — atualizado com análise do Computer-Automation e guia de implementação com IA.*
