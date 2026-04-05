/* ============================================================
   splash.js — Ahira App Splash Screen
   Called once per session on every fresh app open.
   Shows an animated intro then fades out to reveal the app.
   
   HOW TO USE:
   1. Add <div id="ahiraSplash"></div> to index.html (first child of body)
   2. Add <script src="/static/splash.js"></script> before </body>
   3. Call AhiraSplash.init() at the very top of window.onload
============================================================ */

const AhiraSplash = (() => {

    // Rotating messages shown during splash
    const GREETINGS = [
        { line1: "Welcome back", line2: "Ahira missed you 💜" },
        { line1: "Good to see you", line2: "Ready for today? ✨" },
        { line1: "Hey you", line2: "Ahira's got your back 🌸" },
        { line1: "You showed up", line2: "That already matters 💜" },
        { line1: "New day", line2: "New energy with Ahira ⚡" },
        { line1: "Hi there", line2: "Let's make today beautiful 🌿" },
    ];

    function getGreeting() {
        const idx = Math.floor(Math.random() * GREETINGS.length);
        return GREETINGS[idx];
    }

    function getTimeEmoji() {
        const h = new Date().getHours();
        if (h < 5)  return "🌙";
        if (h < 12) return "🌅";
        if (h < 17) return "☀️";
        if (h < 20) return "🌆";
        return "🌙";
    }

    function buildHTML(greeting) {
        return `
        <div id="ahiraSplashInner">
            <!-- Background blobs -->
            <div class="splash-blob splash-blob-1"></div>
            <div class="splash-blob splash-blob-2"></div>
            <div class="splash-blob splash-blob-3"></div>

            <!-- Ripple rings -->
            <div class="splash-ring splash-ring-1"></div>
            <div class="splash-ring splash-ring-2"></div>
            <div class="splash-ring splash-ring-3"></div>

            <!-- Logo -->
            <div class="splash-logo-wrap">
                <div class="splash-logo-bg"></div>
                <img src="/static/images/logo.png" class="splash-logo" alt="Ahira">
                <div class="splash-logo-glow"></div>
            </div>

            <!-- Brand -->
            <div class="splash-brand">AHIRA</div>

            <!-- Greeting -->
            <div class="splash-greeting">
                <div class="splash-line1">${getTimeEmoji()} ${greeting.line1}</div>
                <div class="splash-line2">${greeting.line2}</div>
            </div>

            <!-- Floating particles -->
            <div class="splash-particles" id="splashParticles"></div>

            <!-- Loading dots -->
            <div class="splash-dots">
                <span class="splash-dot"></span>
                <span class="splash-dot"></span>
                <span class="splash-dot"></span>
            </div>
        </div>`;
    }

    function buildCSS() {
        return `
        #ahiraSplash {
            position: fixed;
            inset: 0;
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0d0820;
            overflow: hidden;
            transition: opacity 0.7s ease, transform 0.7s ease;
        }

        #ahiraSplash.splash-exit {
            opacity: 0;
            transform: scale(1.04);
            pointer-events: none;
        }

        #ahiraSplashInner {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            z-index: 2;
            animation: splashFadeIn 0.6s ease forwards;
        }

        @keyframes splashFadeIn {
            from { opacity: 0; transform: translateY(16px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* Background blobs */
        .splash-blob {
            position: absolute;
            border-radius: 50%;
            filter: blur(60px);
            pointer-events: none;
            z-index: 0;
        }
        .splash-blob-1 {
            width: 300px; height: 300px;
            background: radial-gradient(circle, rgba(138,108,255,0.45), transparent 70%);
            top: -80px; left: -60px;
            animation: blobFloat1 6s ease-in-out infinite;
        }
        .splash-blob-2 {
            width: 250px; height: 250px;
            background: radial-gradient(circle, rgba(244,114,182,0.35), transparent 70%);
            bottom: -60px; right: -40px;
            animation: blobFloat2 7s ease-in-out infinite;
        }
        .splash-blob-3 {
            width: 180px; height: 180px;
            background: radial-gradient(circle, rgba(251,146,60,0.2), transparent 70%);
            top: 40%; left: 60%;
            animation: blobFloat3 5s ease-in-out infinite;
        }
        @keyframes blobFloat1 {
            0%,100% { transform: translate(0,0) scale(1); }
            50%      { transform: translate(20px, 30px) scale(1.1); }
        }
        @keyframes blobFloat2 {
            0%,100% { transform: translate(0,0) scale(1); }
            50%      { transform: translate(-25px, -20px) scale(1.08); }
        }
        @keyframes blobFloat3 {
            0%,100% { transform: translate(0,0); }
            50%      { transform: translate(-15px, 20px); }
        }

        /* Ripple rings */
        .splash-ring {
            position: absolute;
            border-radius: 50%;
            border: 1.5px solid rgba(138,108,255,0.2);
            pointer-events: none;
        }
        .splash-ring-1 { width: 180px; height: 180px; animation: ringPulse 2.4s ease-out infinite; }
        .splash-ring-2 { width: 240px; height: 240px; animation: ringPulse 2.4s ease-out 0.6s infinite; }
        .splash-ring-3 { width: 300px; height: 300px; animation: ringPulse 2.4s ease-out 1.2s infinite; }
        @keyframes ringPulse {
            0%   { transform: scale(0.85); opacity: 0.6; }
            100% { transform: scale(1.3);  opacity: 0; }
        }

        /* Logo */
        .splash-logo-wrap {
            position: relative;
            width: 88px; height: 88px;
            margin-bottom: 20px;
        }
        .splash-logo-bg {
            position: absolute; inset: -6px;
            border-radius: 50%;
            background: linear-gradient(135deg, #8a6cff, #f472b6);
            opacity: 0.25;
            filter: blur(12px);
            animation: logoBgPulse 2s ease-in-out infinite;
        }
        @keyframes logoBgPulse {
            0%,100% { transform: scale(1);    opacity: 0.25; }
            50%      { transform: scale(1.15); opacity: 0.45; }
        }
        .splash-logo {
            width: 88px; height: 88px;
            object-fit: contain;
            position: relative; z-index: 1;
            filter: drop-shadow(0 0 18px rgba(138,108,255,0.7));
            animation: logoEntrance 0.8s cubic-bezier(0.175,0.885,0.32,1.275) 0.2s both;
        }
        @keyframes logoEntrance {
            from { transform: scale(0.3) rotate(-15deg); opacity: 0; }
            to   { transform: scale(1) rotate(0deg);     opacity: 1; }
        }
        .splash-logo-glow {
            position: absolute; inset: 0;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(138,108,255,0.3), transparent 70%);
            animation: glowPulse 2s ease-in-out infinite;
        }
        @keyframes glowPulse {
            0%,100% { opacity: 0.5; }
            50%      { opacity: 1; }
        }

        /* Brand name */
        .splash-brand {
            font-family: 'Poppins', sans-serif;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 10px;
            background: linear-gradient(135deg, #c4a8ff 0%, #ffffff 50%, #f9a8d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            animation: brandSlideUp 0.6s ease 0.5s both;
        }
        @keyframes brandSlideUp {
            from { opacity: 0; transform: translateY(12px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* Greeting */
        .splash-greeting {
            text-align: center;
            animation: greetingFade 0.6s ease 0.8s both;
            margin-bottom: 36px;
        }
        @keyframes greetingFade {
            from { opacity: 0; transform: translateY(8px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .splash-line1 {
            font-family: 'Poppins', sans-serif;
            font-size: 15px;
            font-weight: 500;
            color: rgba(255,255,255,0.6);
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .splash-line2 {
            font-family: 'Poppins', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: rgba(255,255,255,0.95);
        }

        /* Floating particles */
        .splash-particles {
            position: absolute;
            inset: 0;
            pointer-events: none;
            overflow: hidden;
            z-index: 0;
        }
        .splash-particle {
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
            animation: particleFloat linear infinite;
        }

        @keyframes particleFloat {
            0%   { transform: translateY(100vh) scale(0); opacity: 0; }
            10%  { opacity: 1; }
            90%  { opacity: 0.6; }
            100% { transform: translateY(-20px) scale(1); opacity: 0; }
        }

        /* Loading dots */
        .splash-dots {
            display: flex;
            gap: 8px;
            animation: dotsFade 0.5s ease 1.1s both;
        }
        @keyframes dotsFade {
            from { opacity: 0; }
            to   { opacity: 1; }
        }
        .splash-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: linear-gradient(135deg, #8a6cff, #f472b6);
            animation: dotBounce 1.2s ease-in-out infinite;
        }
        .splash-dot:nth-child(1) { animation-delay: 0s; }
        .splash-dot:nth-child(2) { animation-delay: 0.2s; }
        .splash-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dotBounce {
            0%,100% { transform: translateY(0);   opacity: 0.4; }
            50%      { transform: translateY(-8px); opacity: 1; }
        }
        `;
    }

    function spawnParticles() {
        const container = document.getElementById("splashParticles");
        if (!container) return;

        const EMOJIS   = ["💜", "✨", "🌸", "⭐", "💫", "🌿"];
        const COLORS   = [
            "rgba(138,108,255,0.6)",
            "rgba(244,114,182,0.6)",
            "rgba(251,191,36,0.5)",
            "rgba(196,181,253,0.5)",
        ];
        const COUNT = 18;

        for (let i = 0; i < COUNT; i++) {
            const p = document.createElement("div");
            p.className = "splash-particle";

            const useEmoji = Math.random() > 0.5;
            if (useEmoji) {
                p.textContent = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
                p.style.fontSize = (Math.random() * 12 + 8) + "px";
                p.style.background = "none";
                p.style.width = "auto";
                p.style.height = "auto";
                p.style.borderRadius = "0";
            } else {
                const size = Math.random() * 5 + 2;
                p.style.width  = size + "px";
                p.style.height = size + "px";
                p.style.background = COLORS[Math.floor(Math.random() * COLORS.length)];
                p.style.boxShadow  = `0 0 ${size * 3}px ${COLORS[0]}`;
            }

            p.style.left              = (Math.random() * 100) + "%";
            p.style.bottom            = "-20px";
            p.style.animationDuration = (Math.random() * 3 + 2) + "s";
            p.style.animationDelay    = (Math.random() * 2.5) + "s";

            container.appendChild(p);
        }
    }

    function init(duration = 2800) {
        // 1. Inject CSS
        const style = document.createElement("style");
        style.textContent = buildCSS();
        document.head.appendChild(style);

        // 2. Build splash HTML
        const greeting = getGreeting();
        const splash   = document.getElementById("ahiraSplash");
        if (!splash) return;

        splash.innerHTML = buildHTML(greeting);

        // 3. Spawn particles after a tiny delay
        setTimeout(spawnParticles, 100);

        // 4. Auto-dismiss after duration
        setTimeout(() => {
            splash.classList.add("splash-exit");
            setTimeout(() => {
                splash.style.display = "none";
            }, 750);
        }, duration);
    }

    return { init };
})();
