// Recharts wrappers with the KrishiVeda chart style:
// thin marks, recessive grid, tooltips on hover, one y-axis per chart (never dual-axis).
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, LabelList,
} from "recharts";

export const CHART = {
  leaf: "#2f7d4a",
  sky: "#2f6db3",
  sun: "#c4661b",
  grid: "#e6e9e2",
  axis: "#56645b",
};

const axisProps = { tick: { fill: CHART.axis, fontSize: 12 }, tickLine: false, axisLine: { stroke: CHART.grid } };
const tooltipStyle = { borderRadius: 12, border: "1px solid #dfe3d8", fontSize: 13 };

/** Two temperature series (max/min) on one shared °C axis. */
export function TempChart({ data, maxLabel, minLabel }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 16, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid stroke={CHART.grid} vertical={false} />
        <XAxis dataKey="label" {...axisProps} />
        <YAxis {...axisProps} unit="°" width={44} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v} °C`} />
        <Legend iconType="plainline" wrapperStyle={{ fontSize: 13 }} />
        <Line type="monotone" dataKey="max" name={maxLabel} stroke={CHART.sun} strokeWidth={2} dot={{ r: 4, strokeWidth: 2, fill: "#fff" }} activeDot={{ r: 6 }}>
          <LabelList dataKey="max" position="top" fontSize={11} fill={CHART.axis} formatter={(v) => `${Math.round(v)}°`} />
        </Line>
        <Line type="monotone" dataKey="min" name={minLabel} stroke={CHART.sky} strokeWidth={2} dot={{ r: 4, strokeWidth: 2, fill: "#fff" }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

/** Single-series bar chart (vertical bars). */
export function SimpleBarChart({ data, dataKey, nameKey = "label", color = CHART.leaf, unit = "", height = 220, valueLabel }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 18, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid stroke={CHART.grid} vertical={false} />
        <XAxis dataKey={nameKey} {...axisProps} interval={0} />
        <YAxis {...axisProps} width={48} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(47,125,74,0.06)" }} formatter={(v) => [`${v}${unit}`, valueLabel]} />
        <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} maxBarSize={36}>
          <LabelList dataKey={dataKey} position="top" fontSize={11} fill={CHART.axis} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Single-series horizontal bars — good for long category names (crops, markets). */
export function HorizontalBarChart({ data, dataKey, nameKey = "label", color = CHART.leaf, format = (v) => v, valueLabel }) {
  const height = Math.max(120, data.length * 40 + 30);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, left: 8, bottom: 4 }}>
        <CartesianGrid stroke={CHART.grid} horizontal={false} />
        <XAxis type="number" {...axisProps} hide />
        <YAxis type="category" dataKey={nameKey} {...axisProps} width={110} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(47,125,74,0.06)" }} formatter={(v) => [format(v), valueLabel]} />
        <Bar dataKey={dataKey} fill={color} radius={[0, 4, 4, 0]} barSize={20}>
          <LabelList dataKey={dataKey} position="right" fontSize={12} fill={CHART.axis} formatter={format} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
