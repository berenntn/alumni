"""Factory for generating sample announcement data."""

import random
from typing import Optional, List

from app.models.announcement import Announcement

SAMPLE_ANNOUNCEMENTS = [
    (
        "Mezunlar Buluşması",
        "Üniversitemizin mezunlar buluşmasına tüm mezunlarımız davetlidir.",
    ),
    (
        "Kariyer Günleri",
        "Kariyer günleri etkinliğinde sektör profesyonelleriyle tanışabilirsiniz.",
    ),
    (
        "Staj Fırsatları",
        "Mezunlarımız için yeni staj ve iş fırsatları yayımlandı.",
    ),
    (
        "Mezuniyet Töreni",
        "Mezuniyet töreniyle ilgili detaylar yakında duyurulacaktır.",
    ),
    (
        "Alumni Mentorluk Programı",
        "Mezunlarımız mentorluk programına başvurabilir.",
    ),
]


class AnnouncementFactory:
    """Generate valid sample announcements."""

    @staticmethod
    def create(index: Optional[int] = None) -> Announcement:
        if index is None:
            title, content = random.choice(SAMPLE_ANNOUNCEMENTS)
        else:
            title, content = SAMPLE_ANNOUNCEMENTS[
                index % len(SAMPLE_ANNOUNCEMENTS)
            ]

        return Announcement(
            title=title,
            content=content,
            created_by=None,
        )

    @staticmethod
    def create_batch(count: int = 5) -> List[Announcement]:
        if count < 0:
            raise ValueError("count cannot be negative")

        return [
            AnnouncementFactory.create(index=i)
            for i in range(count)
        ]
