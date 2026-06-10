# AUDITORÍA — AFRICA STRIKES BACK
> Generada 2026-06-10 noche (loop autónomo). Verificado con Playwright en prod (despedida-mario-africa.vercel.app) a 390×844 y 1280×800 + lectura completa del flujo JS.
> Convención: una tarea = un commit verificado = se tacha aquí.

## P0 — Bugs que rompen el juego

- [x] **P0.1 Juego fantasma al pulsar "VOLVER AL MENÚ" en la transition card.** ✅ d28d482 — resolve {cancelled:true} antes del dispatch; verificado Playwright (back→sin ghost, start→juego OK).
  Reproducido en prod: `jumpToRound(7)` → click `transition-back-btn` → quedas en `screen-victims` PERO `body.game-running=true` y el clicker está montado en el stage oculto con key handlers + timers vivos. Al expirar el juego llama `showResult` (la guard `game-running` pasa porque `startGame` la re-activó) → suma chupitos a una ronda que el jugador canceló y dispara `resolve` en el API.
  **Causa raíz**: en `showTransitionCard` (index.html:3894-3920), el handler del back llama `backToVictims()` que despacha `start-game`; el listener `document('start-game')` resuelve la promise con `undefined` ANTES de que el handler ejecute `resolveOuter({cancelled:true})` → `jumpToRound`/`nextRound` ven "no cancelado" y llaman `startGame(v)`.
  **Fix**: resolver `{cancelled:true}` ANTES de llamar `backToVictims()` (o flag `cancelled` que el listener de start-game consulte).

- [x] **P0.2 Toast pegado para siempre en móvil (multilínea).** ✅ — opacity gate + pointer-events:none; verificado Playwright (expira→0, cambio de pantalla→0).
  Reproducido: toast "⏱ TIMEOUT — Paz lo toma como mentira" (3 líneas a 390px) sigue visible 3 pantallas y varios minutos después (map → final). `clearToast()`/timer quitan `.visible`, pero el estado oculto es solo `translateY(-150px)` con `top:90px` (index.html:1933-1951) — un toast de ~70px+ de alto sigue asomando por arriba. `opacity` queda a 1 siempre.
  **Fix**: `.toast { opacity:0; pointer-events:none; }` + `.toast.visible { opacity:1; }` (mantener el translate para la animación).

## P1 — Cambios confirmados por Javier (alta prioridad)

> **MANDATO GRÁFICO (Javier 2026-06-10 noche): luz verde para cambiar los gráficos y hacer algo más profesional aún.** Aplica a mapa (P1.D), rhythm (P1.C), intro (P1.E) y a cualquier juego/pantalla que lo necesite — siempre dentro de las lecciones (colores planos GBC, raster pixelated, sin viewBox zoom).

- [ ] **P1.A Quiz F1 (ronda 6): REVERTIR al set simple** anterior a af4e461 / be051ec / 283a2e1 (humor negro + troll). Extraer el set previo con `git show 830ffbc:index.html` (F1_QUESTIONS es). Sincronizar `instruction` de Helmer (es dice "21 preguntas — humor MUY negro"; gl/ng dicen 12). Verificar quiz completo tras revert.

- [ ] **P1.B ¿QUIÉN QUIERE SER MILLONARIO? — nuevo minijuego que SUSTITUYE la ronda 11** (fuera el polígrafo de Paz de esa posición).
  - 6-7 preguntas A/B/C/D dificultad creciente, lore Mario+Anna (UFV, F1 Fantasy África, Menorca sept 2025, boda Cádiz 2026, "¡Mil veces sí!", Noniná, Paz Sálvame, Albert ex-Barça). Array JS comentado y editable (Javier las ajusta mañana).
  - Comodín del público: voto QR Neon. ⚠️ `api/vote.js` solo acepta `choice 0|1` y `api/state.js` solo devuelve counts si/no → extender a `choice 0..3` + counts por opción (compat si/no intacta) + página móvil con botones A/B/C/D cuando round id ∈ rango comodín (p.ej. 800+N).
  - Presentador: copys + dramatismo + luces; voz `speechSynthesis` es-ES tras flag `MILLONARIO_VOICE_ENABLED` (Javier meterá voces grabadas después).
  - Integración completa: transition card (apuestas) → juego → showResult → ranking. Actualizar VICTIMS[10] (nombre del juego, instruction, i18n gl/ng).
  - Decidir destino de `gamePoligrafo`: queda sin víctima → ¿borrar o conservar? (ver P5.1).

