import { AyurvedaLoader } from "@/components/ui/AyurvedaLoader";

export function PageLoading({ label }: { label?: string }) {
  return <AyurvedaLoader fullscreen label={label} />;
}
