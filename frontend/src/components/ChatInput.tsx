import { useState, useRef, KeyboardEvent, ChangeEvent } from "react";
import { Send, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

interface ChatInputProps {
  onSend: (text: string, image?: File) => void;
  isLoading: boolean;
  onClear?: () => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const ChatInput = ({ onSend, isLoading, onClear }: ChatInputProps) => {
  const [text, setText] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const validateImage = (file: File) => {
    if (!file.type.startsWith("image/")) {
      toast.error("Please select a valid image file");
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      toast.error("Image size must be less than 10MB");
      return false;
    }
    return true;
  };

  const handleImageSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!validateImage(file)) return;

    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const removeImage = () => {
    setImageFile(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);

    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSend = () => {
    const trimmed = text.trim();

    if (!trimmed && !imageFile) {
      toast.error("Please enter a message or select an image");
      return;
    }

    onSend(trimmed, imageFile || undefined);

    // Reset input
    setText("");
    removeImage();
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border bg-card p-4 shadow-lg">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Image preview */}
        {imagePreview && (
          <div className="relative inline-block">
            <img
              src={imagePreview}
              alt="Preview"
              className="max-h-32 rounded-lg border-2 border-primary shadow-md"
            />
            <Button
              type="button"
              size="icon"
              variant="destructive"
              onClick={removeImage}
              className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Input row */}
        <div className="flex gap-2 items-end">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />

          <Button
            type="button"
            size="icon"
            variant="outline"
            disabled={isLoading}
            onClick={() => fileInputRef.current?.click()}
            aria-label="Upload image"
          >
            <ImageIcon className="h-5 w-5" />
          </Button>

          <Textarea
            ref={textareaRef}
            value={text}
            disabled={isLoading}
            placeholder="Ask about crops, pests, weather, or upload an image..."
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 min-h-[60px] max-h-[200px] resize-none"
          />

          <Button
            type="button"
            size="icon"
            onClick={handleSend}
            disabled={isLoading || (!text.trim() && !imageFile)}
            className="h-[60px] w-[60px]"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </Button>

          {onClear && (
            <Button
              type="button"
              variant="outline"
              disabled={isLoading}
              onClick={onClear}
            >
              Clear
            </Button>
          )}
        </div>

        <p className="text-xs text-muted-foreground text-center">
          Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for new line
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
