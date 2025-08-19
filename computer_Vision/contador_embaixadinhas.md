  **um `main.py` completo, em POO** , que usa **MediaPipe** (pose) + **YOLO (Ultralytics)** para detectar a **bola** (classe `sports ball`) e a **pessoa** (via pose), contar **push-ups** e **embaixadinhas (keepie-uppies)** em tempo real com a webcam e exibir tudo na tela (contadores, FPS, dicas). Também explico como calibrar, instalar dependências e **opcionalmente** conectar um Arduino via serial pra receber o número de repetições.

> Observação importante: detecção perfeita depende de iluminação, ângulo da câmera e qualidade do modelo YOLO. Teste/combine thresholds e zonas de proximidade para reduzir falsos positivos.

---

## O que o script faz (resumo)

* **PoseCounter** : usa MediaPipe Pose para contar push-ups com base no ângulo do cotovelo (subida/descida).
* **BallDetector** : usa YOLO para detectar a bola (classe `sports ball`) e combina com landmarks do MediaPipe (nariz/tornozelos) para estimar toques (head/foot).
* **VideoApp** : captura vídeo da webcam, une tudo, desenha overlays (contadores, barras, mensagens).
* **Serial (opcional)** : envia contagens para Arduino via USB/Serial (usar `pyserial`).

---

## Instalação (recomendada em virtualenv)

<pre class="overflow-visible!" data-start="1219" data-end="1400"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"></div></pre>
