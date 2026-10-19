"""Per-user language for everything a normal user sees.

Each language is one dict in CATALOG. A key missing from a language, or a
language without a catalog yet, falls back to English, so the bot never shows
an empty message and adding a language is a single dict here.
"""

from telegram import InlineKeyboardButton

# code -> (button label, english name, is RTL)
LANGUAGES = [
    ('en', 'English', 'English'),
    ('hi', 'हिन्दी', 'Hindi'),
    ('bn', 'বাংলা', 'Bengali'),
    ('ta', 'தமிழ்', 'Tamil'),
    ('te', 'తెలుగు', 'Telugu'),
    ('mr', 'मराठी', 'Marathi'),
    ('gu', 'ગુજરાતી', 'Gujarati'),
    ('pa', 'ਪੰਜਾਬੀ', 'Punjabi'),
    ('kn', 'ಕನ್ನಡ', 'Kannada'),
    ('ml', 'മലയാളം', 'Malayalam'),
    ('ur', 'اردو', 'Urdu'),
    ('or', 'ଓଡ଼ିଆ', 'Odia'),
    ('as', 'অসমীয়া', 'Assamese'),
    ('ne', 'नेपाली', 'Nepali'),
    ('si', 'සිංහල', 'Sinhala'),
    ('ar', 'العربية', 'Arabic'),
    ('fa', 'فارسی', 'Persian'),
    ('id', 'Bahasa Indonesia', 'Indonesian'),
    ('ms', 'Bahasa Melayu', 'Malay'),
    ('vi', 'Tiếng Việt', 'Vietnamese'),
    ('th', 'ไทย', 'Thai'),
    ('zh', '中文', 'Chinese'),
    ('ja', '日本語', 'Japanese'),
    ('ko', '한국어', 'Korean'),
    ('es', 'Español', 'Spanish'),
    ('fr', 'Français', 'French'),
    ('de', 'Deutsch', 'German'),
    ('pt', 'Português', 'Portuguese'),
    ('it', 'Italiano', 'Italian'),
    ('ru', 'Русский', 'Russian'),
    ('tr', 'Türkçe', 'Turkish'),
    ('pl', 'Polski', 'Polish'),
    ('nl', 'Nederlands', 'Dutch'),
    ('sw', 'Kiswahili', 'Swahili'),
]

# Shown on the first page, in this order.
TOP_LANGUAGES = ['en', 'hi', 'bn', 'ta', 'te', 'mr', 'gu', 'pa']

BUTTONS_PER_PAGE = 8

