"""Verifie les ratios de contraste WCAG 2.x des paires declarees dans docs/design-tokens.json.

Usage : python3 docs/tools/check_contrast.py [chemin/design-tokens.json]
Code de sortie 1 si une paire est sous son seuil `min` (4.5 texte, 3.0 non-texte).
Bibliotheque standard uniquement.
"""

import json
import sys
from pathlib import Path

DEFAULT_TOKENS = Path(__file__).resolve().parent.parent / "design-tokens.json"
# Constantes de la definition WCAG 2.x de la luminance relative (sRGB).
LINEAR_THRESHOLD = 0.04045
LINEAR_DIVISOR = 12.92
GAMMA_OFFSET = 0.055
GAMMA_DIVISOR = 1.055
GAMMA = 2.4
LUMA_WEIGHTS = (0.2126, 0.7152, 0.0722)
FLARE = 0.05
CHANNEL_MAX = 255


def _channel(value: int) -> float:
    c = value / CHANNEL_MAX
    if c <= LINEAR_THRESHOLD:
        return c / LINEAR_DIVISOR
    return ((c + GAMMA_OFFSET) / GAMMA_DIVISOR) ** GAMMA


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    return sum(w * _channel(v) for w, v in zip(LUMA_WEIGHTS, rgb))


def contrast(fg: str, bg: str) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + FLARE) / (lo + FLARE)


def _token_hexes(node: object) -> set[str]:
    """Collecte toutes les valeurs hexadecimales declarees dans un bloc de tokens."""
    if isinstance(node, dict):
        return set().union(*(_token_hexes(v) for v in node.values()))
    if isinstance(node, list):
        return set().union(*(_token_hexes(v) for v in node))
    if isinstance(node, str) and node.startswith("#"):
        return {node.upper()}
    return set()


def _orphans(tokens: dict) -> list[str]:
    """Paires dont une couleur n'existe pas dans les tokens (derive de copie)."""
    known = _token_hexes(tokens["tailwind"]) | _token_hexes(tokens["semantic"])
    return [
        f"{pair['name']} ({color})"
        for pair in tokens["contrastPairs"]
        for color in (pair["fg"], pair["bg"])
        if color.upper() not in known
    ]


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TOKENS
    tokens = json.loads(path.read_text(encoding="utf-8"))
    pairs = tokens["contrastPairs"]
    orphans = _orphans(tokens)
    failures = 0
    for orphan in orphans:
        print(f"ORPHELINE (couleur absente des tokens) : {orphan}")
    print("| Paire | Avant-plan | Fond | Ratio | Seuil | Resultat |")
    print("|---|---|---|---|---|---|")
    for pair in pairs:
        ratio = contrast(pair["fg"], pair["bg"])
        ok = ratio >= pair["min"]
        failures += 0 if ok else 1
        verdict = "OK" if ok else "ECHEC"
        print(
            f"| {pair['name']} | `{pair['fg']}` | `{pair['bg']}` "
            f"| {ratio:.2f}:1 | {pair['min']}:1 | {verdict} |"
        )
    print(f"\n{len(pairs) - failures}/{len(pairs)} paires conformes")
    print(f"{len(orphans)} couleur(s) orpheline(s)")
    return 1 if failures or orphans else 0


if __name__ == "__main__":
    sys.exit(main())
