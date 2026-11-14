# UML-Klassendiagramm

```mermaid
classDiagram
    class Baustein {
        +str id
        +tuple~int, int, int~ masse
        +bool ist_gold
        +tuple~int, int, int~ position
        +tuple~int, int, int~ ausrichtung
        +volumen() int
        +get_rotationen() list~tuple~
    }

    class Kiste {
        +int breite
        +int hoehe
        +int tiefe
        +list~list~list~ grid
        +volumen() int
        +ist_frei(x, y, z, dx, dy, dz) bool
        +platziere(baustein, x, y, z, ausrichtung) void
        +entferne(baustein) void
        +finde_naechste_freie_zelle() tuple
    }

    class DateiManager {
        +lese_eingabe(dateipfad) tuple~Kiste, list~Baustein~~
        +schreibe_ausgabe(ausgabepfad, kiste, bausteine) void
        +schreibe_fehler(ausgabepfad, nachricht) void
    }

    class RaetselLoeser {
        -Kiste kiste
        -list~Baustein~ bausteine
        +loese() bool
        -_vorab_pruefung() tuple~bool, str~
        -_platziere_goldenen_wuerfel() bool
        -_backtrack(verfuegbare_steine) bool
    }

    class Visualisierer {
        +generiere_schicht_ansicht(kiste, bausteine) str
        +zeige_2d_plot(kiste, bausteine) void
    }

    RaetselLoeser --> Kiste : verwaltet
    RaetselLoeser --> Baustein : platziert
    DateiManager ..> Kiste : erstellt / liest
    DateiManager ..> Baustein : erstellt / liest
    Visualisierer ..> Kiste : stellt dar