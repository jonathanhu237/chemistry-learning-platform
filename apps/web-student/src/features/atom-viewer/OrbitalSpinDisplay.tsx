type SpinState = "up" | "down";

type OrbitalSpinDisplayProps = {
  occupancy: number[];
  slotLabels: string[];
  subshellLabel: string;
};

const SPIN_UP = "\u2191";
const SPIN_DOWN = "\u2193";

function buildSpinSlotsFromOccupancy(occupancy: number[], slotCount: number) {
  return Array.from({ length: slotCount }, (_, index) => {
    const electronCount = Math.min(Math.max(occupancy[index] ?? 0, 0), 2);
    const spins: SpinState[] = [];

    if (electronCount >= 1) {
      spins.push("up");
    }

    if (electronCount >= 2) {
      spins.push("down");
    }

    return spins;
  });
}

function formatSpin(spin: SpinState) {
  return spin === "up" ? SPIN_UP : SPIN_DOWN;
}

function renderSpinBox(label: string, spins: SpinState[]) {
  return (
    <div key={label} className="spin-box" aria-label={`${label}: ${spins.length} 个电子`}>
      <small>{label}</small>
      <span className="spin-arrows">
        {spins.map((spin) => (
          <i key={spin}>{formatSpin(spin)}</i>
        ))}
      </span>
    </div>
  );
}

export function OrbitalSpinDisplay({ occupancy, slotLabels, subshellLabel }: OrbitalSpinDisplayProps) {
  const spinSlots = buildSpinSlotsFromOccupancy(occupancy, slotLabels.length);
  const isFOrbital = slotLabels.length === 7;
  const spinItems = slotLabels.map((label, index) => ({
    label,
    spins: spinSlots[index],
  }));

  return (
    <section className="spin-display" aria-label={`${subshellLabel} 电子自旋占据`}>
      <div className="spin-display-heading">
        <span>电子自旋</span>
        <strong>{subshellLabel}</strong>
      </div>

      {isFOrbital ? (
        <div className="spin-box-row spin-box-row-f">
          <div className="spin-box-line spin-box-line-4">
            {spinItems.slice(0, 4).map((item) => renderSpinBox(item.label, item.spins))}
          </div>
          <div className="spin-box-line spin-box-line-3">
            {spinItems.slice(4).map((item) => renderSpinBox(item.label, item.spins))}
          </div>
        </div>
      ) : (
        <div className="spin-box-row">{spinItems.map((item) => renderSpinBox(item.label, item.spins))}</div>
      )}
    </section>
  );
}
