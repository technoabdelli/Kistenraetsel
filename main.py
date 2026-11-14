import os
from itertools import permutations
from typing import List, Optional, Tuple


class RaetselException(Exception):
    pass


class Baustein:

    def __init__(self, stein_id: str, masse: Tuple[int, int, int], ist_gold: bool = False):
        if any(k <= 0 for k in masse):
            raise RaetselException(f"Ungültige Kantenlängen für Baustein {stein_id}: {masse}")
        self.id = stein_id
        self.masse = masse  # (dx, dy, dz)
        self.ist_gold = ist_gold
        self.position: Optional[Tuple[int, int, int]] = None  # (x, y, z)
        self.ausrichtung: Optional[Tuple[int, int, int]] = None

    @property
    def volumen(self) -> int:
        return self.masse[0] * self.masse[1] * self.masse[2]

    def get_rotationen(self) -> List[Tuple[int, int, int]]:
        return sorted(list(set(permutations(self.masse))), reverse=True)

    def __repr__(self) -> str:
        typ = "GOLD" if self.ist_gold else "Stein"
        return f"<{typ} {self.id}: Maße={self.masse}, Pos={self.position}, Rot={self.ausrichtung}>"


class Kiste:
    def __init__(self, breite: int, hoehe: int, tiefe: int):
        if breite <= 0 or hoehe <= 0 or tiefe <= 0:
            raise RaetselException(f"Kistenmaße müssen positiv sein: {breite}x{hoehe}x{tiefe}")
        self.breite = breite  # X-Achse
        self.hoehe = hoehe    # Y-Achse
        self.tiefe = tiefe    # Z-Achse (Schichten)
        self.grid: List[List[List[Optional[str]]]] = [
            [[None for _ in range(breite)] for _ in range(hoehe)]
            for _ in range(tiefe)
        ]

    @property
    def volumen(self) -> int:
        return self.breite * self.hoehe * self.tiefe

    def ist_platzierbar(self, x: int, y: int, z: int, dx: int, dy: int, dz: int) -> bool:
        if x < 0 or y < 0 or z < 0:
            return False
        if x + dx > self.breite or y + dy > self.hoehe or z + dz > self.tiefe:
            return False

        for cz in range(z, z + dz):
            for cy in range(y, y + dy):
                for cx in range(x, x + dx):
                    if self.grid[cz][cy][cx] is not None:
                        return False
        return True

    def platziere(self, stein: Baustein, x: int, y: int, z: int, ausrichtung: Tuple[int, int, int]) -> None:
        dx, dy, dz = ausrichtung
        if not self.ist_platzierbar(x, y, z, dx, dy, dz):
            raise RaetselException(f"Kollision oder Grenzüberschreitung bei {stein.id} an ({x},{y},{z})")

        for cz in range(z, z + dz):
            for cy in range(y, y + dy):
                for cx in range(x, x + dx):
                    self.grid[cz][cy][cx] = stein.id

        stein.position = (x, y, z)
        stein.ausrichtung = ausrichtung

    def entferne(self, stein: Baustein) -> None:
        if stein.position is None or stein.ausrichtung is None:
            return
        x, y, z = stein.position
        dx, dy, dz = stein.ausrichtung

        for cz in range(z, z + dz):
            for cy in range(y, y + dy):
                for cx in range(x, x + dx):
                    self.grid[cz][cy][cx] = None

        stein.position = None
        stein.ausrichtung = None

    def finde_naechste_freie_zelle(self) -> Optional[Tuple[int, int, int]]:
        for z in range(self.tiefe):
            for y in range(self.hoehe):
                for x in range(self.breite):
                    if self.grid[z][y][x] is None:
                        return (x, y, z)
        return None


