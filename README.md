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

**Crafting from nearby chests (v1.0.10):** The packaged `config/seneaL.valheim.ui.cfg` explicitly enables `[Chests] FromChests = true` and `ChestRange = 100` for crafting and upgrading within 100 meters of the crafting station. `[Server] AllowCraftFromChests = true` permits this on dedicated servers and hosted games, with the existing `MaxCraftRange = 100` limit and `Enforce = true`. Server permission allows the feature; the client setting enables it. Install the pack's config on both clients and the dedicated server at `BepInEx/config/seneaL.valheim.ui.cfg`, with SeneaL UI and SeneaL API installed on both. Existing profiles may retain old config values; exit the game/server before copying or merging these settings. Chest exclusions and normal recipe costs still apply. Building from chests is also enabled with `[Chests] BuildFromChests = true`, `BuildRange = 100`, and `[Server] AllowBuildFromChests = true`.

Keys verified against the README and configuration strings in the [exact SeneaL UI 1.2.3 package](https://thunderstore.io/package/download/seneaL/SeneaL_UI/1.2.3/): its configuration table lists `[Chests] FromChests` / `ChestRange` (1–100 meters), and its server rules list `AllowCraftFromChests` / `MaxCraftRange`.

**Additional enabled defaults (v1.0.10):** `[Automation] Smelters = true` and `SmelterAuto = true` enable SeneaL UI autosmelters and automatic refilling; the existing `[Server] AllowSmelterAuto = true` permits it. Switch on the desired materials for each station in its window (hold Shift and press use by default); these per-station choices are stored in the world. Automatic refilling operates near a player (about 40 meters) and draws from chests, not the player's bag. Existing ValheimPlus fuel/input/output automation and its limits are unchanged; check the combined behavior in game before relying on station-specific SeneaL filters.

`[Inventory] Wallet = true` enables the coin wallet, with the existing `[Server] AllowWallet = true`. Coins retain normal weight (`AllowCoinWeight = false`). `[Map] OreDetect = true` enables automatic discovery of nearby ore deposits, and `[Server] AllowOreDetect = true` permits it. Ore detection radius and ore marker options retain the mod's defaults. `[Map] MarkerByView = true` makes the player arrow on both the minimap and world map follow the camera instead of the character. These keys are documented in the exact 1.2.3 package configuration table and present in its DLL configuration strings. The 32-slot main inventory cap, locked-recipe restriction, normal production costs, and fuel consumption are preserved.

**TreesReborn:** its respawn probability and workstation restrictions are configurable. This pack does not invent undocumented config names. Run the game once with TreesReborn, edit its actual generated file under `BepInEx/config`, then copy it into this repository's `config/` directory (preserving its exact filename) and rebuild. For a conservative feel, consider lowering the replant chance from 100%; verify each key in your installed version first.

Check that mod managers actually apply pack configs to the active profile (existing configurations can be retained). Back up your world and character before major mod changes.

## GitHub CI / publishing

The GitHub Actions workflow validates the manifest and package and builds a ZIP on pull requests and pushes. A push to **main** creates a **GitHub Release** and version tag from `manifest.json` (for example, `v1.0.3`), attaching the package ZIP. Existing releases are left unchanged; bump the manifest version to publish another release. Pushing a matching `vX.Y.Z` tag also publishes a release if it does not exist. Pull requests and manual workflow runs only build artifacts. Pushes to main also publish to Thunderstore using tcli. Use a new manifest version for each publication; duplicate versions are reported by tcli and fail the publishing job. Tags must match `manifest.json` version.

To enable Thunderstore publishing, create a service-account API token for your Thunderstore team and add it as the `prod` environment secret `THUNDERSTORE_API_TOKEN` (Settings → Environments → prod → Environment secrets). The team namespace defaults to `Jolene`; override it with the Actions variable `THUNDERSTORE_NAMESPACE` if needed. The token must have permission to publish under that team. Optional `THUNDERSTORE_CATEGORIES` is a comma-separated list of Valheim category slugs (default: `modpacks`). Missing credentials fail immediately, before invoking tcli. If the workflow log shows an empty `THUNDERSTORE_API_TOKEN`, check that it is saved as a secret in the `prod` environment; the dedicated publishing job selects `prod` and follows its protection rules. There is no Python API preflight: tcli performs the upload and reports API failures directly. Only pushes to main publish to Thunderstore; pull requests, tags, and manual runs do not. Bump `manifest.json` for each new version. Publishing uses the official Thunderstore CLI (`tcli` 0.2.3), installed with .NET 8. The existing ZIP is passed to `tcli publish --file`; Python only prepares temporary CLI configuration from the manifest and repository variables. The token is supplied through `TCLI_AUTH_TOKEN`, never a command argument or config file. CLI reference: [official Thunderstore CLI documentation](https://github.com/thunderstore-io/thunderstore-cli/wiki). Builds and GitHub Releases run independently of the `prod` environment; the publishing job downloads and repacks the validated artifact without changing its contents. GitHub Releases require the workflow’s existing `contents: write` permission; no additional GitHub secret is needed. A 403 can still indicate an invalid service-account token or a team namespace mismatch.

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

## Upgrade dependency versions

Run `make upgrade` (or `python3 scripts/update_dependencies.py`) to check every dependency already listed in `manifest.json` against Thunderstore and update its version to the latest active release. The script uses Python 3's standard library; no extra packages or API token are needed.

Preview changes without writing files:

```bash
python3 scripts/update_dependencies.py --dry-run
```

All lookups must succeed before the manifest is replaced. Deprecated packages, inactive releases, malformed responses, and network errors fail without a partial update. The updater preserves dependency order, never downgrades a pinned version, and changes only dependency versions. It does not add transitive dependencies, change configs, bump the modpack version, commit, or publish. Add or remove mods through the manifest; the script needs no mod-specific edits.

Review the reported upgrades and each mod's compatibility/config changes, then update the modpack version and changelog before building a release. Run the offline updater tests with `python3 scripts/test_update_dependencies.py`.
