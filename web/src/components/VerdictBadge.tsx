import type { VerdictLabel } from "../types";

const LABELS: Record<VerdictLabel, string> = {
  pass: "通过",
  fail: "未通过",
  unsure: "待确认",
  pending: "未检查",
  confirmed: "已人工确认",
};

export default function VerdictBadge({ status }: { status: VerdictLabel }) {
  return <span className={`badge ${status}`}>{LABELS[status] ?? status}</span>;
}