CATALOG = {
    'en': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'Type the movie name here to search.',
        'no_results': '😕 <b>No movie found</b>',
        'request_it': 'Request it using <code>{command}</code>.',
        'request_ok': '✅ <b>Request Submitted</b>',
        'lbl_movie': '🎥 Movie',
        'lbl_year': '📅 Year',
        'lbl_audio': '🔊 Audio',
        'lbl_quality': '🖥 Quality',
        'lbl_request_id': '📝 Request ID',
        'notify_line': '🕒 We will notify you as soon as it is uploaded.',
        'timer': '⏳ <b>Message Timer</b>',
        'timer_line': '{user}, you can send the next message after <b>{seconds} seconds</b>.',
        'rule_title': '🚫 <b>Group Rule</b>',
        'rule_attachment': 'Attachments (files, videos, music, photos, stickers) are not allowed here.',
        'rule_link': 'Links and channel promotion are not allowed here.',
        'delivered': '✅ File delivered. Enjoy watching!',
        'download_button': '🔗 Click Here To Download Movie',
        'language_title': '🌐 <b>Choose your language</b>',
        'language_saved': '✅ Language saved: <b>{name}</b>',
        'language_more': '🌐 More languages',
        'country_title': (
            '🌍 <b>Select your country</b>\n\n'
            'It shows us which country\'s movies to upload next.'
        ),
        'country_saved': '✅ Country saved: <b>{name}</b>',
        'country_more': '🌍 More countries',
        'country_unknown': '⚠️ That country is not on our list.',
        'number_title': (
            '📱 <b>Share your number</b>\n\n'
            'Tap the button and Telegram asks you once. Nothing is sent without '
            'your press, and only our admins see the list.'
        ),
        'number_shared': '✅ Number saved: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram did not send a number. Please tap the button again.',
        'number_private': '🔓 Open me in a private chat to share your number.',
        'select_country': '🌍 Select Country',
        'share_number': '📱 Share My Number',
        'search_query': '🔎 <b>Search Query</b>',
        'search_result': '🎬 <b>Search Result</b>',
        'search_pages': '📄 <b>Pages</b>',
        'search_files': '<b>{count} files</b>',
        'search_select': '⬇️ Here is your query result, please select',
        'uploader': '📤 Uploaded by',
    },
    'hi': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'मूवी का नाम यहाँ लिखें और खोजें।',
        'no_results': '😕 <b>कोई मूवी नहीं मिली</b>',
        'request_it': '<code>{command}</code> लिखकर मूवी माँगें।',
        'request_ok': '✅ <b>रिक्वेस्ट भेज दी गई</b>',
        'lbl_movie': '🎥 मूवी',
        'lbl_year': '📅 साल',
        'lbl_audio': '🔊 ऑडियो',
        'lbl_quality': '🖥 क्वालिटी',
        'lbl_request_id': '📝 रिक्वेस्ट नंबर',
        'notify_line': '🕒 अपलोड होते ही हम आपको खबर देंगे।',
        'timer': '⏳ <b>संदेश टाइमर</b>',
        'timer_line': '{user}, आप अगला संदेश <b>{seconds} सेकंड</b> बाद भेज सकते हैं।',
        'rule_title': '🚫 <b>ग्रुप नियम</b>',
        'rule_attachment': 'यहाँ फाइल, वीडियो, म्यूजिक, फोटो या स्टिकर भेजना मना है।',
        'rule_link': 'यहाँ लिंक या चैनल प्रमोशन मना है।',
        'delivered': '✅ फाइल मिल गई। मजे से देखिए!',
        'download_button': '🔗 मूवी डाउनलोड करने के लिए क्लिक करें',
        'language_title': '🌐 <b>अपनी भाषा चुनें</b>',
        'language_saved': '✅ भाषा सेव हो गई: <b>{name}</b>',
        'language_more': '🌐 और भाषाएँ',
        'country_title': (
            '🌍 <b>अपना देश चुनें</b>\n\n'
            'इससे हमें पता चलता है कि आगे किस देश की मूवी डालनी है।'
        ),
        'country_saved': '✅ देश सेव हो गया: <b>{name}</b>',
        'country_more': '🌍 और देश',
        'country_unknown': '⚠️ यह देश हमारी सूची में नहीं है।',
        'number_title': (
            '📱 <b>नंबर शेयर करें</b>\n\n'
            'बटन दबाइए, Telegram एक बार पूछेगा। दबाए बिना कुछ नहीं भेजा जाता, '
            'और यह सूची सिर्फ़ एडमिन को दिखती है।'
        ),
        'number_shared': '✅ नंबर सेव हो गया: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram ने नंबर नहीं भेजा। बटन दोबारा दबाएँ।',
        'number_private': '🔓 नंबर भेजने के लिए मुझे private चैट में खोलें।',
        'select_country': '🌍 देश चुनें',
        'share_number': '📱 नंबर शेयर करें',
        'search_query': '🔎 <b>खोज</b>',
        'search_result': '🎬 <b>खोज का नतीजा</b>',
        'search_pages': '📄 <b>पेज</b>',
        'search_files': '<b>{count} फाइलें</b>',
        'search_select': '⬇️ आपकी खोज का नतीजा, चुनिए',
        'uploader': '📤 अपलोडर',
    },
    'bn': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'মুভির নাম এখানে লিখুন।',
        'no_results': '😕 <b>কোনো মুভি পাওয়া যায়নি</b>',
        'request_it': '<code>{command}</code> লিখে মুভি চান।',
        'request_ok': '✅ <b>রিকোয়েস্ট পাঠানো হয়েছে</b>',
        'lbl_movie': '🎥 মুভি',
        'lbl_year': '📅 বছর',
        'lbl_audio': '🔊 অডিও',
        'lbl_quality': '🖥 কোয়ালিটি',
        'lbl_request_id': '📝 রিকোয়েস্ট নম্বর',
        'notify_line': '🕒 আপলোড হওয়ামাত্র আপনাকে জানাব।',
        'timer': '⏳ <b>মেসেজ টাইমার</b>',
        'timer_line': '{user}, আপনি <b>{seconds} সেকেন্ড</b> পরে পরবর্তী মেসেজ পাঠাতে পারবেন।',
        'rule_title': '🚫 <b>গ্রুপের নিয়ম</b>',
        'rule_attachment': 'এখানে ফাইল, ভিডিও, মিউজিক, ফটো বা স্টিকার পাঠানো যাবে না।',
        'rule_link': 'এখানে লিংক বা চ্যানেল প্রমোশন যাবে না।',
        'delivered': '✅ ফাইল পেয়ে গেছেন। উপভোগ করুন!',
        'download_button': '🔗 মুভি ডাউনলোড করতে ক্লিক করুন',
        'language_title': '🌐 <b>আপনার ভাষা বেছে নিন</b>',
        'language_saved': '✅ ভাষা সেভ হয়েছে: <b>{name}</b>',
        'language_more': '🌐 আরও ভাষা',
        'country_title': '🌍 <b>আপনার দেশ বেছে নিন</b>\n\nএতে কোন দেশের মুভি তোলা হবে তা আমরা বুঝতে পারি।',
        'country_saved': '✅ দেশ সেভ হয়েছে: <b>{name}</b>',
        'country_more': '🌍 আরও দেশ',
        'country_unknown': '⚠️ এই দেশ আমাদের তালিকায় নেই।',
        'number_title': '📱 <b>নম্বর শেয়ার করুন</b>\n\nবটনটি চাপুন, Telegram একবার জিজ্ঞেস করবে। না চাপা পর্যন্ত কিছু পাঠানো হয় না, আর তালিকা শুধু অ্যাডমিন দেখেন।',
        'number_shared': '✅ নম্বর সেভ হয়েছে: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram নম্বর পাঠায়নি। বটন আবার চাপুন।',
        'number_private': '🔓 নম্বর পাঠাতে আমাকে private চ্যাটে খুলুন।',
        'select_country': '🌍 দেশ বেছে নিন',
        'share_number': '📱 নম্বর শেয়ার করুন',
        'search_query': '🔎 <b>খোঁজা শব্দ</b>',
        'search_result': '🎬 <b>খোঁজার ফলাফল</b>',
        'search_pages': '📄 <b>পেজ</b>',
        'search_files': '<b>{count}টি ফাইল</b>',
        'search_select': '⬇️ আপনার খোঁজার ফল, বেছে নিন',
        'uploader': '📤 আপলোড করেছে',
    },
    'ta': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'படத்தின் பெயரை இங்கே தட்டச்சு செய்யுங்கள்.',
        'no_results': '😕 <b>படம் எதுவும் இல்லை</b>',
        'request_it': '<code>{command}</code> என்று எழுதி படம் கேளுங்கள்.',
        'request_ok': '✅ <b>கோரிக்கை அனுப்பப்பட்டது</b>',
        'lbl_movie': '🎥 படம்',
        'lbl_year': '📅 ஆண்டு',
        'lbl_audio': '🔊 ஒலி',
        'lbl_quality': '🖥 தரம்',
        'lbl_request_id': '📝 கோரிக்கை எண்',
        'notify_line': '🕒 பதிவேற்றம் ஆனவுடன் உங்களுக்கு தெரிவிப்போம்.',
        'timer': '⏳ <b>செய்தி நேரம்</b>',
        'timer_line': '{user}, அடுத்த செய்தியை <b>{seconds} வினாடிகள்</b> பிறகு அனுப்பலாம்.',
        'rule_title': '🚫 <b>குழு விதி</b>',
        'rule_attachment': 'இங்கே ஃபைல், வீடியோ, பாடல், போটோ, ஸ்டிக்கர் அனுப்பக்கூடாது.',
        'rule_link': 'இங்கே லிங்க் அல்லது சேனல் விளம்பரம் கூடாது.',
        'delivered': '✅ ஃபைல் கிடைத்தது. ரசியுங்கள்!',
        'download_button': '🔗 படத்தை பதிவிறக்க கிளிக் செய்யுங்கள்',
        'language_title': '🌐 <b>உங்கள் மொழியை தேர்வு செய்யுங்கள்</b>',
        'language_saved': '✅ மொழி சேமிக்கப்பட்டது: <b>{name}</b>',
        'language_more': '🌐 மேலும் மொழிகள்',
        'country_title': '🌍 <b>உங்கள் நாட்டைத் தேர்ந்தெடுக்கவும்</b>\n\nஎந்த நாட்டுப் படங்களை அடுத்தது ஏற்ற வேண்டும் என்பதை இது சொல்லும்.',
        'country_saved': '✅ நாடு சேமிக்கப்பட்டது: <b>{name}</b>',
        'country_more': '🌍 மேலும் நாடுகள்',
        'country_unknown': '⚠️ இந்த நாடு எங்கள் பட்டியலில் இல்லை.',
        'number_title': '📱 <b>உங்கள் எண்ணைப் பகிரவும்</b>\n\nபட்டனை அழுத்தினால் Telegram ஒரு முறை கேட்கும். அழுத்தும் வரை எதுவும் செல்லாது; பட்டியலை நிர்வாகிகள் மட்டுமே பார்ப்பார்கள்.',
        'number_shared': '✅ எண் சேமிக்கப்பட்டது: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram எண்ணை அனுப்பவில்லை. பட்டனை மீண்டும் அழுத்தவும்.',
        'number_private': '🔓 எண்ணைப் பகிர என்னை தனிப்பட்ட உரையாடலில் திறக்கவும்.',
        'select_country': '🌍 நாட்டைத் தேர்வு',
        'share_number': '📱 எண்ணைப் பகிரவும்',
        'search_query': '🔎 <b>தேடல்</b>',
        'search_result': '🎬 <b>தேடல் முடிவு</b>',
        'search_pages': '📄 <b>பக்கங்கள்</b>',
        'search_files': '<b>{count} ஃபைல்கள்</b>',
        'search_select': '⬇️ தேடல் முடிவுகள், தேர்வு செய்யுங்கள்',
        'uploader': '📤 பதிவேற்றியவர்',
    },
    'te': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'సినిమా పేరును ఇక్కడ టైప్ చేయండి.',
        'no_results': '😕 <b>సినిమా దొరకలేదు</b>',
        'request_it': '<code>{command}</code> అని టైప్ చేసి సినిమా అడగండి.',
        'request_ok': '✅ <b>అభ్యర్థన పంపబడింది</b>',
        'lbl_movie': '🎥 సినిమా',
        'lbl_year': '📅 సంవత్సరం',
        'lbl_audio': '🔊 ఆడియో',
        'lbl_quality': '🖥 నాణ్యత',
        'lbl_request_id': '📝 అభ్యర్థన నంబర్',
        'notify_line': '🕒 అప్‌లోడ్ అయిన వెంటనే తెలియజేస్తాం.',
        'timer': '⏳ <b>సందేశ టైమర్</b>',
        'timer_line': '{user}, తదుపరి సందేశాన్ని <b>{seconds} సెకన్ల</b> తర్వాత పంపవచ్చు.',
        'rule_title': '🚫 <b>గ్రూప్ నియమం</b>',
        'rule_attachment': 'ఇక్కడ ఫైల్, వీడియో, మ్యూజిక్, ఫోటో, స్టికర్ పంపకూడదు.',
        'rule_link': 'ఇక్కడ లింక్, ఛానెల్ ప్రమోషన్ ఖచ్చితంగా నిషేధం.',
        'delivered': '✅ ఫైల్ వచ్చింది. ఆనందించండి!',
        'download_button': '🔗 సినిమా డౌన్‌లోడ్ కోసం క్లిక్ చేయండి',
        'language_title': '🌐 <b>మీ భాష ఎంచుకోండి</b>',
        'language_saved': '✅ భాష సేవ్ అయింది: <b>{name}</b>',
        'language_more': '🌐 మరింత భాషలు',
        'country_title': '🌍 <b>మీ దేశాన్ని ఎంచుకోండి</b>\n\nతదుపరి ఏ దేశ సినిమాలు అప్\u200cలోడ్ చేయాలో ఇది మాకు చెబుతుంది.',
        'country_saved': '✅ దేశం సేవ్ అయింది: <b>{name}</b>',
        'country_more': '🌍 మరిన్ని దేశాలు',
        'country_unknown': '⚠️ ఆ దేశం మా జాబితాలో లేదు.',
        'number_title': '📱 <b>మీ నంబర్ షేర్ చేయండి</b>\n\nబటన్ నొక్కితే Telegram ఒకసారి అడుగుతుంది. నొక్కేవరకు ఏమీ పంపబడదు, జాబితా అడ్మిన్\u200cలకు మాత్రమే కనిపిస్తుంది.',
        'number_shared': '✅ నంబర్ సేవ్ అయింది: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram నంబర్ పంపలేదు. బటన్ మళ్లీ నొక్కండి.',
        'number_private': '🔓 నంబర్ పంపడానికి నన్ను ప్రైవేట్ చాట్\u200cలో ఓపెన్ చేయండి.',
        'select_country': '🌍 దేశం ఎంచుకోండి',
        'share_number': '📱 నంబర్ షేర్ చేయండి',
        'search_query': '🔎 <b>శోధన</b>',
        'search_result': '🎬 <b>శోధన ఫలితం</b>',
        'search_pages': '📄 <b>పేజీలు</b>',
        'search_files': '<b>{count} ఫైల్స్</b>',
        'search_select': '⬇️ మీ శోధన ఫలితాలు, ఎంచుకోండి',
        'uploader': '📤 అప్‌లోడ్ చేసినవారు',
    },
    'mr': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'इथे सिनेमाचं नाव लिहा.',
        'no_results': '😕 <b>सिनेमा सापडला नाही</b>',
        'request_it': '<code>{command}</code> लिहून सिनेमा मागा.',
        'request_ok': '✅ <b>विनंती पाठवली</b>',
        'lbl_movie': '🎥 सिनेमा',
        'lbl_year': '📅 वर्ष',
        'lbl_audio': '🔊 ऑडिओ',
        'lbl_quality': '🖥 क्वालिटी',
        'lbl_request_id': '📝 विनंती क्रमांक',
        'notify_line': '🕒 अपलोड होताच आम्ही तुम्हाला कळवू.',
        'timer': '⏳ <b>संदेश टाइमर</b>',
        'timer_line': '{user}, तुम्ही पुढचा संदेश <b>{seconds} सेकंदांनंतर</b> पाठवू शकता.',
        'rule_title': '🚫 <b>ग्रुप नियम</b>',
        'rule_attachment': 'इथे फाइल, व्हिडिओ, म्युझिक, फोटो किंवा स्टिकर चालत नाही.',
        'rule_link': 'इथे लिंक किंवा चॅनेल प्रमोशन चालत नाही.',
        'delivered': '✅ फाइल मिळाली. आनंद घ्या!',
        'download_button': '🔗 सिनेमा डाउनलोड करण्यासाठी क्लिक करा',
        'language_title': '🌐 <b>तुमची भाषा निवडा</b>',
        'language_saved': '✅ भाषा जतन झाली: <b>{name}</b>',
        'language_more': '🌐 आणखी भाषा',
        'country_title': '🌍 <b>तुमचा देश निवडा</b>\n\nपुढे कोणत्या देशातील चित्रपट टाकावेत हे त्यावरून कळते.',
        'country_saved': '✅ देश जतन झाला: <b>{name}</b>',
        'country_more': '🌍 अधिक देश',
        'country_unknown': '⚠️ हा देश आमच्या यादीत नाही.',
        'number_title': '📱 <b>तुमचा नंबर शेअर करा</b>\n\nबटन दाबल्यास Telegram एकदा विचारेल. दाबेपर्यंत काहीही पाठवत नाही, यादी फक्त अ\u200dॅडमिनला दिसते.',
        'number_shared': '✅ नंबर जतन झाला: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram ने नंबर पाठवला नाही. बटन पुन्हा दाबा.',
        'number_private': '🔓 नंबर पाठवण्यासाठी मला प्रायव्हेट चॅटमध्ये उघडा.',
        'select_country': '🌍 देश निवडा',
        'share_number': '📱 नंबर शेअर करा',
        'search_query': '🔎 <b>शोध</b>',
        'search_result': '🎬 <b>शोधाचा निकाल</b>',
        'search_pages': '📄 <b>पाने</b>',
        'search_files': '<b>{count} फाइल्स</b>',
        'search_select': '⬇️ शोधाचे निकाल, निवडा',
        'uploader': '📤 अपलोडकर्ता',
    },
    'gu': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'અહીં મૂવીનું નામ લખો.',
        'no_results': '😕 <b>કોઈ મૂવી મળી નથી</b>',
        'request_it': '<code>{command}</code> લખીને મૂવી માંગો.',
        'request_ok': '✅ <b>વીનંતી મોકલાઈ</b>',
        'lbl_movie': '🎥 મૂવી',
        'lbl_year': '📅 વર્ષ',
        'lbl_audio': '🔊 ઓડિયો',
        'lbl_quality': '🖥 ક્વોલિટી',
        'lbl_request_id': '📝 વીનંતી નંબર',
        'notify_line': '🕒 અપલોડ થાય એટલે અમે જણાવીશું.',
        'timer': '⏳ <b>સંદેશ ટાઇમર</b>',
        'timer_line': '{user}, તમે પછીનો સંદેશ <b>{seconds} સેકંડ</b> પછી મોકલી શકો.',
        'rule_title': '🚫 <b>ગ્રુપ નિયમ</b>',
        'rule_attachment': 'અહીં ફાઇલ, વીડિયો, મ્યુઝિક, ફોટો કે સ્ટિકર મોકલી શકાતા નથી.',
        'rule_link': 'અહીં લિંક કે ચેનલ પ્રમોશન ચાલે નહીં.',
        'delivered': '✅ ફાઇલ મળી ગઈ. આનંદ લો!',
        'download_button': '🔗 મૂવી ડાઉનલોડ કરવા ક્લિક કરો',
        'language_title': '🌐 <b>તમારી ભાષા પસંદ કરો</b>',
        'language_saved': '✅ ભાષા સેવ થઈ: <b>{name}</b>',
        'language_more': '🌐 વધુ ભાષાઓ',
        'country_title': '🌍 <b>તમારો દેશ પસંદ કરો</b>\n\nઆગળ કયા દેશની મૂવી નાખવી તે સમજાય.',
        'country_saved': '✅ દેશ સેવ થયો: <b>{name}</b>',
        'country_more': '🌍 વધુ દેશો',
        'country_unknown': '⚠️ આ દેશ અમારી યાદીમાં નથી.',
        'number_title': '📱 <b>તમારો નંબર શેર કરો</b>\n\nબટન દબાવો એટલે Telegram એક વાર પૂછશે. ન દબાવ્યાર કંઈ જવાતું નથી, યાદી માત્ર એડમિન જુએ છે.',
        'number_shared': '✅ નંબર સેવ થયો: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram એ નંબર મોકલ્યો નથી. બટન ફરી દબાવો.',
        'number_private': '🔓 નંબર મોકલવા માટે મને પ્રાઇવેટ ચેટમાં ખોલો.',
        'select_country': '🌍 દેશ પસંદ કરો',
        'share_number': '📱 નંબર શેર કરો',
        'search_query': '🔎 <b>શોધ</b>',
        'search_result': '🎬 <b>શોધ પરિણામ</b>',
        'search_pages': '📄 <b>પાનાં</b>',
        'search_files': '<b>{count} ફાઇલો</b>',
        'search_select': '⬇️ શોધના પરિણામ, પસંદ કરો',
        'uploader': '📤 અપલોડર',
    },
    'pa': {
        'brand': '🎬 <b>Cinema Kingdom</b>',
        'search_hint': 'ਇੱਥੇ ਫ਼ਿਲਮ ਦਾ ਨਾਂ ਲਿਖੋ।',
        'no_results': '😕 <b>ਕੋਈ ਫ਼ਿਲਮ ਨਹੀਂ ਮਿਲੀ</b>',
        'request_it': '<code>{command}</code> ਲਿਖ ਕੇ ਫ਼ਿਲਮ ਮੰਗੋ।',
        'request_ok': '✅ <b>ਬੇਨਤੀ ਭੇਜੀ ਗਈ</b>',
        'lbl_movie': '🎥 ਫ਼ਿਲਮ',
        'lbl_year': '📅 ਸਾਲ',
        'lbl_audio': '🔊 ਆਡੀਓ',
        'lbl_quality': '🖥 ਕੁਆਲਿਟੀ',
        'lbl_request_id': '📝 ਬੇਨਤੀ ਨੰਬਰ',
        'notify_line': '🕒 ਅੱਪਲੋਡ ਹੁੰਦੇ ਹੀ ਤੁਨੂੰ ਸੂਚਿਤ ਕਰਾਂਗੇ।',
        'timer': '⏳ <b>ਸੁਨੇਹਾ ਟਾਈਮਰ</b>',
        'timer_line': '{user}, ਤੁਸੀਂ ਅਗਲਾ ਸੁਨੇਹਾ <b>{seconds} ਸਕਿੰਟ</b> ਬਾਅਦ ਭੇਜ ਸਕਦੇ ਹੋ।',
        'rule_title': '🚫 <b>ਗਰੁੱਪ ਨਿਯਮ</b>',
        'rule_attachment': 'ਇੱਥੇ ਫ਼ਾਈਲ, ਵੀਡੀਓ, ਮਿਊਜ਼ਿਕ, ਫ਼ੋਟੋ ਜਾਂ ਸਟਿੱਕਰ ਨਹੀਂ ਭੇਜ ਸਕਦੇ।',
        'rule_link': 'ਇੱਥੇ ਲਿੰਕ ਜਾਂ ਚੈਨਲ ਪ੍ਰਮੋਸ਼ਨ ਵਰਜਿਤ ਹੈ।',
        'delivered': '✅ ਫ਼ਾਈਲ ਮਿਲ ਗਈ। ਆਨੰਦ ਲਓ!',
        'download_button': '🔗 ਫ਼ਿਲਮ ਡਾਊਨਲੋਡ ਕਰਨ ਲਈ ਕਲਿੱਕ ਕਰੋ',
        'language_title': '🌐 <b>ਆਪਣੀ ਭਾਸ਼ਾ ਚੁਣੋ</b>',
        'language_saved': '✅ ਭਾਸ਼ਾ ਸੇਵ ਹੋਈ: <b>{name}</b>',
        'language_more': '🌐 ਹੋਰ ਭਾਸ਼ਾਵਾਂ',
        'country_title': '🌍 <b>ਆਪਣਾ ਦੇਸ਼ ਚੁਣੋ</b>\n\nਅੱਗੇ ਕਿਸ ਦੇਸ਼ ਦੀ ਫ਼ਿਲਮ ਪਾਉਣੀ ਹੈ, ਇਹ ਉਸ ਦੱਸਦਾ ਹੈ।',
        'country_saved': '✅ ਦੇਸ਼ ਸੇਵ ਹੋਿਆ: <b>{name}</b>',
        'country_more': '🌍 ਹੋਰ ਦੇਸ਼',
        'country_unknown': '⚠️ ਇਹ ਦੇਸ਼ ਸਾਡੀ ਸੂਚੀ ਵਿੱਚ ਨਹੀਂ।',
        'number_title': '📱 <b>ਆਪਣਾ ਨੰਬਰ ਸਾਂਝਾ ਕਰੋ</b>\n\nਬਟਨ ਦਬਾਓ ਤੇ Telegram ਇੱਕ ਵਾਰ ਪੁੱਛੇਗਾ। ਦਬਾਉਣ ਤੱਕ ਕੁਝ ਨਹੀਂ ਜਾਂਦਾ, ਸੂਚੀ ਸਿਰਫ਼ ਐਡਮਿਨ ਵੇਖਦੇ ਹਨ।',
        'number_shared': '✅ ਨੰਬਰ ਸੇਵ ਹੋਇਆ: <code>{phone}</code>',
        'number_failed': '⚠️ Telegram ਨੇ ਨੰਬਰ ਨਹੀਂ ਭੇਜਿਆ। ਬਟਨ ਦੁਬਾਰਾ ਦਬਾਓ।',
        'number_private': '🔓 ਨੰਬਰ ਭੇਜਣ ਲਈ ਮੈਨੂੰ private ਚੈੱਟ ਵਿੱਚ ਖੋਲ੍ਹੋ।',
        'select_country': '🌍 ਦੇਸ਼ ਚੁਣੋ',
        'share_number': '📱 ਨੰਬਰ ਸਾਂਝਾ ਕਰੋ',
        'search_query': '🔎 <b>ਖੋਜ</b>',
        'search_result': '🎬 <b>ਖੋਜ ਦਾ ਨਤੀਜਾ</b>',
        'search_pages': '📄 <b>ਸਫ਼ੇ</b>',
        'search_files': '<b>{count} ਫ਼ਾਈਲਾਂ</b>',
        'search_select': '⬇️ ਖੋਜ ਦੇ ਨਤੀਜੇ, ਚੁਣੋ',
        'uploader': '📤 ਅੱਪਲੋਡ ਕਰਤਾ',
    },
}

