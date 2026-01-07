def format_post(title: str, link: str, topic: str, lang: str) -> str:
    if lang == "ua":
        return (
            f"📰 {title}\n\n"
            f"Коротко: новина зі стрічки {topic.upper()}.\n"
            f"Деталі: {link}\n\n"
            f"#{topic} #UA #HelloWorldIntel"
        )

    # lang == "en"
    return (
        f"📰 {title}\n\n"
        f"Brief: update from {topic.upper()} feed.\n"
        f"Details: {link}\n\n"
        f"#{topic} #EN #HelloWorldIntel"
    )
