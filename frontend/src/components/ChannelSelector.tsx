import { useEffect, useState } from "react";
import { useChannel } from "../ChannelContext";

type Props = {
  showStatus?: boolean;
};

export default function ChannelSelector({ showStatus = false }: Props) {
  const { channel, setChannelByValue, options, statusMessage } = useChannel();
  const [pending, setPending] = useState(channel.value);

  useEffect(() => {
    setPending(channel.value);
  }, [channel.value]);

  const handleApply = () => {
    setChannelByValue(pending);
  };

  return (
    <div className="flex flex-col gap-2 text-sm">
      <div className="flex items-center gap-2">
        <label className="text-slate-700" htmlFor="channel-select">
          채널 선택
        </label>
        <select
          id="channel-select"
          className="border rounded px-2 py-1"
          value={pending}
          onChange={(e) => setPending(e.target.value)}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
              {option.supported ? " (지원됨)" : " (지원 예정)"}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="px-3 py-1 rounded bg-slate-800 text-white"
          onClick={handleApply}
        >
          적용
        </button>
      </div>
      {showStatus && <div className="text-slate-600">{statusMessage}</div>}
    </div>
  );
}
