"""Newsletter related constants."""

REFLECTION_MAP = {
    "1": {
        "folder_name":"top_news",
        "zh": "🌎 今日头条",
        "en": "🌎 Top News",
        # "ja": "🌎 今日のトップニュース",
        # "ko": "🌎 오늘의 주요 뉴스",
        # "de": "🌎 Top-Nachrichten",
        # "es": "🌎 Noticias Principales",
        # "fr": "🌎 Actualités Principales",
        # "it": "🌎 Notizie Principali",
        # "nl": "🌎 Topnieuws",
        # "pl": "🌎 Główne Wiadomości",
        # "pt": "🌎 Notícias Principais",
        # "da": "🌎 Top Nyheder",
        # "id": "🌎 Berita Utama",
        # "tr": "🌎 En Büyük Haberler",
    },
    "2": {
        "folder_name":"finance",
        "zh": "📈 金融动态",
        "en": "📈 Finance News",
        # "ja": "📈 金融ニュース",
        # "ko": "📈 금융 뉴스",
        # "de": "📈 Finanznachrichten",
        # "es": "📈 Noticias Financieras",
        # "fr": "📈 Actualités Financières",
        # "it": "📈 Notizie Finanziarie",
        # "nl": "📈 Financieel Nieuws",
        # "pl": "📈 Wiadomości Finansowe"
    },
    "3": {
        "folder_name":"startup",
        "zh": "🚀 初创动态",
        "en": "🚀 Startup News",
        # "ja": "🚀 スタートアップニュース",
        # "ko": "🚀 스타트업 뉴스",
        # "de": "🚀 Startup-Nachrichten",
        # "es": "🚀 Noticias de Startups",
        # "fr": "🚀 Actualités des Startups",
        # "it": "🚀 Notizie sulle Startup",
        # "nl": "🚀 Startup-Nieuws",
        # "pl": "🚀 Wiadomości o Startupach"
    },
    "4": {
        "folder_name":"tech",
        "zh": "💻 科技前沿",
        "en": "💻 Tech Trends",
        # "ja": "💻 テックトレンド",
        # "ko": "💻 기술 트렌드",
        # "de": "💻 Technologie-Trends",
        # "es": "💻 Tendencias Tecnológicas",
        # "fr": "💻 Tendances Technologiques",
        # "it": "💻 Tendenze Tecnologiche",
        # "nl": "💻 Technologische Trends",
        # "pl": "💻 Trendy Technologiczne"
    },
    "5": {
        "folder_name":"ai",
        "zh": "🤖 AI洞察",
        "en": "🤖 AI Insights",
        # "ja": "🤖 AIインサイト",
        # "ko": "🤖 AI 인사이트",
        # "de": "🤖 KI-Einblicke",
        # "es": "🤖 Perspectivas de IA",
        # "fr": "🤖 Perspectives IA",
        # "it": "🤖 Approfondimenti IA",
        # "nl": "🤖 AI-Inzichten",
        # "pl": "🤖 Wgląd w AI"
    },
    "6": {
        "folder_name":"web3",
        "zh": "🌐 Web3前沿",
        "en": "🌐 Web3 Insights",
        # "ja": "🌐 Web3インサイト",
        # "ko": "🌐 Web3 인사이트",
        # "de": "🌐 Web3-Einblicke",
        # "es": "🌐 Perspectivas Web3",
        # "fr": "🌐 Perspectives Web3",
        # "it": "🌐 Approfondimenti Web3",
        # "nl": "🌐 Web3-Inzichten",
        # "pl": "🌐 Wgląd w Web3"
    },
    "7": {
        "folder_name":"business",
        "zh": "💰 商业动态",
        "en": "💰 Business Insights",
    },
    "8": {
        "folder_name":"economy",
        "zh": "💰 经济动态",
        "en": "💰 Economy Insights",
    }
}

