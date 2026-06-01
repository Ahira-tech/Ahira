/* ==========================================================
   AHIRA — chat.js  v3.1
   FIXES: rotating cycle insights, rotating hydration tips,
   working settings drawer, edit profile modal,
   period settings modal, 4 legal pages with full content.
========================================================== */

/* ─── CONTENT LIBRARY ──────────────────────────────────── */
const _QUOTES=[
"You have survived every hard day so far. That's a 100% success rate.",
"Strength doesn't always roar. Sometimes it's the quiet voice saying I'll try again tomorrow.",
"You are not behind. You are on your own beautiful timeline.",
"The fact that you're still here, still trying — that's extraordinary.",
"Difficult roads often lead to the most breathtaking destinations.",
"You've been through storms before. You know how to weather them.",
"Every setback is setting you up for a stronger comeback.",
"You are braver than you believe, stronger than you seem, and more loved than you know.",
"Growth is uncomfortable because you're expanding. Keep going.",
"You are worthy of love, rest, joy, and abundance — right now, as you are.",
"Your worth is not measured by your productivity. You are enough.",
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
"You — exactly as you are — are enough. Always.",
];

const _PERIOD_TIPS=[
"A heating pad on your lower abdomen relaxes uterine muscles and eases cramps naturally.",
"Gentle yoga poses like Child Pose and Cat-Cow can reduce period cramps within minutes.",
"A warm bath with Epsom salts helps relax pelvic muscles and soothes period pain.",
"Light walking improves blood flow and triggers endorphins that act as natural painkillers.",
"Massaging your lower abdomen with lavender or clary sage oil can reduce cramping.",
"Drinking chamomile tea has anti-inflammatory and antispasmodic effects on uterine muscles.",
"Applying heat is often as effective as ibuprofen for mild to moderate period cramps.",
"Ginger tea steeped in hot water is a powerful natural anti-inflammatory for cramps.",
"Iron-rich foods like lentils, spinach, and red meat help replace iron lost during bleeding.",
"Vitamin C helps your body absorb iron — pair iron foods with lemon, orange, or tomato.",
"Magnesium-rich foods like dark chocolate, almonds, and avocado reduce PMS symptoms.",
"Omega-3 fatty acids in salmon, walnuts, and flaxseed reduce period pain inflammation.",
"Calcium-rich foods like dairy, leafy greens, and tofu help reduce mood swings and cramps.",
"Reduce salt intake before your period to minimise bloating and water retention.",
"Avoid excessive sugar during your period — it spikes then crashes energy and worsens mood.",
"Turmeric contains curcumin, a natural anti-inflammatory — add it to warm milk or curries.",
"Tracking your cycle for 3 months reveals your personal patterns, not just averages.",
"A normal cycle is anywhere from 21 to 35 days — not just the textbook 28.",
"PMS affects up to 75% of menstruating people — you are not imagining it.",
"Emotional sensitivity before your period is driven by progesterone drops, not being dramatic.",
"Reducing caffeine the week before your period can significantly lower PMS anxiety.",
"Exercise in the luteal phase helps metabolise excess estrogen and reduce PMS.",
"B6 vitamin supplements can help reduce PMS mood symptoms like irritability and depression.",
"A consistent sleep schedule during the luteal phase dramatically improves PMS symptoms.",
"Your cycle has four phases: menstrual, follicular, ovulatory, and luteal. Each feels different.",
"Estrogen peaks around ovulation, making you feel sociable, confident, and energised.",
"Progesterone rises after ovulation, making you feel more introspective and tired.",
"Your metabolism speeds up in the luteal phase — you genuinely need slightly more calories.",
"Cortisol disrupts your hormonal cycle more than almost anything else — manage your stress.",
"Irregular periods are often your body signalling stress, undereating, or overexercising.",
"Your hormones affect your skin, mood, sleep, digestion, and energy — they are interconnected.",
"Your period is not a weakness. It is evidence of extraordinary biological complexity.",
"Understanding your cycle phases helps you plan work, exercise, and social events more wisely.",
"Your most productive, energetic days are typically in the follicular phase (days 7-13).",
"Being in sync with women you live with is real — it is called menstrual synchrony.",
];

const _WATER_TIPS=[
"Your body is about 60% water — hydration affects every single system.",
"Even mild dehydration (1-2%) impairs concentration, mood, and physical performance.",
"Water helps flush toxins through your kidneys — the body's natural filtration system.",
"Proper hydration supports glowing skin more than most skincare products.",
"Water lubricates your joints — dehydration is a leading cause of joint pain.",
"Your brain is 73% water. Staying hydrated is literally feeding your brain.",
"Hydration supports a healthy metabolism and helps regulate body temperature.",
"Staying hydrated during your period reduces cramping and bloating significantly.",
"If your urine is pale yellow you're well hydrated. Dark yellow means drink more.",
"A simple formula: drink 30-35 ml of water per kilogram of body weight daily.",
"You need more water when you exercise, when it's hot, or when you're unwell.",
"You lose up to 1.5 litres through breathing, sweating, and digestion daily — replenish it.",
"Your thirst mechanism lags behind actual dehydration — drink before you feel thirsty.",
"Start every morning with a full glass of water before coffee or food.",
"Keep a water bottle visible on your desk — out of sight, out of mind really does apply.",
"Link water drinking to existing habits: after brushing teeth, before meals, after waking.",
"Drink a glass of water before every meal — it also prevents overeating.",
"Add fresh lemon or lime for a vitamin C boost and better taste.",
"Mint and cucumber water is refreshing and supports digestion.",
"Coconut water is an excellent post-exercise hydrator with natural electrolytes.",
"Herbal teas (peppermint, chamomile, rooibos) count as hydration with added benefits.",
"Eating water-rich fruits counts: cucumber is 96% water, watermelon is 92%.",
"A headache is often the first sign your body sends when you're dehydrated.",
"Fatigue that hits midday is frequently dehydration, not just tiredness.",
"Difficulty concentrating? Drink a glass of water before reaching for caffeine.",
"Mood changes and irritability are early symptoms of inadequate hydration.",
"Constipation is frequently a hydration issue — water softens stool and aids digestion.",
"Sipping water throughout the day is more effective than drinking large amounts at once.",
"Electrolytes (sodium, potassium, magnesium) help water enter cells effectively.",
"Room temperature water is absorbed faster than ice-cold water.",
"Alcohol is a diuretic — drink a glass of water for every alcoholic drink you have.",
"Hydration supports better sleep — but stop big drinks 2 hours before bed.",
"Watermelon, strawberries, oranges, and spinach are excellent hydrating foods.",
"Green tea is hydrating AND contains antioxidants — a great water alternative.",
"Set phone reminders every 2 hours if you tend to forget during busy days.",
"Bad breath can be caused by dehydration reducing saliva production.",
"Muscle cramps especially at night are often a sign of dehydration and low electrolytes.",
];

/* Cycle insights — used in the period tracker Cycle Insights card */
const _CYCLE_INSIGHTS=[
{icon:"🌸",text:"Prepare for PMS symptoms and cravings in your luteal phase"},
{icon:"💧",text:"Stay hydrated — your body needs more water during menstruation"},
{icon:"🔥",text:"Use a heating pad for cramps — it works as well as ibuprofen"},
{icon:"🥗",text:"Eat iron-rich foods this week to replenish what is lost during your period"},
{icon:"🧘",text:"Gentle yoga and stretching can reduce cramps significantly"},
{icon:"😴",text:"Your energy is naturally lower right now — rest without guilt"},
{icon:"🍫",text:"Dark chocolate cravings? It's your body asking for magnesium"},
{icon:"🌙",text:"Progesterone makes you more introspective this week — journal it out"},
{icon:"⚡",text:"Ovulation is near — you may feel your most energetic and sociable"},
{icon:"🌱",text:"Your follicular phase is great for starting new projects and goals"},
{icon:"💊",text:"Consider magnesium supplements — they reduce PMS by up to 40%"},
{icon:"🏃",text:"Light exercise releases endorphins that naturally ease period pain"},
{icon:"🍵",text:"Chamomile tea eases cramping and promotes better sleep tonight"},
{icon:"🧂",text:"Reduce salt intake this week to minimize bloating and water retention"},
{icon:"☀️",text:"Your most productive clear-headed days are coming in the follicular phase"},
{icon:"🌊",text:"Your cycle is a superpower — each phase brings different strengths"},
{icon:"💆",text:"A warm bath with Epsom salts can ease muscle tension and cramps"},
{icon:"🫐",text:"Anti-inflammatory foods like blueberries and turmeric help with period pain"},
{icon:"📅",text:"Tracking your cycle for 3 months reveals your unique personal patterns"},
{icon:"💜",text:"Your emotions this week are hormonally driven — be extra gentle with yourself"},
];

const _WELCOME=[
"Welcome back I missed you",
"Hey you — so glad you're here",
"You showed up today. That matters.",
"I'm here for you, always",
"Let's take this day one breath at a time",
"Good to see you again",
"Your safe space is open",
"Ahira is ready when you are",
"You are not alone — not today, not ever",
"Hello, beautiful soul",
"Ready to take on today together?",
"Soft landing, right here",
"Your feelings are safe here",
"New day, new energy — let's go",
"This is your space. Welcome home",
"Whatever today holds, I'm with you",
"Take a breath. You've got this.",
"You are seen. You are valued. You are here.",
"Today is a fresh page. Write something kind",
"Even on hard days, you belong here",
];

function _pick(arr){return arr[Math.floor(Math.random()*arr.length)];}
function _daily(arr){const d=Math.floor((new Date()-new Date(new Date().getFullYear(),0,0))/864e5);return arr[d%arr.length];}
const _sc={};
function _session(key,arr){if(!_sc[key])_sc[key]=_pick(arr);return _sc[key];}

/* Pick N random items from array without repeats */
function _pickN(arr,n){return [...arr].sort(()=>Math.random()-0.5).slice(0,Math.min(n,arr.length));}

const AhiraContent={
  randomQuote:()=>_pick(_QUOTES),
  randomPeriodTip:()=>_pick(_PERIOD_TIPS),
  randomWaterTip:()=>_pick(_WATER_TIPS),
  randomWelcome:()=>_pick(_WELCOME),
  randomCycleInsights:(n)=>_pickN(_CYCLE_INSIGHTS,n||3),
  randomWaterTips:(n)=>_pickN(_WATER_TIPS,n||4),
  dailyQuote:()=>_daily(_QUOTES),
  dailyWelcome:()=>_daily(_WELCOME),
  sessionWater:()=>_session("water",_WATER_TIPS),
  sessionPeriod:()=>_session("period",_PERIOD_TIPS),
  sessionWelcome:()=>_session("welcome",_WELCOME),
  sessionQuote:()=>_daily(_QUOTES),
};

function renderDailyQuote(){safe("dailyQuote",el=>el.innerText='"'+AhiraContent.dailyQuote()+'"');}

/* ─── SETTINGS ──────────────────────────────────────────── */
let appSettings={notifyReminders:true,notifyWater:true,notifyMedicine:true,notifyPeriod:true,showDailyQuotes:true,cycleLength:28};

function loadSettings(){
  const s=localStorage.getItem("ahiraSettings");
  if(s){try{appSettings={...appSettings,...JSON.parse(s)};}catch(e){}}
}
function saveSettings(){localStorage.setItem("ahiraSettings",JSON.stringify(appSettings));}

function applySettingsToDrawer(){
  safe("drawerWaterGoal",el=>el.innerText=waterTarget+" glasses per day");
  const tm={toggleReminders:"notifyReminders",toggleWater:"notifyWater",toggleMedicine:"notifyMedicine",togglePeriod:"notifyPeriod",toggleQuotes:"showDailyQuotes"};
  Object.entries(tm).forEach(([id,key])=>{const b=document.getElementById(id);if(b)b.classList.toggle("on",appSettings[key]);});
}

