/* ==========================================================
   AHIRA — chat.js  (complete)
========================================================== */


/* ─────────────────────────────────────────────────────────
   1. DAILY QUOTES
───────────────────────────────────────────────────────── */

const QUOTES = [
    "You are stronger than you think, braver than you feel, and more loved than you know. 💜",
    "Take care of yourself the way you take care of everyone else. You deserve it.",
    "Small steps every day still move you forward. Progress is progress. 🌸",
    "Your feelings are valid. Rest is productive. And asking for help is brave.",
    "Today doesn't have to be perfect. It just has to be yours. ✨",
    "Be gentle with yourself. You are a work in progress — and that's beautiful.",
    "Nourish your body, rest your mind, and trust the journey you're on. 💜",
    "You don't have to have it all together. Just keep going, one moment at a time.",
    "The most important relationship you have is the one with yourself. 🌿",
    "Celebrate the small wins. They're the foundation of the big ones. 🌟"
];

// ── Inline content (no external file needed) ──────────────
const _QUOTES = [
    "You have survived every hard day so far. That's a 100% success rate. 💜",
    "Strength doesn't always roar. Sometimes it's the quiet voice saying I'll try again tomorrow.",
    "You are not behind. You are on your own beautiful timeline.",
    "The fact that you're still here, still trying — that's extraordinary.",
    "Difficult roads often lead to the most breathtaking destinations.",
    "You've been through storms before. You know how to weather them.",
    "Every setback is setting you up for a stronger comeback.",
    "You are braver than you believe, stronger than you seem, and more loved than you know.",
    "Growth is uncomfortable because you're expanding. Keep going.",
    "You are worthy of love, rest, joy, and abundance — right now, as you are.",
    "Your worth is not measured by your productivity. You are enough by simply existing.",
    "Be as kind to yourself as you are to the people you love most.",
    "You don't need to earn rest. You are not a machine.",
    "Loving yourself is not selfish. It's the foundation of everything.",
    "You deserve the same compassion you so freely give to others.",
    "Healing is not linear. Some days you'll go backwards, and that's still healing.",
    "You don't have to be okay all the time. Let yourself feel what is real.",
    "Give yourself permission to grieve, to rest, to start over.",
    "Letting go is not giving up. It's making room for what truly belongs.",
    "Start before you're ready. The perfect time is a myth.",
    "Small consistent steps beat occasional giant leaps every time.",
    "Your dreams are not too big. Your belief in yourself just needs to catch up.",
    "Done is better than perfect. Ship it. Improve it. Keep moving.",
    "You are not lazy. You may be overwhelmed, burnt out, or in need of rest.",
    "Happiness is not a destination. It's sprinkled in ordinary moments.",
    "You are allowed to feel joy — even when life is hard.",
    "Notice what makes you come alive. Do more of that.",
    "The small moments are not small. They are the whole thing.",
    "Your mental health is not a luxury. It's a necessity.",
    "Asking for help is one of the most courageous things you can do.",
    "Rest is a mental health strategy. Not a reward.",
    "You are not broken. You are human, and humans have hard seasons.",
    "Your feelings are valid even when they're inconvenient.",
    "You deserve a mind that feels safe and a life that feels like home.",
    "The relationship you have with yourself sets the tone for every other one.",
    "Your body works tirelessly for you every single day. Thank it.",
    "Movement is medicine. Even a slow walk counts.",
    "Sleep is not laziness. It's when your body does its most important work.",
    "Taking care of your body is one of the highest forms of self-respect.",
    "Wellness is not a size or a number. It's how alive you feel from the inside.",
    "Change is not betrayal. It's evolution.",
    "You don't have to be fearless. Just act despite the fear.",
    "The bravest thing you can do is begin again, quietly, without applause.",
    "Your past is not your future unless you live there.",
    "Courage is choosing honesty over comfort, growth over safety.",
    "Not every chapter of your life is meant to be pretty. Some teach.",
    "You don't have to figure out the whole path. Just the next step.",
    "Comparison is the thief of joy and the enemy of progress.",
    "Your life is not a competition. Your only opponent is yesterday's version of you.",
    "I am learning. I am growing. I am becoming.",
    "I choose peace over perfection today.",
    "I am worthy of the love I seek. It starts with me.",
    "I am not my mistakes. I am what I choose to do next.",
    "I am doing the best I can with what I have right now.",
    "There is incredible power in your intuition. Trust it.",
    "A woman who knows her worth changes the whole room.",
    "Softness is not weakness. It takes strength to stay tender in a hard world.",
    "Your sensitivity is not a flaw. It's a form of intelligence.",
    "A woman who invests in herself builds something no one can take away.",
    "Today is a new page. What will you write?",
    "You woke up today. That already counts for something.",
    "Even on slow days, you are still moving forward.",
    "It's okay if today is just maintenance. Showing up is enough.",
    "Every day you choose yourself is a victory.",
    "Like the moon, you go through phases. All of them are natural.",
    "After every winter, spring finds a way through. So will you.",
    "Right now, in this moment, you are safe.",
    "Breathe. You don't have to solve everything today.",
    "One breath at a time. One step at a time. One day at a time.",
    "Be here. Not in yesterday's regret or tomorrow's worry.",
    "Stillness is not emptiness. It's where clarity lives.",
    "Something good is coming — even if you can't see it yet.",
    "Your story is not over. Not even close.",
    "The best chapters of your life may not have been written yet.",
    "Hold on. Seasons change. So do circumstances.",
    "You have been in difficult places before and found your way through.",
    "Keep going. The view from the other side of this will be worth it.",
    "You are still here. And that means something beautiful is still possible.",
    "Imperfect action beats perfect inaction every single time.",
    "Your uniqueness is not a bug. It's the whole feature.",
    "You've already done hard things. You'll do this too.",
    "Your presence matters more than your perfection.",
    "You are not defined by your hardest moment.",
    "The courage it takes to keep showing up every day is real.",
    "You — exactly as you are — are enough. Always. 💜",
];

const _PERIOD_TIPS = [
    "A heating pad on your lower abdomen relaxes uterine muscles and eases cramps naturally.",
    "Gentle yoga poses like Child's Pose and Cat-Cow can reduce period cramps within minutes.",
    "A warm bath with Epsom salts helps relax pelvic muscles and soothes period pain.",
    "Light walking improves blood flow and triggers endorphins that act as natural painkillers.",
    "Ginger tea steeped in hot water is a powerful natural anti-inflammatory for cramps.",
    "Iron-rich foods like lentils, spinach, and red meat help replace iron lost during bleeding.",
    "Magnesium-rich foods like dark chocolate, almonds, and avocado reduce PMS symptoms.",
    "Omega-3 fatty acids in salmon, walnuts, and flaxseed reduce period pain inflammation.",
    "Reduce salt intake before your period to minimise bloating and water retention.",
    "Tracking your cycle for 3 months reveals your personal patterns, not just averages.",
    "A normal cycle is anywhere from 21 to 35 days — not just the textbook 28.",
    "PMS affects up to 75% of menstruating people — you are not imagining it.",
    "Reducing caffeine the week before your period can significantly lower PMS anxiety.",
    "A consistent sleep schedule during the luteal phase dramatically improves PMS symptoms.",
    "Your cycle has four phases: menstrual, follicular, ovulatory, and luteal. Each feels different.",
    "Estrogen peaks around ovulation making you feel sociable, confident, and energised.",
    "Progesterone rises after ovulation making you feel more introspective and tired.",
    "Cortisol (stress hormone) disrupts your hormonal cycle more than almost anything else.",
    "Chamomile tea has anti-inflammatory and antispasmodic effects on uterine muscles.",
    "Your period is not a weakness. It is evidence of extraordinary biological complexity.",
];

const _WATER_TIPS = [
    "Your body is about 60% water — hydration affects every single system.",
    "Even mild dehydration (1-2%) impairs concentration, mood, and physical performance.",
    "Water helps flush toxins through your kidneys — the body's natural filtration system.",
    "Proper hydration supports glowing skin more than most skincare products.",
    "Your brain is 73% water. Staying hydrated is literally feeding your brain.",
    "If your urine is pale yellow you're well hydrated. Dark yellow means drink more.",
    "Start every morning with a full glass of water before coffee or food.",
    "Keep a water bottle visible on your desk — out of sight, out of mind really does apply.",
    "Drink a glass of water before every meal — it also prevents overeating.",
    "Add fresh lemon or lime for a vitamin C boost and better taste.",
    "Coconut water is an excellent post-exercise hydrator with natural electrolytes.",
    "A headache is often the first sign your body sends when you're dehydrated.",
    "Fatigue that hits midday is frequently dehydration, not just tiredness.",
    "Difficulty concentrating? Drink a glass of water before reaching for caffeine.",
    "Mood changes and irritability are early symptoms of inadequate hydration.",
    "Constipation is frequently a hydration issue — water softens stool and aids digestion.",
    "Sipping water throughout the day is more effective than drinking large amounts at once.",
    "Watermelon, strawberries, oranges, and spinach are excellent hydrating foods.",
    "Staying hydrated during your period reduces cramping and bloating significantly.",
    "Hydration supports better sleep — but stop big drinks 2 hours before bed.",
];

