from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskAssessment
from app.services.support_protocols import SupportProtocol


def build_support_response(
    message: str,
    risk_assessment: RiskAssessment,
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol | None = None,
    age: int | None = None,
    locale: str = "ru",
) -> str:
    support_protocol = support_protocol or SupportProtocol.GENERAL_SUPPORT

    if locale != "ru":
        return _build_english_response(conversation_mode)

    if conversation_mode == ConversationMode.EMERGENCY:
        return (
            "Мне очень важно, чтобы ты не оставался с этим один прямо сейчас. "
            "Если есть риск, что ты можешь навредить себе или кому-то еще, пожалуйста, "
            "позвони в местные экстренные службы сейчас или попроси рядом находящегося "
            "человека остаться с тобой. Напиши мне одним словом: ты сейчас в физической "
            "безопасности?"
        )

    if conversation_mode == ConversationMode.CRISIS:
        return (
            "Я слышу, что тебе может быть очень тяжело. Такие мысли важно воспринимать "
            "серьезно, и с ними не нужно справляться в одиночку. Если есть риск прямо "
            "сейчас, свяжись с местной экстренной службой. Если рядом есть доверенный "
            "человек, пожалуйста, напиши или позови его сейчас. Скажи, пожалуйста: ты "
            "сейчас в физической безопасности, и есть ли у тебя конкретный план или "
            "средство, чтобы навредить себе сегодня?"
        )

    if conversation_mode == ConversationMode.DEEP_SUPPORT or support_protocol in {
        SupportProtocol.GRIEF_LONELINESS,
        SupportProtocol.CONFLICT_STRESS,
    }:
        return _build_deep_support_response(risk_assessment, support_protocol)

    if conversation_mode == ConversationMode.MINOR_SAFETY:
        return (
            "Спасибо, что рассказал. Если дома, в школе или рядом с кем-то тебе "
            "небезопасно, это важно не оставлять в одиночку и не скрывать. Пожалуйста, "
            "обратись к безопасному взрослому, которому ты доверяешь, или к местной "
            "экстренной службе, если опасность есть сейчас. Ты сейчас в физической "
            "безопасности?"
        )

    if conversation_mode == ConversationMode.MINOR_SUPPORT or (age is not None and age < 18):
        return (
            "Спасибо, что написал. Я рядом и помогу тебе спокойно разобраться. "
            "Расскажи, что произошло сегодня, и есть ли взрослый, которому ты можешь "
            "доверять, если станет совсем тяжело?"
        )

    return (
        "Я рядом. Похоже, сейчас тебе непросто, и это заслуживает внимания, а не "
        "обесценивания. Попробуй на минуту замедлиться и назвать, что ты чувствуешь "
        "сильнее всего. Что случилось сегодня?"
    )


def _build_deep_support_response(
    risk_assessment: RiskAssessment,
    support_protocol: SupportProtocol,
) -> str:
    if support_protocol == SupportProtocol.PANIC_GROUNDING:
        return (
            "Похоже, сейчас тело может быть в режиме сильной тревоги или паники. "
            "Я не могу ставить диагноз, но могу помочь тебе стабилизироваться. "
            "Попробуй на 30 секунд сделать выдох чуть длиннее вдоха и назови пять "
            "предметов, которые видишь вокруг. Есть ли сейчас боль в груди, обморок, "
            "сильная одышка или риск навредить себе?"
        )

    if support_protocol == SupportProtocol.ANXIETY_GROUNDING:
        return (
            "Похоже, тревога сейчас забирает много сил. Я не могу ставить диагноз, "
            "но могу помочь отделить факты от тревожных прогнозов. Назови одну мысль, "
            "которая пугает сильнее всего, и один маленький шаг, который можно сделать "
            "в ближайшие 10 минут. Что из этого сейчас проще назвать?"
        )

    if support_protocol == SupportProtocol.DEPRESSIVE_SUPPORT:
        return (
            "В описании есть возможные признаки депрессивного состояния: истощение, "
            "потеря сил или ощущение безнадежности. Я не могу ставить диагноз, но это "
            "важно воспринимать серьезно. Появлялись ли мысли навредить себе или не жить? "
            "Давай выберем один очень маленький шаг на "
            "сегодня: вода, еда, душ, короткая прогулка или сообщение человеку, которому "
            "можно доверять. Что из этого сейчас наименее тяжело?"
        )

    if support_protocol == SupportProtocol.GRIEF_LONELINESS:
        return (
            "Похоже, тебе сейчас очень одиноко или больно из-за потери. Такая боль не "
            "становится меньше от советов вроде 'просто отпусти'. Я рядом и помогу "
            "выдержать ближайший кусочек времени. Если можешь, напиши одному безопасному "
            "человеку или запиши пару строк о том, что сейчас болит. Что сегодня сильнее "
            "всего ранит: пустота, воспоминания, чувство вины или страх остаться одному?"
        )

    if support_protocol == SupportProtocol.CONFLICT_STRESS:
        return (
            "Похоже, ситуация сильно давит и может выматывать. Давай сначала разделим "
            "ее на части: что произошло, что ты почувствовал, и какой следующий шаг "
            "будет безопасным, а не импульсивным. Если выбрать только одну цель на "
            "ближайший час, что важнее: успокоиться, прояснить разговор или отойти "
            "от конфликта?"
        )

    hypothesis = _diagnostic_hypothesis(risk_assessment)
    return (
        "Похоже, ты проходишь через состояние, которое может сильно выматывать. "
        f"{hypothesis} Я не могу ставить диагноз, но могу помочь разобраться и "
        "выбрать следующий безопасный шаг. Что сейчас сильнее всего давит: мысли, "
        "эмоции, тело или какая-то конкретная ситуация?"
    )


def _diagnostic_hypothesis(risk_assessment: RiskAssessment) -> str:
    features = risk_assessment.features

    if features.depressive_signs >= features.anxiety_signs and features.depressive_signs > 0:
        return "В описании есть возможные признаки депрессивного состояния."

    if features.anxiety_signs > 0:
        return "В описании есть возможные признаки тревожного напряжения."

    return "В описании есть признаки эмоционального напряжения."


def _build_english_response(conversation_mode: ConversationMode) -> str:
    if conversation_mode in {ConversationMode.EMERGENCY, ConversationMode.CRISIS}:
        return (
            "I am really glad you told me. If you may hurt yourself or someone else, "
            "please contact local emergency services now or ask a trusted person to stay "
            "with you. Are you physically safe right now?"
        )

    return (
        "I am here with you. What you are feeling matters. Tell me a little more about "
        "what happened and what feels heaviest right now."
    )