function toggleSetting(btn){
  btn.classList.toggle("on");
  const tm={toggleReminders:"notifyReminders",toggleWater:"notifyWater",toggleMedicine:"notifyMedicine",togglePeriod:"notifyPeriod",toggleQuotes:"showDailyQuotes"};
  const key=tm[btn.id];
  if(key){appSettings[key]=btn.classList.contains("on");saveSettings();}
  if(btn.id==="toggleQuotes"){
    safe("dailyQuote",el=>{const card=el.closest(".thoughtCard");if(card)card.style.display=appSettings.showDailyQuotes?"block":"none";});
  }
}

/* ─── EDIT PROFILE MODAL ────────────────────────────────── */
function openEditProfile(){
  closeDrawer();
  if(!document.getElementById("editProfileModal")){
    const m=document.createElement("div");
    m.id="editProfileModal";
    m.style.cssText="position:fixed;inset:0;z-index:600;display:none;align-items:flex-end;justify-content:center;background:rgba(26,10,60,0.5);backdrop-filter:blur(8px);";
    m.innerHTML='<div class="modalCard" onclick="event.stopPropagation()" style="border-radius:28px 28px 0 0;padding:28px 24px 48px;max-height:85vh;overflow-y:auto;width:100%;max-width:390px;scrollbar-width:none;">'
      +'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">'
      +'<div class="modalTitle" style="margin-bottom:0;">Edit Profile</div>'
      +'<button onclick="closeModal(\'editProfileModal\')" style="width:32px;height:32px;border-radius:50%;border:none;background:rgba(108,63,206,0.1);color:var(--p1);font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;">&#10005;</button>'
      +'</div>'
      +'<div style="text-align:center;margin-bottom:22px;">'
      +'<div id="editAvatarPreview" style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#c4a8ff,#f9a8d4);display:flex;align-items:center;justify-content:center;font-family:Poppins,sans-serif;font-size:28px;font-weight:700;color:white;margin:0 auto 8px;">?</div>'
      +'<div style="font-size:12px;color:var(--t3);">Your profile avatar</div>'
      +'</div>'
      +'<div class="formGroup"><div class="formLabel">Full Name</div><input id="editNameInput" class="formInput" type="text" placeholder="Your name"></div>'
      +'<div class="formGroup" style="margin-top:14px;"><div class="formLabel">Email Address</div><input id="editEmailInput" class="formInput" type="email" placeholder="your@email.com"></div>'
      +'<div id="editProfileError" class="authError" style="display:none;margin-top:10px;"></div>'
      +'<div id="editProfileSuccess" style="display:none;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.28);border-radius:8px;padding:10px 14px;font-size:13px;color:#166534;margin-top:10px;">Profile updated successfully!</div>'
      +'<div class="btnGroup" style="margin-top:18px;">'
      +'<button class="actionBtn" onclick="saveEditProfile()" style="margin-top:0;">Save Changes</button>'
      +'<button class="secondaryBtn" onclick="closeModal(\'editProfileModal\')" style="margin-top:0;">Cancel</button>'
      +'</div></div>';
    m.onclick=(e)=>{if(e.target===m)closeModal("editProfileModal");};
    document.querySelector(".phone").appendChild(m);
  }
  if(currentUser){
    safe("editNameInput",el=>el.value=currentUser.name||"");
    safe("editEmailInput",el=>el.value=currentUser.email||"");
    safe("editAvatarPreview",el=>el.innerText=(currentUser.name||"?").charAt(0).toUpperCase());
  }
  safe("editProfileError",el=>el.style.display="none");
  safe("editProfileSuccess",el=>el.style.display="none");
  const m=document.getElementById("editProfileModal");
  m.style.display="flex";
  safe("editNameInput",el=>{el.oninput=()=>safe("editAvatarPreview",av=>av.innerText=(el.value.trim()||"?").charAt(0).toUpperCase());});
}

async function saveEditProfile(){
  const name=document.getElementById("editNameInput")?.value.trim();
  const email=document.getElementById("editEmailInput")?.value.trim();
  if(!name)return safe("editProfileError",el=>{el.innerText="Name cannot be empty.";el.style.display="block";});
  if(!email||!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email))
    return safe("editProfileError",el=>{el.innerText="Please enter a valid email.";el.style.display="block";});
  safe("editProfileError",el=>el.style.display="none");
  const applyUpdate=()=>{
    currentUser={...currentUser,name,email};
    const init=name.charAt(0).toUpperCase();
    safe("drawerName",el=>el.innerText=name);safe("drawerEmail",el=>el.innerText=email);
    safe("drawerAvatar",el=>el.innerText=init);safe("profileBtn",el=>el.innerText=init);
    const h=new Date().getHours(),g=h<12?"Good morning":h<17?"Good afternoon":"Good evening";
    safe("homeGreeting",el=>el.innerText=g+", "+name+" ");
    safe("editProfileSuccess",el=>el.style.display="block");
    setTimeout(()=>closeModal("editProfileModal"),1500);
  };
  try{
    const res=await fetch("/update_profile",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email})});
    const data=await res.json();
    if(data.status==="ok"||data.status==="success")applyUpdate();
    else safe("editProfileError",el=>{el.innerText=data.message||"Update failed.";el.style.display="block";});
  }catch(e){applyUpdate();}
}

/* ─── PERIOD SETTINGS MODAL ─────────────────────────────── */
let _tempCycle=28,_tempDuration=5;

function openPeriodSettings(){
  closeDrawer();
  if(!document.getElementById("periodSettingsModal")){
    const m=document.createElement("div");
    m.id="periodSettingsModal";
    m.style.cssText="position:fixed;inset:0;z-index:600;display:none;align-items:flex-end;justify-content:center;background:rgba(26,10,60,0.5);backdrop-filter:blur(8px);";
    m.innerHTML='<div class="modalCard" onclick="event.stopPropagation()" style="border-radius:28px 28px 0 0;padding:28px 24px 48px;max-height:85vh;overflow-y:auto;width:100%;max-width:390px;scrollbar-width:none;">'
      +'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">'
      +'<div class="modalTitle" style="margin-bottom:0;">Period Settings</div>'
      +'<button onclick="closeModal(\'periodSettingsModal\')" style="width:32px;height:32px;border-radius:50%;border:none;background:rgba(248,113,113,0.1);color:#dc2626;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;">&#10005;</button>'
      +'</div>'
      +'<div style="background:rgba(255,182,193,0.15);border:1px solid rgba(255,154,118,0.3);border-radius:14px;padding:14px 16px;margin-bottom:18px;font-size:13px;color:#92400E;line-height:1.6;">'
      +'Set your cycle length and last period start date for accurate predictions. Average cycle is 28 days but yours may differ.'
      +'</div>'
      +'<div class="formGroup"><div class="formLabel">Last Period Start Date</div>'
      +'<input id="periodStartDateInput" class="formInput" type="date"></div>'
      +'<div class="formGroup" style="margin-top:16px;"><div class="formLabel">Cycle Length (days)</div>'
      +'<div style="display:flex;align-items:center;gap:12px;margin-top:8px;">'
      +'<button onclick="adjustCycle(-1)" style="width:44px;height:44px;border-radius:50%;border:1.5px solid rgba(108,63,206,0.25);background:rgba(255,255,255,0.8);font-size:24px;color:var(--p1);cursor:pointer;">&#8722;</button>'
      +'<div id="cycleLengthDisplay" style="flex:1;text-align:center;font-family:Poppins,sans-serif;font-size:30px;font-weight:700;color:var(--p1);">28</div>'
      +'<button onclick="adjustCycle(1)" style="width:44px;height:44px;border-radius:50%;border:1.5px solid rgba(108,63,206,0.25);background:rgba(255,255,255,0.8);font-size:24px;color:var(--p1);cursor:pointer;">&#43;</button>'
      +'</div>'
      +'<div style="text-align:center;font-size:12px;color:var(--t3);margin-top:6px;">Most cycles are between 21–35 days</div></div>'
      +'<div class="formGroup" style="margin-top:16px;"><div class="formLabel">Period Duration (days)</div>'
      +'<div style="display:flex;align-items:center;gap:12px;margin-top:8px;">'
      +'<button onclick="adjustDuration(-1)" style="width:44px;height:44px;border-radius:50%;border:1.5px solid rgba(108,63,206,0.25);background:rgba(255,255,255,0.8);font-size:24px;color:var(--p1);cursor:pointer;">&#8722;</button>'
      +'<div id="periodDurationDisplay" style="flex:1;text-align:center;font-family:Poppins,sans-serif;font-size:30px;font-weight:700;color:var(--p1);">5</div>'
      +'<button onclick="adjustDuration(1)" style="width:44px;height:44px;border-radius:50%;border:1.5px solid rgba(108,63,206,0.25);background:rgba(255,255,255,0.8);font-size:24px;color:var(--p1);cursor:pointer;">&#43;</button>'
      +'</div></div>'
      +'<div class="btnGroup" style="margin-top:20px;">'
      +'<button class="actionBtn" onclick="savePeriodSettings()" style="margin-top:0;">Save Settings</button>'
      +'<button class="secondaryBtn" onclick="closeModal(\'periodSettingsModal\')" style="margin-top:0;">Cancel</button>'
      +'</div></div>';
    m.onclick=(e)=>{if(e.target===m)closeModal("periodSettingsModal");};
    document.querySelector(".phone").appendChild(m);
  }
  if(lastPeriodDate)safe("periodStartDateInput",el=>el.value=lastPeriodDate.toISOString().slice(0,10));
  _tempCycle=appSettings.cycleLength||28;
  _tempDuration=parseInt(localStorage.getItem("periodDuration"))||5;
  safe("cycleLengthDisplay",el=>el.innerText=_tempCycle);
  safe("periodDurationDisplay",el=>el.innerText=_tempDuration);
  document.getElementById("periodSettingsModal").style.display="flex";
}
function adjustCycle(d){_tempCycle=Math.max(21,Math.min(35,_tempCycle+d));safe("cycleLengthDisplay",el=>el.innerText=_tempCycle);}
function adjustDuration(d){_tempDuration=Math.max(2,Math.min(10,_tempDuration+d));safe("periodDurationDisplay",el=>el.innerText=_tempDuration);}
function savePeriodSettings(){
  const v=document.getElementById("periodStartDateInput")?.value;
  if(v){lastPeriodDate=new Date(v+"T00:00:00");localStorage.setItem("lastPeriodDate",v);}
  appSettings.cycleLength=_tempCycle;
  localStorage.setItem("periodDuration",_tempDuration);
  saveSettings();calculatePeriod();closeModal("periodSettingsModal");
  showQuickToast("Period settings saved!");
}

