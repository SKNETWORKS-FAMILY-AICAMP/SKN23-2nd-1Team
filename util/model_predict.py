
import pandas as pd
import numpy as np
import re


from collections import Counter



def churn_predict(df):
    df# 상위 50개 게임으로만 이루어진 데이터
    appid_counts = df['appid'].value_counts()
    top50_appids = appid_counts.head(50).index.tolist()
    df_top50 = df[df['appid'].isin(top50_appids)].copy()
    df_model = df_top50.drop(columns=['deck_playtime_at_review', 'developer_response', 'timestamp_dev_responded'])

    # Top50 기반으로 매핑 (네가 적어준 game_style 그대로 반영)
    # ※ 기존 29개에 없던 appid도 포함해서 업데이트

    STYLE_MAP = {
        3241660: "online",  # R.E.P.O
        2807960: "online",  # Battlefield™ 6
        730:     "online",  # Counter-Strike 2
        1808500: "online",  # ARC Raiders
        1030300: "story",   # Hollow Knight: Silksong
        570:     "online",  # Dota 2
        578080:  "online",  # PUBG
        2246340: "video",   # Monster Hunter Wilds
        2592160: "story",   # Dispatch
        553850:  "online",  # HELLDIVERS™ 2
        3240220: "online",  # Grand Theft Auto V Enhanced
        1091500: "story",   # Cyberpunk 2077
        1903340: "video",   # Clair Obscur: Expedition 33
        2001120: "story",   # Split Fiction
        1245620: "video",   # Elden Ring
        1086940: "video",   # Baldur's Gate 3
        1144200: "online",  # Ready or Not
        3167020: "video",   # Escape From Duckov
        3564740: "online",  # Where Winds Meet
        227300:  "video",   # Euro Truck Simulator 2
        108600:  "video",   # Project Zomboid
        413150:  "video",   # Stardew Valley
        1771300: "video",   # Kingdom Come 2
        3489700: "story",   # Stellar Blade™
        1172470: "online",  # Apex
        1222140: "story",   # Detroit: Become Human
        1326470: "video",   # Sons Of The Forest
        990080:  "story",   # Hogwarts Legacy
        1551360: "video",   # Forza Horizon 5
        1623730: "video",   # Palworld
        1145350: "video",   # Hades II
        2183900: "story",   # Space Marine AE
        230410:  "online",  # Warframe
        2139460: "online",  # Once Human
        236390:  "online",  # War Thunder
        440:     "online",  # Team Fortress 2
        1973530: "online",  # Limbus Company
        394360:  "video",   # Hearts of Iron IV
        3932890: "online",  # Escape from Tarkov
        526870:  "video",   # Satisfactory
        3513350: "online",  # Wuthering Waves
        3405690: "online",  # EA SPORTS FC™ 26
        2622380: "video",   # ELDEN RING NIGHTREIGN
        814380:  "video",   # Sekiro™: Shadows Die Twice - GOTY Edition
        648800:  "video",   # Raft
        3159330: "story",   # Assassin’s Creed Shadows
        3527290: "video",   # PEAK
        2651280: "story",   # Spider-Man 2
        294100:  "video",   # RimWorld
        1222670: "video",   # The Sims 4
    }

    # game_style 컬럼 생성
    df_model["game_style"] = df_model["appid"].map(STYLE_MAP)

    # appid별 review 결측치 분포
    review_na_by_app = (
        df_model.groupby("appid")["review"]
        .apply(lambda s: s.isna().sum())
        .rename("review_na_cnt")
        .to_frame()
    )

    # appid별 전체 행 수
    total_by_app = df_model.groupby("appid").size().rename("total_cnt").to_frame()

    # 합치기 + 비율
    review_na_stats = (
        total_by_app.join(review_na_by_app, how="left")
                    .fillna({"review_na_cnt": 0})
    )

    review_na_stats["review_na_ratio"] = review_na_stats["review_na_cnt"] / review_na_stats["total_cnt"]

    # 결측치 많은 순으로 확인
    review_na_stats.sort_values("review_na_cnt", ascending=False).head(30)

    # review NaN 드롭
    before = len(df_model)
    df_model = df_model[df_model["review"].notna()].copy()
    after = len(df_model)
    
    df_model[['review']].isna().sum()
    
    # 공백/빈문자열(whitespace-only 포함) 마스크
    blank_mask = df_model["review"].astype(str).str.strip().eq("")

    blank_by_appid = (
        df_model.assign(is_blank_review=blank_mask)
                .groupby("appid")["is_blank_review"]
                .agg(total_cnt="size", blank_cnt="sum")
    )

    blank_by_appid["blank_ratio"] = blank_by_appid["blank_cnt"] / blank_by_appid["total_cnt"]

    # 공백 리뷰가 있는 appid만, blank_cnt 큰 순으로 보기
    blank_by_appid_nonzero = blank_by_appid[blank_by_appid["blank_cnt"] > 0].sort_values("blank_cnt", ascending=False)

    # 공백/빈 문자열 리뷰 드롭
    before = len(df_model)

    blank_mask = df_model["review"].astype(str).str.strip().eq("")
    df_model = df_model[~blank_mask].copy()

    after = len(df_model)
    print(f"[drop blank review] before={before:,} -> after={after:,} (dropped {before-after:,})")

    # style별 churn 기준일(일 단위)
    STYLE_WINDOW_DAYS = {
        "online": 7,
        "video": 10,
        "story": 5,
    }

    # 리뷰 시각 / 마지막 플레이 시각
    review_dt = pd.to_datetime(df_model["timestamp_created"], unit="s", errors="coerce")
    last_dt   = pd.to_datetime(df_model["last_played"], unit="s", errors="coerce")

    # 리뷰 이후 며칠 뒤에 마지막 플레이가 있었는지
    df_model["days_after_review"] = (last_dt - review_dt).dt.days

    # game_style별 기준일 매핑 (none은 NaN)
    df_model["churn_window_days"] = df_model["game_style"].map(STYLE_WINDOW_DAYS)

    # 기본 churn: days_after_review < window 이면 churn=1 (떠난 것)
    # - window가 없는(none) 행은 일단 NaN으로 둠(나중에 제외/처리)
    df_model["churn"] = df_model["days_after_review"] < df_model["churn_window_days"].astype(int)


    # 예외 처리(기존에 하던 규칙 유지)
    df_model.loc[df_model["last_played"] == 0, "churn"] = 1
    df_model.loc[df_model["days_after_review"] < 0, "churn"] = 1

    # 1) 언어별 키워드 사전
    # - phrases: 문장/구문(부분일치 OK)
    # - words: 단어성 키워드(라틴권은 단어경계 \b 적용)
    # - neg: 부정 구문(걸리면 good=0으로 처리)
    # - boundary: words에 \b를 붙일지 여부 (중국어/일본어/태국어/한국어는 보통 False)
    LEXICON = {
        # English
        "english": {
            "phrases": [
                r"highly recommend(?:ed)?",
                r"definitely recommend",
                r"worth (?:buying|it|the money|the time)",
                r"great game",
                r"amazing game",
                r"awesome game",
                r"best game(?:s)?",
            ],
            "words": [
                r"awesome", r"amazing", r"great", r"excellent", r"fantastic", r"incredible",
                r"masterpiece", r"perfect", r"love", r"fun", r"enjoy", r"recommend", r"worth",
            ],
            "neg": [
                r"not\s+good", r"not\s+great", r"not\s+worth",
                r"(?:do\s*not|don't|dont)\s+recommend",
                r"(?:do\s*not|don't|dont)\s+buy",
                r"can't\s+recommend|cant\s+recommend",
                r"avoid\b", r"refund\b",
            ],
            "boundary": True,
        },

        # Spanish (Spain) + LatAm는 같이 처리
        "spanish": {
            "phrases": [r"muy bueno", r"vale la pena", r"lo recomiendo", r"recomendad[oa]"],
            "words": [r"genial", r"excelente", r"buen[oa]", r"incre[ií]ble", r"recomiendo", r"recomendar"],
            "neg": [r"no\s+recomiendo", r"no\s+vale\s+la\s+pena", r"no\s+es\s+buen[oa]", r"no\s+merece\s+la\s+pena", r"no\s+compr(?:es|ar)"],
            "boundary": True,
        },
        "latam": {  # 라틴아메리카 스페인어
            "phrases": [r"muy bueno", r"vale la pena", r"lo recomiendo", r"recomendad[oa]"],
            "words": [r"genial", r"excelente", r"buen[oa]", r"incre[ií]ble", r"recomiendo", r"recomendar"],
            "neg": [r"no\s+recomiendo", r"no\s+vale\s+la\s+pena", r"no\s+es\s+buen[oa]", r"no\s+merece\s+la\s+pena", r"no\s+compr(?:es|ar)"],
            "boundary": True,
        },

        # Portuguese (PT / BR)
        "portuguese": {
            "phrases": [r"vale a pena", r"recomendo", r"muito bom", r"jogo (?:muito )?bom"],
            "words": [r"ótimo", r"excelente", r"incr[ií]vel", r"perfeito", r"divertido", r"recomendar"],
            "neg": [r"não\s+recomendo", r"nao\s+recomendo", r"não\s+vale\s+a\s+pena", r"nao\s+vale\s+a\s+pena", r"não\s+é\s+bom", r"nao\s+e\s+bom", r"não\s+compr(?:e|ar)", r"nao\s+compr(?:e|ar)"],
            "boundary": True,
        },
        "brazilian": {  # 브라질 포르투갈어
            "phrases": [r"vale a pena", r"recomendo", r"muito bom", r"jogo (?:muito )?bom"],
            "words": [r"ótimo", r"excelente", r"incr[ií]vel", r"perfeito", r"divertido", r"recomendar"],
            "neg": [r"não\s+recomendo", r"nao\s+recomendo", r"não\s+vale\s+a\s+pena", r"nao\s+vale\s+a\s+pena", r"não\s+é\s+bom", r"nao\s+e\s+bom", r"não\s+compr(?:e|ar)", r"nao\s+compr(?:e|ar)"],
            "boundary": True,
        },

        # German
        "german": {
            "phrases": [r"sehr gut", r"klare(?:s)? empfehlung", r"lohnt sich", r"absolut empfehl"],
            "words": [r"genial", r"toll", r"super", r"großartig", r"exzellent", r"empfehle", r"empfehlenswert"],
            "neg": [r"nicht\s+empfehl", r"lohnt\s+sich\s+nicht", r"nicht\s+gut", r"kau(?:f|ft)\s+nicht", r"kein\s+kauf"],
            "boundary": True,
        },

        # French
        "french": {
            "phrases": [r"je recommande", r"vaut le coup", r"tr[eè]s bon", r"excellent jeu"],
            "words": [r"g[eé]nial", r"excellent", r"super", r"incroyable", r"parfait", r"recommande"],
            "neg": [r"je\s+ne\s+recommande\s+pas", r"ne\s+vaut\s+pas\s+le\s+coup", r"pas\s+bon", r"n['’]achetez\s+pas", r"n['’]ach[eè]te\s+pas"],
            "boundary": True,
        },

        # Italian
        "italian": {
            "phrases": [r"lo consiglio", r"vale la pena", r"molto bello", r"gioco (?:molto )?bello"],
            "words": [r"fantastico", r"ottimo", r"eccellente", r"stupendo", r"divertente", r"consiglio", r"consigliare"],
            "neg": [r"non\s+lo\s+consiglio", r"non\s+vale\s+la\s+pena", r"non\s+[eè]\s+bello", r"non\s+compr(?:are|atelo)"],
            "boundary": True,
        },

        # Dutch
        "dutch": {
            "phrases": [r"zeker aanraden", r"de moeite waard", r"heel goed", r"geweldig spel"],
            "words": [r"geweldig", r"fantastisch", r"super", r"leuk", r"aanraden", r"aanbevelen", r"waarde"],
            "neg": [r"niet\s+aanrad", r"niet\s+de\s+moeite\s+waard", r"niet\s+goed", r"koop\s+niet"],
            "boundary": True,
        },

        # Swedish / Norwegian / Danish / Finnish
        "swedish": {
            "phrases": [r"rekommenderar", r"värt det", r"jättebra", r"riktigt bra"],
            "words": [r"fantastisk", r"grym", r"suverän", r"toppen", r"kul", r"rekommendera", r"värd"],
            "neg": [r"rekommenderar\s+inte", r"inte\s+värt", r"inte\s+bra", r"köp\s+inte"],
            "boundary": True,
        },
        "norwegian": {
            "phrases": [r"anbefaler", r"verdt det", r"kjempebra", r"veldig bra"],
            "words": [r"fantastisk", r"råbra", r"suveren", r"gøy", r"anbefale", r"verdt"],
            "neg": [r"anbefaler\s+ikke", r"ikke\s+verdt", r"ikke\s+bra", r"ikke\s+kjøp"],
            "boundary": True,
        },
        "danish": {
            "phrases": [r"anbefaler", r"v[æa]rd at", r"mega god", r"rigtig god"],
            "words": [r"fantastisk", r"fremragende", r"super", r"sjov", r"anbefale", r"v[æa]rd"],
            "neg": [r"anbefaler\s+ikke", r"ikke\s+v[æa]rd", r"ikke\s+god", r"k[oø]b\s+ikke"],
            "boundary": True,
        },
        "finnish": {
            "phrases": [r"suosittelen", r"todella hyv[äa]", r"sen arvoinen", r"hyv[äa] peli"],
            "words": [r"loistava", r"mahtava", r"erinomainen", r"hauska", r"suositella", r"arvoinen"],
            "neg": [r"en\s+suosittele", r"ei\s+kannata", r"ei\s+hyv[äa]", r"älä\s+osta"],
            "boundary": True,
        },

        # Polish / Czech / Romanian / Hungarian / Bulgarian / Greek / Ukrainian / Russian / Turkish
        "polish": {
            "phrases": [r"polecam", r"warto", r"świetna gra", r"bardzo dobra"],
            "words": [r"świetn[aey]", r"super", r"rewelacyjna", r"doskonała", r"polecić", r"warto"],
            "neg": [r"nie\s+polecam", r"nie\s+warto", r"nie\s+jest\s+dobr", r"nie\s+kupuj"],
            "boundary": True,
        },
        "czech": {
            "phrases": [r"doporu[čc]uji", r"stoj[ií]\s+za\s+to", r"skv[ěe]l[aá]", r"v[ýy]born[aá]"],
            "words": [r"super", r"skv[ěe]l", r"v[ýy]born", r"bav[ií]", r"doporu[čc]it"],
            "neg": [r"nedoporu[čc]uji", r"nestoj[ií]\s+za\s+to", r"nen[ií]\s+dobr", r"nekupuj"],
            "boundary": True,
        },
        "romanian": {
            "phrases": [r"recomand", r"merit[ăa]", r"foarte bun", r"joc (?:foarte )?bun"],
            "words": [r"excelent", r"minunat", r"super", r"recomanda", r"merit"],
            "neg": [r"nu\s+recomand", r"nu\s+merit[ăa]", r"nu\s+e\s+bun", r"nu\s+cump[ăa]ra"],
            "boundary": True,
        },
        "hungarian": {
            "phrases": [r"aj[aá]nlom", r"meg[eé]ri", r"nagyon j[oó]", r"szuper j[aá]t[eé]k"],
            "words": [r"szuper", r"fantasztikus", r"kiv[aá]l[oó]", r"nagyon", r"aj[aá]nlani", r"meg[eé]r"],
            "neg": [r"nem\s+aj[aá]nlom", r"nem\s+[eé]ri\s+meg", r"nem\s+j[oó]", r"ne\s+vedd\s+meg"],
            "boundary": True,
        },
        "bulgarian": {
            "phrases": [r"препоръч", r"много добра", r"страхотна", r"заслужава си"],
            "words": [r"страхот", r"отлич", r"супер", r"препоръч", r"шедьовър"],
            "neg": [r"не\s+препоръч", r"не\s+си\s+струва", r"не\s+е\s+доб", r"не\s+купувай"],
            "boundary": False,  # кир릴은 \b가 애매해서 단순부분일치로
        },
        "greek": {
            "phrases": [r"το\s+προτείν", r"αξίζει", r"πολύ\s+καλ", r"εξαιρετικ"],
            "words": [r"τέλει", r"φοβε", r"εξαιρετικ", r"καταπληκτικ", r"προτείν", r"αξίζ"],
            "neg": [r"δεν\s+προτείν", r"δεν\s+αξίζ", r"δεν\s+είναι\s+καλ", r"μην\s+αγοράσ"],
            "boundary": False,
        },
        "ukrainian": {
            "phrases": [r"рекоменд", r"дуже\s+хорош", r"варто", r"чудов"],
            "words": [r"відмін", r"класн", r"шедевр", r"рекоменд", r"варто"],
            "neg": [r"не\s+рекоменд", r"не\s+варто", r"не\s+хорош", r"не\s+купуй"],
            "boundary": False,
        },
        "russian": {
            "phrases": [r"рекоменд", r"очень\s+хорош", r"стоит", r"шедевр"],
            "words": [r"отлич", r"классн", r"супер", r"шедевр", r"рекоменд", r"стоит"],
            "neg": [r"не\s+рекоменд", r"не\s+стоит", r"плох", r"не\s+покупай", r"не\s+берите"],
            "boundary": False,
        },
        "turkish": {
            "phrases": [r"kesinlikle tavsiye", r"tavsiye ederim", r"çok iyi", r"mükemmel", r"harika"],
            "words": [r"güzel", r"mükemmel", r"harika", r"şahane", r"tavsiye", r"değer"],
            "neg": [r"tavsiye etmem", r"tavsiye etmiyorum", r"iyi değil", r"alma", r"almayın", r"değmez"],
            "boundary": True,
        },

        # Korean / Japanese / Chinese / Arabic / Thai / Vietnamese / Indonesian
        "koreana": {
            "phrases": [r"강추", r"완전 추천", r"강력 추천", r"갓겜", r"명작", r"존잼", r"개꿀잼", r"재밌", r"재미있"],
            "words": [r"추천", r"최고", r"꿀잼", r"재미", r"좋다", r"훌륭", r"완벽", r"감동"],
            "neg": [r"비추", r"추천\s*안", r"추천\s*하지", r"재미없", r"별로", r"최악", r"사지\s*마", r"사지마", r"환불"],
            "boundary": False,
        },
        "japanese": {
            "phrases": [r"おすすめ", r"オススメ", r"最高", r"神ゲー", r"買う価値", r"面白い", r"楽しい"],
            "words": [r"おすすめ", r"最高", r"神", r"面白", r"楽しい", r"良い", r"素晴らしい"],
            "neg": [r"おすすめしない", r"買わない方が", r"つまらない", r"面白くない", r"最悪", r"返品"],
            "boundary": False,
        },
        "schinese": {
            "phrases": [r"强烈推荐", r"非常推荐", r"值得买", r"值得入", r"很值得", r"很好玩", r"神作", r"精品"],
            "words": [r"推荐", r"值得", r"好玩", r"很好", r"优秀", r"完美", r"喜欢"],
            "neg": [r"不推荐", r"不值得", r"不好玩", r"垃圾", r"别买", r"千万别买", r"退款"],
            "boundary": False,
        },
        "tchinese": {
            "phrases": [r"強烈推薦", r"非常推薦", r"值得買", r"值得入", r"很值得", r"很好玩", r"神作", r"精品"],
            "words": [r"推薦", r"值得", r"好玩", r"很好", r"優秀", r"完美", r"喜歡"],
            "neg": [r"不推薦", r"不值得", r"不好玩", r"垃圾", r"別買", r"千萬別買", r"退款"],
            "boundary": False,
        },
        "arabic": {
            "phrases": [r"أنصح", r"ممتاز", r"رائع", r"يستحق", r"لعبة رائعة", r"ممتعة"],
            "words": [r"ممتاز", r"رائع", r"جميل", r"ممتع", r"يستحق", r"أنصح"],
            "neg": [r"لا\s+أنصح", r"لا\s+يستحق", r"سيئ", r"لا\s+تشتري", r"استرجاع"],
            "boundary": False,
        },
        "thai": {
            "phrases": [r"แนะนำ", r"ดีมาก", r"สุดยอด", r"คุ้มค่า", r"สนุกมาก", r"โคตรสนุก"],
            "words": [r"แนะนำ", r"ดี", r"สนุก", r"สุดยอด", r"คุ้ม", r"ชอบ"],
            "neg": [r"ไม่แนะนำ", r"ไม่คุ้ม", r"ไม่ดี", r"แย่", r"อย่าซื้อ", r"ขอคืนเงิน"],
            "boundary": False,
        },
        "vietnamese": {
            "phrases": [r"rất hay", r"tuyệt vời", r"đáng mua", r"đáng tiền", r"nên mua", r"khuyên dùng"],
            "words": [r"hay", r"tuyệt", r"xuất sắc", r"đáng", r"thích", r"khuyên", r"nên"],
            "neg": [r"không\s+khuyên", r"không\s+đáng", r"đừng\s+mua", r"tệ", r"chán", r"hoàn tiền"],
            "boundary": True,
        },
        "indonesian": {
            "phrases": [r"sangat bagus", r"rekomendasi", r"worth it", r"layak dibeli", r"seru banget"],
            "words": [r"bagus", r"keren", r"mantap", r"seru", r"rekomend", r"layak"],
            "neg": [r"tidak\s+rekomend", r"jangan\s+beli", r"tidak\s+layak", r"jelek", r"buruk", r"refund"],
            "boundary": True,
        },
    }

    # 없는 언어는 english로 fallback
    DEFAULT_LANG = "english"


    # 2) 정규식 빌더
    def _compile_lexicon(cfg):
        boundary = cfg.get("boundary", True)

        parts_good = []
        for p in cfg.get("phrases", []):
            parts_good.append(f"(?:{p})")
        for w in cfg.get("words", []):
            if boundary:
                parts_good.append(rf"\b{w}\b")
            else:
                parts_good.append(f"(?:{w})")

        good_pat = "|".join(parts_good) if parts_good else r"$^"
        good_re = re.compile(good_pat, flags=re.UNICODE)

        neg_parts = [f"(?:{p})" for p in cfg.get("neg", [])]
        neg_pat = "|".join(neg_parts) if neg_parts else r"$^"
        neg_re = re.compile(neg_pat, flags=re.UNICODE)

        return good_re, neg_re


    _COMPILED = {}
    for lang, cfg in LEXICON.items():
        _COMPILED[lang] = _compile_lexicon(cfg)
    _COMPILED[DEFAULT_LANG] = _COMPILED.get(DEFAULT_LANG, _compile_lexicon(LEXICON["english"]))


    def add_good_flag_multilang(df_model, text_col="review", lang_col="language"):
        out = df_model.copy()

        text = out[text_col].fillna("").astype(str).str.casefold()
        lang = out[lang_col].fillna(DEFAULT_LANG).astype(str)

        good_hit = pd.Series(False, index=out.index)
        neg_hit  = pd.Series(False, index=out.index)

        for l in lang.unique():
            mask = (lang == l)
            good_re, neg_re = _COMPILED.get(l, _COMPILED[DEFAULT_LANG])

            good_hit.loc[mask] = text.loc[mask].str.contains(good_re, regex=True)
            neg_hit.loc[mask]  = text.loc[mask].str.contains(neg_re,  regex=True)

        out["good_review"] = (good_hit & (~neg_hit)).astype(int)
        return out


    # df_good = add_good_flag_multilang(df, text_col="review", lang_col="language")
    # print(df_good["good_review"].value_counts())
    df_model = add_good_flag_multilang(df_model, text_col="review", lang_col="language")
    print(df_model["good_review"].value_counts())
    
    ### 추가한 파생변수..

    # 1. 리뷰 시점 플레이 집중도 (플레이타임 “규모” → “강도 / 몰입도”로 바꾸기)
    # 게임 많이 가진데 이 게임만 오래 함 → 비이탈 / 게임 많고 얕게만 함 → 이탈 가능성↑
    df_model['playtime_per_game'] = np.log1p(df_model['playtime_at_review'] / (df_model['num_games_owned'] + 1))


    # 2. 리뷰 작성 시점의 몰입 단계 => churn과 매우 잘 갈림 (충성도?)

    # log 변환
    df_model['log_playtime'] = np.log1p(df_model['playtime_at_review'])
    # 구간 나누기
    bins = [-np.inf, 4, 8, np.inf]
    labels = ['short', 'mid', 'long']

    df_model['playtime_stage'] = pd.cut(
        df_model['log_playtime'],
        bins=bins,
        labels=labels
    )
    # 원하는 이름으로 0/1 컬럼 만들기
    df_model['is_short_play'] = (df_model['playtime_stage'] == 'short').astype(int)
    df_model['is_mid_play']   = (df_model['playtime_stage'] == 'mid').astype(int)
    df_model['is_long_play']  = (df_model['playtime_stage'] == 'long').astype(int)



    # *** 유저 성향 피처 (엄청 중요!)
    # 3. 리뷰어 성향 (리뷰 중독자 vs 일반 유저)
    # 리뷰를 많이 쓰는 사람 → 서비스 잔존율 높음 / 리뷰 거의 안 쓰는 사람 → 이탈 가능성↑ (충성도?)
    df_model['reviews_per_game'] = np.log1p(df_model['num_reviews_author'] / (df_model['num_games_owned'] + 1))



    # 4. “경험 많은/적은 유저” 여부
    df_model['log_num_games_owned'] = np.log1p(df_model['num_games_owned'])
    df_model['log_num_reviews_author'] = np.log1p(df_model['num_reviews_author'])

    # 헤비 유저
    df_model['is_heavy_user'] = (
        (df_model['log_num_games_owned'] > 5.0) & 
        (df_model['log_num_reviews_author'] > 3.5)
    ).astype(int)
    # 라이트 유저 (헤비보다 더 중요한 컬럼.)
    df_model['is_light_user'] = (
        (df_model['log_num_games_owned'] < 2.0) &
        (df_model['log_num_reviews_author'] < 1.0)
    ).astype(int)

    # 5. 리뷰 감정 × 행동 결합 피처 (***핵심!!!)
    # 5-1. 긍정 리뷰 + 낮은 플레이타임 = 위험
    df_model['positive_but_short_play'] = (
        (df_model['good_review'] == 1) & 
        (df_model['playtime_at_review'] < 60)
    ).astype(int)
    # “좋다고는 했는데 금방 떠난 사람” → churn에 엄청 강함

    # 5-2. 부정 리뷰 + 높은 플레이타임
    df_model['negative_but_long_play'] = (
        (df_model['good_review'] == 0) & 
        (df_model['playtime_at_review'] > 1200)
    ).astype(int)
    # -> 욕하면서 계속 하는 타입 = 비이탈



    # 6. 사회적 반응 파생 피처 (반응 여부 자체)
    df_model['has_votes'] = ((df_model['votes_up'] + df_model['votes_funny']) > 0).astype(int)
    df_model['has_comment'] = (df_model['comment_count'] > 0).astype(int)



    # +
    # 7. 리뷰 업데이트의 진정성 (Review Freshness) (아주 좋다고 합니다!!)
    # timestamp_created와 timestamp_updated가 다른 유저는 게임에 아주 깊게 관여하고 있는 유저이다.
    # 리뷰를 수정했다는 것은 이탈하지 않고 게임을 지속하며 의견을 업데이트했다는 강력한 증거.
    # (비이탈 그룹에서 높게 나타날 확률이 큼)
    # # 리뷰 수정 여부 (관여도)
    df_model['is_updated_review'] = (df_model['timestamp_created'] != df_model['timestamp_updated']).astype(int)

    # +
    # 8. 커뮤니티 신뢰도 밀도 (Social Density)
    # votes_up이나 comment_count는 데이터가 매우 희소(sparse).
    # 이를 개별로 두지 않고, 유저의 '활동량' 대비 얼마나 많은 반응을 끌어냈는지 비율로 전환하면 모델이 학습하기 훨씬 수월해진다.
    # 평소 리뷰를 100개 쓰는 사람이 추천 1개 받는 것보다, 리뷰를 1개 썼는데 추천 1개를 받는 것이 훨씬 '핵심 유저'일 가능성이 높다.
    # 영향력 있는 리뷰어는 커뮤니티 활동 때문에라도 이탈률이 낮게 측정되는 경우가 많다.
    # # 리뷰 1개당 평균 반응도 (커뮤니티 영향력)
    df_model['social_density'] = np.log1p((df_model['votes_up'] + df_model['comment_count']) / (df_model['num_reviews_author'] + 1))
    # 이거는 'has_votes', 'has_comment' 조금 겹칠 수 도 있는데 굳이 안빼도 된다고 합니다.
    # 제거할 거면 모델 학습 완료하고, feature importance / coefficient 확인 헤서 위 두개와 비교 후에 제거 하는게 좋다고 합니다!


    # 안전 처리 (inf, -inf 제거)
    df_model.replace([np.inf, -np.inf], 0, inplace=True)

    df_model.head(3)
    
    # df_model[['language', 'voted_up', 'steam_purchase', 'received_for_free', 'written_during_early_access', 'primarily_steam_deck', 'game_style']]

    # 'language' ('english', 'koreana', ...), 'game_style' ('online','video','story') 인코딩 (True/False)
    # df_model['language'].value_counts()     # 카테고리가 많아 상위 10개 미만 값들은 others로 통합.

    # 상위 10개 언어 추출
    top_n = 10
    top_langs = df_model['language'].value_counts().head(top_n).index

    # 상위 10개만 유지, 나머지는 other
    df_model['language'] = df_model['language'].where(
        df_model['language'].isin(top_langs),
        'other'
    )

    df_model = pd.get_dummies(                  #get_dummies 는 columns 를 자동 제거
        df_model,
        columns=['language', 'game_style'],
        drop_first=True
    )
    
    # 원핫인코딩 (True 1, False 0)

    # df_model[['voted_up', 'steam_purchase', 'received_for_free', 'written_during_early_access', 'primarily_steam_deck']]
    # 인코딩된 언어 칼럼들: ['language_english', 'language_french', 'language_german','language_koreana','language_other','language_polish','language_russian','language_schinese','language_spanish','language_turkish']
    # 인코딩된 게임 스타일 칼럼들: ['game_style_story', 'game_style_video']

    bool_cols = ['voted_up', 'steam_purchase', 'received_for_free', 'written_during_early_access', 'primarily_steam_deck',
                'language_english', 'language_french', 'language_german','language_koreana','language_other','language_polish','language_russian','language_schinese','language_spanish','language_turkish',
                'game_style_story', 'game_style_video'
                ]

    for col in bool_cols:
        df_model[col] = df_model[col].astype(int)

    # df_model['voted_up'].value_counts()
    # df_model['language_english'].value_counts()
    # df_model['game_style_story'].value_counts()
    
    TARGET = "churn"

    #  최종 확정한 피처
    FEATURES = [
        "voted_up",
        "steam_purchase",
        "received_for_free",
        "written_during_early_access",
        "primarily_steam_deck",

        # 원핫된 language/game_style 컬럼들 (너가 만든 컬럼명 그대로)
        "language_english", "language_french", "language_german", "language_koreana",
        "language_other", "language_polish", "language_russian", "language_schinese",
        "language_spanish", "language_turkish",
        "game_style_story", "game_style_video",

        # 파생 피처들
        "weighted_vote_score",
        "playtime_per_game",
        "is_short_play", "is_mid_play", "is_long_play",
        "reviews_per_game",
        "is_heavy_user",
        "positive_but_short_play",
        "negative_but_long_play",
        "has_votes",
        "has_comment",
        "social_density",
        "is_updated_review",
    ]

    # 혹시 누락/오타로 없는 컬럼이 있으면 자동 제외(코드 안깨지게)
    FEATURES = [c for c in FEATURES if c in df_model.columns]

