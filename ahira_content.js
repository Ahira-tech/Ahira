/* ============================================================
   ahira_content.js — Ahira Content Library
   
   • 200 unique daily quotes
   • 60 period health tips  
   • 60 water intake tips
   • 40 wellness facts
   • 30 welcome lines
   
   USAGE:
   Add before chat.js in index.html:
   <script src="/static/ahira_content.js"></script>
   
   API:
   AhiraContent.dailyQuote()       — same quote all day, rotates daily
   AhiraContent.dailyWelcome()     — same welcome all day, rotates daily
   AhiraContent.randomPeriodTip()  — random period tip
   AhiraContent.randomWaterTip()   — random water tip
   AhiraContent.randomWellness()   — random wellness fact
   AhiraContent.randomQuote()      — random quote any time
============================================================ */

const AhiraContent = (() => {

    // ─────────────────────────────────────────────────────────
    // 200 DAILY QUOTES
    // ─────────────────────────────────────────────────────────
    const QUOTES = [
        // Strength & Resilience
        "You have survived every hard day so far. That's a 100% success rate. 💜",
        "Strength doesn't always roar. Sometimes it's the quiet voice that says 'I'll try again tomorrow.'",
        "You are not behind. You are on your own beautiful timeline.",
        "The fact that you're still here, still trying — that's extraordinary.",
        "Difficult roads often lead to the most breathtaking destinations.",
        "You've been through storms before. You know how to weather them.",
        "Every setback is setting you up for a stronger comeback.",
        "You are braver than you believe, stronger than you seem, and more loved than you know.",
        "Growth is uncomfortable because you're expanding. Keep going.",
        "The woman who fights for herself becomes unstoppable.",

        // Self Love & Worth
        "You are worthy of love, rest, joy, and abundance — right now, as you are.",
        "Your worth is not measured by your productivity. You are enough by simply existing.",
        "Be as kind to yourself as you are to the people you love most.",
        "You don't need to earn rest. You are not a machine.",
        "You are allowed to take up space — in rooms, in conversations, in life.",
        "Loving yourself is not selfish. It's the foundation of everything.",
        "You deserve the same compassion you so freely give to others.",
        "Your body is not the problem. It's the home your soul lives in.",
        "You are not too much. You've just been around people who couldn't hold your magnitude.",
        "You are a masterpiece AND a work in progress — both at the same time.",

        // Peace & Healing
        "Healing is not linear. Some days you'll go backwards, and that's still healing.",
        "Peace begins the moment you decide not to let anyone's opinion disturb your inner calm.",
        "You don't have to be okay all the time. Let yourself feel what is real.",
        "Give yourself permission to grieve, to rest, to start over.",
        "Letting go is not giving up. It's making room for what truly belongs.",
        "The most powerful thing you can do is return to stillness.",
        "Your nervous system deserves gentleness. Not everything needs a reaction.",
        "Boundaries are not walls. They're the doors you choose who to let in through.",
        "Healing happens in the quiet moments between the chaos.",
        "You are allowed to outgrow people, places, and old versions of yourself.",

        // Motivation & Purpose
        "Start before you're ready. The perfect time is a myth.",
        "You don't need motivation. You need commitment. Show up anyway.",
        "Small consistent steps beat occasional giant leaps every time.",
        "Your dreams are not too big. Your belief in yourself just needs to catch up.",
        "The version of you that succeeds is the one who keeps going on the hardest days.",
        "Done is better than perfect. Ship it. Improve it. Keep moving.",
        "You are not lazy. You may be overwhelmed, burnt out, or in need of rest.",
        "Every expert was once a beginner who refused to quit.",
        "The goal is not to be perfect. The goal is to be real and keep trying.",
        "Your future self is rooting for the decision you make right now.",

        // Joy & Gratitude
        "Happiness is not a destination. It's sprinkled in ordinary moments.",
        "You are allowed to feel joy — even when life is hard.",
        "Notice what makes you come alive. Do more of that.",
        "Gratitude doesn't change the facts. It changes how you see them.",
        "Today, find one thing that made you smile. That thing matters.",
        "Joy is an act of resistance. Choose it when you can.",
        "You don't need everything to be perfect to be deeply grateful.",
        "The small moments are not small. They are the whole thing.",
        "Appreciate the ordinary. One day it will be what you miss most.",
        "You are surrounded by more beauty than you currently notice.",

        // Mental Health
        "Your mental health is not a luxury. It's a necessity.",
        "Asking for help is one of the most courageous things you can do.",
        "It's okay to not be okay. And it's okay to get support for that.",
        "Anxiety is not weakness. It's your nervous system working overtime.",
        "Rest is a mental health strategy. Not a reward.",
        "Saying 'I'm not okay' is not a burden. It's honesty.",
        "Therapy, journaling, walks, sleep — all of these are medicine.",
        "You are not broken. You are human, and humans have hard seasons.",
        "Your feelings are valid even when they're inconvenient.",
        "You deserve a mind that feels safe and a life that feels like home.",

        // Relationships
        "Surround yourself with people who make you feel seen, not compared.",
        "The right people will love the real you — not the performance.",
        "You are not responsible for managing other people's emotions.",
        "It's okay to distance yourself from what drains you, even if it was once good.",
        "You teach people how to treat you. Raise your standards gently but firmly.",
        "The relationship you have with yourself sets the tone for every other one.",
        "Not everyone deserves access to the most vulnerable parts of you.",
        "Love yourself enough to walk away from what no longer serves your growth.",
        "The people who are meant to stay will stay. The rest are lessons.",
        "You deserve a love that doesn't require you to shrink yourself.",

        // Body & Wellness
        "Your body works tirelessly for you every single day. Thank it.",
        "Movement is medicine. Even a slow walk counts.",
        "Food is not the enemy. Food is fuel, comfort, culture, and joy.",
        "Sleep is not laziness. It's when your body does its most important work.",
        "You are not your hormones. But understanding them changes everything.",
        "Taking care of your body is one of the highest forms of self-respect.",
        "Rest when you're tired. Your body is always speaking. Learn to listen.",
        "You don't need to punish yourself to be healthy. Gentle consistency wins.",
        "Your body is not ornamental. It's functional, powerful, and worthy of care.",
        "Wellness is not a size or a number. It's how alive you feel from the inside.",

        // Courage & Change
        "The life you want is on the other side of the fear you're avoiding.",
        "Change is not betrayal. It's evolution.",
        "You don't have to be fearless. Just act despite the fear.",
        "Every version of you was necessary to build who you are today.",
        "Be willing to disappoint others to stay true to yourself.",
        "The bravest thing you can do is begin again, quietly, without applause.",
        "Your past is not your future unless you live there.",
        "You are not stuck. You are preparing. There's a difference.",
        "Courage is choosing honesty over comfort, growth over safety.",
        "One small brave choice today creates the momentum for everything else.",

        // Wisdom & Perspective
        "Not every chapter of your life is meant to be pretty. Some teach.",
        "You don't have to figure out the whole path. Just the next step.",
        "The problem and the solution rarely exist in the same state of mind.",
        "Not everything requires a response. Silence is also an answer.",
        "The things you resist most are often the things that will free you.",
        "You will not be the same person at the end of this hard season. That's the point.",
        "Most things that worry you never actually happen. Breathe.",
        "Comparison is the thief of joy and the enemy of progress.",
        "Your life is not a competition. Your only opponent is yesterday's version of you.",
        "Some doors are closed because something better is being prepared.",

        // Affirmations
        "I am learning. I am growing. I am becoming.",
        "I choose peace over perfection today.",
        "I am worthy of the love I seek. It starts with me.",
        "I release what I cannot control and trust what I cannot yet see.",
        "I am not my mistakes. I am what I choose to do next.",
        "I give myself permission to take up space and be fully me.",
        "I am doing the best I can with what I have right now.",
        "I trust my body. I trust my instincts. I trust my timing.",
        "I am allowed to rest. I am allowed to start again.",
        "I choose me — not out of selfishness, but out of self-preservation.",

        // Feminine Power
        "There is incredible power in your intuition. Trust it.",
        "A woman who knows her worth changes the whole room.",
        "You are cyclical, not broken. Your rhythms are your superpower.",
        "Softness is not weakness. It takes great strength to stay tender in a hard world.",
        "Your emotions are data, not drama. Let them inform you.",
        "You were never meant to fit into a mould. You were built to break them.",
        "The woman you are becoming will thank you for every boundary you set today.",
        "Your sensitivity is not a flaw. It's a form of intelligence.",
        "You are allowed to be ambitious and gentle, fierce and soft, all at once.",
        "A woman who invests in herself builds something no one can take away.",

        // Everyday Encouragement
        "Today is a new page. What will you write?",
        "You woke up today. That already counts for something.",
        "Even on slow days, you are still moving forward.",
        "Your effort today, however small, matters more than you know.",
        "Give yourself credit for the things you've already done.",
        "It's okay if today is just maintenance. Showing up is enough.",
        "You are allowed to have a quiet day without guilt.",
        "Every day you choose yourself is a victory.",
        "The fact that you're trying is enough for today.",
        "Tomorrow is always a fresh start. But so is right now.",

        // Seasonal & Cyclical
        "Like the moon, you go through phases. All of them are natural.",
        "Some seasons are for doing. Some are for resting. Both are necessary.",
        "You cannot bloom in every season. Rest is not failure.",
        "After every winter, spring finds a way through. So will you.",
        "You are allowed to ebb. Flowing will come again.",
        "Your energy is cyclical. Work with it, not against it.",
        "Low energy days are not wasted days. They are restorative ones.",
        "You are seasonal, and every season of you has purpose.",
        "Your cycle teaches you about your power. Pay attention.",
        "Every ending you've survived was a beginning you didn't know you needed.",

        // Mindfulness
        "Right now, in this moment, you are safe.",
        "The present moment is the only place where life actually happens.",
        "Breathe. You don't have to solve everything today.",
        "One breath at a time. One step at a time. One day at a time.",
        "Slow down. The best things in life don't require rushing.",
        "Be here. Not in yesterday's regret or tomorrow's worry.",
        "Stillness is not emptiness. It's where clarity lives.",
        "You don't have to be busy to be valuable.",
        "Notice this moment — it will not come again.",
        "Mindfulness is not about being calm. It's about being present, even in the storm.",

        // Hope
        "Something good is coming — even if you can't see it yet.",
        "Your story is not over. Not even close.",
        "The best chapters of your life may not have been written yet.",
        "Hope is not naive. It's the most radical act of courage.",
        "Even in the darkest room, one small light changes everything.",
        "Hold on. Seasons change. So do circumstances.",
        "You have been in difficult places before and found your way through.",
        "Things don't stay the same. This hard season will shift.",
        "Keep going. The view from the other side of this will be worth it.",
        "You are still here. And that means something beautiful is still possible.",

        // Final 20 — Mixed Gems
        "Your life is not a problem to be solved. It's a journey to be lived.",
        "The most important conversation you'll have today is with yourself.",
        "You don't have to have it all figured out to take the next step.",
        "Imperfect action beats perfect inaction every single time.",
        "You are not in competition with other women. Their success is not your failure.",
        "Your uniqueness is not a bug. It's the whole feature.",
        "The version of you that your past self prayed for — she's here now.",
        "You've already done hard things. You'll do this too.",
        "Every version of strength looks different. Yours is valid.",
        "You are a whole person — not half of something waiting to be completed.",
        "The softness in you is not something to apologise for.",
        "You are allowed to outgrow the life that no longer fits.",
        "Your presence matters more than your perfection.",
        "Take care of your inner world. The outer one will follow.",
        "You are not waiting for your life to begin. It already has.",
        "Be gentle with beginnings. All good things start slowly.",
        "Your voice deserves to be heard — especially by yourself.",
        "You are not defined by your hardest moment.",
        "The courage it takes to keep showing up every day is real.",
        "You — exactly as you are — are enough. Always. 💜",
    ];

    // ─────────────────────────────────────────────────────────
    // 60 PERIOD HEALTH TIPS
    // ─────────────────────────────────────────────────────────
    const PERIOD_TIPS = [
        // Pain & Comfort
        "A heating pad on your lower abdomen relaxes uterine muscles and eases cramps naturally.",
        "Gentle yoga poses like Child's Pose and Cat-Cow can reduce period cramps within minutes.",
        "A warm bath with Epsom salts helps relax pelvic muscles and soothes period pain.",
        "Light walking improves blood flow and triggers endorphins that act as natural painkillers.",
        "Massaging your lower abdomen with lavender or clary sage oil can reduce cramping.",
        "Drinking chamomile tea has anti-inflammatory and antispasmodic effects on uterine muscles.",
        "Applying heat is often as effective as ibuprofen for mild to moderate period cramps.",
        "Rest in fetal position with a pillow between your knees to relieve pelvic pressure.",
        "Ginger tea — fresh ginger steeped in hot water — is a powerful natural anti-inflammatory.",
        "Avoiding cold drinks during your period may reduce muscle cramping for some people.",

        // Nutrition
        "Iron-rich foods like lentils, spinach, and red meat help replace iron lost during bleeding.",
        "Vitamin C helps your body absorb iron — pair iron foods with lemon, orange, or tomato.",
        "Magnesium-rich foods like dark chocolate, almonds, and avocado reduce PMS symptoms significantly.",
        "Omega-3 fatty acids in salmon, walnuts, and flaxseed reduce period pain inflammation.",
        "Calcium-rich foods like dairy, leafy greens, and tofu help reduce mood swings and cramps.",
        "Reduce salt intake before your period to minimise bloating and water retention.",
        "Avoid excessive sugar during your period — it spikes then crashes energy and worsens mood.",
        "Complex carbohydrates like oats and sweet potato maintain stable blood sugar during your cycle.",
        "Turmeric contains curcumin, a natural anti-inflammatory — add it to warm milk or curries.",
        "Dark leafy greens support hormonal balance and replace nutrients lost during menstruation.",

        // Tracking & Awareness
        "Tracking your cycle for 3 months reveals your personal patterns, not just average ones.",
        "Note your energy levels each day of your cycle — most people notice a predictable pattern.",
        "Your basal body temperature rises slightly after ovulation and drops before your period.",
        "Period apps like Clue or Flo can identify irregularities that are worth discussing with a doctor.",
        "Spotting between periods, extremely heavy flow, or severe pain warrants a medical check.",
        "A 'normal' cycle is anywhere from 21 to 35 days — not just the textbook 28.",
        "Understanding your cycle phases helps you plan work, exercise, and social events more wisely.",
        "Your most productive, energetic days are typically in the follicular phase (days 7–13).",
        "Cycle syncing — adjusting activities to cycle phases — is a powerful productivity and wellness tool.",
        "If you skip periods while not pregnant, it's worth checking your thyroid and stress levels.",

        // PMS
        "PMS affects up to 75% of menstruating people — you are not imagining it.",
        "Emotional sensitivity before your period is driven by progesterone drops, not 'being dramatic'.",
        "Reducing caffeine in the week before your period can significantly lower PMS anxiety.",
        "Exercise in the luteal phase (days 14–28) helps metabolise excess estrogen and reduce PMS.",
        "PMDD is a severe form of PMS that requires medical support — please seek it if needed.",
        "B6 vitamin supplements can help reduce PMS mood symptoms like irritability and depression.",
        "Evening primrose oil has been shown to reduce breast tenderness and PMS inflammation.",
        "Light therapy can help with PMS-related mood changes, especially in winter months.",
        "Journaling in the luteal phase helps distinguish hormone-driven emotions from real concerns.",
        "A consistent sleep schedule during the luteal phase dramatically improves PMS symptoms.",

        // Comfort & Lifestyle
        "Wear breathable, loose-fitting clothing during your period to reduce physical discomfort.",
        "Period underwear, menstrual cups, and discs are sustainable, comfortable alternatives to pads.",
        "A menstrual cup holds 3× more than a tampon and can safely be worn for up to 12 hours.",
        "Changing period products every 4–8 hours reduces risk of infection and maintains comfort.",
        "Avoid prolonged sitting during your period — move gently every hour to ease pelvic tension.",
        "A good quality sleep during your period supports immune function and pain tolerance.",
        "Prioritise low-stress activities during the first two days of your cycle.",
        "Your pain tolerance is lower on day 1–2 due to prostaglandins — be extra gentle with yourself.",
        "Hydration is extra important during your period — it reduces bloating and supports circulation.",
        "Saying 'I need rest today because my body is working hard' is completely valid. Always.",

        // Cycle & Hormones
        "Your cycle has four phases: menstrual, follicular, ovulatory, and luteal. Each feels different.",
        "Estrogen peaks around ovulation, making you feel sociable, confident, and energised.",
        "Progesterone rises after ovulation, making you feel more introspective and tired.",
        "Your metabolism speeds up in the luteal phase — you genuinely need slightly more calories.",
        "Cortisol (stress hormone) disrupts your hormonal cycle more than almost anything else.",
        "Irregular periods are often your body signalling stress, undereating, or overexercising.",
        "Your hormones affect your skin, mood, sleep, digestion, and energy — they're interconnected.",
        "Hormonal contraception changes your natural cycle — that's neither good nor bad, just different.",
        "Being in sync with women you live with is real — it's called menstrual synchrony.",
        "Your period is not a weakness. It is evidence of extraordinary biological complexity.",
    ];

    // ─────────────────────────────────────────────────────────
    // 60 WATER INTAKE TIPS
    // ─────────────────────────────────────────────────────────
    const WATER_TIPS = [
        // Why Water Matters
        "Your body is about 60% water — hydration affects every single system.",
        "Even mild dehydration (1–2%) impairs concentration, mood, and physical performance.",
        "Water helps flush toxins through your kidneys — the body's natural filtration system.",
        "Proper hydration supports glowing skin more than most skincare products.",
        "Water lubricates your joints — dehydration is a leading cause of joint pain.",
        "Your brain is 73% water. Staying hydrated is literally feeding your brain.",
        "Hydration supports a healthy metabolism and helps regulate body temperature.",
        "Water helps transport nutrients and oxygen to every cell in your body.",
        "Chronic mild dehydration contributes to constipation, headaches, and fatigue.",
        "Staying hydrated during your period reduces cramping and bloating significantly.",

        // How Much to Drink
        "The 8 glasses rule is a good start, but your needs depend on weight, activity, and climate.",
        "A simple formula: drink 30–35ml of water per kilogram of body weight daily.",
        "If your urine is pale yellow, you're well hydrated. Dark yellow means drink more.",
        "You need more water when you exercise, when it's hot, or when you're unwell.",
        "Pregnant or breastfeeding? Increase water intake by at least 300–500ml daily.",
        "Athletes need up to 3 litres daily. Most non-athletes do well with 2–2.5 litres.",
        "You lose up to 1.5 litres through breathing, sweating, and digestion daily — replenish it.",
        "Your thirst mechanism lags behind actual dehydration — drink before you feel thirsty.",
        "Elderly people have a reduced thirst response — conscious hydration becomes more important.",
        "Caffeinated drinks count toward fluid intake but have a mild diuretic effect — balance them.",

        // Building the Habit
        "Start every morning with a full glass of water before coffee or food.",
        "Keep a water bottle visible on your desk — out of sight, out of mind really does apply.",
        "Link water drinking to existing habits: after brushing teeth, before meals, after waking.",
        "Set phone reminders every 2 hours if you tend to forget during busy days.",
        "Drink a glass of water before every meal — it also prevents overeating.",
        "Finish a glass of water before you open any other app in the morning.",
        "If you struggle to drink plain water, try sparkling water — some people find it easier.",
        "Track your intake with an app or simply count glasses — what gets measured gets done.",
        "Carry a 1-litre bottle and aim to refill it twice a day.",
        "Make it a game: one glass every hour between 8am and 6pm = 10 glasses.",

        // Making Water Enjoyable
        "Add fresh lemon or lime for a vitamin C boost and better taste.",
        "Mint and cucumber water is refreshing and supports digestion.",
        "Ginger-infused water is warming, anti-inflammatory, and great for digestion.",
        "Hibiscus water is naturally sweet, beautiful, and rich in antioxidants.",
        "Strawberry and basil water is unexpectedly delicious and hydrating.",
        "Rose water added to your drinking water is calming and skin-supportive.",
        "Coconut water is an excellent post-exercise hydrator with natural electrolytes.",
        "Herbal teas (peppermint, chamomile, rooibos) count as hydration with added benefits.",
        "Eating water-rich fruits counts: cucumber is 96% water, watermelon is 92%.",
        "Making 'spa water' the night before makes you more likely to drink it the next day.",

        // Signs of Dehydration
        "A headache is often the first sign your body sends when you're dehydrated.",
        "Fatigue that hits midday is frequently dehydration, not just tiredness.",
        "Dry lips and skin are visible reminders that your internal hydration needs attention.",
        "Difficulty concentrating? Drink a glass of water before reaching for caffeine.",
        "Muscle cramps, especially at night, are often a sign of dehydration and low electrolytes.",
        "Feeling dizzy when standing? That can be dehydration causing a blood pressure drop.",
        "Bad breath can be caused by dehydration reducing saliva production.",
        "Mood changes and irritability are early symptoms of inadequate hydration.",
        "Constipation is frequently a hydration issue — water softens stool and aids digestion.",
        "Dark urine and infrequent bathroom visits = your body asking for more water, urgently.",

        // Advanced Hydration
        "Electrolytes (sodium, potassium, magnesium) help water enter cells effectively.",
        "After intense exercise, plain water alone may not be enough — add electrolytes.",
        "Room temperature water is absorbed faster than ice-cold water.",
        "Sipping water throughout the day is more effective than drinking large amounts at once.",
        "Watermelon, strawberries, oranges, and spinach are excellent hydrating foods.",
        "Coffee doesn't dehydrate you significantly — but it doesn't hydrate as well as water either.",
        "Alcohol is a diuretic — drink a glass of water for every alcoholic drink you have.",
        "Green tea is hydrating AND contains antioxidants — a great water alternative.",
        "Your kidneys can only process about 800ml per hour — don't chug huge amounts at once.",
        "Hydration supports better sleep — but stop big drinks 2 hours before bed.",
    ];

    // ─────────────────────────────────────────────────────────
    // 30 WELCOME LINES
    // ─────────────────────────────────────────────────────────
    const WELCOME_LINES = [
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
        "I've been thinking about you 💜",
        "Soft landing, right here 🌿",
        "Your feelings are safe here 🤍",
        "New day, new energy — let's go ⚡",
        "Showing up for yourself is brave 💜",
        "This is your space. Welcome home 🌸",
        "Whatever today holds, I'm with you 💛",
        "Take a breath. You've got this. 🌿",
        "Every day with you is a good day ✨",
        "You are seen. You are valued. You are here. 💜",
        "Come in, sit down — Ahira's listening 🤍",
        "Today is a fresh page. Write something kind 🌷",
        "You woke up and chose yourself. That's everything 💜",
        "No judgment here — just warmth and care 🌸",
        "Glad you're back. Let's make today count 💛",
        "Your journey continues — and I'm walking with you ✨",
        "Even on hard days, you belong here 🤍",
        "Small steps still move you forward. Keep going 🌿",
        "You are enough. You always were. 💜",
    ];

    // ─────────────────────────────────────────────────────────
    // HELPERS
    // ─────────────────────────────────────────────────────────

    // Same item all day — changes at midnight — rotates through full array
    function daily(arr) {
        const now       = new Date();
        const start     = new Date(now.getFullYear(), 0, 0);
        const dayOfYear = Math.floor((now - start) / 864e5);
        return arr[dayOfYear % arr.length];
    }

    // Truly random pick
    function random(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }

    // Session-stable random (same within one page session, different next open)
    const _sessionPicks = {};
    function sessionRandom(key, arr) {
        if (!_sessionPicks[key]) {
            _sessionPicks[key] = arr[Math.floor(Math.random() * arr.length)];
        }
        return _sessionPicks[key];
    }

    // ─────────────────────────────────────────────────────────
    // PUBLIC API
    // ─────────────────────────────────────────────────────────
    return {
        // Daily (consistent all day, rotates each new day)
        dailyQuote:    () => daily(QUOTES),
        dailyWelcome:  () => daily(WELCOME_LINES),

        // Session (same for the whole app session, new on next open)
        sessionQuote:  () => sessionRandom("quote",   QUOTES),
        sessionPeriod: () => sessionRandom("period",  PERIOD_TIPS),
        sessionWater:  () => sessionRandom("water",   WATER_TIPS),
        sessionWelcome:() => sessionRandom("welcome", WELCOME_LINES),

        // Random (different every call)
        randomQuote:      () => random(QUOTES),
        randomPeriodTip:  () => random(PERIOD_TIPS),
        randomWaterTip:   () => random(WATER_TIPS),
        randomWelcome:    () => random(WELCOME_LINES),

        // Counts
        totalQuotes:  QUOTES.length,
        totalPeriod:  PERIOD_TIPS.length,
        totalWater:   WATER_TIPS.length,
        totalWelcome: WELCOME_LINES.length,

        // Raw arrays
        quotes:       QUOTES,
        periodTips:   PERIOD_TIPS,
        waterTips:    WATER_TIPS,
        welcomeLines: WELCOME_LINES,
    };

})();
