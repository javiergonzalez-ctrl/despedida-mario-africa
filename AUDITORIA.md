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

> **MANDATO GRÁFICO (Javier 2026-06-10/11 noche): luz verde total.** Rediseñar gráficos para algo más profesional Y memorable/atractivo para el jugador. Las lecciones ESTÉTICAS (colores planos GBC estrictos, retro purista) quedan a mi criterio — puedo romperlas si el resultado es mejor. Las lecciones TÉCNICAS se mantienen (no SVG viewBox zoom sobre pixel art = artefactos; no SVGs huérfanos en body = bugs visuales; no-cache headers). Criterio rector: ¿lo recordarán los colegas en la fiesta?

- [x] **P1.A Quiz F1 (ronda 6): REVERTIR al set simple** ✅ — restaurado set de 830ffbc (es: 15 preguntas = 12 F1 + 3 Mario; gl/ng intactas) + instruction de Helmer. Verificado Playwright: 15 dots, preguntas clásicas, avance OK.

- [x] **P1.B ¿QUIÉN QUIERE SER MILLONARIO? — SUSTITUYE la ronda 11.** ✅ ac197d4
  - Paz Padilla pasa de polígrafo a PRESENTADORA (orden de víctimas intacto). 7 preguntas lore en `MILLONARIO_QUESTIONS` (array comentado, editable; chupitos por caída en `MILLONARIO_FAIL_SHOTS`).
  - Formato concurso: intro plató → pregunta → selección → "¿RESPUESTA DEFINITIVA?" → suspense con dim de luces + latidos → reveal. Escalera de premios cachondos. Voz presentador `speechSynthesis` es-ES tras `MILLONARIO_VOICE_ENABLED` (nota: sustituir `millSpeak()` por mp3 cuando Javier traiga voces grabadas).
  - Comodines: 50:50 + EL PÚBLICO (QR Neon, rounds 800+idx, barras % en vivo + botones manuales sin móviles; % quedan pegados a las opciones al cerrar).
  - API extendido: `vote.js` choice 0..3, `state.js` counts.byChoice + **fix prioridad open en activeRound** (bug latente: un round 800/900+ cerrado tapaba las apuestas de rondas posteriores). Móvil: botones A/B/C/D para rounds 800-899.
  - Verificado: Playwright 390px+desktop (flujo win/lose, 50:50, público, % persistentes) + E2E prod (vote choice 3 → byChoice=[0,0,0,1]; activeRound prioriza open). `gamePoligrafo` queda sin víctima → P5.1.

- [x] **P1.C Ronda 3 (Lulu's Revenge, rhythm): mejora integral.** ✅ e890371
  - Receptores DDR por carril (cyan/rosa/oro/verde) en la zona de hit: pressed/held/hit-flash. Sustituyen a la fila de teclas Franco que se cortaba abajo (Franco sigue en las notas, que es el chiste).
  - Tap zone = carril COMPLETO (antes franja invisible de 90px que nadie veía). Lulu fuera del campo → header, reacciona con .party en cada PERFECT.
  - Carriles con contraste alternado, colas de hold 2× más anchas con borde, feedback central 60px, escenario con luces moradas. Stage 64dvh → nada cortado a 390px (bottom 756/844). Chart y scoring intactos.
  - Verificado Playwright 390px+desktop: receptores presentes, input teclado+touch con pressed/flash, notas y holds cayendo, sin clipping.

- [x] **P1.D Mapa Tenerife: rediseño.** ✅ 444021a — **Causa raíz: el mapa nunca tuvo CSS** (ni .tenerife-svg ni .island ni .map-pin: isla negra por fill default, SVG sin width, pins sin estilos). Rediseño "mapa de aventura": océano con gradiente+olas+brújula, isla arena+interior verde, Teide nevado con cota, ruta de progreso (oro recorrido / punteado pendiente), 12 pins estado (✓ verde / activo oro con halo pulsante / futuro azul), info card SIGUIENTE PARADA pulida. Pins clicables intactos (jumpToRound). Verificado Playwright 390px+desktop con currentRound=5.

- [x] **P1.E Intro: ritmo y limpieza.** ✅ 5db8923 — Recut total 61s→~32s: terminal ×0.55, counter 2.6→1.8s, gap extra 800ms fuera, África hold 10s→4.5s (labels entran a 400ms+50ms/label), WANTED 2.6s, crawl CSS 40s→22s con corte a 20s. La "imagen sin sentido" principal (mapa Tenerife negro) ya cayó en P1.D. Verificado Playwright: timeline de fases correcta, desemboca en victims a ~32s.

- [x] **P1.F "Saltar intro" SIEMPRE operativo.** ✅ 5db8923 — Botón fixed z-200 visible sobre las 5 fases (ya lo estaba). BUG REAL arreglado: la corrutina async seguía viva tras saltar y su `goToVictims()` final (a los ~40s) te SACABA de la partida en curso. Ahora token `_introToken` + guard `alive()` (token+visibilidad) tras cada await; skip llama `cancelIntro()`. Verificado Playwright: skip a mitad de terminal → victims → jumpToRound(7) → 5s después sigue en screen-game con la intro congelada (corrutina muerta).

- [ ] **P1.G Controles a MITAD de juego: reiniciar Y salir** (Javier 2026-06-11). Hoy en mitad de un juego no puedes ni reiniciar ni salir (◀ MENÚ oculto durante game-running por el fix fat-finger). Añadir DOS controles accesibles durante la partida (pills en el HUD visibles solo con game-running): "↻" reiniciar → jumpToRound(state.currentRound) (la transition card actúa de confirmación natural) y "✕" salir → backToVictims() (menú del juego; desde ahí ya hay ◀ INICIO al menú principal). Verificar teardown limpio del juego en curso (timers, listeners, audio) en ambos caminos.

## P2 — Fricción / bugs móvil (390px)

- [ ] **P2.1 Pantalla final: lang-pills (ES/GL/NAIJA) pisan el pretitle** "DAMAGE REPORT — JUICIO CERRADO" a 390px. Padding-top o esconder pills en screen-final.
- [x] **P2.2 Rhythm: fila de botones táctiles cortada por el borde inferior** ✅ — resuelto en P1.C (e890371): receptores a bottom:32px + stage 64dvh + tap zone carril completo.
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