NAMES = {code: native for code, native, _ in LANGUAGES}

# Second block of strings, kept together so a language is still one place to
# extend. Missing keys fall back to English inside t().
_EXTRA = {
    'en': {
        'request_hint': '🎥 <b>Request a movie</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nExample: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>Please wait</b>',
        'wait_line': 'You can search again in <b>{seconds} seconds</b>.',
        'private_search': '🔒 <b>Private Search Disabled</b>\n\nUse the Cinema Kingdom group to search.',
        'adult_title': '🔞 <b>Age Confirmation Required</b>',
        'adult_line': 'This search may contain 18+ content. Confirm that you are 18 or above.',
        'download_link': '🔗 Generate Download Link',
        'movie_details': 'ℹ️ Movie Details',
        'movie_hint': 'Click below to generate the download link.',
        'validity': '⏳ Link validity: 5 minutes.',
        'link_expired': '❌ <b>Link expired</b>\n\nGenerate a new download link.',
        'invalid_link': '❌ <b>Invalid movie link.</b>',
        'not_found': '❌ <b>Movie not found or deleted.</b>',
        'join_channel': '📢 Join Channel',
        'join_group': '👥 Join Group',
        'joined_yes': "✅ I've Joined",
        'adult_yes': '✅ I am 18 or above',
        'adult_no': '❌ I am under 18',
        'access_title': '🔒 <b>Access Restricted</b>',
        'access_line': 'Join the official channel and community group first, then press <b>I\'ve Joined</b>.',
    },
    'hi': {
        'request_hint': '🎥 <b>मूवी माँगें</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nउदाहरण: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>कृपया रुकें</b>',
        'wait_line': 'आप <b>{seconds} सेकंड</b> बाद फिर खोज सकते हैं।',
        'private_search': '🔒 <b>निजी खोज बंद है</b>\n\nखोजने के लिए Cinema Kingdom ग्रुप में लिखें।',
        'adult_title': '🔞 <b>उम्र की पुष्टि चाहिए</b>',
        'adult_line': 'इस खोज में 18+ सामग्री हो सकती है। पुष्टि करें कि आपकी उम्र 18 या उससे अधिक है।',
        'movie_hint': 'डाउनलोड लिंक बनाने के लिए नीचे बटन दबाएँ।',
        'validity': '⏳ लिंक की मान्यता: 5 मिनट।',
        'link_expired': '❌ <b>लिंक खत्म हो गया</b>\n\nनई डाउनलोड लिंक बनाएँ।',
        'invalid_link': '❌ <b>गलत मूवी लिंक।</b>',
        'not_found': '❌ <b>मूवी नहीं मिली या हटा दी गई।</b>',
        'join_channel': '📢 चैनल जॉइन करें',
        'join_group': '👥 ग्रुप जॉइन करें',
        'joined_yes': '✅ मैंने जॉइन कर लिया',
        'adult_yes': '✅ मेरी उम्र 18+ है',
        'adult_no': '❌ मेरी उम्र 18 से कम',
        'access_title': '🔒 <b>पहुँच सीमित है</b>',
        'access_line': 'पहले आधिकारिक चैनल और कम्युनिटी ग्रुप जॉइन करें, फिर <b>मैंने जॉइन कर लिया</b> दबाएँ।',
    },
    'bn': {
        'request_hint': '🎥 <b>মুভি চান</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nউদাহরণ: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>একটু থামুন</b>',
        'wait_line': 'আপনি <b>{seconds} সেকেন্ড</b> পরে আবার খুঁজতে পারবেন।',
        'private_search': '🔒 <b>প্রাইভেট সার্চ বন্ধ</b>\n\nখুঁজতে Cinema Kingdom গ্রুপে লিখুন।',
        'adult_title': '🔞 <b>বয়স নিশ্চিত করুন</b>',
        'adult_line': 'এই খোঁজে ১৮+ বিষয়বস্তু থাকতে পারে। আপনার বয়স ১৮ বা তার বেশি নিশ্চিত করুন।',
        'movie_hint': 'ডাউনলোড লিংক তৈরি করতে নিচের বোতামে চাপ দিন।',
        'validity': '⏳ লিংকের মেয়াদ: ৫ মিনিট।',
        'link_expired': '❌ <b>লিংকের মেয়াদ শেষ</b>\n\nনতুন ডাউনলোড লিংক তৈরি করুন।',
        'invalid_link': '❌ <b>ভুল মুভি লিংক।</b>',
        'not_found': '❌ <b>মুভি পাওয়া যায়নি বা মুছে দেওয়া হয়েছে।</b>',
        'join_channel': '📢 চ্যানেলে যোগ দিন',
        'join_group': '👥 গ্রুপে যোগ দিন',
        'joined_yes': '✅ আমি যোগ দিয়েছি',
        'adult_yes': '✅ আমার বয়স ১৮+',
        'adult_no': '❌ আমার বয়স ১৮-এর কম',
        'access_title': '🔒 <b>প্রবেশ সীমিত</b>',
        'access_line': 'আগে অফিসিয়াল চ্যানেল ও কমিউনিটি গ্রুপে যোগ দিন, তারপর <b>আমি যোগ দিয়েছি</b> চাপুন।',
    },
    'ta': {
        'request_hint': '🎥 <b>படம் கேளுங்கள்</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nஎடுத்துக்காட்டு: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>சற்று நேரம் பொறுக்கவும்</b>',
        'wait_line': '<b>{seconds} வினாடிகள்</b> கழிவு மீண்டும் தேடலாம்.',
        'private_search': '🔒 <b>தனிப்பட்ட தேடல் இல்லை</b>\n\nதேட Cinema Kingdom குழுவில் எழுதுங்கள்.',
        'adult_title': '🔞 <b>வயது உறுதி தேவை</b>',
        'adult_line': 'இந்த தேடலில் 18+ உள்ளடக்கம் இருக்கலாம். உங்கள் வயது 18 அல்லது அதற்கு மேல் என உறுதிப்படுத்தவும்.',
        'movie_hint': 'பதிவிறக்க இணையத்தை உருவாக்க கீழே உள்ள பொத்தானை அழுத்தவும்.',
        'validity': '⏳ இணையத்தின் நேரம்: 5 நிமிடம்.',
        'link_expired': '❌ <b>இணையத்தின் நேரம் முடிந்தது</b>\n\nபுதிய பதிவிறக்க இணையத்தை உருவாக்கவும்.',
        'invalid_link': '❌ <b>தவறான பட இணையம்.</b>',
        'not_found': '❌ <b>படம் இல்லை அல்லது நீக்கப்பட்டது.</b>',
        'join_channel': '📢 சேனலில் இணையவும்',
        'join_group': '👥 குழுவில் இணையவும்',
        'joined_yes': '✅ நான் இணைந்தேன்',
        'adult_yes': '✅ எனக்கு வயது 18+',
        'adult_no': '❌ எனக்கு வயது 18 குறைவு',
        'access_title': '🔒 <b>அணுகல் தடை</b>',
        'access_line': 'முதலில் அதிகாரப்பூர்வ சேனல் மற்றும் குழுவில் இணைந்த பின் <b>நான் இணைந்தேன்</b> பொத்தானை அழுத்தவும்.',
    },
    'te': {
        'request_hint': '🎥 <b>సినిమా అడగండి</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nఉదాహరణ: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>కొంతసేపు ఆగండి</b>',
        'wait_line': '<b>{seconds} సెకన్ల</b> తర్వాత మళ్లీ శోధించవచ్చు.',
        'private_search': '🔒 <b>వ్యక్తిగత శోధన బంద్</b>\n\nశోధించడానికి Cinema Kingdom గ్రూప్‌లో రాయండి.',
        'adult_title': '🔞 <b>వయస్సు నిర్ధారణ అవసరం</b>',
        'adult_line': 'ఈ శోధనలో 18+ కంటెంట్ ఉండవచ్చు. మీ వయస్సు 18 పైన ఉన్నదని నిర్ధారించండి.',
        'movie_hint': 'డాउन‌లోడ్ లింక్ రావడానికి క్రింద బటన్ నొక్కండి.',
        'validity': '⏳ లింక్ గడువు: 5 నిమిషాలు.',
        'link_expired': '❌ <b>లింక్ గడువు ముగిసింది</b>\n\nకొత్త డాउन‌లోడ్ లింక్ తయారు చేయండి.',
        'invalid_link': '❌ <b>తప్పు సినిమా లింక్.</b>',
        'not_found': '❌ <b>సినిమా దొరకలేదు లేదా తీసివేయబడింది.</b>',
        'join_channel': '📢 ఛానెల్‌లో చేరండి',
        'join_group': '👥 గ్రూప్‌లో చేరండి',
        'joined_yes': '✅ నేను చేరాను',
        'adult_yes': '✅ నా వయసు 18+',
        'adult_no': '❌ నా వయసు 18 క్రింద',
        'access_title': '🔒 <b>యాక్సెస్ నిర్బంధం</b>',
        'access_line': 'ముందు అధికారిక ఛానెల్, కమ్యూనిటీ గ్రూప్‌లలో చేరి తర్వాత <b>నేను చేరాను</b> నొక్కండి.',
    },
    'mr': {
        'request_hint': '🎥 <b>सिनेमा मागा</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nउदाहरण: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>कृपया थांबा</b>',
        'wait_line': 'तुम्ही <b>{seconds} सेकंदांनंतर</b> पुन्हा शोधू शकता.',
        'private_search': '🔒 <b>खाजगी शोध बंद</b>\n\nशोधसाठी Cinema Kingdom ग्रुपमध्ये लिहा.',
        'adult_title': '🔞 <b>वय पुष्टी आवश्यक</b>',
        'adult_line': 'या शोधात १८+ मजकूर असू शकतो. तुमचे वय १८ किंवा त्यापेक्षा जास्त असल्याचे निश्चित करा.',
        'movie_hint': 'डाउनलोड लिंक बनवण्यासाठी खालील बटण दाबा.',
        'validity': '⏳ लिंक वैधता: 5 मिनिटे.',
        'link_expired': '❌ <b>लिंकची मुदत संपली</b>\n\nनवीन डाउनलोड लिंक बनवा.',
        'invalid_link': '❌ <b>चुकीचा सिनेमा लिंक.</b>',
        'not_found': '❌ <b>सिनेमा सापडला नाही किंवा वगळला आहे.</b>',
        'join_channel': '📢 चॅनेल जॉइन करा',
        'join_group': '👥 ग्रुप जॉइन करा',
        'joined_yes': '✅ मी जॉइन केले',
        'adult_yes': '✅ मला वय 18+ आहे',
        'adult_no': '❌ मला वय 18 पेक्षा कमी',
        'access_title': '🔒 <b>प्रवेश मर्यादित</b>',
        'access_line': 'प्रथम अधिकृत चॅनेल आणि कम्युनिटी ग्रुप जॉइन करा, मग <b>मी जॉइन केले</b> दाबा.',
    },
    'gu': {
        'request_hint': '🎥 <b>મૂવી માંગો</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nઉદાહરણ: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>કૃપા કરીને રોકાઓ</b>',
        'wait_line': 'તમે <b>{seconds} સેકંડ</b> પછી ફરી શોધી શકો.',
        'private_search': '🔒 <b>ખાનગી શોધ બંધ</b>\n\nશોધ માટે Cinema Kingdom ગ્રુપમાં લખો.',
        'adult_title': '🔞 <b>વયની ખાતરી જરૂરી</b>',
        'adult_line': 'આ શોધમાં 18+ સામગ્રી હોઈ શકે છે. તમારી ઉંમર 18 કે તેથી વધુ હોવાનું સતયિકિત કરો.',
        'movie_hint': 'ડાઉનલોડ લિંક બનાવવા માટે નીચેનું બટન દબાવો.',
        'validity': '⏳ લિંકની માન્યતા: 5 મિનિટ.',
        'link_expired': '❌ <b>લિંકની મુદત પૂરી થઈ</b>\n\nનવી ડાઉનલોડ લિંક બનાવો.',
        'invalid_link': '❌ <b>ખોટો મૂવી લિંક.</b>',
        'not_found': '❌ <b>મૂવી મળી નથી અથવા કાઢી નાખી છે.</b>',
        'join_channel': '📢 ચેનલમાં જોડાઓ',
        'join_group': '👥 ગ્રુપમાં જોડાઓ',
        'joined_yes': '✅ મેં જોડાઈ ગયો',
        'adult_yes': '✅ મને ઉંમર 18+ છે',
        'adult_no': '❌ મને ઉંમર 18 થી ઓછી',
        'access_title': '🔒 <b>એક્સેસ પ્રતિબંધિત</b>',
        'access_line': 'પહેલા ઓફિશિયલ ચેનલ અને કમ્યુનિટી ગ્રુપમાં જોડાઓ, પછી <b>મેં જોડાઈ ગયો</b> દબાવો.',
    },
    'pa': {
        'request_hint': '🎥 <b>ਫ਼ਿਲਮ ਮੰਗੋ</b>\n\n<code>/request Movie Name - Year - Audio Language - Resolution</code>\nਉਦਾਹਰਨ: <code>/request Don - 2002 - Hindi - 1080p</code>',
        'wait': '⏳ <b>ਸ਼ਰਧਾ ਨਾਲ ਰੁਕੋ</b>',
        'wait_line': 'ਤੁਸੀਂ <b>{seconds} ਸਕਿੰਟ</b> ਬਾਅਦ ਦੁਬਾਰਾ ਖੋਜ ਸਕਦੇ ਹੋ।',
        'private_search': '🔒 <b>ਨਿੱਜੀ ਖੋਜ ਬੰਦ ਹੈ</b>\n\nਖੋਜ ਲਈ Cinema Kingdom ਗਰੁੱਪ ਵਿੱਚ ਲਿਖੋ।',
        'adult_title': '🔞 <b>ਉਮਰ ਦੀ ਪੁਸ਼ਟੀ ਲੋੜੀਂਦੀ</b>',
        'adult_line': 'ਇਸ ਖੋਜ ਵਿੱਚ 18+ ਸਮੱਗਰੀ ਹੋ ਸਕਦੀ ਹੈ। ਪੁਸ਼ਟੀ ਕਰੋ ਕਿ ਤੁਹਾਡੀ ਉਮਰ 18 ਜਾਂ ਇਸ ਤੋਂ ਵੱਧ ਹੈ।',
        'movie_hint': 'ਡਾਊਨਲੋਡ ਲਿੰਕ ਬਣਾਉਣ ਲਈ ਹੇਠਾਂ ਦਿੱਤੇ ਬਟਨ ਨੂੰ ਦਬਾਓ।',
        'validity': '⏳ ਲਿੰਕ ਦੀ ਮਿਆਦ: 5 ਮਿੰਟ।',
        'link_expired': '❌ <b>ਲਿੰਕ ਦੀ ਮਿਆਦ ਪੁੱਗ ਗਈ</b>\n\nਨਵਾਂ ਡਾਊਨਲੋਡ ਲਿੰਕ ਬਣਾਓ।',
        'invalid_link': '❌ <b>ਗਲਤ ਫ਼ਿਲਮ ਲਿੰਕ.</b>',
        'not_found': '❌ <b>ਫ਼ਿਲਮ ਨਹੀਂ ਮਿਲੀ ਜਾਂ ਹਟਾ ਦਿੱਤੀ ਗਈ ਹੈ.</b>',
        'join_channel': '📢 ਚੈਨਲ ਵਿੱਚ ਜੁੜੋ',
        'join_group': '👥 ਗਰੁੱਪ ਵਿੱਚ ਜੁੜੋ',
        'joined_yes': '✅ ਮੈਂ ਜੁੜ ਗਿਆ',
        'adult_yes': '✅ ਮੈਨੂੰ ਉਮਰ 18+ ਹੈ',
        'adult_no': '❌ ਮੈਨੂੰ ਉਮਰ 18 ਤੋਂ ਘੱਟ',
        'access_title': '🔒 <b>ਐਕਸੈਸ ਸੀਮਤ ਹੈ</b>',
        'access_line': 'ਪਹਿਲਾਂ ਅਧਿਕਾਰਤ ਚੈਨਲ ਅਤੇ ਕਮਿਊਨਿਟੀ ਗਰੁੱਪ ਵਿੱਚ ਜੁੜੋ, ਫਿਰ <b>ਮੈਂ ਜੁੜ ਗਿਆ</b> ਦਬਾਓ।',
    },
}

