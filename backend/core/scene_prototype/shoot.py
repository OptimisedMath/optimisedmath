"""PROTOTYPE — throwaway. Rasterise gallery.html so the figures can be eyeballed."""

import pathlib
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
here = pathlib.Path(__file__).parent

theme = sys.argv[1] if len(sys.argv) > 1 else "light"
width = int(sys.argv[2]) if len(sys.argv) > 2 else 1120
height = int(sys.argv[3]) if len(sys.argv) > 3 else 3600

src = here / "gallery.html"
page = src.read_text(encoding="utf-8")
if theme == "dark":
    page = page.replace(
        "<header>",
        '<script>document.documentElement.dataset.theme="dark"</script><header>',
    )
target = here / f"_shot_{theme}_{width}.html"
target.write_text(page, encoding="utf-8")

out = here / f"shot_{theme}_{width}.png"
subprocess.run(
    [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--screenshot={out}",
        f"--window-size={width},{height}",
        f"--force-device-scale-factor=2",
        str(target),
    ],
    check=True,
    capture_output=True,
)
target.unlink()
print(out)
