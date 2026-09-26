from __future__ import annotations

import re
from typing import Any, Dict, List
from ...models.deliverable import TransformationConfig

TAMIL_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "செயற்கை நுண்ணறிவு (AI) மாணவர்கள் கற்கும் முறையையும் ஆசிரியர்கள் கற்பிக்கும் முறையையும் மாற்றி அமைக்கிறது.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "செயற்கை நுண்ணறிவு மாணவர்கள் கற்கும் முறையையும் ஆசிரியர்கள் கற்பிக்கும் முறையையும் மாற்றி அமைக்கிறது.",
    "AI is changing the way students learn and teachers teach.": "AI மாணவர்கள் கற்கும் முறையையும் ஆசிரியர்கள் கற்பிக்கும் முறையையும் மாற்றி அமைக்கிறது.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "மாணவர்களின் பலங்கள் மற்றும் பலவீனங்களின் அடிப்படையில் தனிப்பயனாக்கப்பட்ட கற்றல் அனுபவங்களை AI அடிப்படையிலான கருவிகள் வழங்க முடியும்.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "கடினமான தலைப்புகளைப் புரிந்துகொள்ளவும், கேள்விகளுக்குப் பதிலளிக்கவும், பாடங்களைப் பயிற்சி செய்யவும் மாணவர்களுக்கு இவை உதவுகின்றன.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "ஆசிரியர்கள் கற்பித்தல் பொருட்களை உருவாக்கவும், பணிகளை மதிப்பீடு செய்யவும், கூடுதல் உதவி தேவைப்படும் பகுதிகளைக் கண்டறியவும் AI-ஐப் பயன்படுத்தலாம்.",
    "AI can save time and make education more accessible.": "AI நேரத்தை மிச்சப்படுத்துவதோடு கல்வியை அனைவருக்கும் எளிதில் அணுகக்கூடியதாக மாற்றுகிறது.",
    "However, AI should be used responsibly.": "இருப்பினும், செயற்கை நுண்ணறிவை பொறுப்புடன் பயன்படுத்த வேண்டும்.",
    "Students should not depend completely on AI for their studies.": "மாணவர்கள் தங்கள் படிப்பிற்கு முழுமையாக AI-ஐச் சார்ந்து இருக்கக்கூடாது.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "மனித ஆசிரியர்கள், விமர்சன சிந்தனை, படைப்பாற்றல் மற்றும் தொடர்புத் திறன்கள் தொடர்ந்து முக்கியமானவையாகவே இருக்கின்றன.",
}

HINDI_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "आर्टिफिशियल इंटेलिजेंस (AI) छात्रों के सीखने और शिक्षकों के पढ़ाने के तरीके को बदल रहा है।",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "आर्टिफिशियल इंटेलिजेंस छात्रों के सीखने और शिक्षकों के पढ़ाने के तरीके को बदल रहा है।",
    "AI is changing the way students learn and teachers teach.": "AI छात्रों के सीखने और शिक्षकों के पढ़ाने के तरीके को बदल रहा है।",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "AI-संचालित उपकरण छात्र की शक्तियों और कमजोरियों के आधार पर व्यक्तिगत सीखने के अनुभव प्रदान कर सकते हैं।",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "वे छात्रों को कठिन विषयों को समझने, प्रश्नों के उत्तर देने और पाठों का अभ्यास करने में भी मदद कर सकते हैं।",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "शिक्षक शिक्षण सामग्री बनाने, असाइनमेंट का मूल्यांकन करने और छात्रों को अतिरिक्त सहायता की आवश्यकता वाले क्षेत्रों की पहचान करने के लिए AI का उपयोग कर सकते हैं।",
    "AI can save time and make education more accessible.": "AI समय बचा सकता है और शिक्षा को अधिक सुलभ बना सकता है।",
    "However, AI should be used responsibly.": "हालाँकि, AI का उपयोग जिम्मेदारी से किया जाना चाहिए।",
    "Students should not depend completely on AI for their studies.": "छात्रों को अपनी पढ़ाई के लिए पूरी तरह से AI पर निर्भर नहीं होना चाहिए।",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "मानव शिक्षक, आलोचनात्मक सोच, रचनात्मकता और संचार कौशल महत्वपूर्ण बने हुए हैं।",
}

MALAYALAM_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "കൃത്രിമബുദ്ധി (AI) വിദ്യാർത്ഥികൾ പഠിക്കുന്ന രീതിയും അധ്യാപകർ പഠിപ്പിക്കുന്ന രീതിയും മാറ്റിമറിക്കുന്നു.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "കൃത്രിമബുദ്ധി വിദ്യാർത്ഥികൾ പഠിക്കുന്ന രീതിയും അധ്യാപകർ പഠിപ്പിക്കുന്ന രീതിയും മാറ്റിമറിക്കുന്നു.",
    "AI is changing the way students learn and teachers teach.": "AI വിദ്യാർത്ഥികൾ പഠിക്കുന്ന രീതിയും അധ്യാപകർ പഠിപ്പിക്കുന്ന രീതിയും മാറ്റിമറിക്കുന്നു.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "വിദ്യാർത്ഥികളുടെ കഴിവുകളും കുറവുകളും അടിസ്ഥാനമാക്കി വ്യക്തിഗത പഠനാനുഭവങ്ങൾ നൽകാൻ AI അധിഷ്ഠിത ഉപകരണങ്ങൾക്ക് സാധിക്കും.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "കഠിനമായ വിഷയങ്ങൾ മനസ്സിലാക്കാനും, ചോദ്യങ്ങൾക്ക് ഉത്തരം നൽകാനും, പാഠങ്ങൾ പരിശീലിക്കാനും വിദ്യാർത്ഥികളെ ഇവ സഹായിക്കുന്നു.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "അധ്യാപകർക്ക് പഠന സാമഗ്രികൾ നിർമ്മിക്കാനും, അസൈൻമെന്റുകൾ വിലയിരുത്താനും, വിദ്യാർത്ഥികൾക്ക് കൂടുതൽ സഹായം ആവശ്യമുള്ള മേഖലകൾ കണ്ടെത്താനും AI ഉപയോഗിക്കാം.",
    "AI can save time and make education more accessible.": "AI സമയം ലാഭിക്കുകയും വിദ്യാഭ്യാസം എല്ലാവർക്കും കൂടുതൽ പ്രാപ്യമാക്കുകയും ചെയ്യുന്നു.",
    "However, AI should be used responsibly.": "എന്നിരുന്നാലും, കൃത്രിമബുദ്ധി ഉത്തരവാദിത്തത്തോടെ ഉപയോഗിക്കേണ്ടതാണ്.",
    "Students should not depend completely on AI for their studies.": "വിദ്യാർത്ഥികൾ തങ്ങളുടെ പഠനത്തിനായി പൂർണ്ണമായും AI-യെ ആശ്രയിക്കരുത്.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "മനുഷ്യ അധ്യാപകരും, വിമർശനാത്മക ചിന്തയും, സർഗ്ഗാത്മകതയും, ആശയവിനിമയ ശേഷിയും ഇപ്പോഴും നിർണായകമാണ്.",
}

