import { UserIcon } from "@heroicons/react/24/outline";


const UserMessage = ({ message, index }) => {
  return (
    <div
      className="flex justify-end animate-fadeIn"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className="max-w-xs rounded-[1.5rem] bg-[linear-gradient(145deg,_#8b2328,_#631519)] px-4 py-3 text-white shadow-[0_14px_32px_rgba(139,35,40,0.22)] lg:max-w-md">
        <div className="flex items-start">
          <div className="flex-1">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
            <p className="text-[10px] text-white/70">
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
          <div className="ml-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10">
            <UserIcon className="h-4 w-4 text-white" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserMessage;
