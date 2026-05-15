import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useTrends } from "@/lib/queries";

export function TrendChart() {
  const { data, isLoading } = useTrends();
  if (isLoading) return <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Loading…</div>;
  if (!data?.length) return <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">No trend data yet</div>;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="high" stroke="#ef4444" strokeWidth={2} dot={false} name="High" />
        <Line type="monotone" dataKey="medium" stroke="#f59e0b" strokeWidth={2} dot={false} name="Medium" />
        <Line type="monotone" dataKey="low" stroke="#3b82f6" strokeWidth={2} dot={false} name="Low" />
      </LineChart>
    </ResponsiveContainer>
  );
}