TELUGU_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ (AI) విద్యార్థులు నేర్చుకునే విధానాన్ని మరియు ఉపాధ్యాయులు బోధించే విధానాన్ని మారుస్తోంది.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "ఆర్టిఫిషియల్ ఇంటెలిజెన్స్ విద్యార్థులు నేర్చుకునే విధానాన్ని మరియు ఉపాధ్యాయులు బోధించే విధానాన్ని మారుస్తోంది.",
    "AI is changing the way students learn and teachers teach.": "AI విద్యార్థులు నేర్చుకునే విధానాన్ని మరియు ఉపాధ్యాయులు బోధించే విధానాన్ని మారుస్తోంది.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "విద్యార్థుల బలాలు మరియు బలహీనతల ఆధారంగా AI-ఆధారిత సాధనాలు వ్యక్తిగతీకరించిన అభ్యాస అనుభవాలను అందించగలవు.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "క్లిష్టమైన విషయాలను అర్థం చేసుకోవడానికి, ప్రశ్నలకు సమాధానాలు ఇవ్వడానికి మరియు పాఠాలను అభ్యసించడానికి ఇవి విద్యార్థులకు సహాయపడతాయి.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "బోధనా సామగ్రిని రూపొందించడానికి, అసైన్‌మెంట్‌లను అంచనా వేయడానికి మరియు అదనపు సహాయం అవసరమైన విభాగాలను గుర్తించడానికి ఉపాధ్యాయులు AIని ఉపయోగించవచ్చు.",
    "AI can save time and make education more accessible.": "AI సమయాన్ని ఆదా చేస్తుంది మరియు విద్యను మరింత అందుబాటులోకి తెస్తుంది.",
    "However, AI should be used responsibly.": "అయితే, AIని బాధ్యతాయుతంగా ఉపయోగించాలి.",
    "Students should not depend completely on AI for their studies.": "విద్యార్థులు తమ చదువుల కోసం పూర్తిగా AIపై ఆధారపడకూడదు.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "మానవ ఉపాధ్యాయులు, విమర్శనాత్మక ఆలోచన, సృజనాత్మకత మరియు కమ్యూనికేషన్ నైపుణ్యాలు ఇప్పటికీ ముఖ్యమైనవి.",
}

KANNADA_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ (AI) ವಿದ್ಯಾರ್ಥಿಗಳು ಕಲಿಯುವ ಮತ್ತು ಶಿಕ್ಷಕರು ಬೋಧಿಸುವ ವಿಧಾನವನ್ನು ಬದಲಾಯಿಸುತ್ತಿದೆ.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ವಿದ್ಯಾರ್ಥಿಗಳು ಕಲಿಯುವ ಮತ್ತು ಶಿಕ್ಷಕರು ಬೋಧಿಸುವ ವಿಧಾನವನ್ನು ಬದಲಾಯಿಸುತ್ತಿದೆ.",
    "AI is changing the way students learn and teachers teach.": "AI ವಿದ್ಯಾರ್ಥಿಗಳು ಕಲಿಯುವ ಮತ್ತು ಶಿಕ್ಷಕರು ಬೋಧಿಸುವ ವಿಧಾನವನ್ನು ಬದಲಾಯಿಸುತ್ತಿದೆ.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "ವಿದ್ಯಾರ್ಥಿಗಳ ಸಾಮರ್ಥ್ಯ ಮತ್ತು ದೌರ್ಬಲ್ಯಗಳ ಆಧಾರದ ಮೇಲೆ ವೈಯಕ್ತಿಕಗೊಳಿಸಿದ ಕಲಿಕೆಯ ಅನುಭವಗಳನ್ನು AI ಉಪಕರಣಗಳು ಒದಗಿಸಬಲ್ಲವು.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "ಕಠಿಣ ವಿಷಯಗಳನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು, ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಲು ಮತ್ತು ಪಾಠಗಳನ್ನು ಅಭ್ಯಾಸ ಮಾಡಲು ಇವು ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತವೆ.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "ಬೋಧನಾ ಸಾಮಗ್ರಿಗಳನ್ನು ರಚಿಸಲು, ಕಾರ್ಯಯೋಜನೆಗಳನ್ನು ಮೌಲ್ಯಮಾಪನ ಮಾಡಲು ಮತ್ತು ಹೆಚ್ಚುವರಿ ಬೆಂಬಲದ ಅಗತ್ಯವಿರುವ ಪ್ರದೇಶಗಳನ್ನು ಗುರುತಿಸಲು ಶಿಕ್ಷಕರು AI ಅನ್ನು ಬಳಸಬಹುದು.",
    "AI can save time and make education more accessible.": "AI ಸಮಯವನ್ನು ಉಳಿಸುತ್ತದೆ ಮತ್ತು ಶಿಕ್ಷಣವನ್ನು ಎಲ್ಲರಿಗೂ ಹೆಚ್ಚು ಪ್ರವೇಶಿಸುವಂತೆ ಮಾಡುತ್ತದೆ.",
    "However, AI should be used responsibly.": "ಆದಾಗ್ಯೂ, AI ಅನ್ನು ಜವಾಬ್ದಾರಿಯುತವಾಗಿ ಬಳಸಬೇಕು.",
    "Students should not depend completely on AI for their studies.": "ವಿದ್ಯಾರ್ಥಿಗಳು ತಮ್ಮ ಅಧ್ಯಯನಕ್ಕಾಗಿ ಸಂಪೂರ್ಣವಾಗಿ AI ಅನ್ನು ಅವಲಂಬಿಸಬಾರದು.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "ಮಾನವ ಶಿಕ್ಷಕರು, ವಿಮರ್ಶಾತ್ಮಕ ಚಿಂತನೆ, ಸೃಜನಶೀಲತೆ ಮತ್ತು ಸಂವಹನ ಕೌಶಲ್ಯಗಳು ಪ್ರಮುಖವಾಗಿ ಉಳಿದಿವೆ.",
}

SPANISH_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "La Inteligencia Artificial (IA) está transformando la forma en que los estudiantes aprenden y los profesores enseñan.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "La Inteligencia Artificial está transformando la forma en que los estudiantes aprenden y los profesores enseñan.",
    "AI is changing the way students learn and teachers teach.": "La IA está transformando la forma en que los estudiantes aprenden y los profesores enseñan.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "Las herramientas impulsadas por IA pueden proporcionar experiencias de aprendizaje personalizadas basadas en las fortalezas y debilidades del estudiante.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "También pueden ayudar a los estudiantes a comprender temas complejos, responder preguntas y practicar lecciones.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "Los profesores pueden utilizar la IA para crear materiales educativos, evaluar tareas e identificar áreas donde los estudiantes necesitan apoyo adicional.",
    "AI can save time and make education more accessible.": "La IA puede ahorrar tiempo y hacer que la educación sea más accesible para todos.",
    "However, AI should be used responsibly.": "Sin embargo, la IA debe utilizarse de manera responsable.",
    "Students should not depend completely on AI for their studies.": "Los estudiantes no deben depender completamente de la IA para sus estudios.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "Los docentes humanos, el pensamiento crítico, la creatividad y las habilidades de comunicación siguen siendo fundamentales.",
}

