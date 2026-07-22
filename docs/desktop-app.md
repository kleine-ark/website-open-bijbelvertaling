# Desktop-app (Tauri) — Open Vertaling

De website wordt met [Tauri 2](https://tauri.app) verpakt tot een **offline
desktop-app** voor **Windows** en **Linux**. De volledige bijbeltekst, grondtekst,
kanttekeningen, onderwerpen en opmaak zitten in de app — geen internet nodig.

> Audio (voorlezingen) zit **niet** in de app (11 GB). Wanneer er internet is, kan de
> app de voorlezing alsnog van openvertaling.nl halen.

## Structuur

```
src-tauri/              de Tauri/Rust-wrapper
  tauri.conf.json       app-config (naam, versie, vensters, bundel-targets)
  Cargo.toml            Rust-dependencies
  src/main.rs, lib.rs   entry point
  icons/                app-iconen (gegenereerd met `cargo tauri icon`)
desktop/
  build-dist.mjs        stelt de web-assets samen in desktop/dist/ (excl. audio)
.github/workflows/desktop-release.yml   CI: bouwt + publiceert de release
```

De `beforeBuildCommand` in `tauri.conf.json` draait automatisch `node
desktop/build-dist.mjs`, dat alle benodigde web-bestanden (html, css, js, **data**,
icons, images, fonts, manifest.json, sw.js, embed.js) naar `desktop/dist/` kopieert.
`audio/`, git, venvs, scripts en docs worden bewust overgeslagen.

## Lokaal bouwen

Vereisten: Rust (stable), Node 18+, en op Linux de webkit2gtk-dev-pakketten.

```bash
# Linux: AppImage + .deb
cargo tauri build --bundles appimage deb

# Windows (op een Windows-machine): installer (.exe)
cargo tauri build --bundles nsis
```

De resultaten staan in:

```
src-tauri/target/release/bundle/appimage/*.AppImage
src-tauri/target/release/bundle/deb/*.deb
src-tauri/target/release/bundle/nsis/*-setup.exe   (alleen op Windows)
```

Ontwikkelen met live venster: `cargo tauri dev`.

## Een release maken op GitHub

Windows kan niet betrouwbaar vanaf Linux gecross-compileerd worden, daarom bouwt
**GitHub Actions** beide platforms. Push een versietag:

```bash
git tag v0.21.0
git push origin v0.21.0
```

De workflow `desktop-release.yml` bouwt dan op `windows-latest` en `ubuntu-22.04` en
hangt de bestanden (Windows-installer, Linux-AppImage, .deb) automatisch onder een
nieuwe GitHub-release met dezelfde tag. Handmatig starten kan ook via de Actions-tab
(workflow_dispatch).

De lokaal gebouwde Linux-AppImage kan los aan een bestaande release toegevoegd worden:

```bash
gh release upload v0.21.0 src-tauri/target/release/bundle/appimage/*.AppImage
```

## Versienummer

Houd `version` in `src-tauri/tauri.conf.json` en `src-tauri/Cargo.toml` gelijk aan de
sitestatistieken (`data/stats.json`). De git-tag (`vX.Y.Z`) bepaalt de release-naam.