/* ─── LEGAL PAGES ───────────────────────────────────────── */
function openLegalPage(k){
  closeDrawer();
  const LEGAL={
    privacy:{
      title:"Privacy Policy",icon:"🔒",
      sections:[
        {type:"date",text:"Effective Date: To be added &nbsp;·&nbsp; Last Updated: 2025"},
        {type:"intro",text:"Ahira is committed to protecting your privacy. This Privacy Policy explains how we collect, use, store, and protect your information when you use our application."},
        {type:"section",title:"1. Information We Collect",
          content:"<b>Personal Information:</b> We may collect your name (if provided), email address (if login is used), and user preferences such as language and settings.<br><br><b>Sensitive Information:</b> Ahira may process mood inputs, health-related inputs (period tracking, wellness data), and chat conversations. We do NOT sell or share this data with third parties for advertising."},
        {type:"section",title:"2. How We Use Your Information",
          content:"We use your data to: provide AI-based responses, personalise your user experience, improve app performance, and enable features like reminders, tracking, and wellness suggestions."},
        {type:"section",title:"3. AI & Chat Data",
          content:"Your conversations may be processed by third-party AI providers (e.g., OpenRouter) to generate responses. We recommend not sharing highly sensitive personal information in chat."},
        {type:"section",title:"4. Data Storage",
          content:"Data may be stored locally on your device or on secure servers. We take reasonable steps to protect your data but cannot guarantee absolute security."},
        {type:"section",title:"5. Data Sharing",
          content:"We do NOT sell your data or share personal data for marketing purposes. We may share data with AI service providers (for functionality only) and hosting providers (e.g., Render, Supabase) as required for the app to function."},
        {type:"section",title:"6. User Control",
          content:"You can delete your account data (where the feature is available), uninstall the app to stop data collection, and control device permissions for notifications and storage."},
        {type:"section",title:"7. Children's Privacy",
          content:"Ahira is not intended for users under the age of 13. We do not knowingly collect data from children under 13."},
        {type:"section",title:"8. Security",
          content:"We implement secure API connections (HTTPS) and basic encryption practices. However, no system is 100% secure and we cannot guarantee absolute protection."},
        {type:"section",title:"9. Changes to This Policy",
          content:"We may update this policy periodically. Continued use of Ahira after changes are posted constitutes your acceptance of the updated policy."},
        {type:"section",title:"10. Contact Us",
          content:"For any questions regarding this Privacy Policy, please contact us. Contact details will be added soon."},
        {type:"footer",text:"By using Ahira, you agree to this Privacy Policy."},
      ]
    },
    terms:{
      title:"Terms of Service",icon:"📋",
      sections:[
        {type:"date",text:"Effective Date: To be added &nbsp;·&nbsp; Governed by the laws of India"},
        {type:"intro",text:"By using Ahira, you agree to the following Terms of Service. Please read them carefully before using the application."},
        {type:"warning",text:"Ahira is an AI-based companion and is NOT a replacement for medical advice, psychological therapy, or professional consultation of any kind."},
        {type:"section",title:"1. Nature of Service",
          content:"Ahira is an AI-based companion application designed for emotional support, productivity, and wellness assistance. It is not intended to replace professional services."},
        {type:"section",title:"2. User Responsibility",
          content:"By using this app, you agree not to misuse it for harmful or illegal purposes, not to rely solely on AI for serious decisions, and to provide accurate information where required."},
        {type:"section",title:"3. AI Limitations",
          content:"Ahira uses AI systems which may produce incorrect or incomplete responses. Responses should not be considered factual or professional advice under any circumstances."},
        {type:"section",title:"4. Acceptable Use",
          content:"You must NOT use the app for harmful, abusive, or illegal purposes, or attempt to exploit or reverse-engineer the system in any way."},
        {type:"section",title:"5. Service Availability",
          content:"We do not guarantee continuous availability or error-free performance of the application at all times."},
        {type:"section",title:"6. Limitation of Liability",
          content:"We are not responsible for decisions made based on AI responses, emotional or mental outcomes from app usage, or data loss due to service interruptions."},
        {type:"section",title:"7. Termination",
          content:"We reserve the right to suspend or terminate access, and to modify or discontinue services at any time without notice."},
        {type:"section",title:"8. Updates to Terms",
          content:"These terms may change over time. Continued use of Ahira after changes constitutes your acceptance of the updated terms."},
        {type:"section",title:"9. Governing Law",
          content:"These terms are governed by the laws of India. Any disputes shall be subject to the jurisdiction of Indian courts."},
        {type:"footer",text:"By using Ahira, you accept these Terms of Service."},
      ]
    },
    disclaimer:{
      title:"Disclaimer",icon:"⚠️",
      sections:[
        {type:"intro",text:"Ahira is an AI-based companion designed to provide general emotional support, guidance, and wellness-related suggestions."},
        {type:"warning",text:"Ahira is NOT a medical professional, therapist, counselor, or diagnostic tool of any kind. Please do not treat any information from Ahira as professional advice."},
        {type:"section",title:"Health Disclaimer",
          content:"Any health-related information provided by Ahira — including period tracking, hydration guidance, or wellness tips — is for informational purposes only. Always consult a qualified healthcare professional for any medical concerns."},
        {type:"section",title:"Emotional Support Disclaimer",
          content:"While Ahira aims to provide supportive and empathetic responses, it cannot and does not replace human relationships or professional mental health support. If you are experiencing a mental health crisis, please seek professional help immediately."},
        {type:"section",title:"AI Accuracy",
          content:"Responses generated by the AI may be inaccurate, incomplete, or may not apply to your specific situation. Information provided should always be cross-checked with reliable, professional sources."},
        {type:"section",title:"Data & Privacy",
          content:"While we take steps to protect your data, the nature of AI-based services means that conversations may be processed by third-party providers. Please avoid sharing highly sensitive personal information in chat."},
        {type:"section",title:"No Emergency Services",
          content:"Ahira is not equipped to handle emergencies. If you or someone you know is in immediate danger or experiencing a medical emergency, please contact local emergency services immediately."},
        {type:"footer",text:"Use Ahira at your own discretion. Your wellbeing matters — always seek real human support when needed."},
      ]
    },
    guidelines:{
      title:"Community Guidelines",icon:"🌸",
      sections:[
        {type:"intro",text:"Ahira is a safe, warm space designed to support you. To maintain this experience for everyone, we ask that all users follow these community guidelines."},
        {type:"section",title:"Be Respectful",
          content:"Engage with Ahira in a kind and respectful manner. Avoid abusive, hateful, or harmful language of any kind. Remember that Ahira is designed to support you — treat it accordingly."},
        {type:"section",title:"Use Responsibly",
          content:"Do not rely on Ahira for critical decisions involving your health, safety, legal matters, or finances. Always consult qualified professionals for serious concerns. Ahira is a support tool, not a decision-maker."},
        {type:"section",title:"Protect Your Privacy",
          content:"Avoid sharing highly sensitive personal data such as passwords, financial information, government IDs, or detailed medical records. Ahira is not a secure vault for sensitive information."},
        {type:"section",title:"Support Others",
          content:"If you know someone who may benefit from professional help, please encourage them to seek it. Ahira can be a starting point, but real human connection and professional support are irreplaceable."},
        {type:"section",title:"Prohibited Behaviour",
          content:"Using Ahira to generate harmful, illegal, or abusive content is strictly prohibited. Attempting to manipulate, exploit, or reverse-engineer the AI system is not permitted and may result in account termination."},
        {type:"section",title:"Mental Health Resources",
          content:"If you are experiencing a mental health crisis, please reach out to a professional. In India, you can contact iCall at 9152987821. International users should contact their local crisis helpline."},
        {type:"section",title:"Reporting Issues",
          content:"If you encounter any issues, bugs, or content that concerns you, please reach out to us. Contact details will be available soon. Your feedback helps us make Ahira better and safer."},
        {type:"footer",text:"Ahira is here to support — not replace — real-world help. Take care of yourself."},
      ]
    }
  };
  const page=LEGAL[k];if(!page)return;
  document.getElementById("legalOverlay")?.remove();

  /* Build HTML from sections */
  function buildSections(sections){
    return sections.map(s=>{
      if(s.type==="date") return '<div style="font-size:11px;color:var(--t4);margin-bottom:14px;background:rgba(108,63,206,0.06);padding:7px 12px;border-radius:8px;">'+s.text+'</div>';
      if(s.type==="intro") return '<p style="font-size:14px;color:var(--t1);line-height:1.8;margin-bottom:16px;font-weight:500;">'+s.text+'</p>';
      if(s.type==="warning") return '<div style="background:rgba(251,191,36,0.12);border:1px solid rgba(251,191,36,0.35);border-radius:12px;padding:14px 16px;font-size:13px;color:#92400E;font-weight:600;margin-bottom:18px;line-height:1.6;">'+s.text+'</div>';
      if(s.type==="section") return '<div style="margin-bottom:18px;"><div style="font-family:Poppins,sans-serif;font-size:14px;font-weight:700;color:var(--p1);margin-bottom:8px;padding-bottom:7px;border-bottom:1px solid rgba(108,63,206,0.15);">'+s.title+'</div><p style="font-size:13px;color:var(--t2);line-height:1.8;margin:0;">'+s.content+'</p></div>';
      if(s.type==="footer") return '<div style="background:linear-gradient(135deg,rgba(108,63,206,0.08),rgba(244,114,182,0.08));border:1px solid rgba(196,168,255,0.3);border-radius:14px;padding:18px;text-align:center;font-size:14px;font-weight:700;color:var(--p1);margin-top:24px;">'+s.text+' </div>';
      return '';
    }).join('');
  }

  const ov=document.createElement("div");
  ov.id="legalOverlay";
  ov.style.cssText="position:fixed;inset:0;z-index:700;background:#F1EEFF;display:flex;flex-direction:column;overflow:hidden;animation:legalSlideUp 0.32s cubic-bezier(.4,0,.2,1);";
  ov.innerHTML='<style>@keyframes legalSlideUp{from{transform:translateY(100%);opacity:0}to{transform:translateY(0);opacity:1}}</style>'
    +'<div style="background:linear-gradient(135deg,var(--p1) 0%,#9B6EF3 60%,var(--a1) 100%);padding:52px 22px 22px;flex-shrink:0;display:flex;align-items:center;gap:14px;box-shadow:0 4px 20px rgba(108,63,206,0.25);">'
    +'<span style="font-size:28px;">'+page.icon+'</span>'
    +'<span style="font-family:Poppins,sans-serif;font-size:20px;font-weight:700;color:white;flex:1;">'+page.title+'</span>'
    +'<button onclick="closeLegalPage()" style="width:36px;height:36px;border-radius:50%;border:none;background:rgba(255,255,255,0.2);color:white;font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;">&#10005;</button>'
    +'</div>'
    +'<div style="flex:1;overflow-y:auto;padding:22px 20px 50px;-webkit-overflow-scrolling:touch;scrollbar-width:none;">'
    +buildSections(page.sections)
    +'</div>';
  document.querySelector(".phone").appendChild(ov);
}

function closeLegalPage(){
  const ov=document.getElementById("legalOverlay");
  if(!ov)return;
  ov.style.transition="opacity 0.25s,transform 0.25s";
  ov.style.opacity="0";ov.style.transform="translateY(40px)";
  setTimeout(()=>ov.remove(),280);
}

/* ─── HELPERS ───────────────────────────────────────────── */
function closeModal(id){const el=document.getElementById(id);if(el)el.style.display="none";}
function showQuickToast(msg){
  const t=document.createElement("div");
  t.style.cssText="position:fixed;bottom:120px;left:50%;transform:translateX(-50%);background:#6C3FCE;color:white;padding:10px 20px;border-radius:20px;font-size:13px;font-weight:600;z-index:9999;opacity:0;transition:opacity 0.3s;white-space:nowrap;pointer-events:none;";
  t.innerText=msg;document.body.appendChild(t);
  requestAnimationFrame(()=>t.style.opacity="1");
  setTimeout(()=>{t.style.opacity="0";setTimeout(()=>t.remove(),400);},2200);
}

/* ─── AUTH ──────────────────────────────────────────────── */
let currentUser=null;
function showAuthPanel(id){
  document.getElementById("loginScreen").style.display="none";
  document.getElementById("registerScreen").style.display="none";
  document.getElementById(id).style.display="block";
}
function showAuthError(id,msg){const el=document.getElementById(id);if(!el)return;el.innerText=msg;el.style.display="block";el.scrollIntoView({behavior:"smooth",block:"nearest"});}
function hideAuthError(id){const el=document.getElementById(id);if(el)el.style.display="none";}
function isValidEmail(e){return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e);}
function isValidName(n){return /^[a-zA-Z\u00C0-\u024F\s\-]{2,50}$/.test(n);}

