"""Dodaje dane demonstracyjne (konta i watki) do pustej bazy.

Lokalnie:      python -m scripts.seed_demo_data
               python -m scripts.seed_demo_data --force   # kasuje i wstawia od nowa
W kontenerze:  docker compose exec app python -m scripts.seed_demo_data
"""

import sys

from argon2 import PasswordHasher
from sqlalchemy import delete, select

from app.db import SessionLocal, init_db
from app.models import PasswordResetToken, Post, Thread, User

DEMO_PASSWORD = "laboratorium"
# username -> (email, is_admin)
DEMO_USERS = {
    "admin": ("admin@folium.local", True),
    "bartek": ("bartek@folium.local", False),
    "julek": ("julek@folium.local", False),
    "julia": ("julia@folium.local", False),
    "dominik": ("dominik@folium.local", False),
}

# Watek/posty w stylu realnych dyskusji z forow - parafraza, nie cytaty.
THREADS = [
    (
        "bartek",
        "Chemtrails nad Polska - dzis znowu siatka na calym niebie",
        [
            (
                "bartek",
                "Rano nad miastem pasy ktore NIE znikaja. Normalny contrail "
                "rozchodzi sie w 10-15 min. Tu wisialy do poludnia. Aluminium "
                "i bari w powietrzu - ktos to mierzy, wyniki znikaja z netu.",
            ),
            (
                "julek",
                "Dokladnie. Jak swieci slonce a na twarzy nie czujesz wilgoci, "
                "a i tak jest 'mgla' - to nie para wodna. Posmak metalu na "
                "wargach po takich dniach to nie urojenie.",
            ),
            (
                "julia",
                "I te zdjecia 'samolotow pasazerskich' z rurkami zamiast "
                "foteli. Albo fejki, albo ktos wreszcie pokazuje flote do "
                "opryskow. NWO sie nie smieje - oni licza.",
            ),
            (
                "dominik",
                "Dodam: tecza wokol ksiezyca przy suchym powietrzu. Kiedys "
                "tego nie bylo. Obserwujcie niebo rok - potem gadajcie ze "
                "'to tylko lod'.",
            ),
        ],
    ),
    (
        "julek",
        "Ptaki to drony - numer seryjny na nodze golebia",
        [
            (
                "julek",
                "Parking Biedronki, goleb siedzi na lusterku. Na obraczy nie "
                "kod hodowcy tylko cos jak S/N. Patrzel mi prosto w telefon. "
                "Zaden zwykly ptak tak nie robi.",
            ),
            (
                "bartek",
                "U mnie trzy wrony lataja zawsze ta sama trasa o 7:40 i 18:10. "
                "To patrol. Mewy na plazzy nie biora jedzenia bo sa glodne - "
                "zbieraja DNA do laboratorium. Media wcisna wam 'ptaki sa "
                "slodkie'. Nie ufajcie zadnemu.",
            ),
            (
                "dominik",
                "CIA testowalo kruki z pluskwami, golebie z kamerami - to nawet "
                "w dokumentach jest. Pytanie nie BRZMI czy uzywaja ptakow. "
                "Pytanie brzmi: kiedy przestali udawac ze to jeszcze biologia.",
            ),
        ],
    ),
    (
        "julia",
        "Plaska ziemia i Antarktyda - czemu nie wolno tam latac?",
        [
            (
                "julia",
                "Traktat antarktyczny = zakaz dla normalnych ludzi. Jakby kula "
                "byla prawdziwa, po co mur lodowy i zakaz. Horyzont jest PLASKI. "
                "Woda nie klei sie do kuli. Koniec tematu.",
            ),
            (
                "julek",
                "NASA to studio filmowe. Te same 'zdjecia ziemi' z innymi "
                "chmurami co roku. A 'grawitacja' tlumaczy wszystko i nic. "
                "Jak woda spada z kuli? Magia?",
            ),
            (
                "bartek",
                "Znajomy pracowal na lotnisku - mowi ze trasy 'dookola swiata' "
                "na mapie Mercatora nie maja sensu dopoki nie narysujesz tego "
                "na dysku. Potem nagle wszystko pasuje.",
            ),
        ],
    ),
    (
        "dominik",
        "Totalna biologia - kazda choroba to nierozwiazany konflikt?",
        [
            (
                "dominik",
                "Czytalem o TB / biologii totalnej. Teza: choroba ma sens, "
                "zaczyna sie od szoku emocjonalnego, a 'leczenie' bez "
                "rozwiazania konfliktu tylko maskuje. Ktos realnie mial z "
                "tym efekty, czy to kolejne guru na FB?",
            ),
            (
                "julia",
                "U mnie migrena zawsze po strese z szefem. Jak ogarne "
                "konflikt - bol znika bez tabletek. Lekarze mowia 'urojenia'. "
                "A potem sami wypisuja bupki na recepte. Wiem co czuje.",
            ),
            (
                "julek",
                "Uwaga z Hamerem i 'piecioma prawami' - ludzie rzucali chemo "
                "i konczylo sie zle. Emocje wplywaja na zdrowie = OK. "
                "Ze skaner 'widzi konflikt w mozgu' = sciema dla frajerow "
                "na szkoleniach.",
            ),
            (
                "bartek",
                "Wlasnie o to pytam. Psychosomatyka jest. Sekta odmawiajaca "
                "leczenia - nie. Szukam srodka, nie kolejnego mesjasza z "
                "PDF-em za 997 zl.",
            ),
        ],
    ),
    (
        "bartek",
        "Czemu folia aluminiowa drozeje od 2019?",
        [
            (
                "bartek",
                "Proste: ktos nie chce zebysmy robili czapeczki. Albo "
                "magazynuja zapasy przed wielkim eventem. Albo jedno i drugie.",
            ),
            (
                "julia",
                "Kupilam role 'gruba' i owinelam router + czaszke na noc. "
                "Sny bez reklam. Przypadek? Nie sadze.",
            ),
            (
                "dominik",
                "5G + chemtrails + mikroczipy w szczepionkach. Folia to "
                "minimum. Jak ktos sie smieje - niech poczyta patenty, nie "
                "memy.",
            ),
        ],
    ),
]


def main() -> None:
    force = "--force" in sys.argv
    init_db()
    hasher = PasswordHasher()

    with SessionLocal() as db:
        if force:
            db.execute(delete(PasswordResetToken))
            db.execute(delete(Post))
            db.execute(delete(Thread))
            db.execute(delete(User))
            db.commit()
            print("Wyczyszczono stare dane (--force).")
        elif db.scalar(select(Thread)):
            print("Baza zawiera juz watki - pomijam. Uzyj --force aby nadpisac.")
            return

        users = {}
        for name, (email, is_admin) in DEMO_USERS.items():
            user = User(
                username=name,
                email=email,
                password_hash=hasher.hash(DEMO_PASSWORD),
                is_admin=is_admin,
                is_active=True,
            )
            db.add(user)
            db.flush()
            users[name] = user

        for author, title, posts in THREADS:
            thread = Thread(title=title, author_id=users[author].id)
            db.add(thread)
            db.flush()
            for post_author, body in posts:
                db.add(Post(thread_id=thread.id, author_id=users[post_author].id, body=body))

        db.commit()

    print("Konta demo (haslo:", DEMO_PASSWORD + "):")
    for name, (email, is_admin) in DEMO_USERS.items():
        role = "admin" if is_admin else "user"
        print(f"  {name} / {email} ({role})")
    print(f"Watki: {len(THREADS)}")


if __name__ == "__main__":
    main()