for _code, _entries in _EXTRA.items():
    CATALOG[_code].update(_entries)

# Third block: button confirmations and membership replies.
_BUTTON_MESSAGES = {
    'en': {
        'adult_blocked': '🔞 <b>Not allowed</b>\n\nThis search is only for users aged 18 or above.',
        'expired_confirm': '❌ <b>Expired</b>\n\nThis age confirmation is no longer valid.',
        'join_ok': '✅ <b>Verification successful</b>\n\nSend <code>/start</code> again to continue.',
        'join_pending': '❌ <b>Not joined yet</b>\n\nJoin both the channel and the group first.',
    },
    'hi': {
        'adult_blocked': '🔞 <b>अनुमति नहीं</b>\n\nयह खोज केवल 18 या उससे अधिक उम्र के लिए है।',
        'expired_confirm': '❌ <b>समय समाप्त</b>\n\nयह उम्र पुष्टि अब मान्य नहीं है।',
        'join_ok': '✅ <b>जाँच सफल</b>\n\nजारी रखने के लिए फिर <code>/start</code> भेजें।',
        'join_pending': '❌ <b>अभी जॉइन नहीं किया</b>\n\nपहले चैनल और ग्रुप दोनों जॉइन करें।',
    },
    'bn': {
        'adult_blocked': '🔞 <b>অনুমতি নেই</b>\n\nএই খোঁজ শুধু ১৮ বা তার বেশি বয়সীদের জন্য।',
        'expired_confirm': '❌ <b>মেয়াদ শেষ</b>\n\nএই বয়স নিশ্চিতকরণ এখন আর বৈধ নয়।',
        'join_ok': '✅ <b>যাচাই সফল</b>\n\nচালিয়ে যেতে আবার <code>/start</code> পাঠান।',
        'join_pending': '❌ <b>এখনও যোগ দেননি</b>\n\nআগে চ্যানেল ও গ্রুপ দুটিতেই যোগ দিন।',
    },
    'ta': {
        'adult_blocked': '🔞 <b>அனுமதி இல்லை</b>\n\nஇந்த தேடல் 18+ வயதினருக்கு மட்டும்.',
        'expired_confirm': '❌ <b>காலாவதி</b>\n\nஇந்த வயது உறுதி இப்போது செல்லாது.',
        'join_ok': '✅ <b>சரிபார்ப்பு வெற்றி</b>\n\nதொடர மீண்டும் <code>/start</code> அனுப்பவும்.',
        'join_pending': '❌ <b>இன்னும் இணையவில்லை</b>\n\nமுதலில் சேனல் மற்றும் குழு இரண்டிலும் இணையவும்.',
    },
    'te': {
        'adult_blocked': '🔞 <b>అనుమతి లేదు</b>\n\nఈ శోధన 18+ వయస్సు వారికి మాత్రమే.',
        'expired_confirm': '❌ <b>గడువు ముగిసింది</b>\n\nఈ వయస్సు నిర్ధారణ ఇప్పుడు చెల్లదు.',
        'join_ok': '✅ <b>ధృవీకరణ విజయవంతం</b>\n\nకొనసాగించడానికి మళ్లీ <code>/start</code> పంపండి.',
        'join_pending': '❌ <b>ఇంకా చేరలేదు</b>\n\nముందు ఛానెల్, గ్రూప్ రెండింటిలోనూ చేరండి.',
    },
    'mr': {
        'adult_blocked': '🔞 <b>परवानगी नाही</b>\n\nहा शोध फक्त 18+ वयांसाठी आहे.',
        'expired_confirm': '❌ <b>मुदत संपली</b>\n\nही वय पुष्टी आता वैध नाही.',
        'join_ok': '✅ <b>तपासणी यशस्वी</b>\n\nपुढे चालू ठेवण्यासाठी पुन्हा <code>/start</code> पाठवा.',
        'join_pending': '❌ <b>अजून जॉइन केले नाही</b>\n\nप्रथम चॅनेल आणि ग्रुप दोन्ही जॉइन करा.',
    },
    'gu': {
        'adult_blocked': '🔞 <b>મંજૂરી નથી</b>\n\nઆ શોધ ફક્ત 18+ ઉંમર માટે છે.',
        'expired_confirm': '❌ <b>મુદત પૂરી</b>\n\nઆ ઉંમરની ખાતરી હવે માન્ય નથી.',
        'join_ok': '✅ <b>તપાસ સફળ</b>\n\nઆગળ વધવા ફરી <code>/start</code> મોકલો.',
        'join_pending': '❌ <b>હજી જોડાયા નથી</b>\n\nપહેલા ચેનલ અને ગ્રુપ બંનેમાં જોડાઓ.',
    },
    'pa': {
        'adult_blocked': '🔞 <b>ਇਜਾਜ਼ਤ ਨਹੀਂ</b>\n\nਇਹ ਖੋਜ ਸਿਰਫ਼ 18+ ਉਮਰ ਲਈ ਹੈ।',
        'expired_confirm': '❌ <b>ਮਿਆਦ ਪੁੱਗ ਗਈ</b>\n\nਇਹ ਉਮਰ ਪੁਸ਼ਟੀ ਹੁਣ ਵੈਧ ਨਹੀਂ।',
        'join_ok': '✅ <b>ਜਾਂਚ ਸਫ਼ਲ</b>\n\nਜਾਰੀ ਰੱਖਣ ਲਈ ਫਿਰ <code>/start</code> ਭੇਜੋ।',
        'join_pending': '❌ <b>ਹਾਲੇ ਨਹੀਂ ਜੁੜੇ</b>\n\nਪਹਿਲਾਂ ਚੈਨਲ ਅਤੇ ਗਰੁੱਪ ਦੋਵੇਂ ਜੁੜੋ।',
    },
}

