import { createContext, useContext, useMemo, useState, useEffect, ReactNode } from "react";

export type ChannelOption = {
  value: string;
  label: string;
  supported: boolean;
};

const BASE_CHANNEL_OPTIONS: Omit<ChannelOption, "supported">[] = [
  { value: "smartstore", label: "SmartStore" },
  { value: "coupang", label: "Coupang" },
  { value: "gmarket", label: "Gmarket" },
];

const supportedLabelsFromEnv = (import.meta.env.VITE_SUPPORTED_CHANNEL_LABELS ?? "SmartStore")
  .split(",")
  .map((label) => label.trim().toLowerCase())
  .filter(Boolean);

const CHANNEL_OPTIONS: ChannelOption[] = BASE_CHANNEL_OPTIONS.map((option) => ({
  ...option,
  supported: supportedLabelsFromEnv.includes(option.label.toLowerCase()),
}));

type ChannelContextValue = {
  channel: ChannelOption;
  setChannelByValue: (value: string) => void;
  statusMessage: string;
  options: ChannelOption[];
};

const ChannelContext = createContext<ChannelContextValue | undefined>(undefined);

export function ChannelProvider({ children }: { children: ReactNode }) {
  const [channel, setChannel] = useState<ChannelOption>(CHANNEL_OPTIONS[0]);
  const [statusMessage, setStatusMessage] = useState(
    `현재 채널: ${CHANNEL_OPTIONS[0].label} (지원됨)`
  );

  useEffect(() => {
    setStatusMessage(`현재 채널: ${channel.label} (${channel.supported ? "지원됨" : "지원 예정"})`);
  }, [channel]);

  const setChannelByValue = (value: string) => {
    const next = CHANNEL_OPTIONS.find((option) => option.value === value);
    if (!next) {
      alert("아직 지원하지 않는 채널");
      setStatusMessage("지원되지 않는 채널입니다. SmartStore를 사용해주세요.");
      return;
    }

    setChannel(next);
    if (!next.supported) {
      alert("아직 지원하지 않는 채널");
    }
  };

  const value = useMemo(
    () => ({ channel, setChannelByValue, statusMessage, options: CHANNEL_OPTIONS }),
    [channel, statusMessage]
  );

  return <ChannelContext.Provider value={value}>{children}</ChannelContext.Provider>;
}

export function useChannel() {
  const ctx = useContext(ChannelContext);
  if (!ctx) {
    throw new Error("useChannel must be used within a ChannelProvider");
  }
  return ctx;
}

export const channelOptions = CHANNEL_OPTIONS;
