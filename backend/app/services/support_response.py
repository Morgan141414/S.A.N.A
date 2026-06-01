from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskAssessment


def build_support_response(
    message: str,
    risk_assessment: RiskAssessment,
    conversation_mode: ConversationMode,
    age: int | None = None,
    locale: str = "ru",
) -> str:
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

    if conversation_mode == ConversationMode.DEEP_SUPPORT:
        hypothesis = _diagnostic_hypothesis(risk_assessment)
        return (
            "Похоже, ты проходишь через состояние, которое может сильно выматывать. "
            f"{hypothesis} Я не могу ставить диагноз, но могу помочь разобраться и "
            "выбрать следующий безопасный шаг. Что сейчас сильнее всего давит: мысли, "
            "эмоции, тело или какая-то конкретная ситуация?"
        )

    if conversation_mode == ConversationMode.MINOR_SUPPORT or (age is not None and age < 18):
        return (
            "Спасибо, что написал. Я рядом и помогу тебе спокойно разобраться. "
            "Расскажи, что произошло сегодня, и есть ли взрослый, которому ты можешь "
            "доверять, если станет совсем тяжело?"
        )

    return (
        "Я рядом. Похоже, сейчас тебе непросто, и это заслуживает внимания, а не "
        "обесценивания. Расскажи немного подробнее: что случилось и что ты чувствуешь "
        "сильнее всего прямо сейчас?"
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