const _WELCOME = [
    "Welcome back 💜 I missed you",
    "Hey you — so glad you're here 🌸",
    "You showed up today. That matters. ✨",
    "I'm here for you, always 🤍",
    "Let's take this day one breath at a time 🌿",
    "Good to see you again 💛",
    "Your safe space is open 🌷",
    "Ahira is ready when you are 💜",
    "You are not alone — not today, not ever 🤍",
    "Hello, beautiful soul ✨",
    "Ready to take on today together? 🌸",
    "Soft landing, right here 🌿",
    "Your feelings are safe here 🤍",
    "New day, new energy — let's go ⚡",
    "This is your space. Welcome home 🌸",
    "Whatever today holds, I'm with you 💛",
    "Take a breath. You've got this. 🌿",
    "You are seen. You are valued. You are here. 💜",
    "Today is a fresh page. Write something kind 🌷",
    "Even on hard days, you belong here 🤍",
];

function _pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function _daily(arr) {
    const d = Math.floor((new Date() - new Date(new Date().getFullYear(),0,0)) / 864e5);
    return arr[d % arr.length];
}

// AhiraContent object — works whether ahira_content.js is loaded or not
const AhiraContent = {
    randomQuote:     () => _pick(_QUOTES),
    randomPeriodTip: () => _pick(_PERIOD_TIPS),
    randomWaterTip:  () => _pick(_WATER_TIPS),
    randomWelcome:   () => _pick(_WELCOME),
    dailyQuote:      () => _daily(_QUOTES),
    dailyWelcome:    () => _daily(_WELCOME),
    sessionWater:    () => _pick(_WATER_TIPS),
    sessionPeriod:   () => _pick(_PERIOD_TIPS),
    sessionWelcome:  () => _pick(_WELCOME),
    sessionQuote:    () => _daily(_QUOTES),
};

function renderDailyQuote() {
    safe("dailyQuote", el => {
        el.innerText = `"${AhiraContent.dailyQuote()}"`;
    });
}


/* ─────────────────────────────────────────────────────────
   2. AUTH
───────────────────────────────────────────────────────── */

let currentUser = null;

function showAuthPanel(id) {
    document.getElementById("loginScreen").style.display    = "none";
    document.getElementById("registerScreen").style.display = "none";
    document.getElementById(id).style.display = "block";
}

function showAuthError(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerText = msg;
    el.style.display = "block";
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideAuthError(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
}

function isValidEmail(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e); }
function isValidName(n)  { return /^[a-zA-Z\u00C0-\u024F\s\-]{2,50}$/.test(n); }

async function submitRegister() {
    hideAuthError("registerError");
    const name    = document.getElementById("regName").value.trim();
    const email   = document.getElementById("regEmail").value.trim();
    const pw      = document.getElementById("regPassword").value;
    const confirm = document.getElementById("regPasswordConfirm").value;

    if (!name)                  return showAuthError("registerError", "Please enter your name.");
    if (!isValidName(name))     return showAuthError("registerError", "Name should be letters only, at least 2 characters.");
    if (!email)                 return showAuthError("registerError", "Please enter your email.");
    if (!isValidEmail(email))   return showAuthError("registerError", "Please enter a valid email (e.g. you@example.com).");
    if (!pw)                    return showAuthError("registerError", "Please create a password.");
    if (pw.length < 6)          return showAuthError("registerError", "Password must be at least 6 characters.");
    if (pw !== confirm)         return showAuthError("registerError", "Passwords don't match. Please re-enter.");

    const btn = document.getElementById("registerBtn");
    btn.disabled = true; btn.innerText = "Creating account...";

    try {
        const res  = await fetch("/register", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({name,email,password:pw}) });
        const data = await res.json();
        if (data.status === "ok") { currentUser = data.user; enterApp(); }
        else showAuthError("registerError", data.message || "Registration failed. Please try again.");
    } catch(e) {
        showAuthError("registerError", "Could not connect to server. Please check your internet.");
    } finally { btn.disabled = false; btn.innerText = "Create Account"; }
}

async function submitLogin() {
    hideAuthError("loginError");
    const email = document.getElementById("loginEmail").value.trim();
    const pw    = document.getElementById("loginPassword").value;

    if (!email)               return showAuthError("loginError", "Please enter your email address.");
    if (!isValidEmail(email)) return showAuthError("loginError", "That doesn't look like a valid email address.");
    if (!pw)                  return showAuthError("loginError", "Please enter your password.");

    const btn = document.getElementById("loginBtn");
    btn.disabled = true; btn.innerText = "Signing in...";

    try {
        const res  = await fetch("/login", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({email,password:pw}) });
        const data = await res.json();
        if (data.status === "ok") { currentUser = data.user; enterApp(); }
        else showAuthError("loginError", data.message || "Incorrect email or password.");
    } catch(e) {
        showAuthError("loginError", "Could not connect to server. Please check your internet.");
    } finally { btn.disabled = false; btn.innerText = "Sign In"; }
}



/* ── 4. REPLACE submitLogout ───────────────────────────── */
async function submitLogout() {
    closeDrawer();
    try { await fetch("/logout", { method: "POST" }); } catch(e) {}
    currentUser = null; chatHistory = [];
    ["water","waterTarget","waterLog","waterWeekly","medicines",
     "groceryItems","taskMeta","lastPeriodDate"].forEach(k => localStorage.removeItem(k));
    document.querySelectorAll(".appScreen").forEach(s => s.classList.remove("active"));
    document.getElementById("appWrapper").style.display  = "none";
    document.getElementById("authLogo").style.display    = "block";
    document.getElementById("authWrapper").style.display = "block";
    showAuthPanel("loginScreen");
}


async function checkSession() {
    try {
        const res  = await fetch("/me");
        const data = await res.json();
        if (data.status === "ok") { currentUser = data.user; enterApp(); }
        else showAuth();
    } catch(e) { showAuth(); }
}
 
 
function showAuth() {
    document.querySelectorAll(".appScreen").forEach(s => s.classList.remove("active"));
    document.getElementById("authLogo").style.display    = "block";
    document.getElementById("authWrapper").style.display = "block";
    document.getElementById("appWrapper").style.display  = "none";
    showAuthPanel("loginScreen");
}  

function enterApp() {
    document.getElementById("authLogo").style.display    = "none";
    document.getElementById("authWrapper").style.display = "none";
    document.getElementById("appWrapper").style.display  = "flex";
 
    // Clear any leftover active states
    document.querySelectorAll(".appScreen").forEach(s => s.classList.remove("active"));
 
    const hour = new Date().getHours();
    const timeGreet = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
 
    if (currentUser) {
        const initials = currentUser.name.charAt(0).toUpperCase();
        const btn = document.getElementById("profileBtn");
        if (btn) btn.innerText = initials;
        
        safe("chatWelcomeMsg", el => {
            el.innerText = AhiraContent.randomWelcome() + " How can I help you today?";
        });
        safe("homeGreeting",   el => el.innerText = `${timeGreet}, ${currentUser.name} 💜`);
        safe("drawerName",     el => el.innerText = currentUser.name);
        safe("drawerEmail",    el => el.innerText = currentUser.email);
        safe("drawerAvatar",   el => el.innerText = initials);
    }
 
    water          = parseInt(localStorage.getItem("water"))          || 0;
    waterTarget    = parseInt(localStorage.getItem("waterTarget"))    || 8;
    waterLog       = JSON.parse(localStorage.getItem("waterLog"))     || [];
    waterWeekly    = JSON.parse(localStorage.getItem("waterWeekly"))  || {};
    medicines      = JSON.parse(localStorage.getItem("medicines"))    || [];
    groceryItems   = JSON.parse(localStorage.getItem("groceryItems")) || [];
    lastPeriodDate = localStorage.getItem("lastPeriodDate")
        ? new Date(localStorage.getItem("lastPeriodDate")) : null;
 
    navApp("homeScreen", document.querySelector(".navItem"));
}

/* ─────────────────────────────────────────────────────────
   3. PROFILE DRAWER
───────────────────────────────────────────────────────── */

function openDrawer() {
    document.getElementById("profileDrawer").classList.add("open");
    document.getElementById("drawerOverlay").classList.add("open");
    // Update water goal label in drawer
    safe("drawerWaterGoal", el => el.innerText = `${waterTarget} glasses per day`);
}

function closeDrawer() {
    document.getElementById("profileDrawer").classList.remove("open");
    document.getElementById("drawerOverlay").classList.remove("open");
}

function toggleSetting(btn) {
    btn.classList.toggle("on");
}


/* ─────────────────────────────────────────────────────────
   4. STATE
───────────────────────────────────────────────────────── */

let water            = 0;
let waterTarget      = 8;
let waterLog         = [];
let waterWeekly      = {};
let medicines        = [];
let groceryItems     = [];
let currentGroceryFilter = "all";
let currentMedFilter     = "all";
let selectedTaskType     = "task";
let selectedTaskPriority = "normal";
let selectedMedPriority  = "normal";
let completedVisible     = false;
let lastPeriodDate       = null;

const safe = (id, fn) => { const el = document.getElementById(id); if (el) fn(el); };


/* ─────────────────────────────────────────────────────────
   5. NAVIGATION — isolated screen switching
───────────────────────────────────────────────────────── */
 
