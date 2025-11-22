import { ChatMessage } from "@/store/chatStore";
import { User, Bot } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface ChatBubbleProps {
  message: ChatMessage;
}

const ChatBubble = ({ message }: ChatBubbleProps) => {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 mb-4 animate-fadeInSlide",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-primary" : "bg-accent"
        )}
      >
        {isUser ? (
          <User className="w-5 h-5 text-primary-foreground" />
        ) : (
          <Bot className="w-5 h-5 text-accent-foreground" />
        )}
      </div>

      {/* Message bubble */}
      <div
        className={cn(
          "flex flex-col max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 shadow-md whitespace-pre-wrap break-words",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-card text-card-foreground border border-border rounded-tl-sm"
          )}
        >
          {/* Image */}
          {message.imageUrl && (
            <img
              src={message.imageUrl}
              alt="Uploaded"
              className="max-w-full h-auto rounded-lg mb-2 border border-border"
            />
          )}

          {/* Text content with formatting */}
          <div className="space-y-1">
            {message.content.split("\n").map((line, i) => {
              const trimmed = line.trim();

              // Bullet list
              if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                return (
                  <div key={i} className="ml-3">
                    {line}
                  </div>
                );
              }

              // Section header (ends with :)
              if (trimmed.endsWith(":") && trimmed.length < 50) {
                return (
                  <div key={i} className="font-semibold mt-2">
                    {line}
                  </div>
                );
              }

              return <div key={i}>{line || "\u00A0"}</div>;
            })}
          </div>

          {/* Agent tag (assistant messages only) */}
          {message.agent && (
            <div className="text-xs mt-2 opacity-60">
              Agent: {message.agent}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            "text-xs text-muted-foreground mt-1",
            isUser ? "text-right" : "text-left"
          )}
        >
          {format(message.timestamp, "HH:mm")}
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
