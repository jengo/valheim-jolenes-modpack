# Jolene's Reasonable and QOL Pack

Thoughtful quality-of-life updates for Valheim without making the game feel too cheap or unbalanced. Preserve survival, exploration, crafting, and progression while smoothing out annoyances.

## Mods

- [BepInExPack Valheim](https://thunderstore.io/c/valheim/p/denikson/BepInExPack_Valheim/) — mod loader.
- [TreesReborn](https://thunderstore.io/c/valheim/p/TastyChickenLegs/TreesReborn/) — configurable tree regrowth when stumps are removed.
- [SeneaL UI](https://thunderstore.io/c/valheim/p/seneaL/SeneaL_UI/) — UI overhaul with built-in slot locking.
- [HipWeapons](https://thunderstore.io/c/valheim/p/GemHunter1/HipWeapons/) — wear weapons at your hip.
- [DeathSoundMetalPipe](https://thunderstore.io/c/valheim/p/Pan_kapkan/DeathSoundMetalPipe/) — humorous global death sound.

SlotLock is deliberately **not** separately included. SeneaL UI already provides slot locking.

## Balancing and configuration

**Vanilla main inventory size (32):** `config/seneaL.valheim.ui.cfg` sets `[Inventory] Slots = 32` and `[Server] MaxSlots = 32`, with rule enforcement on. Configs ship within the package's `config/` directory. Existing player configs may take precedence; the cap is authoritative only where SeneaL UI is installed on the server and its rules are enabled. Six action slots are enabled below the hotbar, with a matching server limit. Food, action, equipment, and key slots are separate features and should be reviewed in the UI's F7 settings if you want strictly vanilla inventory behavior.

**TreesReborn:** its respawn probability and workstation restrictions are configurable. This pack does not invent undocumented config names. Run the game once with TreesReborn, edit its actual generated file under `BepInEx/config`, then copy it into this repository's `config/` directory (preserving its exact filename) and rebuild. For a conservative feel, consider lowering the replant chance from 100%; verify each key in your installed version first.

Check that mod managers actually apply pack configs to the active profile (existing configurations can be retained). Back up your world and character before major mod changes.

## GitHub CI / publishing

The GitHub Actions workflow validates the manifest and package, builds a ZIP on pull requests and pushes, then attaches a ZIP to a **GitHub Release** when a `vX.Y.Z` tag is pushed. It does **not** auto-upload to Thunderstore; publish the GitHub Release asset to Thunderstore manually. Tags must match `manifest.json` version.

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
# To release:
git tag v1.0.0
git push origin v1.0.0
```

Repository: [jengo/valheim-jolenes-modpack](https://github.com/jengo/valheim-jolenes-modpack).

Mod binaries are **not** redistributed. Credits to the respective authors.

## ValheimPlus (v1.0.1)
Uses the maintained Grantapher ValheimPlus fork. Automatic kiln/smelter/blast furnace chest handling and fire-source refueling from chests within 10 meters are enabled. Torches consume resin normally and refill from nearby chests; other fires also draw their normal fuel from nearby chests. No infinite fuel is enabled. All production rates, fuel costs, inventory capacity and combat settings stay vanilla. Kiln stops pulling wood when nearby coal reaches 100. ValheimPlus requires client/server installation; server enforces version and synchronizes config.