/* ── 1. REPLACE navApp ─────────────────────────────────── */
function navApp(screen, btn) {
    // Remove active from all screens
    document.querySelectorAll(".appScreen").forEach(s => {
        s.classList.remove("active");
    });
 
    // Add active to target screen
    const target = document.getElementById(screen);
    if (target) {
        target.classList.add("active");
        if (screen === "chatScreen") {
            setTimeout(() => {
                const box = document.getElementById("chatMessages") || document.getElementById("chat");
                if (box) box.scrollTop = box.scrollHeight;
            }, 60);
        } else {
            target.scrollTop = 0;
        }
    }
 
    // Update nav highlight
    document.querySelectorAll(".navItem").forEach(b => b.classList.remove("active"));
    if (btn && btn.classList && btn.classList.contains("navItem")) {
        btn.classList.add("active");
    }
 
    // Run screen loader
    const loaders = {
        homeScreen:     loadHomeData,
        plannerScreen:  loadPlanner,
        wellnessScreen: loadWellnessScreen,
        medicineScreen: loadMedicines,
        waterScreen:    loadWaterScreen,
        groceryScreen:  loadGrocery,
        periodScreen:   calculatePeriod,
    };
    if (loaders[screen]) loaders[screen]();
}
 
const nav = navApp;
  

/* ─────────────────────────────────────────────────────────
   6. HOME
───────────────────────────────────────────────────────── */

async function loadHomeData() {
    updateDateTime();
    renderDailyQuote();
    renderHomeWaterDrops();
    renderWaterTip();
    calculatePeriod();
    renderPeriodTip();
    renderHomeMedCard();
    renderHomeGroceryCard();
    renderHomeAlerts();
    try {
        const res  = await fetch("/reminders");
        const data = await res.json();
        updateSummaryCounts(data.tasks);
    } catch(e) { console.error("[Home]", e); }
}

function updateDateTime() {
    safe("dateTime", el => {
        const now = new Date();
        el.innerText = now.toLocaleDateString("en-IN", {
            weekday:"long", day:"numeric", month:"long", year:"numeric"
        });
    });
}

function updateSummaryCounts(tasks) {
    const today = new Date(); today.setHours(0,0,0,0);
    let overdue=0, tod=0, upcoming=0;
    tasks.forEach(t => {
        if (t.completed===1) return;
        if (!t.date) { upcoming++; return; }
        const d = new Date(t.date); d.setHours(0,0,0,0);
        if      (d < today)                       overdue++;
        else if (d.getTime()===today.getTime()) tod++;
        else                                      upcoming++;
    });
    safe("overdueNum",  el => el.innerText = overdue);
    safe("todayNum",    el => el.innerText = tod);
    safe("upcomingNum", el => el.innerText = upcoming);
}

function renderHomeAlerts() {
    const container = document.getElementById("homeAlerts");
    if (!container) return;
    container.innerHTML = "";
    const lowMeds = medicines.filter(m => m.stock<=5);
    const outMeds = medicines.filter(m => m.stock===0);
    if (outMeds.length>0) container.innerHTML+=`<div class="alertBanner danger" onclick="navApp('medicineScreen')"><span class="alertBannerIcon">💊</span><span class="alertBannerText"><b>${outMeds[0].name}</b>${outMeds.length>1?` +${outMeds.length-1} more`:""} — out of stock!</span><span class="alertBannerArrow">›</span></div>`;
    else if (lowMeds.length>0) container.innerHTML+=`<div class="alertBanner warning" onclick="navApp('medicineScreen')"><span class="alertBannerIcon">💊</span><span class="alertBannerText"><b>${lowMeds[0].name}</b> — running low (${lowMeds[0].stock} left)</span><span class="alertBannerArrow">›</span></div>`;
    const urgGroc = groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked);
    const ovrGroc = groceryItems.filter(g=>g.deadline&&new Date(g.deadline)<new Date()&&!g.checked);
    if (ovrGroc.length>0) container.innerHTML+=`<div class="alertBanner danger" onclick="navApp('groceryScreen')"><span class="alertBannerIcon">🛒</span><span class="alertBannerText"><b>${ovrGroc[0].name}</b> — deadline passed!</span><span class="alertBannerArrow">›</span></div>`;
    else if (urgGroc.length>0) container.innerHTML+=`<div class="alertBanner warning" onclick="navApp('groceryScreen')"><span class="alertBannerIcon">🛒</span><span class="alertBannerText"><b>${urgGroc.length} urgent item${urgGroc.length>1?"s":""}</b> need restocking</span><span class="alertBannerArrow">›</span></div>`;
    if (container.innerHTML===""&&(medicines.length>0||groceryItems.length>0)) container.innerHTML=`<div class="alertBanner ok"><span class="alertBannerIcon">✅</span><span class="alertBannerText">Medicines &amp; grocery all stocked up!</span></div>`;
}

function renderHomeMedCard() {
    if (medicines.length===0) { safe("homeMedSub",el=>{el.innerText="No medicines added yet";el.style.color="#6b21a8";}); safe("homeMedMeta",el=>el.innerText=""); safe("homeMedBarFill",el=>el.style.width="0%"); return; }
    const total=medicines.length, taken=medicines.filter(m=>m.taken).length, low=medicines.filter(m=>m.stock<=5).length, out=medicines.filter(m=>m.stock===0).length;
    safe("homeMedBarFill",el=>el.style.width=Math.round((taken/total)*100)+"%");
    if (out>0) safe("homeMedSub",el=>{el.innerText=`${out} medicine${out>1?"s":""} out of stock ⚠️`;el.style.color="#ff6b8a";});
    else if (low>0) safe("homeMedSub",el=>{el.innerText=`${low} medicine${low>1?"s":""} running low`;el.style.color="#ffb347";});
    else safe("homeMedSub",el=>{el.innerText=`${taken} of ${total} taken today`;el.style.color="#6b21a8";});
    const nextMed=medicines.find(m=>!m.taken&&m.time);
    safe("homeMedMeta",el=>{el.innerText=nextMed?`Next: ${nextMed.name} at ${nextMed.time}`:`${total} medicines tracked`;});
}

function renderHomeGroceryCard() {
    if (groceryItems.length===0) { safe("homeGrocerySub",el=>{el.innerText="No items added yet";el.style.color="#166534";}); safe("homeGroceryMeta",el=>el.innerText=""); safe("homeGroceryBarFill",el=>el.style.width="0%"); return; }
    const total=groceryItems.length, done=groceryItems.filter(g=>g.checked).length, urgent=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked).length, overdue=groceryItems.filter(g=>g.deadline&&new Date(g.deadline)<new Date()&&!g.checked).length;
    safe("homeGroceryBarFill",el=>el.style.width=Math.round((done/total)*100)+"%");
    if (overdue>0) safe("homeGrocerySub",el=>{el.innerText=`${overdue} item${overdue>1?"s":""} past deadline ⚠️`;el.style.color="#ff6b8a";});
    else if (urgent>0) safe("homeGrocerySub",el=>{el.innerText=`${urgent} urgent item${urgent>1?"s":""} to buy`;el.style.color="#ffb347";});
    else safe("homeGrocerySub",el=>{el.innerText=`${done} of ${total} items collected`;el.style.color="#166534";});
    safe("homeGroceryMeta",el=>{el.innerText=urgent>0?`${total-done} remaining · ${urgent} urgent`:`${total-done} remaining`;});
}


/* ─────────────────────────────────────────────────────────
   7. CHAT — OpenRouter direct from browser
───────────────────────────────────────────────────────── */
/* ================================================================
   PATCH FILE — replace sections 7 (CHAT) and 8 (PLANNER) in chat.js

   INSTRUCTIONS:
   In your chat.js file:
   1. Find the comment: "7. CHAT — OpenRouter direct from browser"
      Replace everything from that comment down to (but NOT including)
      "9. WATER" with the CHAT section below.

   2. Find the comment: "8. PLANNER"
      Replace everything from that comment down to (but NOT including)
      "9. WATER" with the PLANNER section below.
================================================================ */


/* ─────────────────────────────────────────────────────────
   7. CHAT — OpenRouter direct from browser
───────────────────────────────────────────────────────── */

const OPENROUTER_KEY = "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";
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const CHAT_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen3-4b:free",
    "google/gemma-3n-e4b-it:free",
    "openrouter/free",
];
let chatHistory = [];

function buildSystemPrompt() {
    const now   = new Date().toLocaleString("en-IN", { weekday:"long", day:"numeric", month:"long", year:"numeric", hour:"2-digit", minute:"2-digit" });
    const today = new Date().toISOString().slice(0,10);
    const name  = currentUser ? currentUser.name : "there";
    return `You are Ahira — a warm caring AI companion for women. User's name: ${name}.
Personality: best-friend energy — kind, emotionally intelligent, genuine. Never robotic.
- Light emojis naturally, not every sentence
- Acknowledge feelings FIRST when someone is sad/anxious, then gently advise
- Real specific responses, not generic platitudes
- Ask follow-up questions before jumping to solutions
- Concise: 2-4 lines for emotions, more for plans/recipes
- Never start with "I understand", "I hear you", "Of course!" or "Absolutely!"
- Don't say you're an AI unless directly asked
- Address user by name (${name}) occasionally
Today: ${now}.
REMINDER TAG: If user asks to set a reminder, confirm warmly, then at the very end on a new line add ONLY:
[REMINDER: task_text | ${today} | HH:MM]
24-hour time. ONLY when user explicitly asks for a reminder.`;
}