- [ ] **P1.C Ronda 3 (Lulu's Revenge, rhythm): mejora integral "a todos los niveles"** (pedido por Javier 2026-06-10).
  - Jugabilidad: revisar ritmo/densidad del chart, ventanas de hit, claridad de los holds, curva de dificultad.
  - Móvil 390px: botones táctiles D/F/J/K pegados/cortados en el borde inferior (safe-area), Lulu (cabra, esquina sup. dcha.) tapada por notas, contraste de carriles.
  - Visual: zona de hit más legible, feedback de acierto/fallo más gordo, scorecard.
  - Verificar partida completa en móvil y desktop tras los cambios.

- [ ] **P1.D Mapa Tenerife: rediseño — "no se entiende na" (Javier).**
  Confirmado en prod: la isla pinta NEGRA (fill computado `rgb(0,0,0)` — el gradiente no se aplica), el SVG mide 176×100px en móvil y los 12 pins (existen en DOM) son invisibles. En desktop igual: borrón negro.
  **Plan**: tilemap pixel-art Pokemon GBC (colores planos, NO gradientes, NO spotlight, transforms raster con image-rendering:pixelated si hay raster), isla reconocible, 12 pins estilo gimnasio visibles y clicables, pin activo destacado, ruta del progreso. Respetar lecciones: pins próximos → dy manual + alternar lado.

- [ ] **P1.E Intro: ritmo y limpieza — "hay cosas lentas, hay imagenes sin sentido" (Javier).**
  Revisar `startIntro` completo: terminal (delays), counter 4.7M, mapa África con 12 labels (hold de 10s — candidato a recorte), WANTED poster, crawl 40s. Acortar tiempos muertos, eliminar/arreglar imágenes que no se entienden, asegurar que el botón "Saltar intro ▸" está siempre visible y que cada beat aporta. El mapa de África pixel-art se mantiene (es de las cosas buenas) pero los labels no deben bloquear 10s.

## P2 — Fricción / bugs móvil (390px)

- [ ] **P2.1 Pantalla final: lang-pills (ES/GL/NAIJA) pisan el pretitle** "DAMAGE REPORT — JUICIO CERRADO" a 390px. Padding-top o esconder pills en screen-final.
- [ ] **P2.2 Rhythm: fila de botones táctiles cortada por el borde inferior** (se solapa con P1.C — resolver ahí).
- [ ] **P2.3 Result screen: scroll-to-top al renderizar** (pendiente del playtest; en móvil aterrizas a mitad de scroll).
- [ ] **P2.4 favicon 404** en todas las cargas — meter favicon inline (data URI emoji 🏁/🥃) y matar el error de consola.

## P3 — Jugabilidad floja

- [ ] **P3.1 Rush (ronda 1) visualmente pobre** — añadir taxi animado / ambiente Lagos (pendiente del playtest 2026-06-09).
- [ ] **P3.2 Revisar dificultad global**: pase final con las 12 rondas seguidas en móvil para calibrar chupitos/duración (mejor al final, post-cambios).

## P4 — Texturas / UI / copys

- [ ] **P4.1 Copys desactualizados en VICTIMS i18n**: gl/ng de Anna (ronda 12) describen el lore viejo ("vestida de noiva co polígrafo, 6 votos") en vez de Wally; gl/ng de Paz dicen "5 acusacións" vs 7 en es. Tras P1.B revisar también VICTIMS[10] entero.
- [ ] **P4.2 Copy lobby**: "⚠ Si Firebase no está configurado..." — Firebase ya no existe (Neon). Reescribir ("Si un móvil no conecta: voto manual desde el portátil").
- [ ] **P4.3 'esperando móviles...' hardcodeado** en el poll de `openLobby` (index.html:3810) — usar `t('lobby_waiting')`.

## P5 — Deuda de código

- [ ] **P5.1 Dead code `gamePress` + `gamePenalty`** (~250 líneas, sin víctima asignada; `PRACTICE_SUPPORTED` aún lista 'penalty'). **PENDIENTE JAVIER**: ¿recuperar Press Conference para alguna víctima o borrar? (decisión creativa — no borro a ciegas).
- [ ] **P5.2 Flag `FIREBASE_ENABLED` + shims `firebaseDB`/`initFirebase`** — renombrar/limpiar a capa backend Neon (cosmético, bajo riesgo, hacer al final).

## P6 — Features creativas (solo si sobra backlog)

- [ ] **P6.1 Música chiptune loop** Web Audio en menú/mapa (ya hay sfx, falta melodía).
- [ ] **P6.2 Resume de progreso del host** (shots/ronda) si la TV recarga a mitad de partida (apuntado en memoria, no implementado).

## NO TOCAR (lecciones + límites)
- No SVG viewBox zoom sobre pixel art; no spotlight oscuro; colores planos GBC; no SVGs huérfanos en body; pins próximos → dy manual + lado alterno; mantener no-cache headers.
- No fotos reales que no existen (las de Álvaro), no audio grabado inventado, no cambiar lore/orden salvo A y B.
- Commits: email `239983809+javiergonzalez-ctrl@users.noreply.github.com`, add por archivo, push a main tras verificar.

## Evidencia de la auditoría
Capturas en `C:\Users\javi1\IA-Proyectos\audit-0*.jpeg` (start/victims/transition/rhythm/quiz/poligrafo/map 390px + map desktop + final 390px). Bugs P0 reproducidos en vivo contra prod con Playwright.