async function submitRegister(){
  hideAuthError("registerError");
  const name=document.getElementById("regName").value.trim(),email=document.getElementById("regEmail").value.trim(),pw=document.getElementById("regPassword").value,confirm=document.getElementById("regPasswordConfirm").value;
  if(!name)return showAuthError("registerError","Please enter your name.");
  if(!isValidName(name))return showAuthError("registerError","Name should be letters only, at least 2 characters.");
  if(!email)return showAuthError("registerError","Please enter your email.");
  if(!isValidEmail(email))return showAuthError("registerError","Please enter a valid email.");
  if(!pw)return showAuthError("registerError","Please create a password.");
  if(pw.length<6)return showAuthError("registerError","Password must be at least 6 characters.");
  if(pw!==confirm)return showAuthError("registerError","Passwords do not match.");
  const btn=document.getElementById("registerBtn");btn.disabled=true;btn.innerText="Creating account...";
  try{const res=await fetch("/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,email,password:pw})});const data=await res.json();if(data.status==="ok"){currentUser=data.user;enterApp();}else showAuthError("registerError",data.message||"Registration failed.");}
  catch(e){showAuthError("registerError","Could not connect to server.");}
  finally{btn.disabled=false;btn.innerText="Create Account";}
}

async function submitLogin(){
  hideAuthError("loginError");
  const email=document.getElementById("loginEmail").value.trim(),pw=document.getElementById("loginPassword").value;
  if(!email)return showAuthError("loginError","Please enter your email.");
  if(!isValidEmail(email))return showAuthError("loginError","That does not look like a valid email.");
  if(!pw)return showAuthError("loginError","Please enter your password.");
  const btn=document.getElementById("loginBtn");btn.disabled=true;btn.innerText="Signing in...";
  try{const res=await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password:pw})});const data=await res.json();if(data.status==="ok"){currentUser=data.user;enterApp();}else showAuthError("loginError",data.message||"Incorrect email or password.");}
  catch(e){showAuthError("loginError","Could not connect to server.");}
  finally{btn.disabled=false;btn.innerText="Sign In";}
}

async function submitLogout(){
  closeDrawer();
  try{await fetch("/logout",{method:"POST"});}catch(e){}
  currentUser=null;chatHistory=[];
  ["water","waterTarget","waterLog","waterWeekly","medicines","groceryItems","taskMeta","lastPeriodDate"].forEach(k=>localStorage.removeItem(k));
  document.querySelectorAll(".appScreen").forEach(s=>{s.classList.remove("active");s.style.display="none";});
  document.getElementById("appWrapper").style.display="none";
  document.getElementById("authLogo").style.display="block";
  document.getElementById("authWrapper").style.display="block";
  showAuthPanel("loginScreen");
}

async function checkSession(){
  try{const res=await fetch("/me");const data=await res.json();if(data.status==="ok"){currentUser=data.user;enterApp();}else showAuth();}
  catch(e){showAuth();}
}

function showAuth(){
  document.querySelectorAll(".appScreen").forEach(s=>{s.classList.remove("active");s.style.display="none";});
  document.getElementById("authLogo").style.display="block";
  document.getElementById("authWrapper").style.display="block";
  document.getElementById("appWrapper").style.display="none";
  showAuthPanel("loginScreen");
}

function enterApp(){
  document.getElementById("authLogo").style.display="none";
  document.getElementById("authWrapper").style.display="none";
  document.getElementById("appWrapper").style.display="flex";
  document.querySelectorAll(".appScreen").forEach(s=>{s.classList.remove("active");s.style.display="none";});
  loadSettings();
  loadChatHistory(); 
  const hour=new Date().getHours(),tg=hour<12?"Good morning":hour<17?"Good afternoon":"Good evening";
  if(currentUser){
    const init=currentUser.name.charAt(0).toUpperCase();
    safe("profileBtn",el=>el.innerText=init);
    safe("chatWelcomeMsg",el=>el.innerText=AhiraContent.randomWelcome()+" How can I help you today?");
    safe("homeGreeting",el=>el.innerText=tg+", "+currentUser.name+" ");
    safe("drawerName",el=>el.innerText=currentUser.name);
    safe("drawerEmail",el=>el.innerText=currentUser.email);
    safe("drawerAvatar",el=>el.innerText=init);
  }
  water=parseInt(localStorage.getItem("water"))||0;
  waterTarget=parseInt(localStorage.getItem("waterTarget"))||8;
  waterLog=JSON.parse(localStorage.getItem("waterLog"))||[];
  waterWeekly=JSON.parse(localStorage.getItem("waterWeekly"))||{};
  medicines=JSON.parse(localStorage.getItem("medicines"))||[];
  groceryItems=JSON.parse(localStorage.getItem("groceryItems"))||[];
  lastPeriodDate=localStorage.getItem("lastPeriodDate")?new Date(localStorage.getItem("lastPeriodDate")):null;
  navApp("homeScreen",document.querySelector(".navItem"));
}

/* ─── DRAWER ────────────────────────────────────────────── */
function openDrawer(){
  document.getElementById("profileDrawer").classList.add("open");
  document.getElementById("drawerOverlay").classList.add("open");
  applySettingsToDrawer();
}
function closeDrawer(){
  document.getElementById("profileDrawer").classList.remove("open");
  document.getElementById("drawerOverlay").classList.remove("open");
}
function openAbout(){
  closeDrawer();
  const modal=document.getElementById("aboutModal");
  if(modal)modal.style.display="flex";
}


function openDeleteDataModal() {
    closeDrawer();
    if (!document.getElementById("deleteDataModal")) {
        const m = document.createElement("div");
        m.id = "deleteDataModal";
        m.style.cssText = "position:fixed;inset:0;z-index:600;display:none;align-items:flex-end;justify-content:center;background:rgba(26,10,60,0.5);backdrop-filter:blur(8px);";
        m.innerHTML = `
        <div class="modalCard" onclick="event.stopPropagation()" style="border-radius:28px 28px 0 0;padding:28px 24px 48px;width:100%;max-width:390px;">
            <div style="text-align:center;margin-bottom:22px;">
                <div style="width:64px;height:64px;border-radius:50%;background:rgba(248,113,113,0.1);display:flex;align-items:center;justify-content:center;font-size:28px;margin:0 auto 12px;">🗑️</div>
                <div style="font-family:Poppins,sans-serif;font-size:18px;font-weight:700;color:#dc2626;margin-bottom:8px;">Delete My Data</div>
                <div style="font-size:13px;color:var(--t3);line-height:1.7;">This will permanently delete all your local data including chat history, reminders, water logs, medicines, grocery lists, period data, and settings. This cannot be undone.</div>
            </div>
            <div style="background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.2);border-radius:12px;padding:14px;margin-bottom:20px;">
                <div style="font-size:12px;color:#dc2626;line-height:1.7;">
                    What will be deleted:<br>
                    Chat history · Reminders · Water logs<br>
                    Medicines · Grocery items · Period data<br>
                    All app settings and preferences
                </div>
            </div>
            <div id="deleteDataConfirmRow" style="display:flex;align-items:center;gap:10px;margin-bottom:16px;background:rgba(248,113,113,0.06);border-radius:10px;padding:12px;">
                <input type="checkbox" id="deleteConfirmCheck" style="width:18px;height:18px;accent-color:#dc2626;cursor:pointer;flex-shrink:0;">
                <label for="deleteConfirmCheck" style="font-size:13px;color:var(--t2);cursor:pointer;line-height:1.5;">I understand this cannot be undone</label>
            </div>
            <button class="actionBtn" onclick="confirmDeleteData()" style="margin-top:0;background:linear-gradient(135deg,#dc2626,#ef4444);">Delete All My Data</button>
            <button class="secondaryBtn" onclick="closeModal('deleteDataModal')" style="margin-top:10px;">Cancel</button>
        </div>`;
        m.onclick = (e) => { if (e.target === m) closeModal("deleteDataModal"); };
        document.querySelector(".phone").appendChild(m);
    }
    document.getElementById("deleteDataModal").style.display = "flex";
    /* Reset checkbox */
    const cb = document.getElementById("deleteConfirmCheck");
    if (cb) cb.checked = false;
}
 
async function confirmDeleteData() {
    const cb = document.getElementById("deleteConfirmCheck");
    if (!cb || !cb.checked) {
        showQuickToast("Please confirm by checking the box");
        return;
    }
 
    /* 1. Clear all localStorage */
    localStorage.clear();
 
    /* 2. Clear in-memory state */
    chatHistory = []; water = 0; waterLog = []; waterWeekly = {};
    medicines = []; groceryItems = []; lastPeriodDate = null;
    appSettings = {notifyReminders:true,notifyWater:true,notifyMedicine:true,notifyPeriod:true,showDailyQuotes:true,cycleLength:28};
 
    /* 3. Delete server-side data (reminders in PostgreSQL) */
    try {
        await fetch("/delete_my_data", {method:"DELETE"});
    } catch(e) {
        /* Endpoint may not exist yet — local data still cleared */
    }
 
    closeModal("deleteDataModal");
 
    /* 4. Log out and show fresh auth screen */
    try { await fetch("/logout", {method:"POST"}); } catch(e) {}
    currentUser = null;
 
    document.querySelectorAll(".appScreen").forEach(s => { s.classList.remove("active"); s.style.display="none"; });
    document.getElementById("appWrapper").style.display  = "none";
    document.getElementById("authLogo").style.display    = "block";
    document.getElementById("authWrapper").style.display = "block";
    showAuthPanel("loginScreen");
 
    showQuickToast("All data deleted. Starting fresh.");
}
 


/* ─── STATE ─────────────────────────────────────────────── */
let water=0,waterTarget=8,waterLog=[],waterWeekly={},medicines=[],groceryItems=[];
let currentGroceryFilter="all",currentMedFilter="all",selectedTaskType="task",selectedTaskPriority="normal",selectedMedPriority="normal",completedVisible=false,lastPeriodDate=null;
const safe=(id,fn)=>{const el=document.getElementById(id);if(el)fn(el);};

/* ─── NAVIGATION ────────────────────────────────────────── */

const _navStack = ["homeScreen"]; /* tracks navigation history */
 