async function sendMessage() {
    const input   = document.getElementById("message");
    const message = input.value.trim();
    if (!message) return;
 
    const chatEl = document.getElementById("chatMessages") || document.getElementById("chat");
    if (!chatEl) return;
    chatEl.querySelector(".chatSuggestions")?.remove();
 
    appendUserBubble(chatEl, message);
    input.value = "";
    chatEl.scrollTop = chatEl.scrollHeight;
 
    const typingWrap = createTypingIndicator();
    chatEl.appendChild(typingWrap);
    chatEl.scrollTop = chatEl.scrollHeight;
    const botMsgEl = typingWrap.querySelector(".botMsg") || typingWrap.querySelector(".bubble--bot");
 
    const messages = [
        { role: "system", content: buildSystemPrompt() },
        ...chatHistory,
        { role: "user", content: message }
    ];
 
    let reply = null;
 
    // Race the first 2 models — use whichever responds first
    const tryModel = (model) => fetch(OPENROUTER_URL, {
        method: "POST",
        headers: {
            "Authorization":      `Bearer ${OPENROUTER_KEY}`,
            "HTTP-Referer":       "https://ahira.app",
            "X-OpenRouter-Title": "Ahira",
            "Content-Type":       "application/json"
        },
        body: JSON.stringify({
            model,
            messages,
            max_tokens:  350,    // shorter = faster
            temperature: 0.80,
        }),
        signal: AbortSignal.timeout(12000)  // 12s timeout per model
    }).then(async r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const d = await r.json();
        const c = d?.choices?.[0]?.message?.content;
        if (!c) throw new Error("empty");
        return c;
    });
 
    // Try models sequentially with short timeout
    for (const model of CHAT_MODELS) {
        try {
            reply = await tryModel(model);
            if (reply) break;
        } catch(e) {
            console.log(`[Chat] ${model} failed: ${e.message}`);
            continue;
        }
    }
 
    if (!reply) {
        if (botMsgEl) {
            botMsgEl.classList.remove("typing");
            botMsgEl.innerHTML = `<b>Connection issue 😕</b><br><span style="font-size:12px;opacity:0.75;">Check your internet and try again.</span>`;
        }
        chatEl.scrollTop = chatEl.scrollHeight;
        return;
    }
 
    const { reply: cleanReply, reminder } = parseReminderTag(reply);
    if (botMsgEl) {
        botMsgEl.classList.remove("typing");
        renderBotText(botMsgEl, cleanReply);
    }
 
    chatHistory.push({ role: "user",      content: message    });
    chatHistory.push({ role: "assistant", content: cleanReply });
    if (chatHistory.length > 30) chatHistory = chatHistory.slice(-30);
 
    if (reminder) {
        await saveReminderToBackend(reminder);
        showReminderToast(reminder);
    }
    chatEl.scrollTop = chatEl.scrollHeight;
}


function parseReminderTag(text) {
    const match = text.match(/\[REMINDER:\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{2}:\d{2})\s*\]/i);
    if (!match) return { reply:text.trim(), reminder:null };
    const today    = new Date().toISOString().slice(0,10);
    const tomorrow = new Date(Date.now()+864e5).toISOString().slice(0,10);
    let date = match[2].trim();
    if (/tomorrow/i.test(date))          date = tomorrow;
    else if (!/\d{4}-\d{2}-\d{2}/.test(date)) date = today;
    return { reply:text.slice(0,match.index).trim(), reminder:{task:match[1].trim(),date,time:match[3].trim()} };
}

async function saveReminderToBackend(reminder) {
    try {
        await fetch("/add_reminder", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({task:reminder.task,date:reminder.date,time:reminder.time,priority:"normal"})
        });
    } catch(e) {}
}

// ── Chat bubble builders ──────────────────────────────────

function appendUserBubble(chatEl, message) {
    const w = document.createElement("div");
    w.className = "msgRow msgRow--user";
    w.innerHTML = `<div class="bubble bubble--user">${escapeHtml(message)}</div>`;
    w.style.animation = "bubbleIn 0.25s ease forwards";
    chatEl.appendChild(w);
}

function createTypingIndicator() {
    const w = document.createElement("div");
    w.className = "msgRow msgRow--bot";
    w.innerHTML = `
        <div class="chatAvatarSmall">A</div>
        <div class="bubble bubble--bot typing">
            <span class="typingDot"></span>
            <span class="typingDot"></span>
            <span class="typingDot"></span>
        </div>`;
    return w;
}

