"""
All conversational copy for Scheme Saathi — bilingual (English / हिंदी).

Each question spec:
  id        unique key (also the profile field name, unless `field` given)
  type      text | int | float | choice | yesno | multichoice
  text_*    question text
  help_*    plain-language explanation shown when the user is stuck / asks
            "BPL kya hai?", "nahi pata", "what does this mean?" (offline help;
            Gemini makes it conversational when a key is configured)
  options   quick-reply choices [{value, label_en, label_hi, show_if?}]
  ask_if    callable(profile) -> bool; question skipped when False
  field     profile field to store into (defaults to id)

The intake engine walks this list in order, skipping questions whose ask_if
fails — that is what makes the flow ADAPTIVE (farmers get land questions,
entrepreneurs get business questions, students get education questions).
"""

from __future__ import annotations

OCC_ENTREPRENEUR = ["business", "self_employed", "artisan", "street_vendor"]
OCC_EDU_RELEVANT = ["student", "business", "self_employed", "artisan", "unemployed"]


def _is_farmer(p: dict) -> bool:
    return p.get("occupation") == "farmer"


def _is_entrepreneur(p: dict) -> bool:
    return p.get("occupation") in OCC_ENTREPRENEUR


def _edu_relevant(p: dict) -> bool:
    return p.get("occupation") in OCC_EDU_RELEVANT


def _low_income(p: dict) -> bool:
    inc = p.get("annual_income")
    return inc is not None and inc <= 300000


# ---------------------------------------------------------------------------
# Option-level visibility guards (options adapt to who's answering — a male
# user is never shown "pregnant/new mother", an urban user never sees SHG…)
# ---------------------------------------------------------------------------


def _female(p: dict) -> bool:
    return p.get("gender") == "female"


def _adult(p: dict) -> bool:
    return (p.get("age") or 0) >= 18


def _childbearing_window(p: dict) -> bool:
    age = p.get("age") or 0
    return p.get("gender") == "female" and 18 <= age <= 50


def _rural_female(p: dict) -> bool:
    return p.get("gender") == "female" and p.get("area_type") == "rural"


WELCOME_EN = (
    "Namaste! 🙏 I'm **Scheme Saathi** — your AI assistant that finds government "
    "schemes you are eligible for.\n\nI'll ask a few quick questions (only the ones "
    "relevant to you), then instantly check **25 central schemes** and explain exactly "
    "why you qualify — or how close you are.\n\nStuck anywhere? Just type your doubt — "
    "e.g. *\"BPL kya hai?\"* — and I'll explain. 💬\n\n**Which language do you prefer?**"
)
WELCOME_HI = (
    "नमस्ते! 🙏 मैं हूँ **स्कीम साथी** — आपका AI सहायक, जो आपके लिए पात्र सरकारी योजनाएँ खोजता है।\n\n"
    "मैं कुछ छोटे सवाल पूछूँगा (सिर्फ वही, जो आपके लिए ज़रूरी हैं), फिर तुरंत **25 केंद्रीय योजनाएँ** "
    "जाँचूँगा और बताऊँगा कि आप क्यों पात्र हैं — या कितने करीब हैं।\n\nकहीं अटकें तो सीधे अपना सवाल "
    "लिखिए — जैसे *\"BPL क्या है?\"* — मैं समझा दूँगा। 💬\n\n**आप किस भाषा में बात करना चाहेंगे?**"
)

