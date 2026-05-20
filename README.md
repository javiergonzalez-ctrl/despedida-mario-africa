# AFRICA STRIKES BACK — Operación Cristóbal

Juego web para la despedida de **Mario Cristóbal** en Tenerife. 12 mini-juegos + intro cinemática + boss final con votación QR.

## ▶ Probar local (30 segundos)

```bash
# Doble click en index.html
# O servirlo:
npx serve .
```

> ⚠ El QR voting **no funciona en local** porque el móvil no puede acceder a `localhost`. Para probar QR hay que deployar.

## ▶ Deploy en Vercel (free, 2 minutos)

1. https://vercel.com → Sign up con GitHub
2. **Add New → Project → Import** este folder (o arrástralo a https://vercel.com/new)
3. Deploy. Te dan URL tipo `africa-strikes-back-xxx.vercel.app`
4. Listo. La URL es la que codifica el QR para el voto.

Alternativa: **Netlify Drop** (https://app.netlify.com/drop) — arrastra el folder y listo.

## ▶ Setup Firebase para el QR voting (5 minutos)

El juego funciona sin Firebase (votación manual con botones `+1 SÍ / +1 NO`), pero si quieres voto real vía móvil:

1. https://console.firebase.google.com → **Add project** → "despedida-mario"
2. Sidebar → **Realtime Database** → Create database → **Test mode** (acepta)
3. Sidebar → **Project Settings** (engranaje) → **General** → Your apps → Web `</>`
4. Register app → te da config tipo:
   ```js
   { apiKey: "...", authDomain: "...", databaseURL: "...", projectId: "..." }
   ```
5. Abre `index.html` → busca `FIREBASE_CONFIG` (línea ~890) → pega tu config
6. Re-deploy

## ▶ Día de la despedida

1. Conecta laptop a TV/proyector del Airbnb
2. Abre la URL en Chrome fullscreen (`F11`)
3. `▶ INICIAR EL JUICIO` → Mario se sienta delante del teclado
4. Cada juego dice qué teclas usar
5. El grupo cuenta chupitos (HUD top-right marca el total)
6. Boss final: QR aparece, todos lo escanean, votan, sentencia

## ▶ Mecánicas por juego

| # | Juego | Input | Dificultad |
|---|-------|-------|------------|
| 1 | Rush Hour Lagos | SPACE (parar barra en verde) | ★★ |
| 2 | Mango Memory | Click (Simon Says con 4 mangos) | ★★★ |
| 3 | Lulu's Revenge | D F J K (rhythm game) | ★★★★ |
| 4 | Deposit Boost x10 | SPACE (slot truqueado) | ★ (suerte) |
| 5 | Carta del Perdón | teclado (typing race) | ★★★ |
| 6 | F1 Pop Quiz | 1 2 3 4 (8 preguntas) | ★★ |
| 7 | Coltán Clicker | SPACE spam (100 en 15s) | ★★★ |
| 8 | Drift Sahara | ← → (esquivar 25s) | ★★★ |
| 9 | Whack-a-Suegra | click (no le pegues a Paz) | ★★★ |
| 10 | Press Conference | teclado (sin palabras prohibidas) | ★★★★ |
| 11 | Penalty vs Ferrer | ← ↑ → (5 disparos) | ★★ |
| 12 | Polígrafo Paz (BOSS) | Y / N + QR voto | ★★★★★ |

## ▶ Notas técnicas

- **Single HTML**, sin build, sin npm. Solo Chrome.
- Avatares: DiceBear API (SVG, gratis, no auth).
- Audio sintetizado vía Web Audio API. Mute con botón en pantalla de inicio.
- Foto real de Mario / Albert / Paz: opcional, drop en `/images/` y modificar las URLs en el HTML.
- Compatible móvil pero **diseñado para laptop** con proyector.

## ▶ Personalización rápida

| Quieres cambiar | Busca en index.html |
|-----------------|---------------------|
| Nombre de víctimas / historia | `const VICTIMS = [` |
| Preguntas F1 | `const F1_QUESTIONS = [` |
| Acusaciones Paz | `const PAZ_ACCUSATIONS = [` |
| Palabras prohibidas (rueda prensa) | `const FORBIDDEN_WORDS = [` |
| Texto del crawl Star Wars | `const CRAWL_TEXT_HTML` |
| Firebase config | `const FIREBASE_CONFIG = {` |

## ▶ Roadmap v2 (si pinta bien)

- [ ] Fotos reales de Albert Ferrer + Paz Padilla en `/images/`
- [ ] Sonido de Sálvame de fondo en el boss final (MP3 + autoplay tras gesture)
- [ ] Leaderboard guardando highscores en localStorage
- [ ] Modo "ronda libre" para repetir un solo juego
- [ ] Confeti en el final