function renderBotText(el, text) {
    el.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;")
        .replace(/"/g,"&quot;");
}

function showReminderToast(reminder) {
    document.getElementById("reminderToast")?.remove();
    const toast = document.createElement("div");
    toast.id = "reminderToast";
    toast.className = "reminderToast";
    toast.innerHTML = `
        <span style="font-size:20px;">✅</span>
        <div>
            <div style="font-weight:700;font-size:13px;color:#4c1d95;">Reminder saved!</div>
            <div style="font-size:12px;color:#6b21a8;margin-top:2px;">
                ${escapeHtml(reminder.task)}
                ${reminder.date ? "· " + reminder.date : ""}
                ${reminder.time ? "at " + reminder.time : ""}
            </div>
        </div>`;
    document.querySelector(".phone").appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("toastVisible"));
    setTimeout(() => {
        toast.classList.remove("toastVisible");
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function quickChat(msg) {
    document.getElementById("message").value = msg;
    sendMessage();
}


/* ─────────────────────────────────────────────────────────
   8. PLANNER
───────────────────────────────────────────────────────── */

function getTaskEmoji(taskText, type) {
    const t = (taskText || "").toLowerCase();
    if (type === "event")                                      return "🎉";
    if (t.includes("exam") || t.includes("test"))             return "📚";
    if (t.includes("doctor") || t.includes("appointment"))    return "🏥";
    if (t.includes("gym") || t.includes("exercise") || t.includes("yoga")) return "🏃";
    if (t.includes("birthday"))                               return "🎂";
    if (t.includes("grocery") || t.includes("shop"))          return "🛒";
    if (t.includes("meeting") || t.includes("call"))          return "📞";
    if (t.includes("medicine") || t.includes("pill"))         return "💊";
    if (t.includes("travel") || t.includes("trip") || t.includes("flight")) return "✈️";
    if (t.includes("dinner") || t.includes("lunch") || t.includes("eat"))   return "🍽️";
    if (type === "reminder")                                  return "🔔";
    return "📋";
}

let calendarTasks    = [];
let selectedCalDate  = null;  // ISO date string of selected calendar day

async function buildCalStrip() {
    const strip = document.getElementById("calStrip");
    if (!strip) return;
    strip.innerHTML = "";

    const today = new Date();

    try {
        const res  = await fetch("/reminders");
        const data = await res.json();
        calendarTasks = data.tasks || [];
    } catch(e) { calendarTasks = []; }

    const localMeta = JSON.parse(localStorage.getItem("taskMeta") || "{}");

    // Show 14 days: 2 past + today + 11 ahead
    for (let i = -2; i <= 11; i++) {
        const d       = new Date(today);
        d.setDate(today.getDate() + i);
        const dateStr = d.toISOString().slice(0, 10);
        const isToday = i === 0;
        const isSel   = dateStr === selectedCalDate;

        const dayTasks    = calendarTasks.filter(t => t.date === dateStr && t.completed !== 1);
        const eventEmojis = dayTasks.slice(0, 2).map(t => {
            const meta = localMeta[`${t.task}__${t.date}`] || {};
            return getTaskEmoji(t.task, meta.type);
        });

        const cell = document.createElement("div");
        cell.className = "calCell" + (isToday ? " calToday" : "") + (isSel ? " calSelected" : "");
        cell.dataset.date = dateStr;
        cell.onclick = () => selectCalDay(dateStr);

        cell.innerHTML = `
            <div class="calDay">${d.toLocaleDateString("en-IN",{weekday:"short"}).slice(0,3)}</div>
            <div class="calNum">${d.getDate()}</div>
            <div class="calEvents">
                ${eventEmojis.map(e => `<span class="calEventDot">${e}</span>`).join("")}
                ${dayTasks.length > 2 ? `<span class="calMore">+${dayTasks.length-2}</span>` : ""}
            </div>`;
        strip.appendChild(cell);
    }

    safe("plannerDateLabel", el => el.innerText =
        today.toLocaleDateString("en-IN", {weekday:"long", month:"long", day:"numeric"}));
}

function selectCalDay(dateStr) {
    selectedCalDate = dateStr;
    // Update selected style
    document.querySelectorAll(".calCell").forEach(c => {
        c.classList.toggle("calSelected", c.dataset.date === dateStr);
    });
    // Show tasks for that day
    renderDayDetail(dateStr);
}

function renderDayDetail(dateStr) {
    const panel = document.getElementById("dayDetailPanel");
    if (!panel) return;

    const localMeta = JSON.parse(localStorage.getItem("taskMeta") || "{}");
    const tasks     = calendarTasks.filter(t => t.date === dateStr);
    const d         = new Date(dateStr + "T00:00:00");
    const label     = d.toLocaleDateString("en-IN", {weekday:"long", day:"numeric", month:"long"});

    if (tasks.length === 0) {
        panel.innerHTML = `
            <div class="dayDetailHeader">${label}</div>
            <div class="dayDetailEmpty">No tasks this day 🌸<br>
                <button class="addPillBtn" style="margin-top:10px;font-size:12px;padding:7px 16px;"
                    onclick="openAddTaskForDate('${dateStr}')">+ Add Task</button>
            </div>`;
    } else {
        panel.innerHTML = `<div class="dayDetailHeader">${label}</div>` +
            tasks.map(t => {
                const meta = localMeta[`${t.task}__${t.date}`] || {};
                const emoji = getTaskEmoji(t.task, meta.type);
                const done  = t.completed === 1;
                return `<div class="dayDetailTask ${done ? "dayDetailDone" : ""}">
                    <span class="dayDetailEmoji">${emoji}</span>
                    <div class="dayDetailInfo">
                        <div class="dayDetailName">${escapeHtml(t.task)}</div>
                        ${t.time ? `<div class="dayDetailTime">⏰ ${t.time}</div>` : ""}
                    </div>
                    <div style="display:flex;gap:4px;margin-left:auto;">
                        <button class="iconBtn ${done?"btnDone":"btnPrimary"}" onclick="toggleTask(${t.id})">✔</button>
                        <button class="iconBtn btnDanger" onclick="deleteTask(${t.id})">🗑</button>
                    </div>
                </div>`;
            }).join("") +
            `<button class="addPillBtn" style="width:100%;margin-top:10px;font-size:12px;padding:7px;"
                onclick="openAddTaskForDate('${dateStr}')">+ Add for this day</button>`;
    }
    panel.style.display = "block";
}

function openAddTaskForDate(dateStr) {
    openAddTask();
    setTimeout(() => {
        const dateInput = document.getElementById("dateInput");
        if (dateInput) dateInput.value = dateStr;
    }, 50);
}

function initChips(containerId, stateKey) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll(".typeChip").forEach(chip => {
        chip.addEventListener("click", () => {
            container.querySelectorAll(".typeChip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            if (stateKey === "task")     selectedTaskType     = chip.dataset.val;
            if (stateKey === "priority") selectedTaskPriority = chip.dataset.val;
            if (stateKey === "medpri")   selectedMedPriority  = chip.dataset.val;
        });
    });
}

function openAddTask() {
    document.getElementById("addTaskModal").style.display = "flex";
    selectedTaskType = "task"; selectedTaskPriority = "normal";
    document.querySelectorAll("#taskTypeChips .typeChip").forEach((c,i) => c.classList.toggle("active", i===0));
    document.querySelectorAll("#taskPriorityChips .typeChip").forEach((c,i) => c.classList.toggle("active", i===0));
}

function closeAddTask(e) {
    if (!e || e.target.classList.contains("modalOverlay"))
        document.getElementById("addTaskModal").style.display = "none";
}

async function saveTask() {
    const task   = document.getElementById("taskInput").value.trim();
    const date   = document.getElementById("dateInput").value;
    const time   = document.getElementById("timeInput").value;
    const pinned = document.getElementById("pinTask").checked;
    if (!task) { alert("Please enter a task name."); return; }

    const localMeta = JSON.parse(localStorage.getItem("taskMeta") || "{}");
    try {
        const res  = await fetch("/add_reminder", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({task, date, time, priority:selectedTaskPriority})
        });
        const data = await res.json();
        if (data.status === "success") {
            localMeta[`${task}__${date}`] = {type:selectedTaskType, pinned};
            localStorage.setItem("taskMeta", JSON.stringify(localMeta));
            document.getElementById("taskInput").value  = "";
            document.getElementById("dateInput").value  = "";
            document.getElementById("timeInput").value  = "";
            document.getElementById("pinTask").checked  = false;
            closeAddTask();
            await loadPlanner();
            // Re-select the date if we added from day detail
            if (date && selectedCalDate === date) renderDayDetail(date);
        } else {
            alert(data.message || "Could not save. Please log in.");
        }
    } catch(e) { alert("Network error."); }
}

async function loadPlanner() {
    await buildCalStrip();
    initChips("taskTypeChips",    "task");
    initChips("taskPriorityChips","priority");

    const todayList     = document.getElementById("todayTaskList");
    const upcomingList  = document.getElementById("upcomingTaskList");
    const completedList = document.getElementById("completedTaskList");
    const pinnedList    = document.getElementById("pinnedList");
    const pinnedSection = document.getElementById("pinnedSection");
    if (!todayList) return;

    todayList.innerHTML = upcomingList.innerHTML = completedList.innerHTML = "";
    if (pinnedList) pinnedList.innerHTML = "";

    // Hide day detail panel until a day is tapped
    const panel = document.getElementById("dayDetailPanel");
    if (panel) panel.style.display = "none";
    selectedCalDate = null;

    try {
        const res  = await fetch("/reminders");
        const data = await res.json();
        const localMeta = JSON.parse(localStorage.getItem("taskMeta") || "{}");
        const now   = new Date(); now.setHours(0,0,0,0);
        let hasPinned = false;

        // Sort: overdue first, then today, then upcoming
        const tasks = data.tasks || [];

        tasks.forEach(task => {
            const meta = localMeta[`${task.task}__${task.date}`] || {};
            const card = buildPlannerCard(task, meta);

            if (meta.pinned && !task.completed) {
                pinnedList.innerHTML += card;
                hasPinned = true;
            }

            if (task.completed) {
                completedList.innerHTML += card;
                return;
            }

            if (!task.date) {
                upcomingList.innerHTML += card;
                return;
            }

            const d = new Date(task.date); d.setHours(0,0,0,0);
            if (d <= now) {
                todayList.innerHTML += card;
            } else {
                upcomingList.innerHTML += card;
            }
        });

        if (!todayList.innerHTML)
            todayList.innerHTML    = emptyMsg("All clear for today 🌸");
        if (!upcomingList.innerHTML)
            upcomingList.innerHTML = emptyMsg("Nothing scheduled ahead");
        if (pinnedSection)
            pinnedSection.style.display = hasPinned ? "block" : "none";

        updateSummaryCounts(tasks);

    } catch(e) { console.error("[Planner]", e); }
}

function buildPlannerCard(task, meta) {
    const done     = task.completed === 1;
    const typeIcon = {task:"📋", event:"🎉", reminder:"🔔"}[meta.type || "task"];
    const hiPri    = task.priority === "high";

    // Status dot colour
    let dotColor = "";
    if (!done && task.date) {
        const today = new Date(); today.setHours(0,0,0,0);
        const d     = new Date(task.date); d.setHours(0,0,0,0);
        dotColor = d < today ? "#F87171" : d.getTime() === today.getTime() ? "#FBBF24" : "#A5B4FC";
    }

    const dot = dotColor
        ? `<span style="width:7px;height:7px;border-radius:50%;background:${dotColor};flex-shrink:0;"></span>`
        : "";

    // Format date nicely
    let dateLabel = "";
    if (task.date) {
        const d = new Date(task.date + "T00:00:00");
        dateLabel = d.toLocaleDateString("en-IN", {day:"numeric", month:"short"});
    }

    return `
    <div class="plannerCard ${done ? "taskDone" : ""}" style="${hiPri ? "border-left:3px solid #F87171;" : ""}">
        <div class="plannerCardLeft">
            <div class="plannerTypeIcon">${typeIcon}</div>
            <div style="flex:1;min-width:0;">
                <div class="taskText" style="display:flex;align-items:center;gap:6px;">
                    ${dot}
                    <span style="${done ? "text-decoration:line-through;opacity:0.55;" : ""}">${escapeHtml(task.task)}</span>
                    ${hiPri ? `<span style="color:#F87171;font-size:10px;">🔥 High</span>` : ""}
                </div>
                <div class="taskMeta">
                    ${dateLabel ? `📅 ${dateLabel}` : ""}
                    ${task.time ? `⏰ ${task.time}` : ""}
                    ${!dateLabel && !task.time ? "No date set" : ""}
                </div>
            </div>
        </div>
        <div style="display:flex;gap:5px;flex-shrink:0;">
            <button class="iconBtn ${done ? "btnDone" : "btnPrimary"}" onclick="toggleTask(${task.id})">✔</button>
            <button class="iconBtn btnDanger" onclick="deleteTask(${task.id})">🗑</button>
        </div>
    </div>`;
}

function emptyMsg(txt) {
    return `<p style="color:var(--t3);font-size:13px;padding:16px 0;text-align:center;">${txt}</p>`;
}

function toggleCompleted() {
    completedVisible = !completedVisible;
    const l = document.getElementById("completedTaskList");
    const a = document.getElementById("completedToggleArrow");
    if (l) l.style.display = completedVisible ? "block" : "none";
    if (a) a.innerText = completedVisible ? "∨" : "›";
}

async function deleteTask(id) {
    await fetch("/reminder/" + id, {method:"DELETE"});
    loadPlanner();
}

async function toggleTask(id) {
    await fetch("/reminder/" + id + "/toggle", {method:"POST"});
    loadPlanner();
}
/* ─────────────────────────────────────────────────────────
   9. WATER
───────────────────────────────────────────────────────── */

function renderHomeWaterDrops() {
    const c=document.getElementById("homeWaterDrops"); if(!c) return; c.innerHTML="";
    for(let i=0;i<waterTarget;i++){const s=document.createElement("span");s.className=`waterDrop ${i<water?"filled":"empty"}`;s.innerText="💧";c.appendChild(s);}
    safe("homeWaterCount",el=>el.innerText=water); safe("homeWaterTarget",el=>el.innerText=waterTarget);
    safe("wellWaterSub",el=>el.innerText=`${water} / ${waterTarget} glasses today`);
    localStorage.setItem("water",water);
}

function loadWaterScreen() { renderWaterRing(); renderWaterGlassGrid(); renderWaterLog(); renderWaterChart(); safe("waterTargetLabel",el=>el.innerText=waterTarget); safe("waterMlLabel",el=>el.innerText=(water*250)+" ml"); }

function renderWaterRing() {
    safe("detailWaterCount",el=>el.innerText=water);
    const c=document.getElementById("waterRingCircle"); if(!c) return;
    c.style.strokeDashoffset=314-Math.min(water/waterTarget,1)*314;
}

function renderWaterGlassGrid() {
    const c=document.getElementById("detailWaterGlasses"); if(!c) return; c.innerHTML="";
    for(let i=0;i<waterTarget;i++){const d=document.createElement("div");d.className="glassItem";d.innerHTML=`<div class="glassTube ${i<water?"active":""}"><div class="glassFill"></div></div><span class="glassNum">${i+1}</span>`;c.appendChild(d);}
}

function renderWaterLog() {
    const c=document.getElementById("waterLog"); if(!c) return;
    if(waterLog.length===0){c.innerHTML=emptyMsg("No glasses logged yet today");return;}
    c.innerHTML=waterLog.slice().reverse().map(e=>`<div class="waterLogEntry"><span class="waterLogTime">${e.time}</span><span class="waterLogGlass">💧 Glass ${e.glass}</span><span style="font-size:12px;color:var(--text-light);">+250ml</span></div>`).join("");
}

function renderWaterChart() {
    const barEl=document.getElementById("waterBarChart"),labelEl=document.getElementById("waterBarLabels"); if(!barEl||!labelEl) return;
    barEl.innerHTML="";labelEl.innerHTML="";
    const days=[]; for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);days.push(d);}
    const maxVal=Math.max(waterTarget,...days.map(d=>waterWeekly[d.toISOString().slice(0,10)]||0));
    const todayKey=new Date().toISOString().slice(0,10);
    days.forEach(d=>{
        const key=d.toISOString().slice(0,10),val=key===todayKey?water:(waterWeekly[key]||0),pct=maxVal>0?Math.round((val/maxVal)*100):0;
        const bar=document.createElement("div");bar.className="waterBar";
        bar.innerHTML=`<div class="waterBarFill ${key===todayKey?"barToday":""}" style="height:${Math.max(pct,4)}%;"><span class="barVal">${val}</span></div>`;
        barEl.appendChild(bar);
        const lbl=document.createElement("div");lbl.className="barLabel";lbl.innerText=d.toLocaleDateString("en-IN",{weekday:"short"}).slice(0,3);labelEl.appendChild(lbl);
    });
}