for _code, _entries in _BUTTON_MESSAGES.items():
    CATALOG[_code].update(_entries)

# Download flow strings, kept in one block like the others.
_DOWNLOAD = {
    'en': {
        'link_ready': '✅ Your download link is ready.',
        'dl_unavailable': '🚫 <b>Download unavailable</b>\n\nThe download service is temporarily down, so this movie cannot be sent right now.\n\n🔁 Please try again in a few minutes.',
        'steps': '1️⃣ Press <b>{button}</b>.\n2️⃣ Complete the page that opens.\n3️⃣ The bot sends the movie file at once.',
    },
    'hi': {
        'link_ready': '✅ आपका डाउनलोड लिंक तैयार है।',
        'dl_unavailable': '🚫 <b>डाउनलोड उपलब्ध नहीं</b>\n\nडाउनलोड सेवा कुछ समय के लिए बंद है, इसलिए यह मूवी अभी नहीं भेजी जा सकती।\n\n🔁 कुछ मिनट बाद फिर कोशिश करें।',
        'steps': '1️⃣ <b>{button}</b> दबाएँ।\n2️⃣ जो पेज खुलेगा उसे पूरा करें।\n3️⃣ बॉट तुरंत मूवी फाइल भेज देगा।',
    },
    'bn': {
        'link_ready': '✅ আপনার ডাউনলোড লিংক প্রস্তুত।',
        'dl_unavailable': '🚫 <b>ডাউনলোড পাচ্ছেন না</b>\n\nডাউনলোড সেবা সাময়িক বন্ধ, তাই এই মুভিটি এখন পাঠানো যাচ্ছে না।\n\n🔁 কয়েক মিনিট পর আবার চেষ্টা করুন।',
        'steps': '1️⃣ <b>{button}</b>-এ চাপ দিন।\n2️⃣ যে পেজ খুলবে সেটি সম্পূর্ণ করুন।\n3️⃣ বট সঙ্গেই মুভির ফাইল পাঠাবে।',
    },
    'ta': {
        'link_ready': '✅ உங்கள் பதிவிறக்க இணையம் தயார்.',
        'dl_unavailable': '🚫 <b>பதிவிறக்கம் இல்லை</b>\n\nசேவை தற்காலிகமாக இல்லை, எனவே இந்த படத்தை இப்போது அனுப்ப முடியாது.\n\n🔁 சில நிமிடங்களில் மீண்டும் முயற்சிக்கவும்.',
        'steps': '1️⃣ <b>{button}</b> ஐ அழுத்தவும்.\n2️⃣ திறக்கும் பக்கத்தை முடிக்கவும்.\n3️⃣ பட ஃபைல் உடனே அனுப்பப்படும்.',
    },
    'te': {
        'link_ready': '✅ మీ డౌన్‌లోడ్ లింక్ సిద్ధంగా ఉంది.',
        'dl_unavailable': '🚫 <b>డౌన్‌లోడ్ అందుబాటులో లేదు</b>\n\nసేవ తాత్కాలికంగా బంద్, కాబట్టి ఈ సినిమా ఇప్పుడు పంపలేము.\n\n🔁 కొన్ని నిమిషాల తర్వాత మళ్లీ ప్రయత్నించండి.',
        'steps': '1️⃣ <b>{button}</b> నొక్కండి.\n2️⃣ తెరిచే పేజీ పూర్తి చేయండి.\n3️⃣ సినిమా ఫైల్ వెంటనే పంపబడుతుంది.',
    },
    'mr': {
        'link_ready': '✅ तुमची डाउनलोड लिंक तयार आहे.',
        'dl_unavailable': '🚫 <b>डाउनलोड उपलब्ध नाही</b>\n\nसेवा तात्पुरती बंद आहे, म्हणून हा सिनेमा आत्ता पाठवता येत नाही.\n\n🔁 काही मिनिटांनी पुन्हा प्रयत्न करा.',
        'steps': '1️⃣ <b>{button}</b> दाबा.\n2️⃣ उघडलेले पेज पूर्ण करा.\n3️⃣ बॉट लगेच सिनेमा फाइल पाठवेल.',
    },
    'gu': {
        'link_ready': '✅ તમારી ડાઉનલોડ લિંક તૈયાર છે.',
        'dl_unavailable': '🚫 <b>ડાઉનલોડ ઉપલબ્ધ નથી</b>\n\nસેવા થોડા સમય માટે બંધ છે, તેથી આ મૂવી હમણાં મોકલી શકાતી નથી.\n\n🔁 થોડી મિનિટ પછી ફરી પ્રયાસ કરો.',
        'steps': '1️⃣ <b>{button}</b> દબાવો.\n2️⃣ ખૂલતા પેજને પૂર્ણ કરો.\n3️⃣ બોટ તરત જ મૂવી ફાઇલ મોકલશે.',
    },
    'pa': {
        'link_ready': '✅ ਤੁਹਾਡਾ ਡਾਊਨਲੋਡ ਲਿੰਕ ਤਿਆਰ ਹੈ।',
        'dl_unavailable': '🚫 <b>ਡਾਊਨਲੋਡ ਉਪਲਬਧ ਨਹੀਂ</b>\n\nਸੇਵਾ ਥੋੜ੍ਹੇ ਸਮੇਂ ਲਈ ਬੰਦ ਹੈ, ਇਸ ਲਈ ਇਹ ਫ਼ਿਲਮ ਹੁਣ ਨਹੀਂ ਭੇਜੀ ਜਾ ਸਕਦੀ।\n\n🔁 ਕੁਝ ਮਿੰਟ ਬਾਅਦ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।',
        'steps': '1️⃣ <b>{button}</b> ਦਬਾਓ।\n2️⃣ ਖੁੱਲ੍ਹਦੇ ਪੰਨੇ ਨੂੰ ਪੂਰਾ ਕਰੋ।\n3️⃣ ਬੌਟ ਤੁਰੰਤ ਫ਼ਿਲਮ ਫ਼ਾਈਲ ਭੇਜ ਦੇਵੇਗਾ।',
    },
}