class RaetselLoeser:

    def __init__(self, kiste: Kiste, bausteine: List[Baustein]):
        self.kiste = kiste
        self.bausteine = bausteine

    def _vorab_pruefung(self) -> Tuple[bool, str]:
        gesamt_volumen_steine = sum(s.volumen for s in self.bausteine)
        if gesamt_volumen_steine != self.kiste.volumen:
            return False, (
                f"Volumen stimmt nicht überein: Kiste benötigt {self.kiste.volumen} cm³, "
                f"Steine haben zusammen {gesamt_volumen_steine} cm³."
            )

        goldene_steine = [s for s in self.bausteine if s.ist_gold]
        if len(goldene_steine) != 1:
            return False, f"Es muss genau 1 goldener Würfel vorhanden sein (gefunden: {len(goldene_steine)})."

        gold = goldene_steine[0]
        for kisten_dim, gold_dim in zip((self.kiste.breite, self.kiste.hoehe, self.kiste.tiefe), gold.masse):
            if (kisten_dim - gold_dim) % 2 != 0:
                return False, (
                    f"Der goldene Würfel ({gold.masse}) kann in der Kiste "
                    f"({self.kiste.breite}x{self.kiste.hoehe}x{self.kiste.tiefe}) nicht exakt mittig platziert werden."
                )

        max_kiste = sorted([self.kiste.breite, self.kiste.hoehe, self.kiste.tiefe])
        for s in self.bausteine:
            if any(sd > kd for sd, kd in zip(sorted(s.masse), max_kiste)):
                return False, f"Baustein {s.id} mit Maßen {s.masse} passt in keiner Ausrichtung in die Kiste."

        return True, "Vorabprüfung erfolgreich."

    def _platziere_goldenen_wuerfel(self) -> Baustein:
        gold = next(s for s in self.bausteine if s.ist_gold)
        gx = (self.kiste.breite - gold.masse[0]) // 2
        gy = (self.kiste.hoehe - gold.masse[1]) // 2
        gz = (self.kiste.tiefe - gold.masse[2]) // 2
        self.kiste.platziere(gold, gx, gy, gz, gold.masse)
        return gold

    def loese(self) -> bool:
        gueltig, meldung = self._vorab_pruefung()
        if not gueltig:
            raise RaetselException(meldung)

        gold = self._platziere_goldenen_wuerfel()
        restliche_steine = [s for s in self.bausteine if s.id != gold.id]

        restliche_steine.sort(key=lambda s: s.volumen, reverse=True)

        erfolg = self._backtrack(restliche_steine)
        if not erfolg:
            raise RaetselException("Für diese Kombination aus Kiste und Bausteinen existiert keine Lösung.")
        return True

    def _backtrack(self, verfuegbare_steine: List[Baustein]) -> bool:
        freie_zelle = self.kiste.finde_naechste_freie_zelle()
        if freie_zelle is None:
            return len(verfuegbare_steine) == 0

        x, y, z = freie_zelle
        getestete_signaturen = set()  # Verhindert redundantes Testen baugleicher Steine

        for idx, stein in enumerate(verfuegbare_steine):
            signatur = tuple(sorted(stein.masse))
            if signatur in getestete_signaturen:
                continue
            getestete_signaturen.add(signatur)

            for ausrichtung in stein.get_rotationen():
                dx, dy, dz = ausrichtung
                if self.kiste.ist_platzierbar(x, y, z, dx, dy, dz):
                    self.kiste.platziere(stein, x, y, z, ausrichtung)
                    naechste_steine = verfuegbare_steine[:idx] + verfuegbare_steine[idx + 1:]

                    if self._backtrack(naechste_steine):
                        return True

                    self.kiste.entferne(stein)

        return False