function addWater() {
    if(water>=waterTarget) return; water++;
    const now=new Date();
    waterLog.push({time:now.toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit"}),glass:water});
    localStorage.setItem("water",water); localStorage.setItem("waterLog",JSON.stringify(waterLog));
    waterWeekly[now.toISOString().slice(0,10)]=water; localStorage.setItem("waterWeekly",JSON.stringify(waterWeekly));
    renderHomeWaterDrops(); loadWaterScreen();
}

function removeWater() { if(water<=0) return; water--; waterLog.pop(); localStorage.setItem("water",water); localStorage.setItem("waterLog",JSON.stringify(waterLog)); renderHomeWaterDrops(); loadWaterScreen(); }
function resetWater()  { water=0;waterLog=[];localStorage.setItem("water",0);localStorage.setItem("waterLog","[]"); renderHomeWaterDrops(); loadWaterScreen(); }
function openWaterTarget()   { document.getElementById("waterTargetModal").style.display="flex"; }
function closeWaterTarget(e) { if(!e||e.target.classList.contains("modalOverlay")) document.getElementById("waterTargetModal").style.display="none"; }
function saveWaterTarget()   { const v=parseInt(document.getElementById("waterTargetInput").value); if(v>0&&v<=20){waterTarget=v;localStorage.setItem("waterTarget",v);} closeWaterTarget(); loadWaterScreen(); renderHomeWaterDrops(); safe("drawerWaterGoal",el=>el.innerText=`${waterTarget} glasses per day`); }



function renderWaterTip() {
    const el = document.getElementById("homeWaterTip");
    if (!el) return;
    if (typeof AhiraContent !== "undefined") {
        el.innerText = "💡 " + AhiraContent.sessionWater();
        el.style.display = "block";
    }
}


/* ─────────────────────────────────────────────────────────
   10. PERIOD
───────────────────────────────────────────────────────── */

 
function setPeriodDate() {
    // Open the native date picker via a hidden input
    let picker = document.getElementById("_periodDatePicker");
    if (!picker) {
        picker = document.createElement("input");
        picker.type = "date";
        picker.id   = "_periodDatePicker";
        picker.style.cssText = "position:fixed;opacity:0;pointer-events:none;top:50%;left:50%;";
        picker.max = new Date().toISOString().slice(0, 10); // can't be future
        document.body.appendChild(picker);
 
        picker.addEventListener("change", () => {
            const val = picker.value;
            if (!val) return;
            lastPeriodDate = new Date(val + "T00:00:00");
            localStorage.setItem("lastPeriodDate", val);
            calculatePeriod();
 
            // Show confirmation toast
            const toast = document.createElement("div");
            toast.style.cssText = "position:fixed;bottom:120px;left:50%;transform:translateX(-50%);background:#6C3FCE;color:white;padding:10px 20px;border-radius:20px;font-size:13px;font-weight:600;z-index:9999;opacity:0;transition:opacity 0.3s;white-space:nowrap;";
            toast.innerText = "✅ Period date saved!";
            document.body.appendChild(toast);
            requestAnimationFrame(() => toast.style.opacity = "1");
            setTimeout(() => {
                toast.style.opacity = "0";
                setTimeout(() => toast.remove(), 400);
            }, 2000);
        });
    }
    picker.showPicker ? picker.showPicker() : picker.click();
}


function calculatePeriod() {
    if (!lastPeriodDate) {
        // Show "Set date" state
        safe("periodBigLabel",  el => el.innerText = "Tap 'Update Date' to begin tracking");
        safe("periodDateLabel", el => el.innerText  = "No period date set yet");
        safe("wellPeriodSub",   el => el.innerText  = "Tap to set your last period date");
        ["periodDays","periodDaysDetail","periodDaysBig"].forEach(id => safe(id, el => el.innerText = "--"));
        return;
    }
 
    const today     = new Date();
    today.setHours(0, 0, 0, 0);
    const start     = new Date(lastPeriodDate);
    start.setHours(0, 0, 0, 0);
 
    const daysSince = Math.floor((today - start) / (1000 * 60 * 60 * 24));
    const cycle     = 28;
 
    // Where in the current cycle are we?
    const dayInCycle = daysSince % cycle;          // 0–27
    const remaining  = cycle - dayInCycle;          // days until next period
    const progress   = (dayInCycle / cycle) * 100; // % through cycle
 
    // Determine current phase
    let phase = "";
    let phaseEmoji = "";
    if (dayInCycle <= 5) {
        phase = "Menstrual Phase"; phaseEmoji = "🌸";
    } else if (dayInCycle <= 13) {
        phase = "Follicular Phase"; phaseEmoji = "🌱";
    } else if (dayInCycle <= 16) {
        phase = "Ovulation Phase"; phaseEmoji = "⭐";
    } else {
        phase = "Luteal Phase"; phaseEmoji = "🌙";
    }
 
    // Next period date
    const nextDate = new Date(start);
    nextDate.setDate(start.getDate() + daysSince + remaining);
    const nextDateStr = nextDate.toLocaleDateString("en-IN", {
        day: "numeric", month: "long", year: "numeric"
    });
 
    // Update all UI elements
    ["periodDays","periodDaysDetail","periodDaysBig"].forEach(id =>
        safe(id, el => el.innerText = remaining)
    );
    ["periodFill","periodFillWell","periodFillDetail"].forEach(id =>
        safe(id, el => el.style.width = progress + "%")
    );
 
    safe("periodBigLabel",  el => el.innerText = `Next Period in ${remaining} Day${remaining !== 1 ? "s" : ""}`);
    safe("periodDateLabel", el => el.innerText  = `📅 Expected: ${nextDateStr}`);
    safe("wellPeriodSub",   el => el.innerText  = `Next in ${remaining} days · ${phaseEmoji} ${phase}`);
 
    // Cycle phase label if element exists
    safe("currentPhaseLabel", el => el.innerText = `${phaseEmoji} ${phase}`);
    safe("dayInCycleLabel",   el => el.innerText = `Day ${dayInCycle + 1} of ${cycle}`);
 
    // Home screen dots
    const dc = document.getElementById("homePeriodDots");
    if (dc) {
        dc.innerHTML = "";
        const filled = Math.floor((dayInCycle / cycle) * 8);
        for (let i = 0; i < 8; i++) {
            const dot = document.createElement("span");
            dot.className = "dot" + (i < filled ? " filled" : "") + (i === filled ? " today" : "");
            dc.appendChild(dot);
        }
    }
}


function renderPeriodTip() {
    const el = document.getElementById("periodTipText");
    if (!el) return;
    if (typeof AhiraContent !== "undefined") {
        el.innerText = AhiraContent.sessionPeriod();
    }
}

/* ─────────────────────────────────────────────────────────
   11. MEDICINE
───────────────────────────────────────────────────────── */

function toggleMedicineForm() { const f=document.getElementById("medicineForm");if(!f) return;const o=f.style.display!=="none";f.style.display=o?"none":"block";if(!o){selectedMedPriority="normal";initChips("medPriorityChips","medpri");} }
function filterMeds(type,btn) { currentMedFilter=type; document.querySelectorAll(".filterTab").forEach(b=>b.classList.remove("active")); if(btn) btn.classList.add("active"); loadMedicines(); }

function addMedicine() {
    const name=document.getElementById("medName").value.trim(),dose=parseInt(document.getElementById("medDose").value)||0,stock=parseInt(document.getElementById("medStock").value)||0,time=document.getElementById("medTime").value,frequency=document.getElementById("medFrequency").value,notes=document.getElementById("medNotes").value.trim();
    if(!name||!stock){alert("Please enter medicine name and stock.");return;}
    const emojis=["💊","🩺","🧴","🍊","🧪","💉"];
    medicines.push({name,dose,stock,originalStock:stock,time,frequency,notes,priority:selectedMedPriority,emoji:emojis[Math.floor(Math.random()*emojis.length)],taken:false,addedDate:new Date().toISOString().slice(0,10)});
    localStorage.setItem("medicines",JSON.stringify(medicines));
    ["medName","medDose","medStock","medTime","medNotes"].forEach(id=>safe(id,el=>el.value=""));
    toggleMedicineForm(); loadMedicines();
}

function loadMedicines() {
    const container=document.getElementById("medicineList"); if(!container) return; container.innerHTML="";
    const filtered=medicines.filter(m=>currentMedFilter==="all"||m.frequency===currentMedFilter);
    const sections={critical:filtered.filter(m=>m.priority==="high"),daily:filtered.filter(m=>m.priority!=="high"&&m.frequency!=="weekly"),weekly:filtered.filter(m=>m.frequency==="weekly")};
    let html="";
    if(sections.critical.length){html+=`<div class="sectionLabel" style="color:#ff6b8a;">🔥 Critical</div>`;sections.critical.forEach(m=>html+=buildMedCard(m,medicines.indexOf(m)));}
    if(sections.daily.length){html+=`<div class="sectionLabel">Daily</div>`;sections.daily.forEach(m=>html+=buildMedCard(m,medicines.indexOf(m)));}
    if(sections.weekly.length){html+=`<div class="sectionLabel">Weekly</div>`;sections.weekly.forEach(m=>html+=buildMedCard(m,medicines.indexOf(m)));}
    if(!html) html=emptyMsg("No medicines added yet 💊");
    container.innerHTML=html;
    const low=medicines.filter(m=>m.stock<=5).length,taken=medicines.filter(m=>m.taken).length;
    safe("medTotalCount",el=>el.innerText=medicines.length); safe("medLowCount",el=>el.innerText=low); safe("medTakenCount",el=>el.innerText=taken);
    safe("wellMedSub",el=>{if(medicines.length===0){el.innerText="No medicines tracked";return;}el.innerText=`${medicines.length} tracked${low>0?` · ${low} low ⚠️`:" · All OK ✅"}`;});
    renderHomeMedCard(); renderHomeAlerts();
}

function buildMedCard(med,i) {
    const sp=med.originalStock>0?Math.round((med.stock/med.originalStock)*100):0,sc=med.stock<=5?"#ff6b8a":med.stock<=10?"#ffb347":"var(--purple)";
    return `<div class="medCard" style="${med.priority==="high"?"border-left:3px solid #ff6b8a;":""}"><div class="medIconBox">${med.emoji||"💊"}</div><div class="medInfo" style="flex:1;"><div class="medName">${med.name}${med.priority==="high"?` <span style="font-size:11px;color:#ff6b8a;">CRITICAL</span>`:""}</div><div class="medMeta">${med.dose?med.dose+"mg · ":""}${med.frequency||"daily"}${med.time?" · ⏰ "+med.time:""}</div>${med.notes?`<div class="medNoteText">📝 ${med.notes}</div>`:""}<div class="medStockBar"><div class="medStockFill" style="width:${sp}%;background:${sc};"></div></div><div style="font-size:11px;color:${sc};margin-top:2px;">📦 ${med.stock} left</div></div><div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;"><div class="medCheck ${med.taken?"checked":""}" onclick="toggleMedTaken(${i})">${med.taken?"✓":""}</div><button class="iconBtn btnDanger" style="font-size:11px;padding:3px 7px;" onclick="deleteMedicine(${i})">🗑</button></div></div>`;
}

function toggleMedTaken(i) { if(!medicines[i].taken&&medicines[i].stock>0) medicines[i].stock=Math.max(0,medicines[i].stock-1); medicines[i].taken=!medicines[i].taken; localStorage.setItem("medicines",JSON.stringify(medicines)); loadMedicines(); }
function deleteMedicine(i)  { medicines.splice(i,1); localStorage.setItem("medicines",JSON.stringify(medicines)); loadMedicines(); }


/* ─────────────────────────────────────────────────────────
   12. GROCERY
───────────────────────────────────────────────────────── */

const catEmoji={veggies:"🥕",dairy:"🥛",snacks:"🍪",other:"📦",all:"🛒"};
function openGroceryForm()   { document.getElementById("groceryFormModal").style.display="flex"; }
function closeGroceryForm(e) { if(!e||e.target.classList.contains("modalOverlay")) document.getElementById("groceryFormModal").style.display="none"; }

function addGroceryItem() {
    const name=document.getElementById("groceryName").value.trim(),qty=parseInt(document.getElementById("groceryQty").value)||1,unit=document.getElementById("groceryUnit").value,category=document.getElementById("groceryCat").value,urgency=document.getElementById("groceryUrgency").value,deadline=document.getElementById("groceryDeadline").value,notes=document.getElementById("groceryNotes").value.trim();
    if(!name){alert("Please enter item name.");return;}
    groceryItems.push({name,qty,unit,category,urgency,deadline,notes,checked:false,emoji:catEmoji[category]||"🛒",addedDate:new Date().toISOString().slice(0,10)});
    localStorage.setItem("groceryItems",JSON.stringify(groceryItems));
    ["groceryName","groceryQty","groceryDeadline","groceryNotes"].forEach(id=>safe(id,el=>el.value=""));
    closeGroceryForm(); loadGrocery();
}

function loadGrocery() {
    const urgentEl=document.getElementById("urgentGroceryList"),fullEl=document.getElementById("groceryFullList"); if(!urgentEl||!fullEl) return;
    urgentEl.innerHTML="";fullEl.innerHTML="";
    const filtered=groceryItems.filter(item=>currentGroceryFilter==="all"||item.category===currentGroceryFilter);
    filtered.forEach(item=>{const i=groceryItems.indexOf(item),card=buildGroceryCard(item,i);if(item.urgency==="urgent"&&!item.checked) urgentEl.innerHTML+=card; else fullEl.innerHTML+=card;});
    if(!urgentEl.innerHTML) urgentEl.innerHTML=emptyMsg("No urgent items ✅");
    if(!fullEl.innerHTML)   fullEl.innerHTML=emptyMsg("No items yet. Tap + Add to start.");
    safe("groceryTotalCount",el=>el.innerText=groceryItems.length);
    safe("groceryUrgentCount",el=>el.innerText=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked).length);
    safe("groceryDoneCount",el=>el.innerText=groceryItems.filter(g=>g.checked).length);
    safe("wellGrocerySub",el=>{const urg=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked).length;el.innerText=urg>0?`${urg} urgent item${urg>1?"s":""} ⚠️`:`${groceryItems.length} items tracked`;});
    renderHomeGroceryCard(); renderHomeAlerts();
}