QUESTIONS: list[dict] = [
    {
        "id": "language",
        "type": "choice",
        "text_en": "Which language do you prefer? / आप किस भाषा में बात करना चाहेंगे?",
        "text_hi": "आप किस भाषा में बात करना चाहेंगे? / Which language do you prefer?",
        "help_en": "Just pick the language you're most comfortable in — the whole chat, report and documents checklist will follow that language.",
        "help_hi": "जिस भाषा में आप आराम से बात करते हैं, वही चुनिए — पूरी चैट, रिपोर्ट और दस्तावेज़ सूची उसी भाषा में आएगी।",
        "options": [
            {"value": "en", "label_en": "English", "label_hi": "English"},
            {"value": "hi", "label_en": "हिंदी (Hindi)", "label_hi": "हिंदी (Hindi)"},
        ],
    },
    {
        "id": "name",
        "type": "text",
        "text_en": "Great! 😊 What is your name?",
        "text_hi": "बहुत बढ़िया! 😊 आपका नाम क्या है?",
        "help_en": "Just type your name (e.g., Ramesh Kumar). It's only used to personalise your report — nothing is saved anywhere.",
        "help_hi": "बस अपना नाम लिखिए (जैसे रमेश कुमार)। यह सिर्फ आपकी रिपोर्ट को व्यक्तिगत बनाने के लिए है — कहीं कुछ सहेजा नहीं जाता।",
    },
    {
        "id": "age",
        "type": "int",
        "text_en": "Nice to meet you, {name}! What is your age?",
        "text_hi": "आपसे मिलकर खुशी हुई, {name} जी! आपकी उम्र क्या है?",
        "help_en": "Your age in years — e.g., 45. Not sure of the exact number? Just tap the closest age-range button below.",
        "help_hi": "आपकी उम्र सालों में — जैसे 45। सटीक उम्र पता नहीं? तो नीचे दिए सबसे करीबी उम्र-वर्ग का बटन दबा दीजिए।",
        "options": [
            {"value": 22, "label_en": "18–25", "label_hi": "18–25"},
            {"value": 30, "label_en": "26–35", "label_hi": "26–35"},
            {"value": 40, "label_en": "36–45", "label_hi": "36–45"},
            {"value": 55, "label_en": "46–60", "label_hi": "46–60"},
            {"value": 65, "label_en": "60+", "label_hi": "60+"},
        ],
    },
    {
        "id": "gender",
        "type": "choice",
        "text_en": "What is your gender?",
        "text_hi": "आपका लिंग क्या है?",
        "help_en": "Many schemes are only for women (Ujjwala, Stand-Up India, Matru Vandana) — that's why this is asked.",
        "help_hi": "बहुत सी योजनाएँ सिर्फ महिलाओं के लिए हैं (उज्ज्वला, स्टैंड-अप इंडिया, मातृ वंदना) — इसीलिए यह पूछा जाता है।",
        "options": [
            {"value": "male", "label_en": "Male", "label_hi": "पुरुष"},
            {"value": "female", "label_en": "Female", "label_hi": "महिला"},
            {"value": "other", "label_en": "Other", "label_hi": "अन्य"},
        ],
    },
    {
        "id": "state",
        "type": "text",
        "text_en": "Which state do you live in?",
        "text_hi": "आप किस राज्य में रहते हैं?",
        "help_en": "The state where you currently live — e.g., Bihar, Maharashtra. You can also tap a button below.",
        "help_hi": "जिस राज्य में आप अभी रहते हैं — जैसे बिहार, महाराष्ट्र। नीचे दिए बटन से भी चुन सकते हैं।",
        "options": [
            {"value": "Uttar Pradesh", "label_en": "Uttar Pradesh", "label_hi": "उत्तर प्रदेश"},
            {"value": "Maharashtra", "label_en": "Maharashtra", "label_hi": "महाराष्ट्र"},
            {"value": "Madhya Pradesh", "label_en": "Madhya Pradesh", "label_hi": "मध्य प्रदेश"},
            {"value": "Bihar", "label_en": "Bihar", "label_hi": "बिहार"},
            {"value": "Rajasthan", "label_en": "Rajasthan", "label_hi": "राजस्थान"},
            {"value": "Delhi", "label_en": "Delhi", "label_hi": "दिल्ली"},
        ],
    },
    {
        "id": "area_type",
        "type": "choice",
        "text_en": "Do you live in a rural or urban area?",
        "text_hi": "आप ग्रामीण या शहरी क्षेत्र में रहते हैं?",
        "help_en": "Village → Rural; city or town → Urban. Housing and skill schemes have separate rural/urban versions, so this decides which one fits you.",
        "help_hi": "गाँव → ग्रामीण; शहर या कस्बा → शहरी। आवास और कौशल योजनाओं के ग्रामीण/शहरी अलग-अलग संस्करण हैं, इसलिए यही तय करता है कि कौन सी आपके लिए सही है।",
        "options": [
            {"value": "rural", "label_en": "Rural (village)", "label_hi": "ग्रामीण (गाँव)"},
            {"value": "urban", "label_en": "Urban (city/town)", "label_hi": "शहरी (शहर/कस्बा)"},
        ],
    },
    {
        "id": "occupation",
        "type": "choice",
        "text_en": "What best describes your current occupation?",
        "text_hi": "आपका वर्तमान कार्य/पेशा क्या है?",
        "help_en": "What do you mainly do every day? Pick the CLOSEST option — the next questions (and the schemes I check) adapt to this. E.g., farming → Farmer, shop/services → Self-employed.",
        "help_hi": "आप रोज़ मुख्य रूप से क्या करते हैं? सबसे करीबी विकल्प चुनिए — अगले सवाल (और जाँची जाने वाली योजनाएँ) इसी पर निर्भर करती हैं। जैसे खेती → किसान, दुकान/सेवा → स्वयं रोज़गार।",
        "options": [
            {"value": "farmer", "label_en": "🌾 Farmer", "label_hi": "🌾 किसान"},
            {"value": "student", "label_en": "🎓 Student", "label_hi": "🎓 छात्र/छात्रा"},
            {"value": "business", "label_en": "🏢 Business owner / Startup", "label_hi": "🏢 व्यवसायी / स्टार्टअप"},
            {"value": "self_employed", "label_en": "🛠️ Self-employed (shop, services)", "label_hi": "🛠️ स्वयं रोज़गार (दुकान, सेवा)"},
            {"value": "artisan", "label_en": "🧵 Artisan / Craftsperson", "label_hi": "🧵 कारीगर / शिल्पकार"},
            {"value": "street_vendor", "label_en": "🛒 Street vendor / Hawker", "label_hi": "🛒 स्ट्रीट वेंडर / फेरीवाला"},
            {"value": "employee", "label_en": "💼 Salaried employee", "label_hi": "💼 नौकरीपेशा"},
            {"value": "unemployed", "label_en": "🔍 Looking for work", "label_hi": "🔍 काम की तलाश में"},
            {"value": "homemaker", "label_en": "🏠 Homemaker", "label_hi": "🏠 गृहिणी"},
            {"value": "retired", "label_en": "Retired / None", "label_hi": "सेवानिवृत्त / कोई नहीं"},
        ],
    },
    {
        "id": "education_level",
        "type": "choice",
        "ask_if": _edu_relevant,
        "text_en": "What is your highest education level?",
        "text_hi": "आपकी उच्चतम शिक्षा क्या है?",
        "help_en": "Your highest completed class/degree. Being 8th-pass or more unlocks business schemes like PMEGP.",
        "help_hi": "आपकी सबसे ऊँची पूरी की हुई कक्षा/डिग्री। 8वीं पास या उससे ऊपर होने पर PMEGP जैसी व्यापार योजनाएँ खुलती हैं।",
        "options": [
            {"value": "none", "label_en": "No formal schooling", "label_hi": "कोई औपचारिक शिक्षा नहीं"},
            {"value": "below_8th", "label_en": "Below 8th", "label_hi": "8वीं से कम"},
            {"value": "8th", "label_en": "8th pass", "label_hi": "8वीं पास"},
            {"value": "10th", "label_en": "10th pass", "label_hi": "10वीं पास"},
            {"value": "12th", "label_en": "12th pass", "label_hi": "12वीं पास"},
            {"value": "graduate", "label_en": "Graduate", "label_hi": "स्नातक"},
            {"value": "post_graduate", "label_en": "Post-graduate", "label_hi": "स्नातकोत्तर"},
        ],
    },
    {
        "id": "annual_income",
        "type": "int",
        "text_en": "What is your approximate annual family income? (yearly, whole family)",
        "text_hi": "आपकी पूरे परिवार की अनुमानित वार्षिक आय कितनी है?",
        "help_en": "Total YEARLY income of your whole family — farming + daily wages + salary + pension, everything added. Don't know exactly? Just tap the closest range button — an estimate is perfectly fine.",
        "help_hi": "पूरे परिवार की एक साल की कुल कमाई — खेती + मज़दूरी + नौकरी + पेंशन, सब जोड़कर। सटीक पता नहीं? नीचे दिए सबसे करीबी रेंज का बटन दबा दीजिए — अंदाज़ा भी बिल्कुल चलेगा।",
        "options": [
            {"value": 80000, "label_en": "Below ₹1 lakh", "label_hi": "₹1 लाख से कम"},
            {"value": 175000, "label_en": "₹1 – ₹2.5 lakh", "label_hi": "₹1 – ₹2.5 लाख"},
            {"value": 375000, "label_en": "₹2.5 – ₹5 lakh", "label_hi": "₹2.5 – ₹5 लाख"},
            {"value": 700000, "label_en": "₹5 – ₹10 lakh", "label_hi": "₹5 – ₹10 लाख"},
            {"value": 1200000, "label_en": "Above ₹10 lakh", "label_hi": "₹10 लाख से अधिक"},
        ],
    },
    {
        "id": "category",
        "type": "choice",
        "text_en": "What is your social category? (for reservation-linked schemes)",
        "text_hi": "आपका सामाजिक वर्ग क्या है? (आरक्षण-संबंधी योजनाओं के लिए)",
        "help_en": "Check your caste certificate — it says General / OBC / SC / ST. Some schemes are reserved for specific categories (extra benefits for SC/ST/OBC).",
        "help_hi": "आपके जाति प्रमाण पत्र में लिखा है — सामान्य / OBC / SC / ST। कुछ योजनाएँ खास वर्गों के लिए आरक्षित हैं (SC/ST/OBC के लिए अतिरिक्त लाभ)।",
        "options": [
            {"value": "general", "label_en": "General", "label_hi": "सामान्य"},
            {"value": "obc", "label_en": "OBC", "label_hi": "ओबीसी"},
            {"value": "sc", "label_en": "SC", "label_hi": "एससी"},
            {"value": "st", "label_en": "ST", "label_hi": "एसटी"},
        ],
    },
    {
        "id": "is_bpl",
        "type": "yesno",
        "ask_if": _low_income,
        "text_en": "Do you have a BPL (Below Poverty Line) ration card, or is your family in the SECC list?",
        "text_hi": "क्या आपके पास बीपीएल (गरीबी रेखा से नीचे) राशन कार्ड है, या आपका परिवार SECC सूची में है?",
        "help_en": "BPL means 'Below Poverty Line'. Check your RATION CARD — if it says BPL or Antyodaya, answer Yes. Not sure? Your Gram Panchayat or CSC centre can check the SECC-2011 list. Still can't tell? Answer No — I'll simply skip BPL-only schemes.",
        "help_hi": "BPL का मतलब है 'गरीबी रेखा से नीचे'। अपना राशन कार्ड देखिए — अगर उस पर BPL या अंत्योदय लिखा है तो 'हाँ' दबाइए। पक्का पता नहीं? आपकी ग्राम पंचायत या CSC केंद्र SECC-2011 सूची जाँच सकता है। फिर भी न समझे तो 'नहीं' दबा दीजिए — मैं BPL-वाली योजनाएँ बस छोड़ दूँगा।",
    },
    {
        "id": "land_holding",
        "type": "float",
        "ask_if": _is_farmer,
        "text_en": "How much agricultural land do you own? (in hectares — 1 hectare ≈ 2.5 acres)",
        "text_hi": "आपके पास कितनी कृषि भूमि है? (हेक्टेयर में — 1 हेक्टेयर ≈ 2.5 एकड़)",
        "help_en": "Land in your/your family's name (see Khatauni/land records). Rough guide: 1 hectare ≈ 2.5 acres ≈ 10 bigha. Just tap the closest button.",
        "help_hi": "वह ज़मीन जो आपके/परिवार के नाम पर है (खतौनी/भू-अभिलेख देखें)। आसान अंदाज़ा: 1 हेक्टेयर ≈ 2.5 एकड़ ≈ 10 बीघा। नीचे दिए सबसे करीबी बटन दबा दीजिए।",
        "options": [
            {"value": 0.25, "label_en": "Less than 0.5 ha (< 1.25 acres)", "label_hi": "0.5 हे. से कम (< 1.25 एकड़)"},
            {"value": 0.75, "label_en": "0.5 – 1 ha", "label_hi": "0.5 – 1 हे."},
            {"value": 1.5, "label_en": "1 – 2 ha", "label_hi": "1 – 2 हे."},
            {"value": 3.0, "label_en": "2 – 4 ha", "label_hi": "2 – 4 हे."},
            {"value": 6.0, "label_en": "More than 4 ha", "label_hi": "4 हे. से अधिक"},
        ],
    },
    {
        "id": "business_age_years",
        "type": "float",
        "ask_if": _is_entrepreneur,
        "text_en": "How old is your business/venture? (or is it just an idea right now?)",
        "text_hi": "आपका व्यवसाय/उद्यम कितना पुराना है? (या अभी सिर्फ एक आइडिया है?)",
        "help_en": "How long has the business been running? Still planning / haven't started → perfectly fine, pick 'Just an idea' — many schemes fund FIRST-TIME entrepreneurs only.",
        "help_hi": "व्यवसाय कब से चल रहा है? अभी सोच रहे हैं / शुरू नहीं किया → कोई बात नहीं, 'सिर्फ आइडिया' चुनिए — बहुत सी योजनाएँ सिर्फ पहली बार उद्यम शुरू करने वालों को ही फंड देती हैं।",
        "options": [
            {"value": 0, "label_en": "Just an idea / not started", "label_hi": "सिर्फ आइडिया / अभी शुरू नहीं हुआ"},
            {"value": 0.5, "label_en": "Less than 1 year", "label_hi": "1 साल से कम"},
            {"value": 1.5, "label_en": "1 – 2 years", "label_hi": "1 – 2 साल"},
            {"value": 3.5, "label_en": "2 – 5 years", "label_hi": "2 – 5 साल"},
            {"value": 7, "label_en": "More than 5 years", "label_hi": "5 साल से अधिक"},
        ],
    },
    {
        "id": "business_sector",
        "type": "choice",
        "ask_if": _is_entrepreneur,
        "text_en": "Which sector is your business in?",
        "text_hi": "आपका व्यवसाय किस क्षेत्र में है?",
        "help_en": "Manufacturing = you MAKE things (food products, furniture). Services = you provide work (salon, repair, coaching, transport). Trading = you buy & sell (kirana, shops).",
        "help_hi": "विनिर्माण = आप चीज़ें बनाते हैं (खाद्य उत्पाद, फर्नीचर)। सेवाएँ = आप काम/सेवा देते हैं (सैलून, रिपेयर, कोचिंग, ट्रांसपोर्ट)। व्यापार = आप खरीदकर बेचते हैं (किराना, दुकानें)।",
        "options": [
            {"value": "manufacturing", "label_en": "🏭 Manufacturing / Production", "label_hi": "🏭 विनिर्माण / उत्पादन"},
            {"value": "services", "label_en": "💡 Services", "label_hi": "💡 सेवाएँ"},
            {"value": "trading", "label_en": "🏪 Trading / Retail", "label_hi": "🏪 व्यापार / खुदरा"},
            {"value": "other", "label_en": "Other", "label_hi": "अन्य"},
        ],
    },
    {
        "id": "owns_pucca_house",
        "type": "yesno",
        "text_en": "Does your family own a pucca (permanent brick/concrete) house anywhere in India?",
        "text_hi": "क्या आपके परिवार के पास भारत में कहीं भी पक्का (ईंट/कंक्रीट का) मकान है?",
        "help_en": "Pucca house = brick/cement/concrete permanent house. Mud walls or tin/thatch roof → kutcha → answer 'No'. This decides housing-scheme (PM Awas) eligibility.",
        "help_hi": "पक्का मकान = ईंट/सीमेंट/कंक्रीट का स्थायी घर। मिट्टी की दीवार या टिन/फूस की छत = कच्चा मकान → 'नहीं' दबाइए। इसी से आवास योजना (पीएम आवास) की पात्रता तय होती है।",
    },
    {
        "id": "has_bank_account",
        "type": "yesno",
        "text_en": "Do you have a bank account in your name?",
        "text_hi": "क्या आपके नाम से बैंक खाता है?",
        "help_en": "Any savings account in YOUR name, in any bank or post office. No account? No problem — answer 'No' and I'll show you Jan Dhan (free, zero-balance account), which then unlocks pension & insurance schemes too.",
        "help_hi": "आपके नाम का किसी भी बैंक या डाकघर का बचत खाता। खाता नहीं है? कोई बात नहीं — 'नहीं' दबाइए, मैं जन धन (मुफ्त, ज़ीरो-बैलेंस खाता) दिखाऊँगा, जिससे फिर पेंशन और बीमा योजनाएँ भी खुल जाती हैं।",
    },
    {
        "id": "special",
        "type": "multichoice",
        "text_en": "Last one! Do any of these apply to you? (choose all that fit, or 'None')",
        "text_hi": "आखिरी सवाल! इनमें से कुछ आप पर लागू होता है? (जो भी सही हों चुनें, या 'कोई नहीं')",
        "help_en": "Tap whatever applies to you — these unlock EXTRA schemes (girl-child savings, maternity benefit, artisan support...). You can even reply like '1, 3'. Nothing applies? Just tap 'None'.",
        "help_hi": "जो भी आप पर लागू हो, टैप कीजिए — इनसे अतिरिक्त योजनाएँ खुलती हैं (बेटी की बचत, मातृत्व लाभ, कारीगर सहायता...)। आप '1, 3' लिखकर भी जवाब दे सकते हैं। कुछ भी लागू न हो तो 'कोई नहीं' दबा दीजिए।",
        "options": [
            {"value": "daughter_under_10", "label_en": "👧 I have a daughter below 10 years", "label_hi": "👧 मेरी 10 साल से छोटी बेटी है",
             "show_if": _adult},
            {"value": "pregnant_or_new_mother", "label_en": "🤰 I am pregnant / a new mother", "label_hi": "🤰 मैं गर्भवती हूँ / नई माँ हूँ",
             "show_if": _childbearing_window},
            {"value": "traditional_artisan", "label_en": "🧶 I practise a traditional craft", "label_hi": "🧶 मैं पारंपरिक शिल्प करता/करती हूँ"},
            {"value": "willing_shg", "label_en": "👩‍👩‍👧 Willing to join a women's Self-Help Group", "label_hi": "👩‍👩‍👧 महिला स्वयं सहायता समूह से जुड़ सकती हूँ",
             "show_if": _rural_female},
            {"value": "differently_abled", "label_en": "♿ I am differently-abled", "label_hi": "♿ मैं दिव्यांग हूँ"},
            {"value": "ex_serviceman", "label_en": "🎖️ I am an ex-serviceman", "label_hi": "🎖️ मैं भूतपूर्व सैनिक हूँ"},
            {"value": "none", "label_en": "None of these", "label_hi": "इनमें से कोई नहीं"},
        ],
    },
]

