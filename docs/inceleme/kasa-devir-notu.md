# Checkout design hand-off note (Claude → Codex, 23 Oct 21:50)

Sena's decision: the checkout design belongs to Codex. The flow Codex proposed (HOMI self-service return point, manager tablet, amber "Review required") will be implemented. Claude no longer touches this file (counterfoil-magaza.blend).

Last commit: 022c19b (main, github.com/kosesena/counterfoil, private).

## File and scene
- docs/gorseller/counterfoil-magaza.blend, scene `Counterfoil_Market_Composite`.
- Sena's viewing window is open (old version). Do not have her save; two windows must not save at the same time.

## Checkout area (Floor 1, front left)
- 3 tills `SE_Till0/1/2_*`: bodies at x -16.7 / -13.5 / -10.2, y -9.6..-7.2. Each one has a POS terminal, a PayPal sticker and a QR stand.
- The scene takes place at Till1. On the belt there are `SE_Till1_Item_*` products and `SE_Till1_Receipt*`.

## Characters
- `Inst_<Role>` empties and `Cast_<Role>` collections.
- Rigs are set up with `tools/rig_and_animate.py`:
  - END=720, WALK_END=590.
  - The customer has a 'pay' arm motion; the manager has a tablet-holding pose.
- Plinths and name labels are hidden. The Insts are at z=-0.16.
- Customer:
  - 1–170: takes a cart outside and enters.
  - 170–590: passes through the security gates (`SE_GateEntry*`, `SE_GateExit*`) and walks to the customer side of Till1 (x -12.3, y -8.75).
  - 604: turns toward -x.
- Reader_Agent and Transaction_Agent were turned into robots:
  - Human face parts are hidden.
  - Added parts: `<Role>_HeadScreen`, `EyeLED*`, `MouthLED`, `HeadAntenna*`, `EarCap*`, `ChestAI`.
  - Positions: Transaction_Agent (-14.45, -9.25), Reader (-15.35, -8.05).
  - If in Codex's design these become on-screen characters or a small helper next to the scanner, the two large figures can be removed and replaced.
- The manager has a tablet and is in the glass "STORE OFFICE" booth (`SE_Office_*`, Inst (-17.85, -11.05)).

## Other new parts of the store
- Basket stand (`tools/basket_stand.py`, `SE_BStand_*`).
- Entry and exit security gates.

## Scenario
- Order $90, 3 items: tray, bowl, vase.
- Return record (RMA) $30, for the tray.
- In the attack, the agent asks for $90.
- The manager rejects the request. $30 is recreated and passes through the gate again. The receipt comes out only after the payment service confirms success.

## Rules
- Do not commit. When done, write what you changed and the render paths; Claude reviews and commits.
- No third-party brands in the video (no IKEA). PayPal logos are in the `marka-dis/` folder (in gitignore).
