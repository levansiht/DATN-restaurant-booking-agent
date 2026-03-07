import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";


const Thinking = () => {
  return (
    <div className="flex justify-start">
      <div className="max-w-xs rounded-[1.5rem] border border-[#dfcfb7] bg-white px-4 py-3 text-[#211814] shadow-[0_10px_30px_rgba(50,34,26,0.08)]">
        <div className="flex items-center">
          <div className="mr-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[linear-gradient(145deg,_#8b2328,_#ba8a46)]">
            <ChatBubbleLeftRightIcon className="h-4 w-4 text-white" />
          </div>
          <div className="flex space-x-1">
            <div className="h-2 w-2 animate-bounce rounded-full bg-[#8b2328]"></div>
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-[#b78946]"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="h-2 w-2 animate-bounce rounded-full bg-[#8b2328]"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Thinking;
