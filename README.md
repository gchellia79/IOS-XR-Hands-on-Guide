# IOS XR Hands-on Guide

MkDocs Material site for the PTA IOS XR lab/demo guide. The published pages walk through commit behaviour, processes, memory leak detection, task groups, and useful debugging commands.

## Run locally

```text
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1` instead of `source`.

Open the URL printed by `mkdocs serve` (typically `http://127.0.0.1:8000`).

Build a static site with:

```text
mkdocs build --strict
```

The output is written to `site/` (ignored by git). GitHub Pages is built from `main` by `.github/workflows/deploy.yml`.

## Add screenshots

1. Put image files in the chapter folder, numbered in order of appearance:
   `docs/NN-short-name/images/image01.png`, `image02.png`, …
2. Reference them from that chapter’s `index.md`:

   ```markdown
   ![Short description](images/image01.png)
   ```

3. If a shot is still missing, leave a placeholder comment instead of a broken link:

   ```html
   <!-- SCREENSHOT: images/imageNN.png | what it should show -->
   ```

Do not commit the source `.docx`, `_import/`, `.venv/`, or `site/`. Never commit passwords, tokens, or other credentials; use placeholders such as `<password>`.
