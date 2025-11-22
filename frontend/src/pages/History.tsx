import { useChatStore } from "@/store/chatStore";
import { Card } from "@/components/ui/card";
import { format } from "date-fns";
import { MessageSquare, Image, Layers } from "lucide-react";

const History = () => {
  const { messages } = useChatStore();

  /** Returns only the user messages in chronological order */
  const userMessages = messages.filter((m) => m.role === "user");

  /** Detect message type: text, image, or multimodal */
  const getMessageType = (msg: typeof messages[0]) => {
    const hasText = msg.content && msg.content.trim() !== "";
    const hasImage = !!msg.imageUrl;

    if (hasText && hasImage)
      return { type: "Multimodal", icon: Layers, color: "text-accent" };

    if (hasImage)
      return { type: "Image", icon: Image, color: "text-primary" };

    return { type: "Text", icon: MessageSquare, color: "text-foreground" };
  };

  /** Given a user message, find the next assistant reply */
  const findAssistantReply = (userMsg: typeof messages[0]) => {
    return messages.find(
      (m) =>
        m.role === "assistant" &&
        new Date(m.timestamp).getTime() >
          new Date(userMsg.timestamp).getTime()
    );
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-background p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Title */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Chat History
          </h1>
          <p className="text-muted-foreground">
            View your past queries and interactions
          </p>
        </div>

        {/* Empty State */}
        {userMessages.length === 0 ? (
          <Card className="p-12 text-center">
            <div className="w-20 h-20 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-10 h-10 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              No history yet
            </h3>
            <p className="text-sm text-muted-foreground">
              Start a conversation to see your chat history here
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {userMessages.map((msg) => {
              const typeInfo = getMessageType(msg);
              const Icon = typeInfo.icon;

              const assistantReply = findAssistantReply(msg);

              return (
                <Card
                  key={msg.id}
                  className="p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex gap-4">
                    {/* Icon */}
                    <div className={`flex-shrink-0 ${typeInfo.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-muted-foreground">
                          {typeInfo.type}
                        </span>

                        {/* FIX: Proper timestamp formatting */}
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(msg.timestamp), "PPp")}
                        </span>
                      </div>

                      {/* User text */}
                      {msg.content && (
                        <p className="text-sm font-medium text-foreground mb-1 truncate">
                          {msg.content}
                        </p>
                      )}

                      {/* Assistant reply (preview) */}
                      {assistantReply && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {assistantReply.content}
                        </p>
                      )}

                      {/* User image */}
                      {msg.imageUrl && (
                        <img
                          src={msg.imageUrl}
                          alt="Uploaded query"
                          className="mt-2 max-h-24 rounded border border-border object-cover"
                        />
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default History;