# ---------------------------------------------------------------------------
# "Ask anytime" help system — a stuck user can simply type their doubt
# ("BPL kya hai?", "nahi pata", "samajh nahi aaya") and the assistant
# explains + gently re-asks, instead of failing with a parse error.
# ---------------------------------------------------------------------------

QUESTION_TOKENS = {
    # romanized Hindi / Hinglish
    "kya", "kyu", "kyun", "kaise", "kaisi", "kaisa", "kaun", "kab", "kitna", "kitni",
    "kitne", "matlab", "batao", "samjhao", "samjha", "madad", "confused",
    # English
    "help", "how", "what", "whats", "why", "meaning", "explain",
    # Devanagari (whole-word only — "नहीं"/"ना" deliberately excluded: they're answers)
    "क्या", "क्यों", "क्यूँ", "कैसे", "कैसा", "कैसी", "कौन", "कब", "कितना", "कितनी",
    "कितने", "मतलब", "बताओ", "बताएं", "बताइए", "समझाओ", "समझाएं", "मदद",
}
QUESTION_PHRASES = [
    # caught the easy way first
    "?",
    # romanized
    "nahi pata", "pata nahi", "nahi maloom", "maloom nahi", "nahi samajh", "samajh nahi",
    "nahi samjha", "nai samajh", "samjh nahi", "don't know", "dont know", "do not know",
    "not sure", "no idea", "what is", "what's", "how to", "how do", "how will", "ka matlab",
    "kaise kare", "kaise karen", "kyu chahiye", "kyun chahiye", "kise kehte", "kise kahte",
    "i am confused", "samajh mein nahi", "samajh nahi aaya", "kya hota hai", "kya hai ye",
    "kya karna hai", "how much", "kitna hota", "bata sakte", "bata do", "mujhe nahi aata",
    "nahi aata", "computer nahi", "phone nahi chalata", "angootha",
    # Devanagari
    "नहीं पता", "पता नहीं", "मालूम नहीं", "नहीं मालूम", "समझ नहीं", "नहीं समझ", "समझ में नहीं",
    "क्या होता है", "क्या है", "मतलब क्या", "कैसे बताऊं", "कैसे बताऊँ", "कैसे करें", "कैसे करूं",
    "कैसे करूँ", "क्यों चाहिए", "किसे कहते", "मुझे नहीं आता", "नहीं आता", "बता सकते",
    "बता दो", "मदद चाहिए",
]
GENERAL_HELP_WORDS = {
    "help", "madad", "help me", "madad chahiye", "bachao", "?", "??", "???",
    "help karo", "madad karo", "मदद", "मदद चाहिए", "हेल्प", "बचाओ",
}