function navApp(screen, btn) {
    /* Hide all screens */
    document.querySelectorAll(".appScreen").forEach(s => {
        s.classList.remove("active");
        s.style.display = "none";
    });
 
    const target = document.getElementById(screen);
    if (target) {
        target.style.display = "";
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
 
    /* Update nav highlight */
    document.querySelectorAll(".navItem").forEach(b => b.classList.remove("active"));
    if (btn && btn.classList && btn.classList.contains("navItem")) btn.classList.add("active");
 
    /* Push to history stack only if different from current */
    const current = _navStack[_navStack.length - 1];
    if (screen !== current) {
        _navStack.push(screen);
        /* Push to browser history so back button fires popstate */
        window.history.pushState({screen}, "", "");
    }
 
    /* Run loader */
    const loaders = {
        homeScreen:     loadHomeData,
        plannerScreen:  loadPlanner,
        wellnessScreen: loadWellnessScreen,
        medicineScreen: loadMedicines,
        waterScreen:    loadWaterScreen,
        groceryScreen:  loadGrocery,
        periodScreen:   calculatePeriod,
        chatScreen:     () => { /* chat loads lazily */ },
    };
    if (loaders[screen]) loaders[screen]();
}
const nav = navApp;
 
/* Back button handler — goes to previous tab in stack */
function handleBackButton() {
    const appVisible = document.getElementById("appWrapper").style.display !== "none";
    if (!appVisible) return false; /* let auth handle it */
 
    /* Remove current from stack */
    if (_navStack.length > 1) {
        _navStack.pop();
        const prev = _navStack[_navStack.length - 1];
        /* Navigate to previous without pushing to stack again */
        document.querySelectorAll(".appScreen").forEach(s => {
            s.classList.remove("active");
            s.style.display = "none";
        });
        const target = document.getElementById(prev);
        if (target) { target.style.display = ""; target.classList.add("active"); target.scrollTop = 0; }
        /* Sync nav tab highlight */
        const tabMap = {homeScreen:"homeScreen",chatScreen:"chatScreen",plannerScreen:"plannerScreen",wellnessScreen:"wellnessScreen"};
        if (tabMap[prev]) {
            document.querySelectorAll(".navItem").forEach((b,i) => {
                b.classList.toggle("active", ["homeScreen","chatScreen","plannerScreen","wellnessScreen"][i] === prev);
            });
        }
        const loaders = {homeScreen:loadHomeData,plannerScreen:loadPlanner,wellnessScreen:loadWellnessScreen,medicineScreen:loadMedicines,waterScreen:loadWaterScreen,groceryScreen:loadGrocery,periodScreen:calculatePeriod};
        if (loaders[prev]) loaders[prev]();
        return true;
    }
    /* At root (home) — let the browser/OS handle it (exit app) */
    return false;
}
 
/* Updated popstate listener — use in window.onload */
// window.addEventListener("popstate", () => { handleBackButton(); });
 
/* ─── HOME ──────────────────────────────────────────────── */
async function loadHomeData(){
  updateDateTime();renderDailyQuote();renderHomeWaterDrops();renderWaterTip();calculatePeriod();renderPeriodTip();renderHomeMedCard();renderHomeGroceryCard();renderHomeAlerts();
  safe("dailyQuote",el=>{const card=el.closest(".thoughtCard");if(card)card.style.display=appSettings.showDailyQuotes?"block":"none";});
  try{const res=await fetch("/reminders");const data=await res.json();updateSummaryCounts(data.tasks);}catch(e){console.error("[Home]",e);}
}
function updateDateTime(){safe("dateTime",el=>el.innerText=new Date().toLocaleDateString("en-IN",{weekday:"long",day:"numeric",month:"long",year:"numeric"}));}
function updateSummaryCounts(tasks){
  const today=new Date();today.setHours(0,0,0,0);let overdue=0,tod=0,upcoming=0;
  tasks.forEach(t=>{if(t.completed===1)return;if(!t.date){upcoming++;return;}const d=new Date(t.date);d.setHours(0,0,0,0);if(d<today)overdue++;else if(d.getTime()===today.getTime())tod++;else upcoming++;});
  safe("overdueNum",el=>el.innerText=overdue);safe("todayNum",el=>el.innerText=tod);safe("upcomingNum",el=>el.innerText=upcoming);
}
function renderHomeAlerts(){
  const c=document.getElementById("homeAlerts");if(!c)return;c.innerHTML="";
  const lm=medicines.filter(m=>m.stock<=5),om=medicines.filter(m=>m.stock===0);
  if(om.length>0)c.innerHTML+='<div class="alertBanner danger" onclick="navApp(\'medicineScreen\')"><span class="alertBannerIcon">&#128138;</span><span class="alertBannerText"><b>'+om[0].name+'</b>'+(om.length>1?' +'+(om.length-1)+' more':'')+' — out of stock!</span><span class="alertBannerArrow">&#8250;</span></div>';
  else if(lm.length>0)c.innerHTML+='<div class="alertBanner warning" onclick="navApp(\'medicineScreen\')"><span class="alertBannerIcon">&#128138;</span><span class="alertBannerText"><b>'+lm[0].name+'</b> — running low ('+lm[0].stock+' left)</span><span class="alertBannerArrow">&#8250;</span></div>';
  const ug=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked),og=groceryItems.filter(g=>g.deadline&&new Date(g.deadline)<new Date()&&!g.checked);
  if(og.length>0)c.innerHTML+='<div class="alertBanner danger" onclick="navApp(\'groceryScreen\')"><span class="alertBannerIcon">&#128715;</span><span class="alertBannerText"><b>'+og[0].name+'</b> — deadline passed!</span><span class="alertBannerArrow">&#8250;</span></div>';
  else if(ug.length>0)c.innerHTML+='<div class="alertBanner warning" onclick="navApp(\'groceryScreen\')"><span class="alertBannerIcon">&#128715;</span><span class="alertBannerText"><b>'+ug.length+' urgent item'+(ug.length>1?"s":"")+'</b> need restocking</span><span class="alertBannerArrow">&#8250;</span></div>';
  if(c.innerHTML===""&&(medicines.length>0||groceryItems.length>0))c.innerHTML='<div class="alertBanner ok"><span class="alertBannerIcon">&#10003;</span><span class="alertBannerText">Medicines &amp; grocery all stocked up!</span></div>';
}
function renderHomeMedCard(){
  if(medicines.length===0){safe("homeMedSub",el=>{el.innerText="No medicines added yet";el.style.color="#6b21a8";});safe("homeMedMeta",el=>el.innerText="");safe("homeMedBarFill",el=>el.style.width="0%");return;}
  const total=medicines.length,taken=medicines.filter(m=>m.taken).length,low=medicines.filter(m=>m.stock<=5).length,out=medicines.filter(m=>m.stock===0).length;
  safe("homeMedBarFill",el=>el.style.width=Math.round((taken/total)*100)+"%");
  if(out>0)safe("homeMedSub",el=>{el.innerText=out+' medicine'+(out>1?"s":"")+" out of stock";el.style.color="#ff6b8a";});
  else if(low>0)safe("homeMedSub",el=>{el.innerText=low+' medicine'+(low>1?"s":"")+" running low";el.style.color="#ffb347";});
  else safe("homeMedSub",el=>{el.innerText=taken+" of "+total+" taken today";el.style.color="#6b21a8";});
  const nm=medicines.find(m=>!m.taken&&m.time);
  safe("homeMedMeta",el=>{el.innerText=nm?"Next: "+nm.name+" at "+nm.time:total+" medicines tracked";});
}
function renderHomeGroceryCard(){
  if(groceryItems.length===0){safe("homeGrocerySub",el=>{el.innerText="No items added yet";el.style.color="#166534";});safe("homeGroceryMeta",el=>el.innerText="");safe("homeGroceryBarFill",el=>el.style.width="0%");return;}
  const total=groceryItems.length,done=groceryItems.filter(g=>g.checked).length,urgent=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked).length,overdue=groceryItems.filter(g=>g.deadline&&new Date(g.deadline)<new Date()&&!g.checked).length;
  safe("homeGroceryBarFill",el=>el.style.width=Math.round((done/total)*100)+"%");
  if(overdue>0)safe("homeGrocerySub",el=>{el.innerText=overdue+' item'+(overdue>1?"s":"")+" past deadline";el.style.color="#ff6b8a";});
  else if(urgent>0)safe("homeGrocerySub",el=>{el.innerText=urgent+' urgent item'+(urgent>1?"s":"")+" to buy";el.style.color="#ffb347";});
  else safe("homeGrocerySub",el=>{el.innerText=done+" of "+total+" items collected";el.style.color="#166534";});
  safe("homeGroceryMeta",el=>{el.innerText=urgent>0?(total-done)+" remaining · "+urgent+" urgent":(total-done)+" remaining";});
}

/* ─── CHAT ──────────────────────────────────────────────── */
const OPENROUTER_KEY="";
const OPENROUTER_URL="https://openrouter.ai/api/v1/chat/completions";
const CHAT_MODELS=["z-ai/glm-4.5-air:free","openai/gpt-oss-20b:free","google/gemma-4-31b-it:free","openai/gpt-oss-120b:free"];

/* Replace: let chatHistory=[]; */
let chatHistory = [];
let isPrivateMode = false;
 
/* Call this once in enterApp() after loading settings */
function loadChatHistory() {
    try {
        const saved = localStorage.getItem("ahiraChatHistory");
        if (saved) {
            chatHistory = JSON.parse(saved);
            /* Re-render saved messages into chat UI */
            restoreChatUI();
        }
    } catch(e) {
        chatHistory = [];
    }
}
 
function saveChatHistory() {
    if (isPrivateMode) return; /* never save private mode messages */
    try {
        /* Keep last 50 messages to avoid localStorage bloat */
        const toSave = chatHistory.slice(-50);
        localStorage.setItem("ahiraChatHistory", JSON.stringify(toSave));
    } catch(e) {}
}
 
function restoreChatUI() {
    const chatEl = document.getElementById("chatMessages");
    if (!chatEl || chatHistory.length === 0) return;
 
    /* Remove the suggestion chips temporarily */
    const chips = chatEl.querySelector(".chatSuggestions");
 
    /* Add messages back */
    chatHistory.forEach(msg => {
        if (msg.role === "user") {
            appendUserBubble(chatEl, msg.content);
        } else if (msg.role === "assistant") {
            const w = document.createElement("div");
            w.className = "msgRow msgRow--bot";
            w.innerHTML = '<div class="chatAvatarSmall">A</div><div class="bubble bubble--bot"></div>';
            const bubble = w.querySelector(".bubble--bot");
            renderBotText(bubble, msg.content);
            chatEl.appendChild(w);
        }
    });
 
    /* Re-append chips at end if they existed */
    if (chips) chatEl.appendChild(chips);
    chatEl.scrollTop = chatEl.scrollHeight;
}
 
function clearChatHistory() {
    chatHistory = [];
    localStorage.removeItem("ahiraChatHistory");
    const chatEl = document.getElementById("chatMessages");
    if (chatEl) {
        chatEl.innerHTML = `
            <div class="chatDateDivider">Today</div>
            <div class="msgRow msgRow--bot">
                <div class="chatAvatarSmall">A</div>
                <div class="bubble bubble--bot" id="chatWelcomeMsg">Hi! I'm Ahira How can I help you today?</div>
            </div>
            <div class="chatSuggestions">
                <button class="suggBtn" onclick="quickChat('What should I cook today?')">Meal ideas</button>
                <button class="suggBtn" onclick="quickChat('Plan my day')">Plan my day</button>
                <button class="suggBtn" onclick="quickChat('I feel stressed')">I feel stressed</button>
            </div>`;
    }
    showQuickToast("Chat cleared");
}
 
/* Updated sendMessage — persists history, respects private mode */
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
 
    const tw = createTypingIndicator();
    chatEl.appendChild(tw);
    chatEl.scrollTop = chatEl.scrollHeight;
    const bme = tw.querySelector(".bubble--bot");
 
    const msgs = [{role:"system",content:buildSystemPrompt()}, ...chatHistory, {role:"user",content:message}];
    let reply = null;
 
    const tryModel = (model) => fetch(OPENROUTER_URL, {
        method: "POST",
        headers: {
            "Authorization":      "Bearer " + OPENROUTER_KEY,
            "HTTP-Referer":       "https://ahira.app",
            "X-Title": "Ahira",
            "X-OpenRouter-Title": "Ahira",
            "Content-Type":       "application/json"
        },
        body: JSON.stringify({model, messages:msgs, max_tokens:350, temperature:0.80}),
        signal: AbortSignal.timeout(12000)
    }).then(async r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        const d = await r.json();
        const c = d?.choices?.[0]?.message?.content;
        if (!c) throw new Error("empty");
        return c;
    });
 
    for (const model of CHAT_MODELS) {
        try { reply = await tryModel(model); if (reply) break; } catch(e) { continue; }
    }
 
    if (!reply) {
        if (bme) {
            bme.classList.remove("typing");
            bme.innerHTML = "<b>Connection issue</b><br><span style='font-size:12px;opacity:0.75;'>Check your internet and try again.</span>";
        }
        chatEl.scrollTop = chatEl.scrollHeight;
        return;
    }
 
    const {reply:cr, reminder} = parseReminderTag(reply);
    if (bme) { bme.classList.remove("typing"); renderBotText(bme, cr); }
 
    /* Only push & save if NOT in private mode */
    if (!isPrivateMode) {
        chatHistory.push({role:"user", content:message});
        chatHistory.push({role:"assistant", content:cr});
        if (chatHistory.length > 60) chatHistory = chatHistory.slice(-60);
        saveChatHistory();
    }
 
    if (reminder) { await saveReminderToBackend(reminder); showReminderToast(reminder); }
    chatEl.scrollTop = chatEl.scrollHeight;
}
 