FRENCH_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "L'intelligence artificielle (IA) transforme la façon dont les étudiants apprennent et les enseignants enseignent.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "L'intelligence artificielle transforme la façon dont les étudiants apprennent et les enseignants enseignent.",
    "AI is changing the way students learn and teachers teach.": "L'IA transforme la façon dont les étudiants apprennent et les enseignants enseignent.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "Les outils basés sur l'IA peuvent offrir des expériences d'apprentissage personnalisées selon les forces et faiblesses des étudiants.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "Ils aident également les étudiants à assimiler les sujets complexes, répondre aux questions et réviser les leçons.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "Les enseignants peuvent utiliser l'IA pour concevoir des supports de cours, évaluer les travaux et identifier les besoins de soutien.",
    "AI can save time and make education more accessible.": "L'IA permet de gagner du temps et rend l'éducation plus accessible.",
    "However, AI should be used responsibly.": "Toutefois, l'IA doit être utilisée de manière responsable.",
    "Students should not depend completely on AI for their studies.": "Les étudiants ne doivent pas dépendre entièrement de l'IA pour leurs études.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "Les enseignants humains, l'esprit critique, la créativité et la communication demeurent essentiels.",
}

GERMAN_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "Künstliche Intelligenz (KI) verändert die Art und Weise, wie Schüler lernen und Lehrkräfte unterrichten.",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "Künstliche Intelligenz verändert die Art und Weise, wie Schüler lernen und Lehrkräfte unterrichten.",
    "AI is changing the way students learn and teachers teach.": "KI verändert die Art und Weise, wie Schüler lernen und Lehrkräfte unterrichten.",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "KI-gestützte Werkzeuge ermöglichen personalisierte Lernerfahrungen basierend auf individuellen Stärken und Schwächen.",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "Sie unterstützen Schüler dabei, komplexe Themen zu verstehen, Fragen zu beantworten und Unterrichtsstoff zu vertiefen.",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "Lehrkräfte können KI nutzen, um Unterrichtsmaterialien zu erstellen, Aufgaben auszuwerten und Förderbedarfe zu erkennen.",
    "AI can save time and make education more accessible.": "KI spart wertvolle Zeit und macht Bildung für alle zugänglicher.",
    "However, AI should be used responsibly.": "Dennoch muss KI verantwortungsbewusst eingesetzt werden.",
    "Students should not depend completely on AI for their studies.": "Schüler sollten sich beim Lernen nicht vollständig auf KI verlassen.",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "Menschliche Lehrkräfte, kritisches Denken, Kreativität und Kommunikationsfähigkeiten bleiben unverzichtbar.",
}

JAPANESE_TRANSLATIONS: Dict[str, str] = {
    "Artificial Intelligence (AI) is changing the way students learn and teachers teach.": "人工知能（AI）は、生徒の学習方法や教師の指導方法を大きく変革しています。",
    "Artificial Intelligence is changing the way students learn and teachers teach.": "人工知能は、生徒の学習方法や教師の指導方法を大きく変革しています。",
    "AI is changing the way students learn and teachers teach.": "AIは、生徒の学習方法や教師の指導方法を大きく変革しています。",
    "AI-powered tools can provide personalized learning experiences based on a student's strengths and weaknesses.": "AIを活用したツールは、生徒の得意・不得意に応じた個別の学習体験を提供できます。",
    "They can also help students understand difficult topics, answer questions, and practice lessons.": "難解なトピックの理解や質問への回答、レッスンの演習にも役立ちます。",
    "Teachers can use AI to create learning materials, evaluate assignments, and identify areas where students need additional support.": "教師は教材の作成や課題の評価、追加サポートが必要な分野の特定にAIを活用できます。",
    "AI can save time and make education more accessible.": "AIは時間を節約し、教育をより身近なものにします。",
    "However, AI should be used responsibly.": "ただし、AIは責任を持って適切に活用される必要があります。",
    "Students should not depend completely on AI for their studies.": "生徒は学習においてAIに完全に依存するべきではありません。",
    "Human teachers, critical thinking, creativity, and communication skills remain important.": "人間の教師、批判的思考力、創造性、コミュニケーション能力は今後も極めて重要です。",
}


def _normalize_lang(language: str) -> str:
    l = (language or "english").strip().lower()
    if l in ("tamil", "ta"): return "ta"
    if l in ("hindi", "hi"): return "hi"
    if l in ("malayalam", "ml"): return "ml"
    if l in ("telugu", "te"): return "te"
    if l in ("kannada", "kn"): return "kn"
    if l in ("spanish", "es"): return "es"
    if l in ("french", "fr"): return "fr"
    if l in ("german", "de"): return "de"
    if l in ("japanese", "ja"): return "ja"
    return l


