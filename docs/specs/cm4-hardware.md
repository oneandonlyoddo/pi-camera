# Hardware: Compute Module 4 instead of Pi Zero 2 W

Status: draft (parked: potential hardware upgrade, no date) · Updated: 2026-11-19

## Goal
Replace the Pi Zero 2 W with a Raspberry Pi Compute Module 4 on a small carrier board, with a 2.8" DSI touchscreen instead of the 3.5" HDMI LCD, to get faster captures and headroom for image effects (film grain, later GLSL filters), without losing touch, button or battery operation.

## Decisions
- **Goal: both capture speed and effects.** Why: the user wants the 6–8 s save gone and room for grain/GPU filters; that is what justifies the extra power and heat.
- **Battery life: ~3.5–4.5 h of preview (estimate) is acceptable for now.** Why: power optimisation comes later; 18650 cells were chosen so they can be swapped on the go.
- **Module: CM4, not CM5.** Why: CM5 is much more expensive and draws even more power, which hurts running from 2× 18650. The CM4 keeps today's camera pipeline (rpi/vc4, same tuning file, same DNG code).
- **Module bought (2026-11-19): CM4101016** = CM4 with wireless, 1 GB RAM, 16 GB eMMC. Consequences: boots from eMMC, not microSD (see Constraints); 1 GB instead of the 2 GB first assumed.
- **Display: a 2.8" DSI touchscreen** (to be bought later; model not fixed yet). Why: DSI over HDMI for less power and no bridge chip; over SPI because SPI can't carry the hardware-plane DRM preview (Notes). Consequence: the carrier must have a DSI port, so the Nano A is out.
- **Photos on a second SD slot, OS on the eMMC (2026-11-19).** Why: the user wants OS and photos separated on a removable card; space is not the concern. The carrier's own SD slot is dead with an eMMC CM4 (it shares the eMMC's SD interface), so a microSD breakout is wired to the CM4's second SD interface on the 40-pin header: GPIO 22 CLK (pin 15), 23 CMD (pin 16), 24–27 DAT0–3 (pins 18, 22, 37, 13), plus 3.3 V and GND; `config.txt`: `dtoverlay=sdio` (4-bit). The card is mounted at `PROJECT_ROOT/DCIM` (fstab), so `PHOTOS_DIR` and R4 stay unchanged: no code change. Risks: not yet checked on a CM4 with wireless (verify the overlay and that Wi-Fi still works); short wires needed for signal quality; the breakout may need pull-ups on CMD/DAT if it has none; GPIO 22–27 are then taken (button on GPIO 17 and DSI touch are unaffected). Rejected alternatives: a USB card reader in the USB-A port (simpler, no soldering, but sticks out of the case and needs `dtoverlay=dwc2,dr_mode=host`; fallback if the sdio route fails), a separate eMMC partition (no removable card).
- **Status: parked.** The user saves this as a potential upgrade plan; it is not scheduled. Resume with `/spec` when the display is bought.

## Requirements
(to be filled when the spec is resumed and the open questions are decided)

## Out of scope
- Code changes beyond what the new board needs (config, SPECS facts, re-tested capture limits, HUD/menu layout for the new display). Using the extra speed (background save worker, GPU preview, grain) stays in its own specs.