for _code, _entries in _DOWNLOAD.items():
    CATALOG[_code].update(_entries)

BUTTON_LABELS = {
    'hi': {'download_link': '🔗 डाउनलोड लिंक बनाएँ', 'movie_details': 'ℹ️ मूवी विवरण'},
    'bn': {'download_link': '🔗 ডাউনলোড লিংক তৈরি করুন', 'movie_details': 'ℹ️ মুভির তথ্য'},
    'ta': {'download_link': '🔗 பதிவிறக்க இணையத்தை உருவாக்குங்கள்', 'movie_details': 'ℹ️ பட விவரங்கள்'},
    'te': {'download_link': '🔗 డౌన్‌లోడ్ లింక్ తయారు చేయండి', 'movie_details': 'ℹ️ సినిమా వివరాలు'},
    'mr': {'download_link': '🔗 डाउनलोड लिंक तयार करा', 'movie_details': 'ℹ️ सिनेमा तपशील'},
    'gu': {'download_link': '🔗 ડાઉનલોડ લિંક બનાવો', 'movie_details': 'ℹ️ મૂવી વિગતો'},
    'pa': {'download_link': '🔗 ਡਾਊਨਲੋਡ ਲਿੰਕ ਬਣਾਓ', 'movie_details': 'ℹ️ ਫ਼ਿਲਮ ਵੇਰਵੇ'},
}