LANGUAGE_MAP = {
    "zh": {
        "name": "中文",
        "prompt": "Use concise phrasing, natural word order, and expressions typical of high-quality Chinese news reporting, avoiding overly formal or literal translations of English structures.",
        "date_format": "%Y年%m月%d日",
        "seo_title_template": "Deeper AI 新闻摘要 - {date}",
        "translations": {
            "home": "首页",
            "curated_by": "由DeeperAI整理",
            "back_to_home": "返回首页",
            "footer_copyright": "© 2025 DeeperAI。版权所有。",
            "visit_homepage": "访问我们的主页"
        }
    },
    "en": {
        "name": "English",
        "prompt": "Employ clear, precise language with a neutral and professional tone, using idiomatic expressions and structures typical of high-quality English journalism.",
        "date_format": "%B %d, %Y",
        "seo_title_template": "Deeper AI Digest - {date}",
        "translations": {
            "home": "Home",
            "curated_by": "Curated by DeeperAI",
            "back_to_home": "Back to Homepage",
            "footer_copyright": "© 2025 DeeperAI. All rights reserved.",
            "visit_homepage": "Visit our homepage"
        }
    },
    # "ja": {
    #     "name": "Japan",
    #     "prompt": "Use polite, concise phrasing with natural Japanese syntax, incorporating formal yet accessible vocabulary typical of high-quality Japanese news reporting.",
    #     "date_format": "%Y年%m月%d日",
    #     "seo_title_template": "Deeper AI ダイジェスト - {date}",
    #     "translations": {
    #         "home": "ホーム",
    #         "curated_by": "DeeperAIによるキュレーション",
    #         "back_to_home": "ホームページに戻る",
    #         "footer_copyright": "© 2025 DeeperAI。すべての権利を保有。",
    #         "visit_homepage": "ホームページをご覧ください"
    #     }
    # },
    # "ko": {
    #     "name": "Korean",
    #     "prompt": "Adopt clear, respectful language with natural flow and precise expressions, reflecting the formal and engaging style of high-quality Korean news writing.",
    #     "date_format": "%Y년 %m월 %d일",
    #     "seo_title_template": "Deeper AI 다이제스트 - {date}",
    #     "translations": {
    #         "home": "홈",
    #         "curated_by": "DeeperAI가 큐레이션함",
    #         "back_to_home": "홈페이지로 돌아가기",
    #         "footer_copyright": "© 2025 DeeperAI. 모든 권리 보유.",
    #         "visit_homepage": "홈페이지 방문"
    #     }
    # },
    # "de": {
    #     "name": "German",
    #     "prompt": "Use precise, structured sentences with accurate compound words and a formal tone, aligning with the factual and detailed style of German news reporting.",
    #     "date_format": "%d. %B %Y",
    #     "seo_title_template": "Deeper AI Digest - {date}",
    #     "translations": {
    #         "home": "Startseite",
    #         "curated_by": "Kuriert von DeeperAI",
    #         "back_to_home": "Zurück zur Startseite",
    #         "footer_copyright": "© 2025 DeeperAI. Alle Rechte vorbehalten.",
    #         "visit_homepage": "Besuchen Sie unsere Startseite"
    #     }
    # },
    # "es": {
    #     "name": "Spanish",
    #     "prompt": "Employ clear, direct phrasing with a focus on readability and emotional resonance, reflecting the dynamic and expressive style of Spanish news writing.",
    #     "date_format": "%d de %B de %Y",
    #     "seo_title_template": "Resumen de Deeper AI - {date}",
    #     "translations": {
    #         "home": "Inicio",
    #         "curated_by": "Curado por DeeperAI",
    #         "back_to_home": "Volver a la página de inicio",
    #         "footer_copyright": "© 2025 DeeperAI. Todos los derechos reservados.",
    #         "visit_homepage": "Visita nuestra página de inicio"
    #     }
    # },
    # "fr": {
    #     "name": "France",
    #     "prompt": "Prioritize elegance, precision, and clarity, using sophisticated yet accessible vocabulary and sentence structures typical of French journalism.",
    #     "date_format": "%d %B %Y",
    #     "seo_title_template": "Digest Deeper AI - {date}",
    #     "translations": {
    #         "home": "Accueil",
    #         "curated_by": "Curaté par DeeperAI",
    #         "back_to_home": "Retour à la page d'accueil",
    #         "footer_copyright": "© 2025 DeeperAI. Tous droits réservés.",
    #         "visit_homepage": "Visitez notre page d'accueil"
    #     }
    # },
    # "it": {
    #     "name": "Italiano",
    #     "prompt": "Use fluid, expressive language with a balance of formality and warmth, incorporating vivid vocabulary typical of high-quality Italian news reporting.",
    #     "date_format": "%d %B %Y",
    #     "seo_title_template": "Deeper AI Digest - {date}",
    #     "translations": {
    #         "home": "Home",
    #         "curated_by": "Curato da DeeperAI",
    #         "back_to_home": "Torna alla homepage",
    #         "footer_copyright": "© 2025 DeeperAI. Tutti i diritti riservati.",
    #         "visit_homepage": "Visita la nostra homepage"
    #     }
    # },
    # "nl": {
    #     "name": "Dutch",
    #     "prompt": "Adopt clear, straightforward phrasing with a formal yet approachable tone, reflecting the pragmatic and precise style of Dutch news writing.",
    #     "date_format": "%d %B %Y",
    #     "seo_title_template": "Deeper AI Digest - {date}",
    #     "translations": {
    #         "home": "Home",
    #         "curated_by": "Samengesteld door DeeperAI",
    #         "back_to_home": "Terug naar de homepage",
    #         "footer_copyright": "© 2025 DeeperAI. Alle rechten voorbehouden.",
    #         "visit_homepage": "Bezoek onze homepage"
    #     }
    # },
    # "pl": {
    #     "name": "Poland",
    #     "prompt": "Use precise, formal language with clear sentence structures, incorporating expressive yet professional vocabulary typical of Polish news reporting.",
    #     "date_format": "%d %B %Y",
    #     "seo_title_template": "Deeper AI Digest - {date}",
    #     "translations": {
    #         "home": "Strona główna",
    #         "curated_by": "Kurator: DeeperAI",
    #         "back_to_home": "Powrót do strony głównej",
    #         "footer_copyright": "© 2025 DeeperAI. Wszystkie prawa zastrzeżone.",
    #         "visit_homepage": "Odwiedź naszą stronę główną"
    #     }
    # },
    # "pt": {
    #     "name": "Portuguese",
    # },
    # "da": {
    #     "name": "Danish",
    # },
    # "id": {
    #     "name": "Indonesian",
    # },
    # "tr": {
    #     "name": "Turkish",
    # },
}