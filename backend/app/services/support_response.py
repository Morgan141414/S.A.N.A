from app.services.risk_classifier import RiskLevel


def build_support_response(
    message: str,
    risk_level: RiskLevel,
    age: int | None = None,
    locale: str = "ru",
) -> str:
    if locale != "ru":
        return _build_english_response(risk_level)

    if risk_level == RiskLevel.EMERGENCY:
        return (
            "Мне очень важно, чтобы ты не оставался с этим один прямо сейчас. "
            "Если есть риск, что ты можешь навредить себе или кому-то еще, пожалуйста, "
            "позвони в местные экстренные службы сейчас или попроси рядом находящегося "
            "человека остаться с тобой. Напиши мне одним словом: ты сейчас в физической "
            "безопасности?"
        )

    if risk_level == RiskLevel.HIGH:
        return (
            "Я слышу, что тебе может быть очень тяжело. Такие мысли важно воспринимать "
            "серьезно, и с ними не нужно справляться в одиночку. Скажи, пожалуйста: "
            "у тебя есть конкретный план или средство, чтобы навредить себе сегодня?"
        )

    if risk_level == RiskLevel.MEDIUM:
        return (
            "Похоже, ты проходишь через состояние, которое может сильно выматывать. "
            "Я не могу ставить диагноз, но могу помочь разобраться и выбрать следующий "
            "безопасный шаг. Что сейчас сильнее всего давит: мысли, эмоции, тело или "
            "какая-то конкретная ситуация?"
        )

    if age is not None and age < 18:
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


def _build_english_response(risk_level: RiskLevel) -> str:
    if risk_level in {RiskLevel.EMERGENCY, RiskLevel.HIGH}:
        return (
            "I am really glad you told me. If you may hurt yourself or someone else, "
            "please contact local emergency services now or ask a trusted person to stay "
            "with you. Are you physically safe right now?"
        )

    return (
        "I am here with you. What you are feeling matters. Tell me a little more about "
        "what happened and what feels heaviest right now."
    )