for _code, _entries in BUTTON_LABELS.items():
    CATALOG[_code].update(_entries)

del _code, _entries


def language_name(code: str) -> str:
    for known_code, native, english in LANGUAGES:
        if known_code == code:
            return native
    return code


def t(code: str, key: str, **kwargs) -> str:
    """One string in the user's language, English when it is not written yet."""
    catalog = CATALOG.get(code) or CATALOG['en']
    template = catalog.get(key) or CATALOG['en'].get(key) or key

    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template

    return template


def language_rows(page: int = 0):
    """Two languages per button row; page 0 is the common languages + More."""
    if page == 0:
        codes = TOP_LANGUAGES
    else:
        rest = [code for code, _, _ in LANGUAGES if code not in TOP_LANGUAGES]
        start = (page - 1) * BUTTONS_PER_PAGE
        codes = rest[start:start + BUTTONS_PER_PAGE]

    rows = []
    for index in range(0, len(codes), 2):
        rows.append([
            InlineKeyboardButton(NAMES[code], callback_data=f'lang_{code}')
            for code in codes[index:index + 2]
        ])
    return rows


def language_pages() -> int:
    rest = len([code for code, _, _ in LANGUAGES if code not in TOP_LANGUAGES])
    return 1 + (rest + BUTTONS_PER_PAGE - 1) // BUTTONS_PER_PAGE
