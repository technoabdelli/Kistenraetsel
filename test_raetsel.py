import os
import pytest
from main import (
    Baustein,
    DateiManager,
    Kiste,
    RaetselException,
    RaetselLoeser,
    verarbeite_raetsel,
)

@pytest.mark.parametrize(
    "kisten_masse, stein_spezifikationen, erwartete_gold_mitte",
    [
        (
            (5, 5, 5),
            [
                ("GOLD", (1, 1, 1), True),
                ("W1", (1, 1, 1), False),
                ("W2", (1, 1, 1), False),
                ("W3", (1, 1, 1), False),
                ("W4", (1, 1, 1), False),
                ("QA1", (1, 2, 4), False),
                ("QA2", (1, 2, 4), False),
                ("QA3", (1, 2, 4), False),
                ("QA4", (1, 2, 4), False),
                ("QA5", (1, 2, 4), False),
                ("QA6", (1, 2, 4), False),
                ("QB1", (2, 2, 3), False),
                ("QB2", (2, 2, 3), False),
                ("QB3", (2, 2, 3), False),
                ("QB4", (2, 2, 3), False),
                ("QB5", (2, 2, 3), False),
                ("QB6", (2, 2, 3), False),
            ],
            (2, 2, 2),
        ),
        (
            (1, 1, 1),
            [("GOLD", (1, 1, 1), True)],
            (0, 0, 0),
        ),
        (
            (3, 3, 3),
            [("GOLD", (1, 1, 1), True)]
            + [(f"Q{i}", (1, 1, 2), False) for i in range(13)],
            (1, 1, 1),
        ),
        (
            (4, 4, 4),
            [("GOLD", (2, 2, 2), True)]
            + [(f"Q{i}", (1, 2, 4), False) for i in range(7)],
            (1, 1, 1),
        ),
    ],
)
def test_loesbare_raetsel(kisten_masse, stein_spezifikationen, erwartete_gold_mitte):
    kiste = Kiste(*kisten_masse)
    bausteine = [
        Baustein(s_id, masse, ist_gold=gold)
        for s_id, masse, gold in stein_spezifikationen
    ]

    loeser = RaetselLoeser(kiste, bausteine)
    assert loeser.loese() is True

    gold_stein = next(s for s in bausteine if s.ist_gold)
    assert gold_stein.position == erwartete_gold_mitte

    assert kiste.finde_naechste_freie_zelle() is None


@pytest.mark.parametrize(
    "kisten_masse, stein_spezifikationen, erwartete_fehlermeldung",
    [
        (
            (4, 4, 4),
            [
                ("GOLD", (1, 1, 1), True),
                ("Q1", (3, 4, 4), False),
                ("Q2", (1, 3, 4), False),
                ("Q3", (1, 1, 3), False),
            ],
            "nicht exakt mittig",
        ),
        (
            (3, 3, 3),
            [
                ("GOLD", (1, 1, 1), True),
                ("Q1", (2, 2, 2), False),
            ],
            "Volumen stimmt nicht überein",
        ),
        (
            (3, 3, 3),
            [
                ("GOLD", (1, 1, 1), True),
                ("Q1", (3, 3, 3), False),
            ],
            "Volumen stimmt nicht überein",
        ),
        (
            (2, 2, 2),
            [("Q1", (2, 2, 2), False)],
            "genau 1 goldener Würfel",
        ),
        (
            (3, 3, 3),
            [
                ("GOLD1", (1, 1, 1), True),
                ("GOLD2", (1, 1, 1), True),
                ("Q1", (1, 5, 5), False),
            ],
            "genau 1 goldener Würfel",
        ),
        (
            (3, 3, 3),
            [
                ("GOLD", (1, 1, 1), True),
                ("Q1", (1, 2, 13), False),  # 1 + 26 = 27 cm³, aber Länge 13 > 3
            ],
            "passt in keiner Ausrichtung",
        ),
        (
            (3, 3, 3),
            [("GOLD", (1, 1, 1), True)]
            + [(f"S{i}", (1, 2, 2), False) for i in range(6)]
            + [("W1", (1, 1, 2), False)],
            "existiert keine Lösung",
        ),
    ],
)
def test_unloesbare_raetsel(kisten_masse, stein_spezifikationen, erwartete_fehlermeldung):
    kiste = Kiste(*kisten_masse)
    bausteine = [
        Baustein(s_id, masse, ist_gold=gold)
        for s_id, masse, gold in stein_spezifikationen
    ]

    loeser = RaetselLoeser(kiste, bausteine)
    with pytest.raises(RaetselException) as exc_info:
        loeser.loese()

    assert erwartete_fehlermeldung in str(exc_info.value)


@pytest.mark.parametrize(
    "breite, hoehe, tiefe",
    [
        (0, 5, 5),
        (5, -1, 5),
        (5, 5, 0),
        (-3, -3, -3),
    ],
)
def test_ungueltige_kisten_masse(breite, hoehe, tiefe):
    with pytest.raises(RaetselException):
        Kiste(breite, hoehe, tiefe)


@pytest.mark.parametrize(
    "masse",
    [
        (0, 1, 1),
        (1, -2, 3),
        (2, 2, 0),
    ],
)
def test_ungueltige_baustein_masse(masse):
    with pytest.raises(RaetselException):
        Baustein("X1", masse)


@pytest.mark.parametrize(
    "datei_inhalt, erwarteter_fehlerteil",
    [
        ("", "Keine KISTE-Definition"),
        ("KISTE 5 5 5\n", "Keine STEIN-Definitionen"),
        ("KISTE 5 5\nSTEIN 1 1 1 1 GOLD\n", "Syntaxfehler"),
        ("KISTE 5 -2 5\nSTEIN 1 1 1 1 GOLD\n", "Kistenmaße müssen positiv sein"),
        ("KISTE 5 5 5\nSTEIN 0 1 1 1 GOLD\n", "Anzahl der Steine muss >= 1"),
        ("KISTE 5 5 5\nSTEIN abc 1 1 1\n", "Syntaxfehler"),
        ("KISTE 5 5 5\nUNBEKANNT 1 2 3\n", "Unbekanntes Schlüsselwort"),
    ],
)
def test_ungueltige_eingabedateien(tmp_path, datei_inhalt, erwarteter_fehlerteil):
    eingabe_datei = tmp_path / "fehlerhafte_eingabe.txt"
    eingabe_datei.write_text(datei_inhalt, encoding="utf-8")

    with pytest.raises(RaetselException) as exc_info:
        DateiManager.lese_eingabe(str(eingabe_datei))

    assert erwarteter_fehlerteil in str(exc_info.value)