function buildGroceryCard(item,i) {
    const isOvr=item.deadline&&new Date(item.deadline)<new Date(),ds=item.deadline?`<span style="color:${isOvr?"#ff6b8a":"var(--text-light)"};">📅 ${item.deadline}</span>`:"",ub=item.urgency==="urgent"?`<span class="urgencyBadge urgent">Urgent</span>`:item.urgency==="low"?`<span class="urgencyBadge low">Low</span>`:"";
    return `<div class="groceryItemCard ${item.checked?"groceryDone":""}"><div class="groceryCheck ${item.checked?"checked":""}" onclick="toggleGrocery(${i})">${item.checked?"✓":""}</div><div style="flex:1;"><div class="groceryName ${item.checked?"strikethrough":""}">${item.emoji} ${item.name} ${ub}</div><div class="groceryMeta">${item.qty} ${item.unit||"pcs"} ${ds} ${item.notes?"· "+item.notes:""}</div></div><button class="iconBtn btnDanger" style="font-size:11px;padding:3px 7px;" onclick="deleteGrocery(${i})">🗑</button></div>`;
}

function toggleGrocery(i)  { groceryItems[i].checked=!groceryItems[i].checked; localStorage.setItem("groceryItems",JSON.stringify(groceryItems)); loadGrocery(); }
function deleteGrocery(i)  { groceryItems.splice(i,1); localStorage.setItem("groceryItems",JSON.stringify(groceryItems)); loadGrocery(); }
function filterGrocery(type,btn) { currentGroceryFilter=type; document.querySelectorAll(".filterTab").forEach(b=>b.classList.remove("active")); if(btn) btn.classList.add("active"); loadGrocery(); }