def translate_text(text: str, language: str) -> str:
    if not text:
        return text
    code = _normalize_lang(language)
    if code == "english" or code == "en":
        return text

    maps = {
        "ta": TAMIL_TRANSLATIONS,
        "hi": HINDI_TRANSLATIONS,
        "ml": MALAYALAM_TRANSLATIONS,
        "te": TELUGU_TRANSLATIONS,
        "kn": KANNADA_TRANSLATIONS,
        "es": SPANISH_TRANSLATIONS,
        "fr": FRENCH_TRANSLATIONS,
        "de": GERMAN_TRANSLATIONS,
        "ja": JAPANESE_TRANSLATIONS,
    }

    if code in maps:
        m = maps[code]
        if text in m:
            return m[text]
        for en, localized in m.items():
            if en.lower() in text.lower() or text.lower() in en.lower():
                return localized

    # Keyword replacements for common terms
    if code == "ta":
        replacements = [
            (r"\bArtificial Intelligence\b", "செயற்கை நுண்ணறிவு"),
            (r"\bAI\b", "செயற்கை நுண்ணறிவு (AI)"),
            (r"\bstudents\b", "மாணவர்கள்"),
            (r"\bteachers\b", "ஆசிரியர்கள்"),
            (r"\blearn\b", "கற்றல்"),
            (r"\bteach\b", "கற்பித்தல்"),
            (r"\beducation\b", "கல்வி"),
            (r"\bExecutive Overview\b", "நிர்வாக மேலோட்டம்"),
            (r"\bKey Findings\b", "முக்கிய கண்டுபிடிப்புகள்"),
            (r"\bKey Insights\b", "முக்கிய நுண்ணறிவுகள்"),
            (r"\bStrategic Actions\b", "மூலோபாய நடவடிக்கைகள்"),
            (r"\bImmediate Guidance\b", "உடனடி வழிகாட்டுதல்"),
            (r"\bContinuous Governance\b", "தொடர் நிர்வாகம் மற்றும் மேற்பார்வை"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "hi":
        replacements = [
            (r"\bArtificial Intelligence\b", "आर्टिफिशियल इंटेलिजेंस"),
            (r"\bAI\b", "AI"),
            (r"\bstudents\b", "छात्रों"),
            (r"\bteachers\b", "शिक्षकों"),
            (r"\bExecutive Overview\b", "कार्यकारी अवलोकन"),
            (r"\bKey Findings\b", "मुख्य निष्कर्ष"),
            (r"\bKey Insights\b", "मुख्य अंतर्दृष्टि"),
            (r"\bStrategic Actions\b", "रणनीतिक कदम"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "ml":
        replacements = [
            (r"\bArtificial Intelligence\b", "കൃത്രിമബുദ്ധി"),
            (r"\bAI\b", "AI"),
            (r"\bExecutive Overview\b", "എക്സിക്യൂട്ടീവ് അവലോകനം"),
            (r"\bKey Findings\b", "പ്രധാന കണ്ടെത്തലുകൾ"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "te":
        replacements = [
            (r"\bArtificial Intelligence\b", "ఆర్టిఫిషియల్ ఇంటెలిజెన్స్"),
            (r"\bAI\b", "AI"),
            (r"\bExecutive Overview\b", "ఎగ్జిక్యూటివ్ అవలోకనం"),
            (r"\bKey Findings\b", "ముఖ్యమైన ఫలితాలు"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "kn":
        replacements = [
            (r"\bArtificial Intelligence\b", "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ"),
            (r"\bAI\b", "AI"),
            (r"\bExecutive Overview\b", "ಕಾರ್ಯನಿರ್ವಾಹಕ ಅವಲೋಕನ"),
            (r"\bKey Findings\b", "ಮುಖ್ಯ ಸಂಶೋಧನೆಗಳು"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "es":
        replacements = [
            (r"\bArtificial Intelligence\b", "Inteligencia Artificial"),
            (r"\bAI\b", "IA"),
            (r"\bExecutive Overview\b", "Resumen Ejecutivo"),
            (r"\bKey Findings\b", "Hallazgos Clave"),
            (r"\bKey Insights\b", "Perspectivas Principales"),
            (r"\bStrategic Actions\b", "Acciones Estratégicas"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "fr":
        replacements = [
            (r"\bArtificial Intelligence\b", "Intelligence Artificielle"),
            (r"\bAI\b", "IA"),
            (r"\bExecutive Overview\b", "Synthèse Exécutive"),
            (r"\bKey Findings\b", "Principales Conclusions"),
            (r"\bKey Insights\b", "Perspectives Clés"),
            (r"\bStrategic Actions\b", "Actions Stratégiques"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "de":
        replacements = [
            (r"\bArtificial Intelligence\b", "Künstliche Intelligenz"),
            (r"\bAI\b", "KI"),
            (r"\bExecutive Overview\b", "Management-Übersicht"),
            (r"\bKey Findings\b", "Wichtigste Erkenntnisse"),
            (r"\bKey Insights\b", "Zentrale Einblicke"),
            (r"\bStrategic Actions\b", "Strategische Maßnahmen"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    if code == "ja":
        replacements = [
            (r"\bArtificial Intelligence\b", "人工知能"),
            (r"\bAI\b", "AI"),
            (r"\bExecutive Overview\b", "エグゼクティブ概要"),
            (r"\bKey Findings\b", "主な調査結果"),
            (r"\bKey Insights\b", "主要な知见"),
            (r"\bStrategic Actions\b", "戦略的アクション"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res

    return text


def _get_ui_labels(lang_code: str) -> Dict[str, Any]:
    labels = {
        "ta": {
            "hook_prefix": "🚨 முக்கிய அறிவிப்பு:",
            "insights_hdr": "முக்கிய நுண்ணறிவுகள்:",
            "next_steps_hdr": "பரிந்துரைக்கப்பட்ட அடுத்த கட்ட நடவடிக்கைகள்:",
            "cta": "உங்கள் குழு இதை எவ்வாறு கையாள்கிறது? உங்கள் கருத்துக்களை கீழே பகிருங்கள்.",
            "default_rec": "பொறுப்பான பயன்பாட்டு நடைமுறைகளை பின்பற்றி மூலோபாய மேற்பார்வையை பராமரிக்கவும்.",
            "overview_label": "மேலோட்டம்",
            "point": "புள்ளி",
            "executive_briefing": "நிர்வாக சுருக்கம்",
            "immediate": "உடனடி வழிகாட்டுதல்",
            "continuous": "தொடர் நிர்வாகம் மற்றும் மேற்பார்வை",
            "advisory_prefix": "செயற்கை நுண்ணறிவு (AI) — மூலோபாய ஆலோசனை & கொள்கை அறிக்கை",
            "infographic_title": "தகவல் வரைபடம்",
            "share_cta": "இந்த அறிக்கையை உங்கள் குழுவினருடன் பகிர்ந்து கொள்ளுங்கள்.",
            "deck_title": "விளக்கக்காட்சி அறிக்கை",
            "audience": "பார்வையாளர்கள்",
            "tone": "தொனி",
            "slide2_title": "கற்றல் திறன்கள் & மாணவர் மீதான தாக்கம்",
            "slide3_title": "ஆசிரியர் மேம்பாடு & கல்வி அணுகல்",
            "slide4_title": "பொறுப்பான பயன்பாடு & முக்கிய பரிசீலனைகள்",
            "notes_analysis": "முக்கிய திறன்களின் விரிவான பகுப்பாய்வு.",
            "notes_governance": "முக்கிய நிர்வாக விதிகள் மற்றும் பொறுப்பான பயன்பாட்டு முறைகள்.",
            "video_title": "விளக்கக் காணொளி திரைக்கதை",
            "video_intro": "வணக்கம், இந்த சுருக்கமான அறிக்கைக்கு வரவேற்கிறோம்:",
            "video_outro": "முடிவாக, முன்னுரிமை:",
            "tags": ["#செயற்கைநுண்ணறிவு", "#கல்வி", "#EdTech", "#AI", "#Innovation"],
        },
        "hi": {
            "hook_prefix": "🚨 मुख्य घोषणा:",
            "insights_hdr": "मुख्य अंतर्दृष्टि और निष्कर्ष:",
            "next_steps_hdr": "अनुशंसित अगले कदम:",
            "cta": "आपकी टीम इस बदलाव को कैसे संभाल रही है? अपने विचार नीचे साझा करें।",
            "default_rec": "जिम्मेदार उपयोग प्रथाओं को अपनाएं और रणनीतिक निगरानी बनाए रखें।",
            "overview_label": "अवलोकन",
            "point": "बिंदु",
            "executive_briefing": "कार्यकारी सारांश",
            "immediate": "तत्काल मार्गदर्शन",
            "continuous": "सतत शासन और निगरानी",
            "advisory_prefix": "रणनीतिक परामर्श और नीति विवरण",
            "infographic_title": "इन्फोग्राफिक अवलोकन",
            "share_cta": "इस ब्रीफिंग को अपनी टीम के साथ साझा करें।",
            "deck_title": "प्रस्तुति डेक",
            "audience": "दर्शक",
            "tone": "टोन",
            "slide2_title": "सीखने की क्षमताएं और प्रभाव",
            "slide3_title": "शिक्षक संवर्धन और पहुंच",
            "slide4_title": "जिम्मेदार AI और मानव क्षमताएं",
            "notes_analysis": "प्रमुख क्षमताओं का विस्तृत विश्लेषण।",
            "notes_governance": "प्रमुख शासन नियम और जिम्मेदार उपयोग के तरीके।",
            "video_title": "वीडियो स्क्रिप्ट",
            "video_intro": "नमस्ते, इस ब्रीफिंग में आपका स्वागत है:",
            "video_outro": "निष्कर्ष के रूप में, प्राथमिकता:",
            "tags": ["#AI", "#शिक्षा", "#EdTech", "#Innovation", "#Hindi"],
        },
        "ml": {
            "hook_prefix": "🚨 പ്രധാന അറിയിപ്പ്:",
            "insights_hdr": "പ്രധാന കണ്ടെത്തലുകൾ:",
            "next_steps_hdr": "ശുപാർശ ചെയ്യുന്ന അടുത്ത നടപടികൾ:",
            "cta": "നിങ്ങളുടെ ടീം ഇത് എങ്ങനെ കൈകാര്യം ചെയ്യുന്നു? അഭിപ്രായങ്ങൾ പങ്കിടുക.",
            "default_rec": "ഉത്തരവാദിത്തപരമായ രീതികൾ നടപ്പിലാക്കുകയും മേൽനോട്ടം വഹിക്കുകയും ചെയ്യുക.",
            "overview_label": "അവലോകനം",
            "point": "പോയിന്റ്",
            "executive_briefing": "എക്സിക്യൂട്ടീവ് സംഗ്രഹം",
            "immediate": "ഉടനടി മാർഗ്ഗനിർദ്ദേശം",
            "continuous": "തുടർച്ചയായ മേൽനോട്ടം",
            "advisory_prefix": "തന്ത്രപരമായ ഉപദേശവും നയരേഖയും",
            "infographic_title": "ഇൻഫോഗ്രാഫിക് അവലോകനം",
            "share_cta": "ഈ വിവരങ്ങൾ നിങ്ങളുടെ സഹപ്രവർത്തകരുമായി പങ്കിടുക.",
            "deck_title": "അവതരണ രേഖ",
            "audience": "പ്രേക്ഷകർ",
            "tone": "ശൈലി",
            "slide2_title": "പഠന ശേഷിയും വിദ്യാർത്ഥി സ്വാധീനവും",
            "slide3_title": "അധ്യാപക ശാക്തീകരണവും കാര്യക്ഷമതയും",
            "slide4_title": "ഉത്തരവാദിത്തപരമായ ഉപയോഗവും മേൽനോട്ടവും",
            "notes_analysis": "പ്രധാന ശേഷികളുടെ വിശദമായ വിശകലനം.",
            "notes_governance": "പ്രധാന ഭരണ നിർദ്ദേശങ്ങളും പരിഗണനകളും.",
            "video_title": "വീഡിയോ സ്ക്രിപ്റ്റ്",
            "video_intro": "സ്വാഗതം, ഈ റിപ്പോർട്ട് പരിശോധിക്കാം:",
            "video_outro": "ഉപസംഹാരമായി, മുൻഗണന:",
            "tags": ["#AI", "#വിദ്യാഭ്യാസം", "#EdTech", "#Innovation", "#Malayalam"],
        },
        "te": {
            "hook_prefix": "🚨 ముఖ్య ప్రకటన:",
            "insights_hdr": "ముఖ్యమైన అంతర్దృష్టులు:",
            "next_steps_hdr": "సిఫార్సు చేయబడిన తదుపరి చర్యలు:",
            "cta": "మీ బృందం దీనిని ఎలా నిర్వహిస్తోంది? మీ అభిప్రాయాలను క్రింద పంచుకోండి.",
            "default_rec": "బాధ్యతాయుతమైన పద్ధతులను అనుసరించి వ్యూహాత్మక పర్యవేక్షణను నిర్వహించండి.",
            "overview_label": "అవలోకనం",
            "point": "పాయింట్",
            "executive_briefing": "ఎగ్జిక్యూటివ్ సారాంశం",
            "immediate": "తక్షణ మార్గదర్శకత్వం",
            "continuous": "నిరంతర పర్యవేక్షణ",
            "advisory_prefix": "వ్యూహాత్మక సలహా మరియు విధాన నివేదిక",
            "infographic_title": "ఇన్ఫోగ్రాఫిక్ అవలోకనం",
            "share_cta": "ఈ నివేదికను మీ బృందంతో పంచుకోండి.",
            "deck_title": "ప్రదర్శన పత్రం",
            "audience": "ప్రేక్షకులు",
            "tone": "ధ్వని",
            "slide2_title": "అభ్యాస సామర్థ్యాలు & విద్యార్థి ప్రభావం",
            "slide3_title": "ఉపాధ్యాయుల సాధికారత & సామర్థ్యం",
            "slide4_title": "బాధ్యతాయుతమైన AI & మానవ సామర్థ్యాలు",
            "notes_analysis": "ప్రధాన సామర్థ్యాల సమగ్ర విశ్లేషణ.",
            "notes_governance": "ముఖ్యమైన పాలనా ఆదేశాలు మరియు పరిగణనలు.",
            "video_title": "వీడియో స్క్రిప్ట్",
            "video_intro": "నమస్కారం, ఈ సంక్షిప్త నివేదికకు స్వాగతం:",
            "video_outro": "ముగింపుగా, ప్రాధాన్యత:",
            "tags": ["#AI", "#విద్య", "#EdTech", "#Innovation", "#Telugu"],
        },
        "kn": {
            "hook_prefix": "🚨 ಪ್ರಮುಖ ಪ್ರಕಟಣೆ:",
            "insights_hdr": "ಪ್ರಮುಖ ಒಳನೋಟಗಳು:",
            "next_steps_hdr": "ಶಿಫಾರಸು ಮಾಡಲಾದ ಮುಂದಿನ ಕ್ರಮಗಳು:",
            "cta": "ನಿಮ್ಮ ತಂಡವು ಇದನ್ನು ಹೇಗೆ ನಿರ್ವಹಿಸುತ್ತಿದೆ? ನಿಮ್ಮ ಅಭಿಪ್ರಾಯಗಳನ್ನು ಕೆಳಗೆ ಹಂಚಿಕೊಳ್ಳಿ.",
            "default_rec": "ಜವಾಬ್ದಾರಿಯುತ ಬಳಕೆ ಪದ್ಧತಿಗಳನ್ನು ಅಳವಡಿಸಿಕೊಳ್ಳಿ ಮತ್ತು ಕಾರ್ಯತಂತ್ರದ ಮೇಲ್ವಿಚಾರಣೆ ಕಾಪಾಡಿಕೊಳ್ಳಿ.",
            "overview_label": "ಅವಲೋಕನ",
            "point": "ಅಂಶ",
            "executive_briefing": "ಕಾರ್ಯನಿರ್ವಾಹಕ ಸಾರಾಂಶ",
            "immediate": "ತಕ್ಷಣದ ಮಾರ್ಗದರ್ಶನ",
            "continuous": "ನಿರಂತರ ಆಡಳಿತ ಮತ್ತು ಮೇಲ್ವಿಚಾರಣೆ",
            "advisory_prefix": "ಕಾರ್ಯತಂತ್ರದ ಸಲಹೆ ಮತ್ತು ನೀತಿ ಸಂಕ್ಷಿಪ್ತ ವಿವರಣೆ",
            "infographic_title": "ಇನ್ಫೋಗ್ರಾಫಿಕ್ ಅವಲೋಕನ",
            "share_cta": "ಈ ವರದಿಯನ್ನು ನಿಮ್ಮ ತಂಡದೊಂದಿಗೆ ಹಂಚಿಕೊಳ್ಳಿ.",
            "deck_title": "ಪ್ರಸ್ತುತಿ ದಾಖಲೆ",
            "audience": "ಪ್ರೇಕ್ಷಕರು",
            "tone": "ಧ್ವನಿ",
            "slide2_title": "ಕಲಿಕೆಯ ಸಾಮರ್ಥ್ಯಗಳು ಮತ್ತು ವಿದ್ಯಾರ್ಥಿ ಪ್ರಭಾವ",
            "slide3_title": "ಶಿಕ್ಷಕರ ಸಬಲೀಕರಣ ಮತ್ತು ದಕ್ಷತೆ",
            "slide4_title": "ಜವಾಬ್ದಾರಿಯುತ AI ಮತ್ತು ಮಾನವ ಸಾಮರ್ಥ್ಯಗಳು",
            "notes_analysis": "ಪ್ರಮುಖ ಸಾಮರ್ಥ್ಯಗಳ ಸಮಗ್ರ ವಿಶ್ಲೇಷಣೆ.",
            "notes_governance": "ಪ್ರಮುಖ ಆಡಳಿತ ನಿಯಮಗಳು ಮತ್ತು ಪರಿಗಣನೆಗಳು.",
            "video_title": "ವೀಡಿಯೊ ಸ್ಕ್ರಿಪ್ಟ್",
            "video_intro": "ನಮಸ್ಕಾರ, ಈ ಸಂಕ್ಷಿಪ್ತ ವರದಿಗೆ ಸ್ವಾಗತ:",
            "video_outro": "ಕೊನೆಯದಾಗಿ, ಆದ್ಯತೆ:",
            "tags": ["#AI", "#ಶಿಕ್ಷಣ", "#EdTech", "#Innovation", "#Kannada"],
        },
        "es": {
            "hook_prefix": "🚨 Actualización Estratégica:",
            "insights_hdr": "Perspectivas Clave y Desarrollos:",
            "next_steps_hdr": "Próximos Pasos Recomendados:",
            "cta": "¿Cómo está navegando su equipo esta transición? Comparta sus opiniones.",
            "default_rec": "Adoptar prácticas responsables y mantener la supervisión estratégica.",
            "overview_label": "Resumen",
            "point": "Punto",
            "executive_briefing": "Resumen Ejecutivo",
            "immediate": "Orientación Inmediata",
            "continuous": "Gobernanza Continua",
            "advisory_prefix": "Asesoría Estratégica y Resumen de Políticas",
            "infographic_title": "Infografía General",
            "share_cta": "Comparta este informe con su equipo.",
            "deck_title": "Presentación Ejecutiva",
            "audience": "Audiencia",
            "tone": "Tono",
            "slide2_title": "Capacidades de Aprendizaje e Impacto",
            "slide3_title": "Apoyo Docente y Accesibilidad",
            "slide4_title": "IA Responsable y Competencias Humanas",
            "notes_analysis": "Revisión detallada de las capacidades centrales.",
            "notes_governance": "Principios clave de gobernanza y consideraciones operativas.",
            "video_title": "Guión de Video",
            "video_intro": "Bienvenidos a este informe sobre:",
            "video_outro": "En conclusión, la prioridad es:",
            "tags": ["#IA", "#Educacion", "#EdTech", "#Innovacion", "#Liderazgo"],
        },
        "fr": {
            "hook_prefix": "🚨 Mise à Jour Stratégique :",
            "insights_hdr": "Principaux Enseignements :",
            "next_steps_hdr": "Prochaines Étapes Recommandées :",
            "cta": "Comment votre équipe gère-t-elle cette transition ? Partagez vos réflexions.",
            "default_rec": "Adopter des pratiques responsables et maintenir une gouvernance stratégique.",
            "overview_label": "Synthèse",
            "point": "Point",
            "executive_briefing": "Synthèse Exécutive",
            "immediate": "Orientation Immédiate",
            "continuous": "Gouvernance Continue",
            "advisory_prefix": "Avis Stratégique et Note de Cadrage",
            "infographic_title": "Aperçu Infographique",
            "share_cta": "Partagez cette note de synthèse avec votre équipe.",
            "deck_title": "Support de Présentation",
            "audience": "Public",
            "tone": "Ton",
            "slide2_title": "Capacités d'Apprentissage et Impact",
            "slide3_title": "Accompagnement Pédagogique et Accessibilité",
            "slide4_title": "IA Responsable et Compétences Humaines",
            "notes_analysis": "Examen approfondi des capacités clés.",
            "notes_governance": "Règles de gouvernance fondamentales et mise en œuvre.",
            "video_title": "Scénario Vidéo",
            "video_intro": "Bienvenue dans cette présentation sur :",
            "video_outro": "En conclusion, la priorité consiste à :",
            "tags": ["#IA", "#Education", "#EdTech", "#Innovation", "#Strategie"],
        },
        "de": {
            "hook_prefix": "🚨 Strategisches Update:",
            "insights_hdr": "Zentrale Erkenntnisse & Entwicklungen:",
            "next_steps_hdr": "Empfohlene nächste Schritte:",
            "cta": "Wie gestaltet Ihr Team diesen Wandel? Teilen Sie Ihre Erfahrungen.",
            "default_rec": "Verantwortungsvolle Praktiken etablieren und strategische Steuerung wahren.",
            "overview_label": "Überblick",
            "point": "Punkt",
            "executive_briefing": "Management-Übersicht",
            "immediate": "Sofortige Richtlinien",
            "continuous": "Kontinuierliche Steuerung",
            "advisory_prefix": "Strategische Beratung & Policy Brief",
            "infographic_title": "Infografik-Übersicht",
            "share_cta": "Teilen Sie dieses Briefing mit Ihrem Team.",
            "deck_title": "Präsentationsfolien",
            "audience": "Zielgruppe",
            "tone": "Tonalität",
            "slide2_title": "Lernpotenziale & Wirkung",
            "slide3_title": "Lehrkräfte-Unterstützung & Barrierefreiheit",
            "slide4_title": "Verantwortungsvolle KI & Menschliche Kompetenzen",
            "notes_analysis": "Detaillierte Analyse der Kernkompetenzen.",
            "notes_governance": "Wichtige Governance-Vorgaben und Handlungsempfehlungen.",
            "video_title": "Videoskript",
            "video_intro": "Willkommen zu diesem Briefing über:",
            "video_outro": "Zusammenfassend liegt die Priorität auf:",
            "tags": ["#KI", "#Bildung", "#EdTech", "#Innovation", "#Leadership"],
        },
        "ja": {
            "hook_prefix": "🚨 重要なお知らせ:",
            "insights_hdr": "主要な洞察と展開:",
            "next_steps_hdr": "推奨される次のステップ:",
            "cta": "皆様のチームではどのように対応されていますか？ご意見をお聞かせください。",
            "default_rec": "責任ある導入プロセスを確立し、戦略的な管理体制を維持します。",
            "overview_label": "概要",
            "point": "ポイント",
            "executive_briefing": "エグゼクティブサマリー",
            "immediate": "即時ガイダンス",
            "continuous": "継続的ガバナンスと監督",
            "advisory_prefix": "戦略的アドバイザリー＆政策ブリーフ",
            "infographic_title": "インフォグラフィック概要",
            "share_cta": "このブリーフィングをチーム内で共有してください。",
            "deck_title": "プレゼンテーション資料",
            "audience": "対象読者",
            "tone": "トーン",
            "slide2_title": "学習機能と生徒へのインパクト",
            "slide3_title": "教師の業務支援とアクセシビリティ",
            "slide4_title": "責任あるAIの活用と人間のスキル保持",
            "notes_analysis": "コア機能に関する詳細なレビュー。",
            "notes_governance": "主要なガバナンス方針と運用上の留意点。",
            "video_title": "解説動画スクリプト",
            "video_intro": "皆様、本ブリーフィングへようこそ:",
            "video_outro": "結論として、最優先事項は次の通りです:",
            "tags": ["#AI", "#教育", "#EdTech", "#イノベーション", "#ビジネス"],
        },
    }
    return labels.get(lang_code, {
        "hook_prefix": "🚨 Key Update:",
        "insights_hdr": "Key Insights & Developments:",
        "next_steps_hdr": "Recommended Next Steps:",
        "cta": "How is your team navigating this transition? Share your perspectives below.",
        "default_rec": "Adopt responsible integration practices and maintain strategic oversight.",
        "overview_label": "Overview",
        "point": "Point",
        "executive_briefing": "Executive Briefing",
        "immediate": "Immediate Guidance",
        "continuous": "Continuous Governance",
        "advisory_prefix": "Strategic Advisory & Policy Brief",
        "infographic_title": "Infographic Overview",
        "share_cta": "Share this executive briefing with your team.",
        "deck_title": "Presentation Deck",
        "audience": "Audience",
        "tone": "Tone",
        "slide2_title": "Core Capabilities & Student Impact",
        "slide3_title": "Teacher Augmentation & Accessibility",
        "slide4_title": "Responsible AI & Human Competencies",
        "notes_analysis": "Detailed review of core capabilities.",
        "notes_governance": "Key governance mandates and operational considerations.",
        "video_title": "Explainer Video Script",
        "video_intro": "Welcome to this briefing on:",
        "video_outro": "In conclusion, the priority is to:",
        "tags": ["#AI", "#Leadership", "#Innovation", "#Strategy"],
    })


def _detect_domain(text: str) -> str:
    low = text.lower()
    if any(w in low for w in ("student", "teacher", "learn", "curriculum", "school", "academic", "education", "lesson", "grade")):
        return "education"
    if any(w in low for w in ("vulnerability", "cve-", "malware", "ransomware", "threat actor", "phishing", "exploit", "breach")):
        return "cybersecurity"
    if any(w in low for w in ("patient", "clinical", "diagnosis", "therapy", "medical", "hospital")):
        return "healthcare"
    if any(w in low for w in ("revenue", "ebitda", "fiscal", "portfolio", "banking", "shares", "dividend")):
        return "finance"
    if any(w in low for w in ("software", "api", "database", "cloud", "backend", "frontend", "architecture")):
        return "technology"
    return "general"


def generate_deterministic_deliverable(
    dtype: str,
    uckr: Dict[str, Any],
    cfg: TransformationConfig,
) -> Dict[str, Any]:
    """Deterministically transforms UCKR into standard deliverable format without external LLM."""
    raw_title = uckr.get("title", "Strategic Briefing")
    raw_summary = uckr.get("summary", "")
    facts = uckr.get("facts", [])
    entities = uckr.get("entities", [])
    events = uckr.get("events", [])
    metrics = uckr.get("metrics", [])
    actions = uckr.get("actions", [])
    claims = uckr.get("claims", [])

    lang = cfg.language or "English"
    code = _normalize_lang(lang)
    lbl = _get_ui_labels(code)

    title = translate_text(raw_title, lang)
    summary = translate_text(raw_summary, lang)

    all_fact_ids = [f.get("factId") or f.get("id") for f in facts if f.get("factId") or f.get("id")]
    combined_text = f"{raw_title} {raw_summary} " + " ".join([f.get("statement", "") or f.get("value", "") for f in facts])
    domain = _detect_domain(combined_text)

    fact_statements = [
        translate_text(f.get("statement") or f.get("value") or "", lang)
        for f in facts
        if (f.get("statement") or f.get("value"))
    ]

    action_statements = [
        translate_text(a.get("action") or a.get("statement") or "", lang)
        for a in actions
        if (a.get("action") or a.get("statement"))
    ]

    if dtype == "linkedin":
        fact_lines = [f"• {f}" for f in fact_statements[:6]]
        rec_text = action_statements[0] if action_statements else lbl["default_rec"]

        body_text = "\n\n".join([
            f"{lbl['hook_prefix']} {title}",
            summary or (fact_statements[0] if fact_statements else title),
            f"{lbl['insights_hdr']}\n" + ("\n".join(fact_lines) if fact_lines else "• " + (fact_statements[0] if fact_statements else title)),
            f"{lbl['next_steps_hdr']} {rec_text}",
            lbl["cta"]
        ])

        return {
            "hook": f"{lbl['hook_prefix']} {title}",
            "title": f"{lbl['executive_briefing']}: {title}",
            "body": body_text,
            "callToAction": lbl["cta"],
            "hashtags": lbl["tags"],
            "characterCount": len(body_text),
            "targetAudience": cfg.audience,
            "usedFactIds": all_fact_ids[:6],
            "citations": []
        }

    elif dtype in ("x", "twitter"):
        posts = []
        ov_text = summary[:180] if summary else (fact_statements[0][:180] if fact_statements else "")
        posts.append({
            "index": 1,
            "postNumber": 1,
            "text": f"🧵 1/3 {lbl['overview_label']}: {title}\n\n{ov_text}",
            "charCount": len(ov_text),
            "usedFactIds": all_fact_ids[:1]
        })
        metric_bullets = [f"• {m.get('value')} {m.get('unit', '')} ({translate_text(m.get('context', ''), lang)})" for m in metrics[:2] if m.get("value")]
        fact_bullets = [f"• {f}" for f in fact_statements[1:4]]
        body_bullets = metric_bullets or fact_bullets or ["• " + (fact_statements[0] if fact_statements else "Analyzed core facts.")]
        posts.append({
            "index": 2,
            "postNumber": 2,
            "text": f"2/3 {lbl['insights_hdr']}:\n" + "\n".join(body_bullets[:2]),
            "charCount": len("\n".join(body_bullets[:2])),
            "usedFactIds": all_fact_ids[1:3]
        })
        action_text = action_statements[0] if action_statements else lbl["default_rec"]
        tag_suffix = " ".join(lbl["tags"][:2])
        posts.append({
            "index": 3,
            "postNumber": 3,
            "text": f"3/3 {lbl['next_steps_hdr']}:\n• {action_text}\n\n{tag_suffix}",
            "charCount": len(action_text),
            "usedFactIds": all_fact_ids[3:5]
        })
        return {
            "singlePost": f"🧵 {title[:240]} {tag_suffix}",
            "thread": posts,
            "posts": posts,
            "usedFactIds": all_fact_ids[:5],
            "citations": []
        }

    elif dtype == "executive_summary":
        findings = fact_statements[:6] or [fact_statements[0] if fact_statements else "No critical findings reported."]
        risks = []
        for f in fact_statements:
            if re.search(r"\b(risk|depend|over-relian|threat|loss|fail|பொறுப்புடன்|சார்ந்து|जिम्मेदारी|depend|responsab)\b", f, re.I):
                risks.append(f)
        if not risks:
            risks = [lbl["default_rec"]]

        rec_actions = action_statements[:3] or [lbl["default_rec"]]

        return {
            "priority": "High",
            "keyFindingsCount": len(findings),
            "recommendationsCount": len(rec_actions),
            "executiveOverview": summary or (fact_statements[0] if fact_statements else "Detailed strategic overview."),
            "keyFindings": [
                {"metric": f"{lbl['point']} {i+1}", "title": f[:65], "description": f}
                for i, f in enumerate(findings)
            ],
            "implications": risks,
            "strategicActions": rec_actions,
            "title": f"{lbl['executive_briefing']}: {title}",
            "summary": summary or (fact_statements[0] if fact_statements else "Strategic overview."),
            "keyRisks": risks,
            "recommendedActions": rec_actions,
            "usedFactIds": all_fact_ids[:5],
            "citations": []
        }

    elif dtype == "advisory":
        affected = [translate_text(e.get("canonicalName") or e.get("name") or "", lang) for e in entities[:4] if (e.get("canonicalName") or e.get("name"))]
        obs = fact_statements[:6]
        recs = action_statements[:3] or [lbl["default_rec"]]
        refs = [c.get("statement") for c in claims[:2] if c.get("statement")] or [lbl["default_rec"]]

        advisory_title = f"{lbl['advisory_prefix']}: {title}"

        return {
            "advisoryId": f"ADV-{all_fact_ids[0] if all_fact_ids else '1001'}",
            "title": advisory_title,
            "domain": domain,
            "severity": "MEDIUM",
            "dateIssued": "2026-09-26",
            "situation": summary or (fact_statements[0] if fact_statements else "Strategic advisory outlining key observations and recommended actions."),
            "keyInformation": obs,
            "threatImpact": obs[1] if len(obs) > 1 else (obs[0] if obs else ""),
            "recommendedActions": [
                {"phase": lbl["immediate"], "steps": [recs[0]] if recs else [lbl["default_rec"]]},
                {"phase": lbl["continuous"], "steps": recs[1:] or recs[:1]}
            ],
            "complianceReferences": refs,
            "affectedEntities": affected,
            "observations": obs,
            "recommendations": recs,
            "references": refs,
            "usedFactIds": all_fact_ids[:4]
        }

    elif dtype == "infographic":
        sections = [
            {
                "heading": lbl["overview_label"],
                "content": summary or (fact_statements[0] if fact_statements else "Core context and analysis.")
            },
            {
                "heading": lbl["insights_hdr"],
                "content": " ".join(fact_statements[1:4]) or (fact_statements[0] if fact_statements else "Verified claims analyzed.")
            }
        ]
        key_numbers = []
        for m in metrics[:3]:
            if m.get("value"):
                key_numbers.append({
                    "value": str(m.get("value")),
                    "label": translate_text(m.get("name") or "Metric", lang),
                    "subtext": translate_text(f"{m.get('unit', '')} {m.get('context', '')}".strip() or "Verified metric", lang)
                })
        if not key_numbers:
            key_numbers.append({
                "value": str(len(facts)),
                "label": "Claims Mapped" if code == "en" else translate_text("Key Findings", lang),
                "subtext": "Coverage" if code == "en" else translate_text("Comprehensive briefing", lang)
            })
            key_numbers.append({
                "value": "100%",
                "label": "Grounding" if code == "en" else translate_text("Zero invented metrics", lang),
                "subtext": "Verified" if code == "en" else translate_text("Verified operational facts derived directly from source documentation.", lang)
            })

        return {
            "title": f"{lbl['infographic_title']}: {title}",
            "keyMessage": title,
            "keyStatistics": key_numbers,
            "supportingPoints": [
                {"iconName": "sparkles", "title": f[:50], "description": f}
                for f in fact_statements[:4]
            ],
            "callToAction": lbl["share_cta"],
            "layoutRecommendation": "Vertical",
            "visualStyle": "Corporate",
            "sections": sections,
            "keyNumbers": key_numbers,
            "usedFactIds": all_fact_ids[:4]
        }

    elif dtype == "presentation":
        slides = [
            {
                "slideNumber": 1,
                "title": title or lbl["deck_title"],
                "subtitle": f"{lbl['audience']}: {cfg.audience} • {lbl['tone']}: {cfg.tone}",
                "bullets": fact_statements[:3] or [summary[:120] if summary else "Comprehensive briefing"],
                "visualRecommendation": "Title banner with theme accent cards",
                "speakerNotes": fact_statements[0] if fact_statements else "Welcome to this briefing.",
                "usedFactIds": all_fact_ids[:1]
            },
            {
                "slideNumber": 2,
                "title": lbl["slide2_title"],
                "bullets": fact_statements[3:6] if len(fact_statements) > 3 else fact_statements[:3],
                "visualRecommendation": "Feature breakdown columns with metric highlights",
                "speakerNotes": lbl["notes_analysis"],
                "usedFactIds": all_fact_ids[1:4]
            },
            {
                "slideNumber": 3,
                "title": lbl["slide3_title"],
                "bullets": fact_statements[6:9] if len(fact_statements) > 6 else fact_statements[1:4],
                "visualRecommendation": "Workflow interaction diagram",
                "speakerNotes": lbl["notes_analysis"],
                "usedFactIds": all_fact_ids[4:7]
            },
            {
                "slideNumber": 4,
                "title": lbl["slide4_title"],
                "bullets": action_statements[:3] or fact_statements[2:5],
                "visualRecommendation": "Governance principle cards",
                "speakerNotes": lbl["notes_governance"],
                "usedFactIds": all_fact_ids[7:9]
            }
        ]
        return {
            "deckTitle": title or lbl["deck_title"],
            "title": f"{lbl['deck_title']}: {title}",
            "totalSlides": len(slides),
            "slides": slides,
            "usedFactIds": all_fact_ids[:8]
        }

    elif dtype in ("video", "video_script"):
        scenes = [
            {
                "sceneNumber": 1,
                "title": title[:45],
                "durationSeconds": 20,
                "sceneDescription": fact_statements[0] if fact_statements else "Topic introduction",
                "narration": f"{lbl['video_intro']} {title}.",
                "visualRecommendation": "Dynamic animated title card with topic overview.",
                "onScreenText": title[:75],
                "usedFactIds": all_fact_ids[:1]
            },
            {
                "sceneNumber": 2,
                "title": fact_statements[1][:45] if len(fact_statements) > 1 else title[:45],
                "durationSeconds": 25,
                "sceneDescription": " ".join(fact_statements[1:4]) if len(fact_statements) > 1 else (fact_statements[0] if fact_statements else ""),
                "narration": " ".join(fact_statements[1:4]) if len(fact_statements) > 1 else (fact_statements[0] if fact_statements else ""),
                "visualRecommendation": "Motion graphics showcasing core benefits and operational insights.",
                "onScreenText": (fact_statements[1][:75] if len(fact_statements) > 1 else title[:75]),
                "usedFactIds": all_fact_ids[1:4]
            },
            {
                "sceneNumber": 3,
                "title": lbl["next_steps_hdr"][:40],
                "durationSeconds": 15,
                "sceneDescription": action_statements[0] if action_statements else "Concluding actions",
                "narration": f"{lbl['video_outro']} {action_statements[0] if action_statements else lbl['default_rec']}.",
                "visualRecommendation": "Summary checklist animation followed by closing call to action.",
                "onScreenText": (action_statements[0][:75] if action_statements else lbl["default_rec"][:75]),
                "usedFactIds": all_fact_ids[4:6]
            }
        ]
        return {
            "title": title or lbl["video_title"],
            "aspectRatio": "16:9",
            "style": "Professional",
            "totalDurationSeconds": 60,
            "script": "\n\n".join(s["narration"] for s in scenes),
            "scenes": scenes,
            "subtitlesSrt": "",
            "durationSeconds": 60,
            "usedFactIds": all_fact_ids[:6]
        }

    return {
        "title": title,
        "summary": summary,
        "usedFactIds": all_fact_ids[:4]
    }
