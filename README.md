# Jolene's Reasonable and QOL Pack

Thoughtful quality-of-life updates for Valheim without making the game feel too cheap or unbalanced. Preserve survival, exploration, crafting, and progression while smoothing out annoyances.

## Mods

- [BepInExPack Valheim](https://thunderstore.io/c/valheim/p/denikson/BepInExPack_Valheim/) — mod loader.
- [TreesReborn](https://thunderstore.io/c/valheim/p/TastyChickenLegs/TreesReborn/) — configurable tree regrowth when stumps are removed.
- [SeneaL UI](https://thunderstore.io/c/valheim/p/seneaL/SeneaL_UI/) — UI overhaul with built-in slot locking.
- [HipWeapons](https://thunderstore.io/c/valheim/p/GemHunter1/HipWeapons/) — wear weapons at your hip.
- [DeathTweaks](https://thunderstore.io/c/valheim/p/Muindor/DeathTweaks/) — keep items, active food, and skills on death.
- [DeathSoundMetalPipe](https://thunderstore.io/c/valheim/p/Pan_kapkan/DeathSoundMetalPipe/) — humorous global death sound.

SlotLock is deliberately **not** separately included. SeneaL UI already provides slot locking.

## Balancing and configuration

**Easier deaths (v1.0.4):** `config/muindor.DeathTweaks.cfg` enables `KeepAllItems` and `KeepFoodLevels`, disables `ReduceSkills`, and enables server `ConfigPriority`. Install DeathTweaks on every player and on the server/host to apply shared rules. Players without the mod are unaffected. Existing profile configs may need updating. SeneaL UI extra-slot retention still needs an in-game compatibility check.

**Vanilla main inventory size (32):** `config/seneaL.valheim.ui.cfg` sets `[Inventory] Slots = 32` and `[Server] MaxSlots = 32`, with rule enforcement on. Configs ship within the package's `config/` directory. Existing player configs may take precedence; the cap is authoritative only where SeneaL UI is installed on the server and its rules are enabled. Six action slots are enabled below the hotbar, with a matching server limit. Food, action, equipment, and key slots are separate features and should be reviewed in the UI's F7 settings if you want strictly vanilla inventory behavior.

**TreesReborn:** its respawn probability and workstation restrictions are configurable. This pack does not invent undocumented config names. Run the game once with TreesReborn, edit its actual generated file under `BepInEx/config`, then copy it into this repository's `config/` directory (preserving its exact filename) and rebuild. For a conservative feel, consider lowering the replant chance from 100%; verify each key in your installed version first.

Check that mod managers actually apply pack configs to the active profile (existing configurations can be retained). Back up your world and character before major mod changes.

## GitHub CI / publishing

The GitHub Actions workflow validates the manifest and package and builds a ZIP on pull requests and pushes. A push to **main** creates a **GitHub Release** and version tag from `manifest.json` (for example, `v1.0.3`), attaching the package ZIP. Existing releases are left unchanged; bump the manifest version to publish another release. Pushing a matching `vX.Y.Z` tag also publishes a release if it does not exist. Pull requests and manual workflow runs only build artifacts. It does **not** auto-upload to Thunderstore; publish the GitHub Release asset to Thunderstore manually. Tags must match `manifest.json` version.

The Actions artifact download (`valheim-modpack.zip`) is also ready to upload directly to Thunderstore. Both downloads contain `manifest.json`, `icon.png`, and `README.md` at the ZIP root. Older Actions artifacts wrap the package ZIP inside another ZIP; extract those downloads and upload the inner `Jolenes_Reasonable_and_QOL_Pack-*.zip` file instead. Do not upload GitHub's source-code ZIP.

```bash
python3 scripts/validate.py
python3 scripts/build.py
# after creating your GitHub repository:
git init
git add .
git commit -m "Initial modpack"
git branch -M main
git remote add origin git@github.com:jengo/valheim-jolenes-modpack.git
git push -u origin main
# To release: update manifest.json and CHANGELOG.md, commit, and push main.
```

Repository: [jengo/valheim-jolenes-modpack](https://github.com/jengo/valheim-jolenes-modpack).

Mod binaries are **not** redistributed. Credits to the respective authors.

## ValheimPlus (v1.0.2)
Uses the maintained Grantapher ValheimPlus fork. Automatic kiln/smelter/blast furnace chest handling and fire-source refueling from chests within 10 meters are enabled. Torches consume resin normally and refill from nearby chests; other fires also draw their normal fuel from nearby chests. No infinite fuel is enabled. All production rates, fuel costs, inventory capacity and combat settings stay vanilla. Kiln stops pulling wood when nearby coal reaches 100. ValheimPlus requires client/server installation; server enforces version and synchronizes config.