/* ─────────────────────────────────────────────────────────
   13. WELLNESS LOADER
───────────────────────────────────────────────────────── */

 
function loadWellnessScreen() {
    calculatePeriod();
    renderHomeWaterDrops();
    loadMedicines();
    loadGrocery();
 
    // Rotate wellness tip on every load (uses AhiraContent if available)
    const tipEl = document.getElementById("wellnessDailyTip");
    if (tipEl && typeof AhiraContent !== "undefined") {
        tipEl.innerText = AhiraContent.randomWaterTip();
    }
 
    // Rotate period tip on every load
    const periodTipEl = document.getElementById("wellnessPeriodTip");
    if (periodTipEl && typeof AhiraContent !== "undefined") {
        periodTipEl.innerText = "💡 " + AhiraContent.randomPeriodTip();
    }
}
 

/* ─────────────────────────────────────────────────────────
   14. MOOD CHECKER
───────────────────────────────────────────────────────── */

function selectMood(btn, mood, emoji) {
    document.querySelectorAll(".moodBtn").forEach(b=>b.classList.remove("selected")); btn.classList.add("selected");

    const allResponses = {
        happy: [
            {text:`${emoji} You're absolutely glowing today! That energy is contagious 🌟\n\nKeep doing whatever made you feel this way. Maybe share that joy with someone you love?`, tip:"Write down 3 things that made you happy today — it reinforces the good feelings."},
            {text:`${emoji} Love this energy! Happy looks so good on you 💛\n\nRide this wave — it's a perfect day to do something you've been putting off.`, tip:"Celebrate even small wins today. Joy multiplies when you acknowledge it."},
            {text:`${emoji} This makes me so happy to hear! 🎉\n\nHappy days are worth remembering. Take a photo, call a friend, soak it in.`, tip:"Share your mood with someone — happiness grows when it's passed on."},
        ],
        calm: [
            {text:`${emoji} What a peaceful state to be in 🌿\n\nCalmness is a superpower. Use this energy to focus, create, or just breathe.`, tip:"Try a 5-minute mindful breathing session to deepen this calm."},
            {text:`${emoji} That quiet stillness you're feeling? Protect it 🕊️\n\nNot every moment needs to be productive. Peace is its own reward.`, tip:"Limit screen time for the next hour — let the calm linger."},
            {text:`${emoji} Calm is rare and beautiful 🌙\n\nUse this headspace wisely — journal, plan, or simply be present with yourself.`, tip:"Light a candle or make herbal tea. Anchor this feeling with a simple ritual."},
        ],
        tired: [
            {text:`${emoji} You deserve rest — no guilt about that 💤\n\nDrink some water, take a short nap, and don't push yourself too hard today.`, tip:"A 20-minute power nap restores alertness. Avoid screens before sleeping."},
            {text:`${emoji} Your body is sending a clear message — listen to it 🛌\n\nRest isn't laziness. It's how you come back stronger tomorrow.`, tip:"Close your eyes for 10 minutes even if you don't fully sleep. It still helps."},
            {text:`${emoji} Being tired is your body asking for care 💜\n\nSomething warm to drink, dim lights, and gentle music can do wonders.`, tip:"Check your water and food intake — sometimes tiredness is just dehydration or low blood sugar."},
        ],
        sad: [
            {text:`${emoji} It's okay to feel sad. You don't have to be okay all the time 💜\n\nAhira is here. Take it one moment at a time. Be gentle with yourself.`, tip:"Step outside for 10 minutes. Fresh air can gently lift your mood."},
            {text:`${emoji} Sadness is a feeling, not a life sentence 🌧️\n\nLet yourself feel it without judgment. You're allowed to have hard days.`, tip:"Write down what's making you sad. Getting it out of your head helps."},
            {text:`${emoji} You don't have to carry this alone 💜\n\nReach out to someone you trust, or just talk to me — I'm here, always.`, tip:"Do one small kind thing for yourself today. Even making your favourite snack counts."},
        ],
        stressed: [
            {text:`${emoji} Take a breath — you've handled hard things before 💪\n\nBreak whatever is stressing you into tiny steps. You don't have to solve everything right now.`, tip:"Write down what's stressing you, then pick just one small thing to act on."},
            {text:`${emoji} Stress means you care. But it also means you need a moment 🌬️\n\nStep away for 5 minutes. Make tea. Come back fresh.`, tip:"The 2-minute rule: if something takes less than 2 minutes, do it now. Clear the small stuff."},
            {text:`${emoji} The pressure you're feeling is real — and so is your ability to get through it 💜\n\nYou've survived every hard day so far. This one is no different.`, tip:"Box breathing: in 4, hold 4, out 4, hold 4. Repeat 4 times. Instant calm."},
        ],
        anxious: [
            {text:`${emoji} Your feelings are valid. Anxiety is hard 💜\n\nTry 5-4-3-2-1 grounding: name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste.`, tip:"Slow breathing — 4 in, hold 4, out 6 — calms your nervous system."},
            {text:`${emoji} When anxiety spikes, your body thinks it's in danger — but you're safe 🌿\n\nPlace your feet flat on the floor. Feel the ground. You are here. You are okay.`, tip:"Cold water on your wrists or splashing your face triggers the dive reflex — it calms anxiety fast."},
            {text:`${emoji} Anxiety lies to us sometimes 💜\n\nAsk yourself: is this thought based on fact or fear? Often, just naming it shrinks it.`, tip:"Write your anxious thought, then write the most realistic counter-thought. Reality is usually kinder."},
        ],
        energetic: [
            {text:`${emoji} Love this energy! ⚡ Channel it well today!\n\nThis is the perfect time to tackle something you've been putting off.`, tip:"Use this energy on your top 1-2 priorities. Don't scatter it."},
            {text:`${emoji} You're on fire today! 🔥 Absolute main character energy.\n\nStart with the hardest task first — you've got the fuel for it right now.`, tip:"Set a timer for 25 minutes and go all in. The Pomodoro method turns energy into results."},
            {text:`${emoji} This kind of energy is gold ⚡\n\nMove your body — even a quick walk or dance break will supercharge it further.`, tip:"Protect this energy by avoiding time-wasting apps. Make the most of it while it lasts."},
        ],
        grateful: [
            {text:`${emoji} Gratitude is one of the most powerful feelings 🥰\n\nYou're in a beautiful headspace. Appreciate the small things — they add up to everything.`, tip:"Text someone you're grateful for today. It'll make you both feel wonderful."},
            {text:`${emoji} A grateful heart is a magnet for more good things 🌸\n\nThis feeling you have? It's a sign things are going well — even if imperfectly.`, tip:"Write 3 specific things you're grateful for. Specificity makes gratitude more powerful."},
            {text:`${emoji} You noticed the good today — that's not nothing. That's everything 💜\n\nGratitude is a practice and you're doing it beautifully.`, tip:"Take a photo of something beautiful around you right now. Capture what you're grateful for."},
        ],
    };

    const options = allResponses[mood];
    const r = options[Math.floor(Math.random() * options.length)];
    const el = document.getElementById("moodResponse"); if(!el||!r) return;
    el.innerHTML=`<div style="margin-bottom:8px;">${r.text.replace(/\n/g,"<br>")}</div><div style="background:rgba(138,108,255,0.08);border-radius:8px;padding:8px 10px;font-size:12px;color:var(--purple);font-weight:500;">💡 ${r.tip}</div><button onclick="document.getElementById('message').value='I feel ${mood}';navApp('chatScreen',null);sendMessage();" style="margin-top:10px;width:100%;padding:9px;border:none;border-radius:12px;background:linear-gradient(135deg,var(--purple),#b06fff);color:white;font-size:13px;font-weight:600;font-family:'DM Sans',sans-serif;cursor:pointer;">💬 Talk to Ahira about this</button>`;
    el.classList.add("visible");
}


/* ─────────────────────────────────────────────────────────
   15. INIT
───────────────────────────────────────────────────────── */



/* ── 5. REPLACE window.onload (at very bottom of chat.js) ─ */
 
window.onload = function() {
    document.getElementById("authLogo").style.display    = "none";
    document.getElementById("authWrapper").style.display = "none";
    document.getElementById("appWrapper").style.display  = "none";
    document.querySelectorAll(".appScreen").forEach(s => s.classList.remove("active"));
 
    // Intercept browser back button — go home instead of closing
    window.history.pushState({ screen: "homeScreen" }, "", "");
    window.addEventListener("popstate", (e) => {
        const appVisible = document.getElementById("appWrapper").style.display !== "none";
        if (!appVisible) return; // auth screen — let it close
 
        // If not on home, go home
        const home = document.getElementById("homeScreen");
        if (home && !home.classList.contains("active")) {
            navApp("homeScreen", document.querySelector(".navItem"));
            window.history.pushState({ screen: "homeScreen" }, "", "");
        } else {
            // Already on home — push state again to prevent close
            window.history.pushState({ screen: "homeScreen" }, "", "");
        }
    });
 
    if (typeof AhiraSplash !== "undefined") AhiraSplash.init(2600);
    checkSession();
};