GENERAL_HELP_EN = (
    "No worries at all 😊 Here's how I work:\n"
    "1️⃣ I ask simple questions, one at a time\n"
    "2️⃣ You tap a button or type your answer\n"
    "3️⃣ **Stuck on any question? Just ASK me** — e.g. \"BPL kya hai?\" or \"income kaise batayein?\"\n"
    "4️⃣ At the end, I show every government scheme you're eligible for, with reasons\n\n"
    "Now, let's continue 👇"
)
GENERAL_HELP_HI = (
    "बिल्कुल चिंता मत कीजिए 😊 मैं ऐसे काम करता हूँ:\n"
    "1️⃣ मैं एक-एक करके आसान सवाल पूछता हूँ\n"
    "2️⃣ आप बटन दबाइए या अपना जवाब लिखिए\n"
    "3️⃣ **कोई सवाल समझ न आए? मुझसे सीधे पूछिए** — जैसे \"BPL क्या है?\" या \"आय कैसे बताएँ?\"\n"
    "4️⃣ अंत में मैं आपको वो सारी सरकारी योजनाएँ बताऊँगा जिनके आप हक़दार हैं, वजह समझाकर\n\n"
    "चलिए, आगे बढ़ते हैं 👇"
)

# Post-intake copy
DONE_EN = (
    "All done, {name}! 🎯 I checked your profile against **{total} government schemes** — "
    "here is your personal eligibility report:"
)
DONE_HI = (
    "हो गया, {name} जी! 🎯 मैंने आपकी प्रोफ़ाइल **{total} सरकारी योजनाओं** से मिलाई — "
    "ये रही आपकी व्यक्तिगत पात्रता रिपोर्ट:"
)

