  **um `main.py` completo, em POO** , que usa **MediaPipe** (pose) + **YOLO (Ultralytics)** para detectar a **bola** (classe `sports ball`) e a **pessoa** (via pose), contar **push-ups** e **embaixadinhas (keepie-uppies)** em tempo real com a webcam e exibir tudo na tela (contadores, FPS, dicas). Também explico como calibrar, instalar dependências e **opcionalmente** conectar um Arduino via serial pra receber o número de repetições.

> Observação importante: detecção perfeita depende de iluminação, ângulo da câmera e qualidade do modelo YOLO. Teste/combine thresholds e zonas de proximidade para reduzir falsos positivos.

---

## O que o script faz (resumo)

* **PoseCounter** : usa MediaPipe Pose para contar push-ups com base no ângulo do cotovelo (subida/descida).
* **BallDetector** : usa YOLO para detectar a bola (classe `sports ball`) e combina com landmarks do MediaPipe (nariz/tornozelos) para estimar toques (head/foot).
* **VideoApp** : captura vídeo da webcam, une tudo, desenha overlays (contadores, barras, mensagens).
* **Serial (opcional)** : envia contagens para Arduino via USB/Serial (usar `pyserial`).

---

## Ajustes / calibração (essenciais)

* **threshold_down / threshold_up** em `PoseCounter`: teste com você fazendo pushups até definir bons valores (ex.: 90 e 160). Se sua câmera tiver ângulo lateral, ajuste.
* **cooldown_time** em `BallDetector`: reduz contagens duplicadas em toques muito rápidos.
* **threshold_head / threshold_foot** em `BallDetector.try_count_touch`: multiplicadores baseados na altura do frame (`h * 0.08` etc.). Ajuste se detectar muitos falsos positivos.
* **Se YOLO não detectar a bola** : confira se o nome do rótulo corresponde (alguns modelos têm label `sports ball`, `ball`, etc.). Use `print(r.names)` para inspecionar.

---

## Dicas práticas de gravação

* Posicione a câmera frontal/um pouco acima da sua cabeça para pegar corpo todo e a bola.
* Fundo liso e boa iluminação = menor ruído.
* Use bola com cor contrastante (não muito pequena) para melhorar a detecção.
* Faça testes curtos (30s) e ajuste thresholds.

---

## Integração Arduino (opcional)

* No `main.py`, ative `--arduino --port COM3` (ajuste porta).
* No Arduino, abra `Serial.begin(115200)` e leia linhas `P,<pushups>,<embaixadas>\n`.
* Exemplo Arduino pseudo:

<pre class="overflow-visible!" data-start="14998" data-end="15220"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"></div></pre>
