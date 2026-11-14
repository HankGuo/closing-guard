# Sample data, labels, and licenses

The images in `data/samples/` are **test fixtures**, not part of the Apache-2.0
source license. Each image keeps its original license; resized copies are
derivative works under the same license. Attribution:

| File | Source (Wikimedia Commons) | Author | License | Changes |
|---|---|---|---|---|
| `gas_valve_closed.jpg` | [Propane cylinder valve 001.jpg](https://commons.wikimedia.org/wiki/File:Propane_cylinder_valve_001.jpg) | Jeuwre | CC BY-SA 4.0 | resized, re-encoded |
| `gas_stove_flame.jpg` | [Gas stove flame.jpg](https://commons.wikimedia.org/wiki/File:Gas_stove_flame.jpg) | Ivan Radic | CC BY 2.0 | resized, re-encoded |
| `power_panel_on.jpg` | [Eaton circuit breaker panel open.JPG](https://commons.wikimedia.org/wiki/File:Eaton_circuit_breaker_panel_open.JPG) | BrokenSphere | CC BY-SA 3.0 | resized, re-encoded |
| `power_panel_off.jpg` | [ABB 230V 16A fuses in fuse box in German shop, 2024.jpg](https://commons.wikimedia.org/wiki/File:ABB_230V_16A_fuses_in_fuse_box_in_German_shop,_2024.jpg) | Pittigrilli | CC0 | resized, re-encoded |
| `door_locked.jpg` | [Padlock with chain.jpg](https://commons.wikimedia.org/wiki/File:Padlock_with_chain.jpg) | Lacz02 | CC BY-SA 4.0 | resized, re-encoded |
| `door_unlocked.jpg` | [Padlock klódka ubt.JPG](https://commons.wikimedia.org/wiki/File:Padlock_kl%C3%B3dka_ubt.JPG) | Tomasz Sienicki | CC BY-SA 3.0 | resized, re-encoded |
| `water_meter.jpg` | [A Water Meter Type LXSC-15E.jpg](https://commons.wikimedia.org/wiki/File:A_Water_Meter_Type_LXSC-15E.jpg) | JULIANISME | CC BY-SA 4.0 | resized, re-encoded |
| `gas_meter_card.jpg` | Generated test card | Closing Guard contributors | Apache-2.0 | synthetic text card, no real meter |

`labels.csv` is released under Apache-2.0 with the rest of the repository.

## Important honesty notes

- `gas_meter_card.jpg` is a **synthetic OCR test card**, clearly labelled as such.
  It validates the OCR path, not real-meter accuracy.
- The water-meter image is a **real photo** with a rolling last digit. OCR is
  expected to be uncertain; the system returns `unsure` and requires human
  confirmation. This is intentional.
- `power_panel_on.jpg` is a known hard case for the 1B model. Mandatory human
  confirmation is the mitigation; see `docs/SAFETY.md`.
- If you redistribute the CC BY-SA images, keep the attribution and share-alike
  terms. If you only redistribute the code, the images can be omitted.
