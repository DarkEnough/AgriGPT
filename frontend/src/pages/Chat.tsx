import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chatStore";
import { askChat } from "@/api/agriApi";

import ChatBubble from "@/components/ChatBubble";
import ChatInput from "@/components/ChatInput";
import Loader from "@/components/Loader";
import { toast } from "sonner";

const Chat = () => {
  const {
    messages,
    isLoading,
    addMessage,
    addImageMessage,
    setLoading,
    setError,
    clearChat
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  /** Smooth scroll to bottom */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /** Core send logic */
  const handleSend = async (text: string, image?: File) => {
    try {
      setLoading(true);
      setError(null);

      if (image) {
        // Add user image message safely
        addImageMessage(image);
      }

      // Add user text message (only if there is text)
      if (text.trim().length > 0) {
        addMessage({
          role: "user",
          content: text
        });
      }

      // Send to backend
      const response = await askChat(text, image);

      // Add assistant reply
      addMessage({
        role: "assistant",
        content: response.response,
        agent: response.agent
      });

      toast.success("Response received");

    } catch (error: any) {
      console.error("Chat error:", error);
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Failed to get response";

      setError(errorMessage);
      toast.error(errorMessage);

    } finally {
      setLoading(false);
    }
  };

  /** Clear chat + revoke object URLs */
  const handleClear = () => {
    clearChat();
    toast.success("Chat cleared");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Chat bubbles */}
      <div className="flex-1 overflow-y-auto bg-background p-4">
        <div className="max-w-4xl mx-auto">

          {messages.length === 0 ? (
            /* ---- Empty State ---- */
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4 py-12">
              <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-4xl">🌾</span>
              </div>

              <div>
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  Welcome to AgriGPT
                </h2>
                <p className="text-muted-foreground max-w-md">
                  Your intelligent farming assistant. Ask questions about crops,
                  pests, diseases, weather, or upload images for diagnosis.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-2xl mt-6">
                <div className="bg-card border border-border rounded-lg p-4 text-left">
                  <p className="text-sm font-medium mb-1">💬 Ask Questions</p>
                  <p className="text-xs text-muted-foreground">
                    Get expert advice on farming practices
                  </p>
                </div>

                <div className="bg-card border border-border rounded-lg p-4 text-left">
                  <p className="text-sm font-medium mb-1">📸 Upload Images</p>
                  <p className="text-xs text-muted-foreground">
                    Diagnose plant diseases and pests
                  </p>
                </div>

                <div className="bg-card border border-border rounded-lg p-4 text-left">
                  <p className="text-sm font-medium mb-1">🌱 Multimodal</p>
                  <p className="text-xs text-muted-foreground">
                    Combine text and images for better insights
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* ---- Messages Section ---- */
            <>
              {messages.map((msg) => (
                <ChatBubble key={msg.id} message={msg} />
              ))}

              {isLoading && <Loader message="AgriGPT is thinking..." />}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input area */}
      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        onClear={messages.length > 0 ? handleClear : undefined}
      />
    </div>
  );
};

export default Chat;