/* Private mode toggle — call from chat header button */
function togglePrivateMode() {
    isPrivateMode = !isPrivateMode;
    const btn = document.getElementById("privateModeBtn");
    if (btn) {
        btn.style.background = isPrivateMode ? "rgba(248,113,113,0.15)" : "rgba(108,63,206,0.1)";
        btn.title = isPrivateMode ? "Private mode ON — messages not saved" : "Private mode OFF";
        btn.innerText = isPrivateMode ? "🔴" : "🔒";
    }
    showQuickToast(isPrivateMode ? "Private mode ON — chat won't be saved" : "Private mode OFF — chat saving resumed");
}
function parseReminderTag(text){const match=text.match(/\[REMINDER:\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{2}:\d{2})\s*\]/i);if(!match)return{reply:text.trim(),reminder:null};const today=new Date().toISOString().slice(0,10),tomorrow=new Date(Date.now()+864e5).toISOString().slice(0,10);let date=match[2].trim();if(/tomorrow/i.test(date))date=tomorrow;else if(!/\d{4}-\d{2}-\d{2}/.test(date))date=today;return{reply:text.slice(0,match.index).trim(),reminder:{task:match[1].trim(),date,time:match[3].trim()}};}
async function saveReminderToBackend(r){try{await fetch("/add_reminder",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task:r.task,date:r.date,time:r.time,priority:"normal"})});}catch(e){}}
function appendUserBubble(ce,msg){const w=document.createElement("div");w.className="msgRow msgRow--user";w.innerHTML='<div class="bubble bubble--user">'+escapeHtml(msg)+'</div>';w.style.animation="bubbleIn 0.25s ease forwards";ce.appendChild(w);}
function createTypingIndicator(){const w=document.createElement("div");w.className="msgRow msgRow--bot";w.innerHTML='<div class="chatAvatarSmall">A</div><div class="bubble bubble--bot typing"><span class="typingDot"></span><span class="typingDot"></span><span class="typingDot"></span></div>';return w;}
function renderBotText(el,text){el.innerHTML=escapeHtml(text).replace(/\n/g,"<br>");}
function escapeHtml(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function showReminderToast(r){
  document.getElementById("reminderToast")?.remove();
  const t=document.createElement("div");t.id="reminderToast";t.className="reminderToast";
  t.innerHTML='<span style="font-size:20px;">&#10003;</span><div><div style="font-weight:700;font-size:13px;color:#4c1d95;">Reminder saved!</div><div style="font-size:12px;color:#6b21a8;margin-top:2px;">'+escapeHtml(r.task)+(r.date?" · "+r.date:"")+(r.time?" at "+r.time:"")+'</div></div>';
  document.querySelector(".phone").appendChild(t);
  requestAnimationFrame(()=>t.classList.add("toastVisible"));
  setTimeout(()=>{t.classList.remove("toastVisible");setTimeout(()=>t.remove(),400);},3500);
}
function quickChat(msg){document.getElementById("message").value=msg;sendMessage();}

/* ─── PLANNER ───────────────────────────────────────────── */
function getTaskEmoji(t,type){const tx=(t||"").toLowerCase();if(type==="event")return"🎉";if(tx.includes("exam")||tx.includes("test"))return"📚";if(tx.includes("doctor")||tx.includes("appointment"))return"🏥";if(tx.includes("gym")||tx.includes("exercise")||tx.includes("yoga"))return"🏃";if(tx.includes("birthday"))return"🎂";if(tx.includes("grocery")||tx.includes("shop"))return"🛒";if(tx.includes("meeting")||tx.includes("call"))return"📞";if(tx.includes("medicine")||tx.includes("pill"))return"💊";if(tx.includes("travel")||tx.includes("trip")||tx.includes("flight"))return"✈️";if(tx.includes("dinner")||tx.includes("lunch")||tx.includes("eat"))return"🍽️";if(type==="reminder")return"🔔";return"📋";}
let calendarTasks=[],selectedCalDate=null;
async function buildCalStrip(){
  const strip=document.getElementById("calStrip");if(!strip)return;strip.innerHTML="";const today=new Date();
  try{const res=await fetch("/reminders");const data=await res.json();calendarTasks=data.tasks||[];}catch(e){calendarTasks=[];}
  const lm=JSON.parse(localStorage.getItem("taskMeta")||"{}");
  for(let i=-2;i<=11;i++){
    const d=new Date(today);d.setDate(today.getDate()+i);const ds=d.toISOString().slice(0,10),isT=i===0,isS=ds===selectedCalDate;
    const dt=calendarTasks.filter(t=>t.date===ds&&t.completed!==1),ee=dt.slice(0,2).map(t=>{const m=lm[t.task+"__"+t.date]||{};return getTaskEmoji(t.task,m.type);});
    const cell=document.createElement("div");cell.className="calCell"+(isT?" calToday":"")+(isS?" calSelected":"");cell.dataset.date=ds;cell.onclick=()=>selectCalDay(ds);
    cell.innerHTML='<div class="calDay">'+d.toLocaleDateString("en-IN",{weekday:"short"}).slice(0,3)+'</div><div class="calNum">'+d.getDate()+'</div><div class="calEvents">'+ee.map(e=>'<span class="calEventDot">'+e+'</span>').join("")+(dt.length>2?'<span class="calMore">+'+(dt.length-2)+'</span>':"")+'</div>';
    strip.appendChild(cell);
  }
  safe("plannerDateLabel",el=>el.innerText=today.toLocaleDateString("en-IN",{weekday:"long",month:"long",day:"numeric"}));
}
function selectCalDay(ds){selectedCalDate=ds;document.querySelectorAll(".calCell").forEach(c=>c.classList.toggle("calSelected",c.dataset.date===ds));renderDayDetail(ds);}
function renderDayDetail(ds){
  const panel=document.getElementById("dayDetailPanel");if(!panel)return;
  const lm=JSON.parse(localStorage.getItem("taskMeta")||"{}"),tasks=calendarTasks.filter(t=>t.date===ds);
  const d=new Date(ds+"T00:00:00"),label=d.toLocaleDateString("en-IN",{weekday:"long",day:"numeric",month:"long"});
  if(tasks.length===0){panel.innerHTML='<div class="dayDetailHeader">'+label+'</div><div class="dayDetailEmpty">No tasks this day<br><button class="addPillBtn" style="margin-top:10px;font-size:12px;padding:7px 16px;" onclick="openAddTaskForDate(\''+ds+'\')">+ Add Task</button></div>';}
  else{panel.innerHTML='<div class="dayDetailHeader">'+label+'</div>'+tasks.map(t=>{const m=lm[t.task+"__"+t.date]||{},em=getTaskEmoji(t.task,m.type),done=t.completed===1;return'<div class="dayDetailTask '+(done?"dayDetailDone":"")+'"><span class="dayDetailEmoji">'+em+'</span><div class="dayDetailInfo"><div class="dayDetailName">'+escapeHtml(t.task)+'</div>'+(t.time?'<div class="dayDetailTime">'+t.time+'</div>':"")+'</div><div style="display:flex;gap:4px;margin-left:auto;"><button class="iconBtn '+(done?"btnDone":"btnPrimary")+'" onclick="toggleTask('+t.id+')">&#10003;</button><button class="iconBtn btnDanger" onclick="deleteTask('+t.id+')">&#128465;</button></div></div>';}).join("")+'<button class="addPillBtn" style="width:100%;margin-top:10px;font-size:12px;padding:7px;" onclick="openAddTaskForDate(\''+ds+'\')">+ Add for this day</button>';}
  panel.style.display="block";
}
function openAddTaskForDate(ds){openAddTask();setTimeout(()=>{const di=document.getElementById("dateInput");if(di)di.value=ds;},50);}
function initChips(cid,sk){const c=document.getElementById(cid);if(!c)return;c.querySelectorAll(".typeChip").forEach(chip=>{chip.addEventListener("click",()=>{c.querySelectorAll(".typeChip").forEach(x=>x.classList.remove("active"));chip.classList.add("active");if(sk==="task")selectedTaskType=chip.dataset.val;if(sk==="priority")selectedTaskPriority=chip.dataset.val;if(sk==="medpri")selectedMedPriority=chip.dataset.val;});});}
function openAddTask(){document.getElementById("addTaskModal").style.display="flex";selectedTaskType="task";selectedTaskPriority="normal";document.querySelectorAll("#taskTypeChips .typeChip").forEach((c,i)=>c.classList.toggle("active",i===0));document.querySelectorAll("#taskPriorityChips .typeChip").forEach((c,i)=>c.classList.toggle("active",i===0));}
function closeAddTask(e){if(!e||e.target.classList.contains("modalOverlay"))document.getElementById("addTaskModal").style.display="none";}
async function saveTask(){
  const task=document.getElementById("taskInput").value.trim(),date=document.getElementById("dateInput").value,time=document.getElementById("timeInput").value,pinned=document.getElementById("pinTask").checked;
  if(!task){alert("Please enter a task name.");return;}
  const lm=JSON.parse(localStorage.getItem("taskMeta")||"{}");
  try{const res=await fetch("/add_reminder",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task,date,time,priority:selectedTaskPriority})});const data=await res.json();
  if(data.status==="success"){lm[task+"__"+date]={type:selectedTaskType,pinned};localStorage.setItem("taskMeta",JSON.stringify(lm));document.getElementById("taskInput").value="";document.getElementById("dateInput").value="";document.getElementById("timeInput").value="";document.getElementById("pinTask").checked=false;closeAddTask();await loadPlanner();if(date&&selectedCalDate===date)renderDayDetail(date);}
  else alert(data.message||"Could not save. Please log in.");}catch(e){alert("Network error.");}
}
async function loadPlanner(){
  await buildCalStrip();initChips("taskTypeChips","task");initChips("taskPriorityChips","priority");
  const tl=document.getElementById("todayTaskList"),ul=document.getElementById("upcomingTaskList"),cl=document.getElementById("completedTaskList"),pl=document.getElementById("pinnedList"),ps=document.getElementById("pinnedSection");
  if(!tl)return;tl.innerHTML=ul.innerHTML=cl.innerHTML="";if(pl)pl.innerHTML="";
  const panel=document.getElementById("dayDetailPanel");if(panel)panel.style.display="none";selectedCalDate=null;
  try{
    const res=await fetch("/reminders");const data=await res.json();
    const lm=JSON.parse(localStorage.getItem("taskMeta")||"{}"),now=new Date();now.setHours(0,0,0,0);let hp=false;
    (data.tasks||[]).forEach(task=>{const m=lm[task.task+"__"+task.date]||{},card=buildPlannerCard(task,m);if(m.pinned&&!task.completed){pl.innerHTML+=card;hp=true;}if(task.completed){cl.innerHTML+=card;return;}if(!task.date){ul.innerHTML+=card;return;}const d=new Date(task.date);d.setHours(0,0,0,0);if(d<=now)tl.innerHTML+=card;else ul.innerHTML+=card;});
    if(!tl.innerHTML)tl.innerHTML=emptyMsg("All clear for today");if(!ul.innerHTML)ul.innerHTML=emptyMsg("Nothing scheduled ahead");if(ps)ps.style.display=hp?"block":"none";updateSummaryCounts(data.tasks||[]);
  }catch(e){console.error("[Planner]",e);}
}
function buildPlannerCard(task,meta){
  const done=task.completed===1,ti={task:"📋",event:"🎉",reminder:"🔔"}[meta.type||"task"],hp=task.priority==="high";
  let dc="";if(!done&&task.date){const today=new Date();today.setHours(0,0,0,0);const d=new Date(task.date);d.setHours(0,0,0,0);dc=d<today?"#F87171":d.getTime()===today.getTime()?"#FBBF24":"#A5B4FC";}
  const dot=dc?'<span style="width:7px;height:7px;border-radius:50%;background:'+dc+';flex-shrink:0;"></span>':"";
  let dl="";if(task.date){const d=new Date(task.date+"T00:00:00");dl=d.toLocaleDateString("en-IN",{day:"numeric",month:"short"});}
  return '<div class="plannerCard '+(done?"taskDone":"")+'" style="'+(hp?"border-left:3px solid #F87171;":"")+'"><div class="plannerCardLeft"><div class="plannerTypeIcon">'+ti+'</div><div style="flex:1;min-width:0;"><div class="taskText" style="display:flex;align-items:center;gap:6px;">'+dot+'<span style="'+(done?"text-decoration:line-through;opacity:0.55;":"")+'">'+escapeHtml(task.task)+'</span>'+(hp?'<span style="color:#F87171;font-size:10px;">High</span>':"")+'</div><div class="taskMeta">'+(dl?"📅 "+dl:"")+(task.time?" ⏰ "+task.time:"")+((!dl&&!task.time)?"No date set":"")+'</div></div></div><div style="display:flex;gap:5px;flex-shrink:0;"><button class="iconBtn '+(done?"btnDone":"btnPrimary")+'" onclick="toggleTask('+task.id+')">&#10003;</button><button class="iconBtn btnDanger" onclick="deleteTask('+task.id+')">&#128465;</button></div></div>';
}
function emptyMsg(txt){return'<p style="color:var(--t3);font-size:13px;padding:16px 0;text-align:center;">'+txt+'</p>';}
function toggleCompleted(){completedVisible=!completedVisible;const l=document.getElementById("completedTaskList"),a=document.getElementById("completedToggleArrow");if(l)l.style.display=completedVisible?"block":"none";if(a)a.innerText=completedVisible?"∨":"›";}
async function deleteTask(id){await fetch("/reminder/"+id,{method:"DELETE"});loadPlanner();}
async function toggleTask(id){await fetch("/reminder/"+id+"/toggle",{method:"POST"});loadPlanner();}