class Visualisierer:
    @staticmethod
    def generiere_text_bericht(kiste: Kiste, bausteine: List[Baustein], mit_ansi_farben: bool = False) -> str:
        """Erzeugt eine verständliche Dokumentation inklusive Schichtansicht der Kiste."""
        zeilen = [
            "====================================================================",
            "               LÖSUNG DES WÜRFEL- UND QUADER-RÄTSELS                ",
            "====================================================================",
            "",
            "1. ERKLÄRUNG DER DARSTELLUNG:",
            f"   - Kistenmaße: {kiste.breite} (X) x {kiste.hoehe} (Y) x {kiste.tiefe} (Z) cm",
            "   - Koordinatensystem: (x, y, z) gibt die untere linke vordere Ecke",
            "     eines Bausteins an (0-basiert).",
            "   - Kennzeichnung: 'GOLD' markiert den goldenen Würfel in der Mitte.",
            "     Alle weiteren Steine haben eindeutige IDs (z. B. Q1, Q2, W1...).",
            "",
            "2. LISTE ALLER PLATZIERTEN BAUSTEINE (Position & Ausrichtung):",
            "   ID    | Typ    | Originalmaße | Ausrichtung (dx,dy,dz) | Position (x,y,z)",
            "   ------+--------+--------------+------------------------+-----------------",
        ]

        sortierte_steine = sorted(bausteine, key=lambda s: (not s.ist_gold, s.id))
        for s in sortierte_steine:
            typ = "GOLD" if s.ist_gold else "Quader"
            orig = f"{s.masse[0]}x{s.masse[1]}x{s.masse[2]}"
            ausr = f"{s.ausrichtung[0]}x{s.ausrichtung[1]}x{s.ausrichtung[2]}" if s.ausrichtung else "-"
            pos = f"({s.position[0]}, {s.position[1]}, {s.position[2]})" if s.position else "-"
            zeilen.append(f"   {s.id:<5} | {typ:<6} | {orig:<12} | {ausr:<22} | {pos}")

        zeilen.append("")
        zeilen.append("3. SCHICHTWEISE DARSTELLUNG DER KISTE (Z-Ebenen von unten nach oben):")

        for z in range(kiste.tiefe):
            zeilen.append(f"\n   --- Schicht Z = {z} (Ebene {z + 1} von {kiste.tiefe}) ---")
            header = "      " + " ".join(f"X={x:<3}" for x in range(kiste.breite))
            zeilen.append(header)
            for y in range(kiste.hoehe):
                reihe_zellen = []
                for x in range(kiste.breite):
                    zelle = kiste.grid[z][y][x] or "...."
                    if mit_ansi_farben and zelle == "GOLD":
                        reihe_zellen.append(f"\033[93m\033[1m{zelle:<4}\033[0m")
                    else:
                        reihe_zellen.append(f"{zelle:<4}")
                zeilen.append(f"   Y={y} " + " ".join(reihe_zellen))

        return "\n".join(zeilen)

    @staticmethod
    def zeige_2d_schicht_grafik(kiste: Kiste, bausteine: List[Baustein], bild_pfad: str = "out/loesung_visualisierung.png") -> None:
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import random
        except ImportError:
            print("Hinweis: 'matplotlib' nicht installiert – überspringe PNG-Export.")
            return

        random.seed(42)
        farben = {}
        for s in bausteine:
            if s.ist_gold:
                farben[s.id] = "#FFD700"  # Eindeutiges Goldgelb
            else:
                farben[s.id] = f"#{random.randint(0x44, 0xCC):02x}{random.randint(0x44, 0xCC):02x}{random.randint(0x44, 0xCC):02x}"

        fig, axes = plt.subplots(1, kiste.tiefe, figsize=(3.5 * kiste.tiefe, 4))
        if kiste.tiefe == 1:
            axes = [axes]

        for z in range(kiste.tiefe):
            ax = axes[z]
            ax.set_xlim(0, kiste.breite)
            ax.set_ylim(0, kiste.hoehe)
            ax.set_aspect("equal")
            ax.invert_yaxis()
            ax.set_title(f"Schicht Z = {z}")
            ax.set_xticks(range(kiste.breite + 1))
            ax.set_yticks(range(kiste.hoehe + 1))
            ax.grid(True, color="black", linewidth=0.8)

            for y in range(kiste.hoehe):
                for x in range(kiste.breite):
                    stein_id = kiste.grid[z][y][x]
                    if stein_id:
                        rect = patches.Rectangle((x, y), 1, 1, facecolor=farben[stein_id], edgecolor="black", lw=0.5)
                        ax.add_patch(rect)
                        ax.text(
                            x + 0.5, y + 0.5, stein_id,
                            ha="center", va="center", fontsize=8,
                            fontweight="bold" if stein_id == "GOLD" else "normal"
                        )

        plt.tight_layout()
        os.makedirs(os.path.dirname(bild_pfad), exist_ok=True)
        plt.savefig(bild_pfad, dpi=150)
        plt.close()