ERROR_EN = "Hmm, I didn't quite get that. 🤔 "
ERROR_HI = "माफ़ कीजिए, मैं समझ नहीं पाया। 🤔 "

PROFILE_NOTE_EN = {
    "farmer": "Since you're a farmer, I'll also check agriculture-specific schemes like PM-KISAN and crop insurance. 🌾",
    "student": "Since you're a student, I'll check all scholarships too. 🎓",
    "business": "Since you run a business, I'll check all enterprise loan & subsidy schemes too. 🏢",
    "self_employed": "Since you're self-employed, I'll check enterprise loan & subsidy schemes too. 🛠️",
    "artisan": "Since you're an artisan, I'll check craft/artisan-specific schemes like PM Vishwakarma too. 🧵",
    "street_vendor": "Since you're a street vendor, I'll check PM SVANidhi and other vendor schemes too. 🛒",
}
PROFILE_NOTE_HI = {
    "farmer": "चूँकि आप किसान हैं, मैं पीएम-किसान और फसल बीमा जैसी कृषि योजनाएँ भी जाँचूँगा। 🌾",
    "student": "चूँकि आप छात्र/छात्रा हैं, मैं सभी छात्रवृत्तियाँ भी जाँचूँगा। 🎓",
    "business": "चूँकि आप व्यवसाय चलाते हैं, मैं सभी उद्यम लोन व सब्सिडी योजनाएँ भी जाँचूँगा। 🏢",
    "self_employed": "चूँकि आप स्वरोज़गार करते हैं, मैं उद्यम लोन व सब्सिडी योजनाएँ भी जाँचूँगा। 🛠️",
    "artisan": "चूँकि आप कारीगर हैं, मैं पीएम विश्वकर्मा जैसी शिल्प-योजनाएँ भी जाँचूँगा। 🧵",
    "street_vendor": "चूँकि आप स्ट्रीट वेंडर हैं, मैं पीएम स्वनिधि और अन्य वेंडर योजनाएँ भी जाँचूँगा। 🛒",
}