/* ─── WATER ─────────────────────────────────────────────── */
function renderHomeWaterDrops(){
  const c=document.getElementById("homeWaterDrops");if(!c)return;c.innerHTML="";
  for(let i=0;i<waterTarget;i++){const s=document.createElement("span");s.className="waterDrop "+(i<water?"filled":"empty");s.innerText="💧";c.appendChild(s);}
  safe("homeWaterCount",el=>el.innerText=water);safe("homeWaterTarget",el=>el.innerText=waterTarget);
  safe("wellWaterSub",el=>el.innerText=water+" / "+waterTarget+" glasses today");
  localStorage.setItem("water",water);
}
function loadWaterScreen(){
  renderWaterRing();renderWaterGlassGrid();renderWaterLog();renderWaterChart();
  renderRotatingWaterTips();
  safe("waterTargetLabel",el=>el.innerText=waterTarget);
  safe("waterMlLabel",el=>el.innerText=(water*250)+" ml");
}

/* ROTATING HYDRATION TIPS — new every app restart */
function renderRotatingWaterTips(){
  const c=document.getElementById("hydrationTipsList");
  if(!c)return;
  const tips=AhiraContent.randomWaterTips(4);
  const emojis=["💧","🌿","🍋","⏰"];
  c.innerHTML=tips.map((tip,i)=>'<div class="tipItem">'+emojis[i]+" "+tip+"</div>").join("");
}

function renderWaterRing(){
  safe("detailWaterCount",el=>el.innerText=water);
  const c=document.getElementById("waterRingCircle");if(!c)return;
  c.style.strokeDashoffset=314-Math.min(water/waterTarget,1)*314;
}
function renderWaterGlassGrid(){
  const c=document.getElementById("detailWaterGlasses");if(!c)return;c.innerHTML="";
  for(let i=0;i<waterTarget;i++){const d=document.createElement("div");d.className="glassItem";d.innerHTML='<div class="glassTube '+(i<water?"active":"")+'"><div class="glassFill"></div></div><span class="glassNum">'+(i+1)+'</span>';c.appendChild(d);}
}
function renderWaterLog(){
  const c=document.getElementById("waterLog");if(!c)return;
  if(waterLog.length===0){c.innerHTML=emptyMsg("No glasses logged yet today");return;}
  c.innerHTML=waterLog.slice().reverse().map(e=>'<div class="waterLogEntry"><span class="waterLogTime">'+e.time+'</span><span class="waterLogGlass">💧 Glass '+e.glass+'</span><span style="font-size:12px;color:var(--text-light);">+250ml</span></div>').join("");
}
function renderWaterChart(){
  const be=document.getElementById("waterBarChart"),le=document.getElementById("waterBarLabels");if(!be||!le)return;be.innerHTML="";le.innerHTML="";
  const days=[];for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);days.push(d);}
  const mv=Math.max(waterTarget,...days.map(d=>waterWeekly[d.toISOString().slice(0,10)]||0)),tk=new Date().toISOString().slice(0,10);
  days.forEach(d=>{const key=d.toISOString().slice(0,10),val=key===tk?water:(waterWeekly[key]||0),pct=mv>0?Math.round((val/mv)*100):0;const bar=document.createElement("div");bar.className="waterBar";bar.innerHTML='<div class="waterBarFill '+(key===tk?"barToday":"")+'" style="height:'+Math.max(pct,4)+'%;"><span class="barVal">'+val+'</span></div>';be.appendChild(bar);const lbl=document.createElement("div");lbl.className="barLabel";lbl.innerText=d.toLocaleDateString("en-IN",{weekday:"short"}).slice(0,3);le.appendChild(lbl);});
}
function addWater(){
  if(water>=waterTarget)return;water++;
  const now=new Date();waterLog.push({time:now.toLocaleTimeString("en-IN",{hour:"2-digit",minute:"2-digit"}),glass:water});
  localStorage.setItem("water",water);localStorage.setItem("waterLog",JSON.stringify(waterLog));
  waterWeekly[now.toISOString().slice(0,10)]=water;localStorage.setItem("waterWeekly",JSON.stringify(waterWeekly));
  renderHomeWaterDrops();loadWaterScreen();
}
function removeWater(){if(water<=0)return;water--;waterLog.pop();localStorage.setItem("water",water);localStorage.setItem("waterLog",JSON.stringify(waterLog));renderHomeWaterDrops();loadWaterScreen();}
function resetWater(){water=0;waterLog=[];localStorage.setItem("water",0);localStorage.setItem("waterLog","[]");renderHomeWaterDrops();loadWaterScreen();}
function openWaterTarget(){document.getElementById("waterTargetModal").style.display="flex";}
function closeWaterTarget(e){if(!e||e.target.classList.contains("modalOverlay"))document.getElementById("waterTargetModal").style.display="none";}
function saveWaterTarget(){const v=parseInt(document.getElementById("waterTargetInput").value);if(v>0&&v<=20){waterTarget=v;localStorage.setItem("waterTarget",v);appSettings.waterTarget=v;saveSettings();}closeWaterTarget();loadWaterScreen();renderHomeWaterDrops();safe("drawerWaterGoal",el=>el.innerText=waterTarget+" glasses per day");}
function renderWaterTip(){const el=document.getElementById("homeWaterTip");if(!el)return;el.innerText="💡 "+AhiraContent.sessionWater();el.style.display="block";}

/* ─── PERIOD ────────────────────────────────────────────── */
function setPeriodDate(){
  let picker=document.getElementById("_periodDatePicker");
  if(!picker){picker=document.createElement("input");picker.type="date";picker.id="_periodDatePicker";picker.style.cssText="position:fixed;opacity:0;pointer-events:none;top:50%;left:50%;";picker.max=new Date().toISOString().slice(0,10);document.body.appendChild(picker);
  picker.addEventListener("change",()=>{const val=picker.value;if(!val)return;lastPeriodDate=new Date(val+"T00:00:00");localStorage.setItem("lastPeriodDate",val);calculatePeriod();showQuickToast("Period date saved!");});}
  picker.showPicker?picker.showPicker():picker.click();
}

function calculatePeriod(){
  if(!lastPeriodDate){
    safe("periodBigLabel",el=>el.innerText="Tap 'Update Date' to begin tracking");
    safe("periodDateLabel",el=>el.innerText="No period date set yet");
    safe("wellPeriodSub",el=>el.innerText="Tap to set your last period date");
    ["periodDays","periodDaysDetail","periodDaysBig"].forEach(id=>safe(id,el=>el.innerText="--"));
    renderCycleInsights(null);return;
  }
  const today=new Date();today.setHours(0,0,0,0);const start=new Date(lastPeriodDate);start.setHours(0,0,0,0);
  const daysSince=Math.floor((today-start)/(1000*60*60*24)),cycle=appSettings.cycleLength||28;
  const dayInCycle=daysSince%cycle,remaining=cycle-dayInCycle,progress=(dayInCycle/cycle)*100;
  let phase="",pe="";
  if(dayInCycle<=5){phase="Menstrual Phase";pe="🌸";}
  else if(dayInCycle<=13){phase="Follicular Phase";pe="🌱";}
  else if(dayInCycle<=16){phase="Ovulation Phase";pe="⭐";}
  else{phase="Luteal Phase";pe="🌙";}
  const nextDate=new Date(start);nextDate.setDate(start.getDate()+daysSince+remaining);
  const nextDateStr=nextDate.toLocaleDateString("en-IN",{day:"numeric",month:"long",year:"numeric"});
  ["periodDays","periodDaysDetail","periodDaysBig"].forEach(id=>safe(id,el=>el.innerText=remaining));
  ["periodFill","periodFillWell","periodFillDetail"].forEach(id=>safe(id,el=>el.style.width=progress+"%"));
  safe("periodBigLabel",el=>el.innerText="Next Period in "+remaining+" Day"+(remaining!==1?"s":""));
  safe("periodDateLabel",el=>el.innerText="📅 Expected: "+nextDateStr);
  safe("wellPeriodSub",el=>el.innerText="Next in "+remaining+" days · "+pe+" "+phase);
  safe("currentPhaseLabel",el=>el.innerText=pe+" "+phase);
  safe("dayInCycleLabel",el=>el.innerText="Day "+(dayInCycle+1)+" of "+cycle);
  const dc=document.getElementById("homePeriodDots");
  if(dc){dc.innerHTML="";const filled=Math.floor((dayInCycle/cycle)*8);for(let i=0;i<8;i++){const dot=document.createElement("span");dot.className="dot"+(i<filled?" filled":"")+(i===filled?" today":"");dc.appendChild(dot);}}
  renderCycleInsights(phase);
}

/* ROTATING CYCLE INSIGHTS — new every app restart */
function renderCycleInsights(phase){
  const c=document.getElementById("cycleInsightsList");
  if(!c)return;
  const insights=AhiraContent.randomCycleInsights(3);
  c.innerHTML=insights.map(ins=>'<div class="insightItem"><span class="insightDot" style="background:var(--a1);"></span>'+ins.icon+" "+ins.text+'</div>').join("");
}

function renderPeriodTip(){const el=document.getElementById("periodTipText");if(!el)return;el.innerText=AhiraContent.sessionPeriod();}