## Constraints and risks
- **Carrier needs DSI:** the Waveshare Nano Base Board (A) has no HDMI and no DSI (only CSI, USB-A, the 40-pin header, microSD), so it can't drive the chosen display. The Nano B has DSI (open question).
- **eMMC module:** on the Nano boards the microSD slot works only with CM4 Lite; with the CM4101016 the OS lives on the 16 GB eMMC and the SD slot stays unused. Flashing needs the carrier's BOOT switch + `rpiboot` from the desktop. 16 GB minus the OS (~3–4 GB) leaves roughly 12 GB for DCIM: about 400 12 MP JPG+DNG shots (~28 MB each), or ~3000 JPG-only. The web gallery is the way photos leave the camera, so a full disk becomes reachable; how the camera reacts to a full disk is untested today too. `scripts/dev.sh` is unaffected (SSH). Photos go to a second SD card instead (Decisions).
- **New display = layout work:** the HUD and menu are laid out for 800×480 in `menu.py` / `hud.py` / `docs/design/hud.md`; `PREVIEW_WIDTH/HEIGHT`, `TOUCH_*` calibration and possibly rotation (many small DSI panels are portrait) change. A 2.8" screen is smaller than today's 3.5", so touch targets get physically smaller. The panel needs its own `dtoverlay`; check that it lists the CM4 and that its ribbon fits the carrier's DSI connector (15-pin vs 22-pin).
- **Touch:** small DSI panels usually have capacitive touch on I2C instead of the XPT2046 on SPI. `touchscreen.py` reads any evdev device (device name and `TOUCH_*` flags change); `LiftFilter` probably becomes unnecessary but harmless.
- **Button:** GPIO 17 on the 40-pin header, which every Nano board has. Expected unchanged.
- **Camera:** the Nano boards use a 15-pin 1.0 mm CSI connector, the HQ camera's native one (the Zero needs the 22-pin adapter cable). Compute Modules don't auto-detect the camera: `config.txt` needs `camera_auto_detect=0` and `dtoverlay=imx477` with the right `cam0`/`cam1` port.
- **Software:** same OS (Raspberry Pi OS Lite arm64, trixie), same picamera2, same libcamera pipeline handler (`rpi/vc4`) and the same `imx477.json` tuning file. Image quality and presets don't change. No apt changes (R1). SPECS hardware facts must be re-measured.
- **Power (SPECS: 2× 18650):** rough estimates, not measured: Zero 2 W ~0.6 W idle, ~3 W peak; CM4 ~1.5–2 W idle, ~6–7 W peak. Camera and display add ~1–1.5 W to both (a 2.8" DSI panel likely less than the HDMI LCD). With ~18 Wh usable from 2× 18650: Zero setup ~5–7 h of preview, CM4 setup ~3.5–4.5 h. The 5 V regulator must deliver ≥ 3 A; under-voltage throttles the CPU (`--health` shows `throttled`).
- **Heat:** the A72 cores run much hotter than the Zero's A53. In a closed enclosure it needs a heatsink, or it throttles at 80 °C, which removes part of the speed gain.
- **Wi-Fi:** the CM4101016 has it. The PCB antenna is weak inside a case; an external antenna needs the U.FL connector and `dtparam=ant2`.
- **Size:** Nano B 56×41 mm plus the CM4 stacked on top (thicker than the Zero 2 W's 65×30 mm).

## Expected gains (estimates, to be measured)
- **CPU:** A72 @ 1.5 GHz is roughly 2.5–3× faster per core than the Zero's A53 @ 1 GHz; memory bandwidth (LPDDR4 vs LPDDR2) several times higher. Our capture work (DNG packing, JPEG encode, numpy) is single-threaded and memory-bound, so it gains from both.
- **Memory:** 1 GB instead of ~416 MB usable (about 2.3× after the GPU share). A 12 MP JPG+DNG capture needs well under that, so the swapping seen on the Zero (SPECS) should stop, and the `buffer_count=2` / ENOMEM / fetch-order limits probably relax (to be re-tested, R8). Less margin than 2 GB for film grain on full 12 MP float arrays: keep effects in uint8/uint16 or strips.
- **eMMC:** faster than microSD for writing the ~24 MB DNG.
- **Shot timing:** guess 12 MP JPG+DNG saved in ~1.5–3 s instead of 5.8–8.1 s. The sensor mode switch (IMX477 at max 10 fps at 12 MP) doesn't get faster, so the 1 s shot-to-shot target stays hard with the current mode-switch capture.
- **Film grain:** the film-grain spec's guess for numpy on the Zero is 1–3 s at 12 MP; on the CM4 roughly 0.3–0.8 s. The GPU changes from VideoCore IV (GLES 2, 2048 px textures) to VideoCore VI (GLES 3.x, 4096 px textures): a 12 MP still (4056×3040) fits one texture, so the film-grain spec's "GPU ruled out" and the planned GPU preview get re-evaluated.
- **Boot:** faster Python imports and eMMC; helps the 10 s boot target.
- **Not faster:** the preset switch (~1.6 s, of which 1 s is the fixed settle sleep), the sensor itself, image quality.

## Verification
- `/on-device` `--health`: picamera2 version, memory, throttling, temperature.
- `--check`, `--test`, `--shoot`: same results as on the Zero.
- Re-measure every SPECS fact: shot timing (12 MP / 3 MP), preset switch, capture memory, `buffer_count`, fetch order, boot to ready.
- Power: current draw at idle preview, during capture and at peak (USB meter), and a battery run time test.
- Photo card: `lsblk` shows the second SD card, it is mounted at DCIM, a `--shoot` lands on it, write speed for a 24 MB DNG, Wi-Fi still works with the overlay on.
- Needs a person: display picture, HUD/menu layout on the 2.8" panel, touch calibration, button, heat in the enclosure.

## Open questions (decide when resumed)
- **Display model:** which 2.8" DSI panel (resolution, orientation, touch controller, overlay, connector). Then the HUD/menu layout for it.
- **Carrier board** (must have DSI): Nano B with the RJ45 (and audio jack, maybe USB-A) desoldered (recommended; 56×41 mm, the Ethernet PHY is on the CM4 so only the jack is lost); Mini Base Board (A) (85×56 mm, still has RJ45); a custom carrier (open CM4 reference design, could also carry the 18650 charger).
- **Missing photo card guard:** if the SD card is missing, the app would write into the empty mount point on the eMMC. Options: `RequiresMountsFor=` in the service (camera doesn't start without the card), or a mount check at startup with a HUD/web warning (camera still usable). Decide when resumed.

## Notes
- **DSI vs HDMI display:**
  - DSI pros: no HDMI cable or HDMI-to-LCD bridge chip (less power, thinner); the panel runs at its native resolution, not 800×480 scaled down to 480×320 as today; small DSI panels have capacitive touch on I2C (multi-touch, no contact loss mid-drag).
  - DSI cons: a new panel, so the HUD and menu layout must fit its resolution, touch calibration is redone, and the panel needs its own `dtoverlay`. Ribbon cables are short and fragile; some panels need an adapter cable for CM boards. Capacitive touch doesn't work with gloves.
  - Same for both: picamera2's DRM preview works on DSI and HDMI (KMS); `touchscreen.py` reads any evdev touch device.
- **SPI display** (user has one; rejected for the viewfinder 2026-11-19):
  - Pros: needs only the 40-pin header, so it works on the Nano A; low power; often the same XPT2046 touch as today.
  - Cons: SPI bandwidth limits the refresh to roughly 10–20 fps at 480×320, often with tearing. picamera2's DRM preview puts the camera image and the HUD on hardware planes of the vc4 display; an SPI panel is a separate, plane-less display (mipi-dbi driver) and `fbcp` doesn't work under KMS. The preview would need our own CPU path (new code in hud.py/digital_camera.py, CPU load competing with capture). Manual focusing with the Pentax lens is harder on a slow preview.
  - Ranking for a viewfinder: DSI > HDMI > SPI.
  - Waveshare DSI panels for reference: 4inch (480×800, capacitive, CM4 listed): https://waveshare.com/wiki/4inch_DSI_LCD; 4.3inch: https://www.waveshare.com/4.3inch-DSI-LCD.htm
- **Carrier boards checked** (2026-11-15): no off-the-shelf CM4 carrier around Pi Zero size with a display output and without Ethernet was found. Waveshare Mini Base Board (A): 85×56 mm, 2× CSI, 1× DSI, 2× HDMI (one as FFC), RJ45 (https://thepihut.com/products/mini-base-board-a-for-raspberry-pi-compute-module-4). Mini Base Board (B): 85×56 mm, RTC, HDMI; DSI not listed. Seeed reRouter: 75×64×21 mm, micro HDMI, CSI, DSI, but dual Ethernet. Open hobby carrier on Hackaday without Ethernet (2× camera, DSI, HDMI): https://hackaday.io/project/165108-carrier-board-for-the-raspberry-pi-compute-module.
- **CM5 rejected** (2026-11-15): see Decisions. Faster (A76 @ 2.4 GHz, PiSP ISP) but cost and power; would also need new tuning files and PiSP raw decompression in `_save_dng`.
- Waveshare CM4-NANO-A: https://www.waveshare.com/cm4-nano-a.htm (CSI 15-pin, USB-A, 40-pin, microSD, 5 V; no HDMI/DSI). BerryBase listing: https://www.berrybase.de/en/nano-base-board-a-for-raspberry-pi-compute-module-4
- Waveshare CM4-NANO-B: https://www.waveshare.com/product/cm4-nano-b.htm (mini HDMI 4K30, DSI 15-pin, CSI 15-pin, USB-A, Gigabit Ethernet, 3.5 mm audio, 56×41 mm, 5 V).
- Power figures are typical published values for the Zero 2 W and Pi 4/CM4, not measured on this camera.