class DateiManager:
    @staticmethod
    def lese_eingabe(dateipfad: str) -> Tuple[Kiste, List[Baustein]]:
        if not os.path.exists(dateipfad):
            raise RaetselException(f"Eingabedatei nicht gefunden: {dateipfad}")

        kiste: Optional[Kiste] = None
        bausteine: List[Baustein] = []
        stein_counter = 1

        with open(dateipfad, "r", encoding="utf-8") as f:
            for zeilen_nr, rohe_zeile in enumerate(f, start=1):
                zeile = rohe_zeile.strip()
                if not zeile or zeile.startswith("#"):
                    continue

                teile = zeile.split()
                schluessel = teile[0].upper()

                try:
                    if schluessel == "KISTE":
                        if len(teile) != 4:
                            raise ValueError("KISTE erwartet genau 3 Maße (Breite Höhe Tiefe).")
                        kiste = Kiste(int(teile[1]), int(teile[2]), int(teile[3]))

                    elif schluessel == "STEIN":
                        if len(teile) not in (5, 6):
                            raise ValueError("STEIN erwartet: STEIN <Anzahl> <B> <H> <T> [GOLD].")
                        anzahl = int(teile[1])
                        if anzahl <= 0:
                            raise ValueError("Anzahl der Steine muss >= 1 sein.")
                        masse = (int(teile[2]), int(teile[3]), int(teile[4]))
                        ist_gold = len(teile) == 6 and teile[5].upper() == "GOLD"

                        for _ in range(anzahl):
                            if ist_gold:
                                s_id = "GOLD"
                            elif masse[0] == masse[1] == masse[2]:
                                s_id = f"W{stein_counter:02d}"
                                stein_counter += 1
                            else:
                                s_id = f"Q{stein_counter:02d}"
                                stein_counter += 1
                            bausteine.append(Baustein(s_id, masse, ist_gold))
                    else:
                        raise ValueError(f"Unbekanntes Schlüsselwort '{schluessel}'.")
                except ValueError as e:
                    raise RaetselException(f"Syntaxfehler in Zeile {zeilen_nr} ('{zeile}'): {e}")

        if kiste is None:
            raise RaetselException("Keine KISTE-Definition in der Eingabedatei gefunden.")
        if not bausteine:
            raise RaetselException("Keine STEIN-Definitionen in der Eingabedatei gefunden.")

        return kiste, bausteine

    @staticmethod
    def schreibe_ausgabe(ausgabepfad: str, inhalt: str) -> None:
        os.makedirs(os.path.dirname(ausgabepfad), exist_ok=True)
        with open(ausgabepfad, "w", encoding="utf-8") as f:
            f.write(inhalt)


def verarbeite_raetsel(eingabe_datei: str, ausgabe_datei: str = "out/loesung.txt") -> None:
    try:
        kiste, bausteine = DateiManager.lese_eingabe(eingabe_datei)
        loeser = RaetselLoeser(kiste, bausteine)
        loeser.loese()

        bericht_konsole = Visualisierer.generiere_text_bericht(kiste, bausteine, mit_ansi_farben=True)
        bericht_datei = Visualisierer.generiere_text_bericht(kiste, bausteine, mit_ansi_farben=False)

        print(bericht_konsole)
        DateiManager.schreibe_ausgabe(ausgabe_datei, bericht_datei)
        Visualisierer.zeige_2d_schicht_grafik(kiste, bausteine, ausgabe_datei.replace(".txt", ".png"))
        print(f"\nErgebnis erfolgreich gespeichert unter: {ausgabe_datei}")

    except RaetselException as e:
        fehlermeldung = f"FEHLER: Das Rätsel konnte nicht gelöst werden.\nGrund: {e}"
        print(fehlermeldung)
        DateiManager.schreibe_ausgabe(ausgabe_datei, fehlermeldung)


if __name__ == "__main__":
    eingabe_pfad = input("Bitte gib den Pfad zur Rätsel-Textdatei ein (z. B. in/beispiel1.txt): ").strip().strip('"').strip("'")

    if not eingabe_pfad:
        print("FEHLER: Es wurde kein Dateipfad eingegeben.")
    else:
        datei_basisname = os.path.splitext(os.path.basename(eingabe_pfad))[0]
        ausgabe_pfad = os.path.join("out", f"loesung_{datei_basisname}.txt")

        verarbeite_raetsel(eingabe_pfad, ausgabe_pfad)