/* ─── MEDICINE ──────────────────────────────────────────── */
function toggleMedicineForm(){const f=document.getElementById("medicineForm");if(!f)return;const o=f.style.display!=="none";f.style.display=o?"none":"block";if(!o){selectedMedPriority="normal";initChips("medPriorityChips","medpri");}}
function filterMeds(type,btn){currentMedFilter=type;document.querySelectorAll(".filterTab").forEach(b=>b.classList.remove("active"));if(btn)btn.classList.add("active");loadMedicines();}
function addMedicine(){
  const name=document.getElementById("medName").value.trim(),dose=parseInt(document.getElementById("medDose").value)||0,stock=parseInt(document.getElementById("medStock").value)||0,time=document.getElementById("medTime").value,frequency=document.getElementById("medFrequency").value,notes=document.getElementById("medNotes").value.trim();
  if(!name||!stock){alert("Please enter medicine name and stock.");return;}
  const emojis=["💊","🩺","🧴","🍊","🧪","💉"];
  medicines.push({name,dose,stock,originalStock:stock,time,frequency,notes,priority:selectedMedPriority,emoji:emojis[Math.floor(Math.random()*emojis.length)],taken:false,addedDate:new Date().toISOString().slice(0,10)});
  localStorage.setItem("medicines",JSON.stringify(medicines));
  ["medName","medDose","medStock","medTime","medNotes"].forEach(id=>safe(id,el=>el.value=""));
  toggleMedicineForm();loadMedicines();
}
function loadMedicines(){
  const c=document.getElementById("medicineList");if(!c)return;c.innerHTML="";
  const filtered=medicines.filter(m=>currentMedFilter==="all"||m.frequency===currentMedFilter);
  const s={critical:filtered.filter(m=>m.priority==="high"),daily:filtered.filter(m=>m.priority!=="high"&&m.frequency!=="weekly"),weekly:filtered.filter(m=>m.frequency==="weekly")};
  let html="";if(s.critical.length){html+='<div class="sectionLabel" style="color:#ff6b8a;">Critical</div>';s.critical.forEach(m=>html+=buildMedCard(m,medicines.indexOf(m)));}
  if(s.daily.length){html+='<div class="sectionLabel">Daily</div>';s.daily.forEach(m=>html+=buildMedCard(m,medicines.indexOf(m)));}
  if(s.weekly.length){html+='<div class="sectionLabel">Weekly</div>';s.weekly.forEach(m=>html+=buildMedCard(m,medicines.indexOf(m)));}
  if(!html)html=emptyMsg("No medicines added yet");c.innerHTML=html;
  const low=medicines.filter(m=>m.stock<=5).length,taken=medicines.filter(m=>m.taken).length;
  safe("medTotalCount",el=>el.innerText=medicines.length);safe("medLowCount",el=>el.innerText=low);safe("medTakenCount",el=>el.innerText=taken);
  safe("wellMedSub",el=>{if(medicines.length===0){el.innerText="No medicines tracked";return;}el.innerText=medicines.length+" tracked"+(low>0?" · "+low+" low":" · All OK");});
  renderHomeMedCard();renderHomeAlerts();
}
function buildMedCard(med,i){
  const sp=med.originalStock>0?Math.round((med.stock/med.originalStock)*100):0,sc=med.stock<=5?"#ff6b8a":med.stock<=10?"#ffb347":"var(--purple)";
  return '<div class="medCard" style="'+(med.priority==="high"?"border-left:3px solid #ff6b8a;":"")+'"><div class="medIconBox">'+(med.emoji||"💊")+'</div><div class="medInfo" style="flex:1;"><div class="medName">'+med.name+(med.priority==="high"?' <span style="font-size:11px;color:#ff6b8a;">CRITICAL</span>':"")+'</div><div class="medMeta">'+(med.dose?med.dose+"mg · ":"")+(med.frequency||"daily")+(med.time?" · ⏰ "+med.time:"")+'</div>'+(med.notes?'<div class="medNoteText">'+med.notes+'</div>':"")+'<div class="medStockBar"><div class="medStockFill" style="width:'+sp+'%;background:'+sc+';"></div></div><div style="font-size:11px;color:'+sc+';margin-top:2px;">'+med.stock+' left</div></div><div style="display:flex;flex-direction:column;gap:5px;align-items:flex-end;"><div class="medCheck '+(med.taken?"checked":"")+'" onclick="toggleMedTaken('+i+')">'+(med.taken?"✓":"")+'</div><button class="iconBtn btnDanger" style="font-size:11px;padding:3px 7px;" onclick="deleteMedicine('+i+')">&#128465;</button></div></div>';
}
function toggleMedTaken(i){if(!medicines[i].taken&&medicines[i].stock>0)medicines[i].stock=Math.max(0,medicines[i].stock-1);medicines[i].taken=!medicines[i].taken;localStorage.setItem("medicines",JSON.stringify(medicines));loadMedicines();}
function deleteMedicine(i){medicines.splice(i,1);localStorage.setItem("medicines",JSON.stringify(medicines));loadMedicines();}

/* ─── GROCERY ───────────────────────────────────────────── */
const catEmoji={veggies:"🥕",dairy:"🥛",snacks:"🍪",other:"📦",all:"🛒"};
function openGroceryForm(){document.getElementById("groceryFormModal").style.display="flex";}
function closeGroceryForm(e){if(!e||e.target.classList.contains("modalOverlay"))document.getElementById("groceryFormModal").style.display="none";}
function addGroceryItem(){
  const name=document.getElementById("groceryName").value.trim(),qty=parseInt(document.getElementById("groceryQty").value)||1,unit=document.getElementById("groceryUnit").value,category=document.getElementById("groceryCat").value,urgency=document.getElementById("groceryUrgency").value,deadline=document.getElementById("groceryDeadline").value,notes=document.getElementById("groceryNotes").value.trim();
  if(!name){alert("Please enter item name.");return;}
  groceryItems.push({name,qty,unit,category,urgency,deadline,notes,checked:false,emoji:catEmoji[category]||"🛒",addedDate:new Date().toISOString().slice(0,10)});
  localStorage.setItem("groceryItems",JSON.stringify(groceryItems));
  ["groceryName","groceryQty","groceryDeadline","groceryNotes"].forEach(id=>safe(id,el=>el.value=""));
  closeGroceryForm();loadGrocery();
}
function loadGrocery(){
  const ue=document.getElementById("urgentGroceryList"),fe=document.getElementById("groceryFullList");if(!ue||!fe)return;ue.innerHTML="";fe.innerHTML="";
  const filtered=groceryItems.filter(item=>currentGroceryFilter==="all"||item.category===currentGroceryFilter);
  filtered.forEach(item=>{const i=groceryItems.indexOf(item),card=buildGroceryCard(item,i);if(item.urgency==="urgent"&&!item.checked)ue.innerHTML+=card;else fe.innerHTML+=card;});
  if(!ue.innerHTML)ue.innerHTML=emptyMsg("No urgent items");if(!fe.innerHTML)fe.innerHTML=emptyMsg("No items yet. Tap + Add to start.");
  safe("groceryTotalCount",el=>el.innerText=groceryItems.length);safe("groceryUrgentCount",el=>el.innerText=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked).length);safe("groceryDoneCount",el=>el.innerText=groceryItems.filter(g=>g.checked).length);
  safe("wellGrocerySub",el=>{const urg=groceryItems.filter(g=>g.urgency==="urgent"&&!g.checked).length;el.innerText=urg>0?urg+" urgent item"+(urg>1?"s":""):groceryItems.length+" items tracked";});
  renderHomeGroceryCard();renderHomeAlerts();
}
function buildGroceryCard(item,i){
  const io=item.deadline&&new Date(item.deadline)<new Date(),ds=item.deadline?'<span style="color:'+(io?"#ff6b8a":"var(--text-light)")+';">📅 '+item.deadline+'</span>':"",ub=item.urgency==="urgent"?'<span class="urgencyBadge urgent">Urgent</span>':item.urgency==="low"?'<span class="urgencyBadge low">Low</span>':"";
  return '<div class="groceryItemCard '+(item.checked?"groceryDone":"")+'"><div class="groceryCheck '+(item.checked?"checked":"")+'" onclick="toggleGrocery('+i+')">'+(item.checked?"✓":"")+'</div><div style="flex:1;"><div class="groceryName '+(item.checked?"strikethrough":"")+'">'+item.emoji+" "+item.name+" "+ub+'</div><div class="groceryMeta">'+item.qty+" "+(item.unit||"pcs")+" "+ds+(item.notes?" · "+item.notes:"")+'</div></div><button class="iconBtn btnDanger" style="font-size:11px;padding:3px 7px;" onclick="deleteGrocery('+i+')">&#128465;</button></div>';
}
function toggleGrocery(i){groceryItems[i].checked=!groceryItems[i].checked;localStorage.setItem("groceryItems",JSON.stringify(groceryItems));loadGrocery();}
function deleteGrocery(i){groceryItems.splice(i,1);localStorage.setItem("groceryItems",JSON.stringify(groceryItems));loadGrocery();}
function filterGrocery(type,btn){currentGroceryFilter=type;document.querySelectorAll(".filterTab").forEach(b=>b.classList.remove("active"));if(btn)btn.classList.add("active");loadGrocery();}

/* ─── WELLNESS ──────────────────────────────────────────── */
function loadWellnessScreen(){calculatePeriod();renderHomeWaterDrops();loadMedicines();loadGrocery();}

/* ─── MOOD ──────────────────────────────────────────────── */
function selectMood(btn,mood,emoji){
  document.querySelectorAll(".moodBtn").forEach(b=>b.classList.remove("selected"));btn.classList.add("selected");
  const ar={
    happy:[{text:emoji+" You're absolutely glowing today! That energy is contagious.\n\nKeep doing whatever made you feel this way.",tip:"Write down 3 things that made you happy today — it reinforces the good feelings."}],
    calm:[{text:emoji+" What a peaceful state to be in.\n\nCalmness is a superpower. Use this energy to focus, create, or just breathe.",tip:"Try a 5-minute mindful breathing session to deepen this calm."}],
    tired:[{text:emoji+" You deserve rest — no guilt about that.\n\nDrink some water, take a short nap, and don't push yourself today.",tip:"A 20-minute power nap restores alertness. Avoid screens before sleeping."}],
    sad:[{text:emoji+" It's okay to feel sad. You don't have to be okay all the time.\n\nAhira is here. Take it one moment at a time.",tip:"Step outside for 10 minutes. Fresh air can gently lift your mood."}],
    stressed:[{text:emoji+" Take a breath — you've handled hard things before.\n\nBreak whatever is stressing you into tiny steps.",tip:"Write down what's stressing you, then pick just one small thing to act on."}],
    anxious:[{text:emoji+" Your feelings are valid. Anxiety is hard.\n\nTry 5-4-3-2-1 grounding: name 5 things you see, 4 you touch, 3 you hear.",tip:"Slow breathing — 4 in, hold 4, out 6 — calms your nervous system."}],
    energetic:[{text:emoji+" Love this energy! Channel it well today!\n\nThis is the perfect time to tackle something you've been putting off.",tip:"Use this energy on your top 1-2 priorities. Don't scatter it."}],
    grateful:[{text:emoji+" Gratitude is one of the most powerful feelings.\n\nYou're in a beautiful headspace.",tip:"Text someone you're grateful for today. It'll make you both feel wonderful."}],
  };
  const opts=ar[mood]||ar.calm,r=opts[Math.floor(Math.random()*opts.length)];
  const el=document.getElementById("moodResponse");if(!el||!r)return;
  el.innerHTML='<div style="margin-bottom:8px;">'+r.text.replace(/\n/g,"<br>")+'</div><div style="background:rgba(138,108,255,0.08);border-radius:8px;padding:8px 10px;font-size:12px;color:var(--purple);font-weight:500;">'+r.tip+'</div><button onclick="document.getElementById(\'message\').value=\'I feel '+mood+'\';navApp(\'chatScreen\',null);sendMessage();" style="margin-top:10px;width:100%;padding:9px;border:none;border-radius:12px;background:linear-gradient(135deg,var(--purple),#b06fff);color:white;font-size:13px;font-weight:600;cursor:pointer;">Talk to Ahira about this</button>';
  el.classList.add("visible");
}

/* ─── INIT ──────────────────────────────────────────────── */

window.onload = function() {
    document.getElementById("authLogo").style.display    = "none";
    document.getElementById("authWrapper").style.display = "none";
    document.getElementById("appWrapper").style.display  = "none";
 
    /* Seed the browser history stack */
    window.history.replaceState({screen:"homeScreen"}, "", "");
 
    /* Back button: go to previous tab, not always home */
    window.addEventListener("popstate", () => {
        const appVisible = document.getElementById("appWrapper").style.display !== "none";
        if (!appVisible) return;
 
        const handled = handleBackButton();
        if (!handled) {
            /* At root of app — push state so next back press can exit */
            window.history.pushState({screen:"homeScreen"}, "", "");
        }
    });
 
    /* Inject Private Mode button into chat header */
    setTimeout(() => {
        const chatHeader = document.querySelector(".chatHeader");
        if (chatHeader && !document.getElementById("privateModeBtn")) {
            const btn = document.createElement("button");
            btn.id = "privateModeBtn";
            btn.title = "Private mode OFF — messages are saved";
            btn.innerText = "🔒";
            btn.style.cssText = "margin-left:auto;width:36px;height:36px;border-radius:50%;border:none;background:rgba(108,63,206,0.1);font-size:16px;cursor:pointer;transition:background 0.2s;flex-shrink:0;";
            btn.onclick = togglePrivateMode;
            chatHeader.appendChild(btn);
        }
 
        /* Inject Clear Chat button */
        const chatInputWrap = document.querySelector(".chatInputWrap");
        if (chatInputWrap && !document.getElementById("clearChatBtn")) {
            const clearBtn = document.createElement("button");
            clearBtn.id = "clearChatBtn";
            clearBtn.innerHTML = '<span style="font-size:11px;color:var(--t3);">Clear chat</span>';
            clearBtn.style.cssText = "width:100%;text-align:center;background:none;border:none;padding:6px 0 0;cursor:pointer;";
            clearBtn.onclick = () => {
                if (confirm("Clear all chat history? This cannot be undone.")) clearChatHistory();
            };
            chatInputWrap.appendChild(clearBtn);
        }
    }, 500);
 
    if (typeof AhiraSplash !== "undefined") AhiraSplash.init(2600);
    checkSession();
};
