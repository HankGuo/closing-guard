# Closing Guard — pilot evaluation

- Generated: 2026-11-14T16:35:22+0800
- API: http://127.0.0.1:8010
- Samples: 8
- Verdict accuracy: **87.5%**
- False-pass on expected-fail items: **0** (0.0%)
- Mean capture latency: **1.85 s**

| Checkpoint | Image | Expected | Actual | Jev | Confidence | Latency (s) | Note |
|---|---|---|---|---|---|---|---|
| gas_valve | gas_valve_closed.jpg | pass | pass | — | 0.80 | 1.16 | 阀门把手与管道大致垂直且画面无火焰或烟雾，阀门本体完整，符合关闭状态合格标准。 |
| gas_valve | gas_stove_flame.jpg | fail | fail | — | 0.85 | 1.06 | 火焰颜色交叉检查：画面中检测到明火/高饱和火焰色，燃气未关闭 |
| power_panel | power_panel_off.jpg | pass | pass | — | 0.80 | 1.48 | 所有开关手柄均朝下表示 OFF（断电），除部分常开回路外，其余均处于断电状态，符合闭店安全巡检标准。 |
| power_panel | power_panel_on.jpg | fail | unsure | — | 0.50 | 1.27 | 所有断路器手柄均朝下表示 OFF（断电），除可能存在的监控回路外，其余开关处于关闭状态，符合闭店安全巡检标准。 |
| door_lock | door_locked.jpg | pass | pass | — | 0.80 | 1.04 | 锁舌伸出且挂锁处于锁定状态，门缝无明显被撬痕迹，锁梁未打开，符合可靠锁闭标准。 |
| door_lock | door_unlocked.jpg | fail | fail | — | 0.80 | 0.91 | 锁梁未扣入锁体，挂锁处于未锁定状态，不符合可靠锁闭标准。 |
| gas_meter | gas_meter_card.jpg | pass | pass | 0.983 | 0.98 | 4.08 | 读数已识别，建议人工确认末位；Jev 一致性 0.98 |
| gas_meter | water_meter.jpg | unsure | unsure | 0.004 | 0.00 | 3.82 | Jev 一致性分数很低，读数与图像可能不一致，请人工确认 |

## Per-checkpoint

| Checkpoint | n | Accuracy | False pass | Mean latency (s) |
|---|---|---|---|---|
| gas_valve | 2 | 100.0% | 0 | 1.11 |
| power_panel | 2 | 50.0% | 0 | 1.38 |
| door_lock | 2 | 100.0% | 0 | 0.98 |
| gas_meter | 2 | 100.0% | 0 | 3.95 |

## Interpretation

This is a small pilot set, not a statistically significant benchmark. It is intentionally adversarial: the gas-flame case is caught by the CV flame cross-check, while the power-panel ON case is a known 1B weakness. That is exactly why every critical `pass` requires a human confirmation before the session can be completed. The false-pass number here is **model-only**; the system-level ledger cannot close without the human confirmation.

The water-meter case is a deliberate uncertainty case: the last digit is rolling, so OCR must not be trusted as an accounting value. The system returns `unsure` and asks for human confirmation.
